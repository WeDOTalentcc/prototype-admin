"""Pure mapping: PlanExecutor progress events → WS frame status/progress/label.

Single source of truth for translating the internal progress events emitted by
``PlanExecutor`` (via ``progress_callback``) into the ``background_task_update``
status + a 0-100 progress integer consumed by the chat UI.

Canonical event names are PRODUCED by ``PlanExecutor`` in
``app/shared/execution/plan_executor.py``: ``plan_started``, ``step_running``,
``step_completed``, ``step_skipped``, ``plan_completed``. Consumers MUST align to
these names — never the reverse (canonical-fix: fix the consumer, the producer
names are authoritative).

Historical bug (fixed 2026-06-03): the WS consumer ``_ws_plan_progress`` compared
``event_type`` against ``"plan_complete"``/``"plan_error"`` — names the producer
NEVER emits — so the derived status was permanently ``"running"`` and ``progress``
was permanently ``0``. This module + ``tests/contract/test_plan_progress_contract.py``
pin the contract so the mismatch cannot return.
"""
from __future__ import annotations

from typing import Any

# ── Canonical event names emitted by PlanExecutor._emit(...) ───────────────────
# Pinned against the source by tests/contract/test_plan_progress_contract.py.
PLAN_STARTED = "plan_started"
STEP_RUNNING = "step_running"
STEP_COMPLETED = "step_completed"
STEP_SKIPPED = "step_skipped"
PLAN_COMPLETED = "plan_completed"

PLAN_PROGRESS_EVENTS = frozenset(
    {PLAN_STARTED, STEP_RUNNING, STEP_COMPLETED, STEP_SKIPPED, PLAN_COMPLETED}
)

# Terminal plan statuses (plan.status.value) that map to a failed WS status.
_FAILED_PLAN_STATUSES = {"failed"}


def new_plan_progress_state() -> dict[str, int]:
    """Create the mutable counter the mapper threads across an event stream."""
    return {"total": 0, "done": 0}


def map_plan_event(
    event_type: str,
    data: dict[str, Any],
    state: dict[str, int],
) -> dict[str, Any]:
    """Translate one PlanExecutor progress event into WS frame fields.

    Mutates ``state`` (``total``/``done`` counters) so ``progress`` is monotonic
    across the event stream. Returns ``{"status", "progress", "label"}``.

    - ``plan_started`` resets the counters from ``total_tasks``.
    - ``step_completed`` / ``step_skipped`` advance the done counter.
    - ``plan_completed`` forces ``progress=100`` and derives terminal status from
      the producer-supplied ``data["status"]`` (plan.status.value).
    - every other event is ``status="running"`` with progress = done/total.
    """
    if event_type == PLAN_STARTED:
        state["total"] = int(data.get("total_tasks") or 0)
        state["done"] = 0
    elif event_type in (STEP_COMPLETED, STEP_SKIPPED):
        state["done"] = state.get("done", 0) + 1

    total = state.get("total") or 0
    done = state.get("done", 0)

    if event_type == PLAN_COMPLETED:
        progress = 100
        status = (
            "failed"
            if str(data.get("status")) in _FAILED_PLAN_STATUSES
            else "completed"
        )
    else:
        progress = round(done / total * 100) if total > 0 else 0
        status = "running"

    label = data.get("label") or data.get("pattern") or "Plano multi-step"
    return {"status": status, "progress": progress, "label": label}
