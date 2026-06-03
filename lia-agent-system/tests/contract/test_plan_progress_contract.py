"""Contract sensor: PlanExecutor progress events ↔ WS plan_progress mapping.

Pins the event-name contract between the PRODUCER (``PlanExecutor._emit``) and the
CONSUMER mapping (``plan_progress_mapper``). Guards against the 2026-06-03 stale-
contract bug where the WS consumer checked ``plan_complete``/``plan_error`` —
names the producer never emits — leaving status stuck on ``running`` and
``progress`` stuck on ``0``.

Computational sensor (no LLM). If it fails, the message tells the agent exactly
what to change.
"""
from __future__ import annotations

import re
from pathlib import Path

from app.shared.execution.plan_progress_mapper import (
    PLAN_PROGRESS_EVENTS,
    map_plan_event,
    new_plan_progress_state,
)

_PLAN_EXECUTOR = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "shared"
    / "execution"
    / "plan_executor.py"
)


def _emitted_event_names() -> set[str]:
    src = _PLAN_EXECUTOR.read_text(encoding="utf-8")
    return set(re.findall(r'_emit\(\s*progress_callback,\s*"([^"]+)"', src))


def test_every_producer_event_is_handled_by_mapper() -> None:
    emitted = _emitted_event_names()
    assert emitted, (
        "Regex found no `_emit(progress_callback, \"...\")` calls in "
        f"{_PLAN_EXECUTOR}. The producer changed shape — update the regex "
        "or the contract."
    )
    missing = emitted - set(PLAN_PROGRESS_EVENTS)
    assert not missing, (
        f"PlanExecutor emits {sorted(missing)} but plan_progress_mapper does not "
        "list them in PLAN_PROGRESS_EVENTS. → Fix: add the name(s) to "
        "PLAN_PROGRESS_EVENTS and handle them in map_plan_event()."
    )


def test_old_buggy_names_are_not_emitted_by_producer() -> None:
    # Regression pin for the original mismatch.
    emitted = _emitted_event_names()
    assert "plan_complete" not in emitted, (
        "Producer emits 'plan_complete'? The canonical name is 'plan_completed'. "
        "Do not reintroduce the consumer/producer name mismatch."
    )
    assert "plan_error" not in emitted


def test_plan_completed_maps_to_completed_not_running() -> None:
    state = new_plan_progress_state()
    map_plan_event("plan_started", {"total_tasks": 2}, state)
    out = map_plan_event("plan_completed", {"status": "completed"}, state)
    assert out["status"] == "completed", (
        "plan_completed must map to a terminal 'completed' status, not 'running'."
    )
    assert out["progress"] == 100


def test_failed_plan_maps_to_failed() -> None:
    state = new_plan_progress_state()
    map_plan_event("plan_started", {"total_tasks": 1}, state)
    out = map_plan_event("plan_completed", {"status": "failed"}, state)
    assert out["status"] == "failed"
    assert out["progress"] == 100


def test_progress_is_monotonic_across_steps() -> None:
    state = new_plan_progress_state()
    map_plan_event("plan_started", {"total_tasks": 4, "pattern": "x"}, state)
    p_before = map_plan_event("step_running", {}, state)["progress"]
    map_plan_event("step_completed", {"status": "completed"}, state)
    p_after = map_plan_event("step_running", {}, state)["progress"]
    assert p_before == 0
    assert p_after == 25


def test_label_falls_back_to_pattern_then_default() -> None:
    state = new_plan_progress_state()
    assert map_plan_event("plan_started", {"pattern": "sourcing_flow"}, state)[
        "label"
    ] == "sourcing_flow"
    assert map_plan_event("step_running", {}, state)["label"] == "Plano multi-step"
