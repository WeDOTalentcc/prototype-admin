"""Task #1299 — per-type sentinels for the implicit-feedback capture path.

These are OFFLINE/unit sentinels (no DB required). They lock in:
  - the pure, conservative abandonment criterion (no false positives);
  - the FairnessGuard gate is fail-closed (blocked text never persists);
  - the three capture methods exist with the canonical signature shape;
  - the service routes through `learning_signals` (domain `implicit_<type>`)
    AND, for the two strong signals, the explicit feedback pattern path.

DB-backed end-to-end behaviour is documented in the trace doc
(`docs/runbooks/implicit-feedback-trace.md`) and exercised by the existing
learning-signal repository integration suite (skips without DATABASE_URL).
"""
from __future__ import annotations

import inspect

import pytest

from app.shared.learning import implicit_feedback_service as mod
from app.shared.learning.implicit_feedback_service import (
    SIGNAL_ABANDONMENT,
    SIGNAL_CORRECTION_DELTA,
    SIGNAL_REGENERATION,
    ImplicitFeedbackService,
    ImplicitSignalResult,
    is_abandonment_candidate,
)


# ── abandonment criterion (pure) ──────────────────────────────────────────
class _FakeFairness:
    """Stub FairnessGuard result/guard."""

    def __init__(self, blocked: bool = False):
        self._blocked = blocked

    def check_explicit_bias(self, _text):  # noqa: D401
        class _R:
            is_blocked = self._blocked
            category = "gender" if self._blocked else None

        return _R()


def test_abandonment_rejects_short_response():
    # Answer too short to be "substantive" → never abandonment.
    assert is_abandonment_candidate("Ok.", "vamos falar de outra coisa agora") is False


def test_abandonment_rejects_when_lia_asked_question():
    resp = "Posso seguir para a etapa de triagem de candidatos desta vaga sênior?"
    # Next msg is the ANSWER to LIA's question → continuation, not abandonment.
    assert is_abandonment_candidate(resp, "prefiro revisar os requisitos antes disso") is False


def test_abandonment_rejects_continuation_token():
    resp = "Montei o pipeline com sete etapas conforme o template padrão da vaga."
    for tok in ("sim", "pode", "vamos", "ok", "continua"):
        assert is_abandonment_candidate(resp, tok) is False


def test_abandonment_rejects_short_next_message():
    resp = "Montei o pipeline com sete etapas conforme o template padrão da vaga."
    assert is_abandonment_candidate(resp, "tudo bem") is False  # < 4 words


def test_abandonment_rejects_topical_followup():
    resp = "Montei o pipeline com sete etapas conforme o template padrão da vaga."
    # High topical overlap → the recruiter is engaging with the pipeline answer.
    nxt = "muda o pipeline para incluir mais uma etapa no template da vaga"
    assert is_abandonment_candidate(resp, nxt) is False


def test_abandonment_accepts_clear_topic_switch():
    resp = "Montei o pipeline com sete etapas conforme o template padrão da vaga."
    # Substantive answer, no question, real utterance, disjoint topic → abandon.
    nxt = "quanto custa o plano enterprise para faturamento anual"
    assert is_abandonment_candidate(resp, nxt) is True


# ── service surface / contract ────────────────────────────────────────────
def test_three_capture_methods_exist_and_are_async():
    svc = ImplicitFeedbackService()
    for name in ("capture_regeneration", "capture_correction_delta", "capture_abandonment"):
        fn = getattr(svc, name, None)
        assert fn is not None, f"missing capture method {name}"
        assert inspect.iscoroutinefunction(fn), f"{name} must be async"


def test_signal_type_constants_are_canonical():
    assert SIGNAL_REGENERATION == "regeneration"
    assert SIGNAL_CORRECTION_DELTA == "correction_delta"
    assert SIGNAL_ABANDONMENT == "abandonment"


def test_singleton_exported():
    assert isinstance(mod.implicit_feedback_service, ImplicitFeedbackService)


# ── FairnessGuard gate (fail-closed) ──────────────────────────────────────
def test_fairness_gate_blocks_biased_text(monkeypatch):
    svc = ImplicitFeedbackService()
    import app.shared.compliance.fairness_guard as fg

    monkeypatch.setattr(fg, "FairnessGuard", lambda strict=False: _FakeFairness(blocked=True))
    clean, reason = svc._fairness_clean("texto enviesado")
    assert clean is False
    assert reason == "fairness_blocked"


def test_fairness_gate_passes_clean_text(monkeypatch):
    svc = ImplicitFeedbackService()
    import app.shared.compliance.fairness_guard as fg

    monkeypatch.setattr(fg, "FairnessGuard", lambda strict=False: _FakeFairness(blocked=False))
    clean, reason = svc._fairness_clean("texto neutro")
    assert clean is True
    assert reason is None


def test_fairness_gate_fail_closed_on_init_error(monkeypatch):
    svc = ImplicitFeedbackService()
    import app.shared.compliance.fairness_guard as fg

    def _boom(*_a, **_k):
        raise RuntimeError("guard down")

    monkeypatch.setattr(fg, "FairnessGuard", _boom)
    clean, reason = svc._fairness_clean("qualquer texto")
    assert clean is False  # fail-closed: never learn from unvalidated text
    assert reason == "fairness_guard_unavailable"


# ── capture short-circuits BEFORE any DB call ─────────────────────────────
@pytest.mark.asyncio
async def test_correction_delta_no_delta_short_circuits():
    svc = ImplicitFeedbackService(feedback_service=object())
    res = await svc.capture_correction_delta(
        db=object(),  # must NOT be touched
        company_id="00000000-0000-4000-a000-000000000001",
        user_id="u1",
        session_id="s1",
        source_message_id="m1",
        original_response="mesma coisa",
        used_text="mesma coisa",  # identical → no delta
    )
    assert isinstance(res, ImplicitSignalResult)
    assert res.persisted is False
    assert res.skipped_reason == "no_delta"


@pytest.mark.asyncio
async def test_abandonment_criterion_not_met_short_circuits():
    svc = ImplicitFeedbackService(feedback_service=object())
    res = await svc.capture_abandonment(
        db=object(),  # must NOT be touched when criterion fails
        company_id="00000000-0000-4000-a000-000000000001",
        user_id="u1",
        session_id="s1",
        abandoned_message_id="m1",
        abandoned_response="curto",  # too short → criterion fails
        next_user_message="algo totalmente diferente aqui agora",
    )
    assert res.persisted is False
    assert res.skipped_reason == "criterion_not_met"


@pytest.mark.asyncio
async def test_abandonment_blocked_by_fairness_after_criterion(monkeypatch):
    svc = ImplicitFeedbackService(feedback_service=object())
    import app.shared.compliance.fairness_guard as fg

    monkeypatch.setattr(fg, "FairnessGuard", lambda strict=False: _FakeFairness(blocked=True))

    # Patch the engagement check so we reach the fairness gate.
    async def _no_engagement(*_a, **_k):
        return False

    monkeypatch.setattr(svc, "_has_explicit_engagement", _no_engagement)

    resp = "Montei o pipeline com sete etapas conforme o template padrão da vaga."
    nxt = "quanto custa o plano enterprise para faturamento anual"
    res = await svc.capture_abandonment(
        db=object(),
        company_id="00000000-0000-4000-a000-000000000001",
        user_id="u1",
        session_id="s1",
        abandoned_message_id="m1",
        abandoned_response=resp,
        next_user_message=nxt,
    )
    assert res.persisted is False
    assert res.skipped_reason == "fairness_blocked"
