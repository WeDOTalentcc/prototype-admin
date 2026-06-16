"""Orchestrator-level e2e — post-wizard create-then-publish continuity (Task #1216).

The park → offer → confirm → execute lifecycle has fast unit coverage using an
in-memory fake store (``tests/unit/orchestrator/routing/test_post_wizard_continuation.py``).
What those unit tests CANNOT catch are the orchestrator wiring regressions:

  • phase ordering — the dedicated continuation handler runs BEFORE Phase 0;
  • job_id binding — the freshly-created job_id flows from the wizard's
    ``ws_stage_payload`` into the parked continuation and then into the dispatch;
  • offer surfacing — ``build_offer_message`` is appended to the wizard's terminal
    reply only when a composite continuation was parked at bootstrap;
  • dispatch wiring — a "yes" confirmation builds a Plan & Execute task bound to
    the created job (``ats_integration.sync_job`` with ``job_id``), never a job
    *creation* step.

This drives a REAL composite request ("criar a vaga e publicar no ATS") through
``MainOrchestrator._try_wizard_canonical`` (real continuation store + real
detection), then a REAL PT-BR confirmation through
``_handle_post_wizard_continuation`` (real classifier + real dispatch_for).
Only the wizard LangGraph session (``WizardSessionService``) and the external
ATS executor (``PlanExecutor``) are mocked — everything in between is the
production code path.

Run: pytest tests/integration/orchestrator/test_post_wizard_continuation_e2e_t1216.py \
     -o addopts="" -p no:cov -v
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.orchestrator.context.context_adapter import UniversalContext
from app.orchestrator.execution.main_orchestrator import MainOrchestrator
from app.orchestrator.routing.post_wizard_continuation import (
    clear_continuation,
    get_continuation,
)

CONV_ID = "conv-e2e-T1216"
COMPANY_ID = "00000000-0000-4000-a000-000000000001"
JOB_ID = "job-777"


def _ctx(message: str) -> UniversalContext:
    ctx = UniversalContext(
        message=message,
        user_id="user-demo",
        company_id=COMPANY_ID,
        conversation_id=CONV_ID,
    )
    ctx.skip_memory_persist = True
    return ctx


@pytest.fixture
def orch() -> MainOrchestrator:
    return MainOrchestrator(orchestrator=MagicMock())


@pytest.fixture(autouse=True)
def _clean_store():
    """The orchestrator uses the global pending_action_store — isolate per test."""
    clear_continuation(CONV_ID)
    yield
    clear_continuation(CONV_ID)


def _patch_wizard(stage: str, *, active: bool, payload_extra: dict | None = None):
    """Patch WizardSessionService for one wizard turn.

    ``active`` mirrors the handler-level wizard pin (turno ≥2). The returned
    ``ws_stage_payload`` carries ``stage`` and, for terminal stages, the
    freshly-created job id so the offer can bind it.
    """
    payload = {"stage": stage}
    if payload_extra:
        payload.update(payload_extra)
    WSS = patch(
        "app.domains.job_creation.services.wizard_session_service.WizardSessionService"
    ).start()
    WSS.is_session_active = AsyncMock(return_value=active)
    WSS.derive_thread_id = MagicMock(return_value="wiz-thread-T1216")
    WSS.process_message = AsyncMock(
        return_value=(f"[wizard:{stage}]", payload, 0)
    )
    return WSS


async def _drive_wizard_to_offer(orch: MainOrchestrator) -> "object":
    """Run the composite request through bootstrap → terminal stage.

    Returns the wizard ChatResponse for the terminal turn (the one carrying the
    surfaced offer).
    """
    # Turno 1 — bootstrap. Composite "criar a vaga e publicar no ATS" parks the
    # continuation; wizard is still mid-flow (intake), so no offer yet.
    wss = _patch_wizard("intake", active=False)
    try:
        boot = await orch._try_wizard_canonical(
            ctx=_ctx("criar a vaga e publicar no ATS"),
            conv_id=CONV_ID,
            conv=None,
            db=None,
        )
    finally:
        patch.stopall()

    assert boot is not None, "turno 1 deve disparar o wizard"
    parked = get_continuation(CONV_ID)
    assert parked is not None, "continuation deve ser estacionada no bootstrap"
    assert parked.awaiting_confirmation is False, "ainda não foi oferecida"
    assert parked.collected_params["continuation_kind"] == "publish_job"
    assert parked.collected_params["job_id"] is None, "job ainda não existe"

    # Turno 2 — wizard chega ao stage terminal e devolve o job criado.
    _patch_wizard(
        "done", active=True, payload_extra={"job_vacancy_id": JOB_ID}
    )
    try:
        done = await orch._try_wizard_canonical(
            ctx=_ctx("pode finalizar a vaga"),
            conv_id=CONV_ID,
            conv=None,
            db=None,
        )
    finally:
        patch.stopall()
    return done


@pytest.mark.asyncio
async def test_create_then_publish_offer_then_confirm_executes_bound_to_job(orch):
    """Happy path: composite request → offer surfaces → 'pode publicar' executes."""
    done = await _drive_wizard_to_offer(orch)

    # ── Offer surfaced, bound to the created job ──────────────────────────────
    assert done is not None
    assert "publicar a vaga no ATS" in done.content, (
        "a oferta de continuidade deve aparecer no texto do wizard terminal"
    )
    offered = get_continuation(CONV_ID)
    assert offered is not None
    assert offered.awaiting_confirmation is True, "agora aguarda confirmação"
    assert offered.collected_params["job_id"] == JOB_ID, "job_id deve estar vinculado"

    # ── Confirmation turn — 'pode publicar' → execute via Plan & Execute ──────
    captured: dict = {}

    fake_completed = MagicMock()
    fake_completed.plan_id = f"continuation_{CONV_ID}"
    fake_completed.detected_pattern = "post_wizard_publish_job"
    fake_completed.status = MagicMock(value="completed")

    async def _fake_execute(plan, **kwargs):
        captured["plan"] = plan
        captured["kwargs"] = kwargs
        return fake_completed

    fake_executor = MagicMock()
    fake_executor.execute = AsyncMock(side_effect=_fake_execute)
    fake_executor.build_consolidated_response = MagicMock(
        return_value=MagicMock(message="Vaga publicada no ATS com sucesso.")
    )

    with patch(
        "app.shared.execution.plan_executor.PlanExecutor",
        return_value=fake_executor,
    ):
        resp = await orch._handle_post_wizard_continuation(
            ctx=_ctx("pode publicar"),
            conv_id=CONV_ID,
            db=None,
            conv=None,
        )

    # ── The publish/sync path ran, bound to the created job_id ────────────────
    assert resp is not None
    assert resp.intent_detected == "continuation_executed"
    assert resp.action_executed is True
    assert resp.content == "Vaga publicada no ATS com sucesso."
    assert resp.structured_data["job_id"] == JOB_ID
    assert resp.structured_data["continuation_kind"] == "publish_job"

    fake_executor.execute.assert_awaited_once()
    plan = captured["plan"]
    assert len(plan.tasks) == 1
    task = plan.tasks[0]
    assert task.domain_id == "ats_integration", "deve despachar para o ATS"
    assert task.action_id == "sync_job", "deve sincronizar/publicar, nunca criar vaga"
    assert task.params.get("job_id") == JOB_ID, "task vinculada ao job criado"
    assert captured["kwargs"].get("base_context") == {"job_id": JOB_ID}
    assert captured["kwargs"].get("tenant_id") == COMPANY_ID

    # Continuation consumed — a second confirmation finds nothing pending.
    assert get_continuation(CONV_ID) is None


@pytest.mark.asyncio
async def test_create_then_publish_offer_then_decline_executes_nothing(orch):
    """Negative path: 'agora não' cancels cleanly and nothing is executed."""
    await _drive_wizard_to_offer(orch)
    offered = get_continuation(CONV_ID)
    assert offered is not None and offered.awaiting_confirmation is True

    with patch(
        "app.shared.execution.plan_executor.PlanExecutor"
    ) as PlanExecutorCls:
        resp = await orch._handle_post_wizard_continuation(
            ctx=_ctx("agora não"),
            conv_id=CONV_ID,
            db=None,
            conv=None,
        )

    assert resp is not None
    assert resp.intent_detected == "continuation_declined"
    assert resp.action_executed is False
    # No executor was ever constructed — nothing dispatched.
    PlanExecutorCls.assert_not_called()
    # Continuation dropped — declining clears the parked offer.
    assert get_continuation(CONV_ID) is None


@pytest.mark.asyncio
async def test_confirmation_before_offer_is_a_noop(orch):
    """Guard: a confirmation with no offered continuation returns None (no-op).

    Proves the handler does not fire on a parked-but-not-yet-offered state, so a
    stray "pode publicar" mid-wizard never short-circuits the flow.
    """
    # Park only (bootstrap), do NOT reach a terminal stage / mark_offered.
    wss = _patch_wizard("intake", active=False)
    try:
        await orch._try_wizard_canonical(
            ctx=_ctx("criar a vaga e publicar no ATS"),
            conv_id=CONV_ID,
            conv=None,
            db=None,
        )
    finally:
        patch.stopall()

    parked = get_continuation(CONV_ID)
    assert parked is not None and parked.awaiting_confirmation is False

    resp = await orch._handle_post_wizard_continuation(
        ctx=_ctx("pode publicar"),
        conv_id=CONV_ID,
        db=None,
        conv=None,
    )
    assert resp is None, "sem oferta ativa, o handler não deve agir"
    # Parked continuation untouched.
    assert get_continuation(CONV_ID) is not None
