"""Sprint F.2 (2026-05-20) — Sensor: supervisor classifier MUST be SKIPPED
when checkpoint state carries an active wizard stage.

Canonical fix (Option A): when ``prior_state.current_stage`` is one of
the 8 active wizard stages, the pre-graph supervisor classifier is
bypassed and the JobCreationGraph is invoked directly (via
``Command(resume=user_message)`` when interrupted, otherwise via fresh
invoke). Short HITL responses like "modo compacto", "aprovado", "ok"
must never be re-classified mid-flow.

Bug history: turn 5 of the JD wizard E2E sent "modo compacto, 7 perguntas"
while the graph was paused at the competency_gate. Without this skip,
the supervisor (with no conversation_history in the REST payload) saw a
context-less short message, classified it as ``create_new`` or returned
a "mensagem cortada" fallback, and the graph was never resumed — the
wizard regressed to intake.

This sensor parametrizes across all 8 active stages and across multiple
short HITL replies. It mocks ``_run_supervisor`` to assert it is NOT
called when the skip condition holds, and asserts the supervisor IS
called for ``intake`` / terminal stages (where re-classification is
safe). It also asserts skip honors the canonical stage set verbatim —
adding a new stage to ``WizardStage`` without updating the skip set
would trigger this sensor.
"""
from __future__ import annotations

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


ACTIVE_STAGES = (
    # PR-15 (2026-05-26): "intake" + "pipeline_template" added to canonical
    # _ACTIVE_WIZARD_STAGES (PR-1 of the wizard fixes plan). Supervisor must
    # SKIP for short HITL replies during these stages too.
    "intake", "jd_enrichment", "pipeline_template",
    "bigfive", "salary", "competency",
    "wsi_questions", "eligibility", "review", "publish",
)
# PR-15: "intake" removed from NON_ACTIVE — it is now an active stage.
# Re-classification-safe stages remain: calibration / handoff / done /
# None (no prior stage at all).
NON_ACTIVE_STAGES = ("calibration", "handoff", "done", None)
HITL_REPLIES = (
    "modo compacto, 7 perguntas",
    "aprovado",
    "ok",
    "sim",
    "modo full",
)


def _enable_supervisor_env(monkeypatch):
    """Make sure supervisor would normally run (flag ON, fake API key)."""
    monkeypatch.setenv("LIA_WIZARD_SUPERVISOR_CLASSIFIER", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-used")
    monkeypatch.delenv("AI_INTEGRATIONS_ANTHROPIC_API_KEY", raising=False)
    # Fase 8: default flipped to orchestrator ON. Force graph legado path.
    monkeypatch.setenv("LIA_WIZARD_ORCHESTRATOR", "0")


async def _drive(monkeypatch, *, prior_stage, user_message):
    """Invoke the session service path that decides supervisor skip.

    Returns ``(supervisor_called_count, graph_invoked)`` — the booleans
    the sensor asserts against. Mocks every collaborator so no LLM,
    DB, or LangGraph runtime actually runs.
    """
    _enable_supervisor_env(monkeypatch)

    from app.domains.job_creation.services import (
        wizard_session_service as wss_mod,
    )
    WSS = wss_mod.WizardSessionService
    WSS._dotenv_cache = {}

    # Fake prior_state with the target stage (mid-flow if active).
    prior_state = (
        {"current_stage": prior_stage, "conversation_messages": []}
        if prior_stage is not None
        else {}
    )

    # Counters / spies.
    supervisor_spy = AsyncMock(return_value={"intent": "continue_current", "short_circuit": False})
    aresume_spy = AsyncMock(return_value={"messages": [], "current_stage": prior_stage or "intake"})
    is_interrupted_spy = MagicMock(return_value=True)
    post_process_spy = AsyncMock(return_value=("reply", {}, 0))
    fake_graph = MagicMock()
    fake_graph.is_interrupted = is_interrupted_spy
    fake_graph.aresume_with_message = aresume_spy

    # Patch the symbols WSS reaches into.
    monkeypatch.setattr(
        WSS, "_get_prior_state",
        AsyncMock(return_value=prior_state),
    )
    monkeypatch.setattr(WSS, "_run_supervisor", supervisor_spy)
    monkeypatch.setattr(WSS, "_post_process_result", post_process_spy)

    # get_job_creation_graph() must return our fake.
    monkeypatch.setattr(
        "app.domains.job_creation.graph.get_job_creation_graph",
        lambda: fake_graph,
    )

    await WSS.process_message(
        thread_id="thr-test",
        user_message=user_message,
        user_id="user-test",
        company_id="company-test",
        session_id="sess-test",
        context={},
    )
    return supervisor_spy.await_count, aresume_spy.await_count


@pytest.mark.asyncio
@pytest.mark.parametrize("stage", ACTIVE_STAGES)
@pytest.mark.parametrize("reply", HITL_REPLIES)
async def test_supervisor_SKIPPED_when_active_stage(monkeypatch, stage, reply):
    """Sprint F.2 canonical fix: short HITL replies during an active
    wizard stage MUST NOT re-trigger the supervisor classifier. The
    graph resume path must run directly."""
    sup_calls, resume_calls = await _drive(
        monkeypatch, prior_stage=stage, user_message=reply,
    )
    assert sup_calls == 0, (
        f"supervisor was called {sup_calls}x for stage={stage!r} "
        f"reply={reply!r} — Sprint F.2 fix regressed; mid-flow "
        f"re-classification will lose HITL gate responses and "
        f"regress the wizard."
    )
    assert resume_calls == 1, (
        f"graph aresume_with_message must be invoked exactly once for "
        f"stage={stage!r}, got {resume_calls}."
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("stage", NON_ACTIVE_STAGES)
async def test_supervisor_RUNS_when_not_active_stage(monkeypatch, stage):
    """When there is no prior state OR the stage is intake / terminal,
    the supervisor still runs — it is the canonical detector of
    meta_question / exit_wizard before/after the wizard proper."""
    sup_calls, _ = await _drive(
        monkeypatch, prior_stage=stage, user_message="quero abrir uma vaga nova",
    )
    assert sup_calls == 1, (
        f"supervisor should run for stage={stage!r} (non-active) — "
        f"got {sup_calls} calls. Skipping here would lose the ability "
        f"to detect create_new / meta_question / exit_wizard pre-flow."
    )


def test_active_stage_set_matches_wizardstage_literal_minus_safe():
    """Defense-in-depth: if someone adds a new stage to ``WizardStage``
    without updating ``_ACTIVE_WIZARD_STAGES`` in
    ``wizard_session_service.py``, this sensor flags it loudly.

    The active set is the canonical WizardStage Literal MINUS the
    re-classification-safe stages (intake + terminals)."""
    import re
    from pathlib import Path

    src = Path(
        "app/domains/job_creation/services/wizard_session_service.py"
    ).read_text(encoding="utf-8")
    m = re.search(
        r"_ACTIVE_WIZARD_STAGES\s*=\s*frozenset\(\{([^}]+)\}\)",
        src,
        re.DOTALL,
    )
    assert m, "Could not locate _ACTIVE_WIZARD_STAGES in session service"
    declared = frozenset(
        s.strip().strip('"').strip("'")
        for s in m.group(1).replace("\n", ",").split(",")
        if s.strip().strip('"').strip("'")
    )

    # Canonical WizardStage Literal from app/domains/job_creation/state.py
    # (kept in sync with this test by the test_active_stage_set sentinel).
    # PR-15 (2026-05-26): "intake" + "pipeline_template" added — PR-1 of
    # the wizard fixes plan extended _ACTIVE_WIZARD_STAGES to skip the
    # supervisor classifier on short HITL replies during these stages
    # too. Re-classification-safe set remains: calibration / handoff /
    # done (terminals).
    canonical_active = frozenset({
        "intake", "jd_enrichment", "pipeline_template",
        "bigfive", "salary", "competency",
        "wsi_questions", "eligibility", "review", "publish",
    })
    assert declared == canonical_active, (
        f"_ACTIVE_WIZARD_STAGES drift: declared={sorted(declared)} "
        f"expected={sorted(canonical_active)}. If WizardStage Literal "
        f"changed, update both the set AND this sensor."
    )
