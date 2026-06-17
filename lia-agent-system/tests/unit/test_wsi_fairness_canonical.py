"""Consolidacao WSI Fase 2.3: FairnessGuard portado para o canonico cv_screening.

Pina o contrato de fairness (pre-check + L4 drop + audit) no produtor canonico,
de forma que Settings (endpoint) E o wizard conversacional herdem o mesmo filtro.
Testes puros: monkeypatcham o helper _wsi_fairness_check (sem LLM, sem guard real).
"""
from dataclasses import dataclass

import pytest

from app.domains.cv_screening.services.wsi_service import service as svc_mod
from app.domains.cv_screening.services.wsi_service.models import WSIQuestion


@dataclass
class _FakeRes:
    is_blocked: bool
    category: str | None = None
    blocked_terms: list | None = None
    educational_message: str | None = None


def _q(text, qid="q1"):
    return WSIQuestion(
        id=qid, competency="X", framework="CBI", question_type="contextual",
        question_text=text, weight=0.9, expected_signals=["a"], scoring_criteria={},
    )


@pytest.mark.medium
def test_l4_drops_blocked_and_collects_audit(monkeypatch):
    svc = svc_mod.WSIService()

    def fake_check(text):
        return _FakeRes(is_blocked="VIES" in text, category="gender",
                        blocked_terms=["VIES"], educational_message="nope")
    monkeypatch.setattr(svc_mod, "_wsi_fairness_check", fake_check)

    dropped = []
    kept = svc._apply_fairness_l4(
        [_q("pergunta limpa", "a"), _q("pergunta com VIES", "b"), _q("outra limpa", "c")],
        collect_dropped=dropped,
    )
    assert [k.id for k in kept] == ["a", "c"]
    assert len(dropped) == 1
    assert dropped[0]["category"] == "gender"
    assert dropped[0]["blocked_terms"] == ["VIES"]


@pytest.mark.medium
def test_l4_fail_open_keeps_all_when_guard_unavailable(monkeypatch):
    svc = svc_mod.WSIService()
    monkeypatch.setattr(svc_mod, "_wsi_fairness_check", lambda text: None)  # guard indisponivel
    kept = svc._apply_fairness_l4([_q("a", "a"), _q("b", "b")])
    assert len(kept) == 2


@pytest.mark.medium
@pytest.mark.asyncio
async def test_suggest_single_pre_block_skips_llm(monkeypatch):
    svc = svc_mod.WSIService()
    monkeypatch.setattr(svc_mod, "_wsi_fairness_check",
                        lambda text: _FakeRes(is_blocked=True, category="age"))

    called = {"llm": False}

    async def _boom(*a, **k):
        called["llm"] = True
        return "{}"
    monkeypatch.setattr(svc.llm, "safe_invoke", _boom)

    res = await svc.suggest_single_question(prompt="apenas homens jovens", block_id=3)
    assert res["success"] is False
    assert res["blocked_category"] == "age"
    assert called["llm"] is False  # nao chamou LLM


@pytest.mark.medium
@pytest.mark.asyncio
async def test_suggest_single_l4_blocks_generated_question(monkeypatch):
    svc = svc_mod.WSIService()

    # prompt passa; pergunta gerada e' bloqueada
    def fake_check(text):
        return _FakeRes(is_blocked=("VIES" in text), category="gender")
    monkeypatch.setattr(svc_mod, "_wsi_fairness_check", fake_check)

    async def _fake_llm(*a, **k):
        return '{"question": "pergunta com VIES", "type": "classificatory"}'
    monkeypatch.setattr(svc.llm, "safe_invoke", _fake_llm)

    res = await svc.suggest_single_question(prompt="ok limpo", block_id=3)
    assert res["success"] is False
    assert res["blocked_category"] == "gender"


@pytest.mark.medium
@pytest.mark.asyncio
async def test_suggest_single_happy_path_passes_guard(monkeypatch):
    svc = svc_mod.WSIService()
    monkeypatch.setattr(svc_mod, "_wsi_fairness_check", lambda text: _FakeRes(is_blocked=False))

    async def _fake_llm(*a, **k):
        return '{"question": "Conte sobre sua experiencia com X", "type": "classificatory", "category": "technical"}'
    monkeypatch.setattr(svc.llm, "safe_invoke", _fake_llm)

    res = await svc.suggest_single_question(prompt="experiencia com X", block_id=3)
    assert res["success"] is True
    assert "experiencia" in res["question"].lower()
