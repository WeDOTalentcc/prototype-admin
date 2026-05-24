"""Sprint 1.2 (F) — Phase 1 MUST persist pending when emitting needs_confirmation.

Bug: `main_orchestrator._try_action_executor` returns ChatResponse with
needs_confirmation=True, relying on the stale comment
    # PendingActionStore já foi atualizado pelo ActionExecutor
But `action_executor.try_execute` only creates `ActionResult(needs_confirmation, ...)`
— it never calls `pending_action_store.save()`. Result: next turn, Phase 0 sees
empty store, returns None, Phase 1 retries on "sim" → duplicate confirmation
(N5) or "mensagem incompleta" (N4 collateral).

Canonical fix: persist a `PendingActionState` to the store at the Phase 1
boundary, so Phase 0 can pick up the next user message ("sim"/"não"/param).
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.orchestrator.action_executor.action_types import ActionResult
from app.orchestrator.execution.main_orchestrator import MainOrchestrator
from app.orchestrator.execution.pending_action import pending_action_store


@pytest.fixture(autouse=True)
def _clean_store():
    """Ensure store is empty before each test."""
    pending_action_store.remove("test-conv-F")
    yield
    pending_action_store.remove("test-conv-F")


def _make_ctx(message: str):
    ctx = MagicMock()
    ctx.message = message
    ctx.candidates = []
    ctx.selected_candidate_ids = []
    ctx.job_context = None
    ctx.user_id = "test-user"
    ctx.company_id = "test-company-uuid"
    ctx.extra = {}
    return ctx


@pytest.mark.asyncio
async def test_try_action_executor_persists_pending_on_needs_confirmation():
    """RED: when Phase 1 emits needs_confirmation, store MUST have the entry
    so next-turn 'sim' is caught by Phase 0.
    """
    orch = MainOrchestrator.__new__(MainOrchestrator)
    ctx = _make_ctx("criar vaga assistente comercial")

    fake_result = ActionResult(
        status="needs_confirmation",
        message="Vou criar a vaga **Assistente Comercial**. Confirma?",
        action_type="create_job",
        pending_action_id="test-pending-uuid-001",
        confirmation_summary={
            "message": "Vou criar a vaga. Confirma?",
            "action_id": "create_job",
            "intent": "create_job",
            "params": {"job_title": "Assistente Comercial"},
        },
        data={
            "collected_params": {"job_title": "Assistente Comercial"},
            "intent": "create_job",
        },
    )

    with patch(
        "app.orchestrator.execution.main_orchestrator.action_executor.try_execute",
        new=AsyncMock(return_value=fake_result),
    ):
        response = await orch._try_action_executor(ctx, "test-conv-F")

    assert response is not None, "Phase 1 returned None when it should have emitted confirmation"
    assert response.needs_confirmation is True

    # CRITICAL F ASSERTION: store MUST have the pending entry now.
    stored = pending_action_store.get("test-conv-F")
    assert stored is not None, (
        "Phase 1 emitted needs_confirmation but pending_action_store is empty. "
        "Next-turn 'sim' will fall through Phase 0 and trigger duplicate confirmation "
        "or 'mensagem incompleta' (N4 collateral)."
    )
    assert stored.intent == "create_job"
    assert stored.awaiting_confirmation is True
    assert stored.collected_params.get("job_title") == "Assistente Comercial"


@pytest.mark.asyncio
async def test_try_action_executor_persists_pending_on_needs_params():
    """RED: same canonical fix for needs_params (multi-turn param collection)."""
    orch = MainOrchestrator.__new__(MainOrchestrator)
    ctx = _make_ctx("mover candidato")

    fake_result = ActionResult(
        status="needs_params",
        message="Para qual etapa devo mover?",
        action_type="move_candidate",
        pending_action_id="test-pending-uuid-002",
        missing_params=["to_stage"],
        data={
            "collected_params": {"candidate_id": "cand-1"},
            "intent": "move_candidate",
        },
    )

    with patch(
        "app.orchestrator.execution.main_orchestrator.action_executor.try_execute",
        new=AsyncMock(return_value=fake_result),
    ):
        response = await orch._try_action_executor(ctx, "test-conv-F")

    assert response is not None
    stored = pending_action_store.get("test-conv-F")
    assert stored is not None, (
        "Phase 1 emitted needs_params but pending_action_store is empty. "
        "Next-turn param value will fall through Phase 0."
    )
    assert stored.intent == "move_candidate"
    assert stored.missing_params == ["to_stage"]
    assert stored.collected_params.get("candidate_id") == "cand-1"
    # needs_params != awaiting_confirmation
    assert stored.awaiting_confirmation is False


@pytest.mark.asyncio
async def test_try_action_executor_no_save_on_executed():
    """Defense: when status='executed', no pending should be stored (action is done)."""
    orch = MainOrchestrator.__new__(MainOrchestrator)
    ctx = _make_ctx("listar minhas vagas")

    fake_result = ActionResult(
        status="executed",
        message="3 vagas encontradas",
        action_type="list_jobs",
        data={"jobs": []},
    )

    with patch(
        "app.orchestrator.execution.main_orchestrator.action_executor.try_execute",
        new=AsyncMock(return_value=fake_result),
    ):
        await orch._try_action_executor(ctx, "test-conv-F")

    stored = pending_action_store.get("test-conv-F")
    assert stored is None, "executed action should not create a pending entry"


@pytest.mark.asyncio
async def test_try_action_executor_no_save_on_not_actionable():
    """Defense: when status='not_actionable', no pending."""
    orch = MainOrchestrator.__new__(MainOrchestrator)
    ctx = _make_ctx("oi")

    fake_result = ActionResult(status="not_actionable")

    with patch(
        "app.orchestrator.execution.main_orchestrator.action_executor.try_execute",
        new=AsyncMock(return_value=fake_result),
    ):
        response = await orch._try_action_executor(ctx, "test-conv-F")

    assert response is None, "not_actionable should return None to fall through to Phase 1.5+"
    stored = pending_action_store.get("test-conv-F")
    assert stored is None
