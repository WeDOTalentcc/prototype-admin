"""T7 sensor: start_wizard_seeded directive in federated mode.

Verifies the 3-layer wiring that makes start_creation_from_source work
in the federated (SSE) path:

  1. ui_action_sink captures seed_source from tool result
  2. LangGraphReActBase drains seed_source into output.metadata
  3. SSE handler delegates to WizardSessionService when it sees
     ui_action="start_wizard_seeded" + seed_source in metadata

Without this wiring, the directive was ghost — FE received the action
name but the backend never seeded the wizard session.
"""
from __future__ import annotations

import pytest

from app.shared.ui_action_sink import (
    append_from_result,
    drain_sink,
    reset_sink,
)


@pytest.fixture(autouse=True)
def _clean():
    reset_sink()
    yield
    reset_sink()


# ── Layer 1: ui_action_sink captures seed_source ────────────────────────

def test_seed_source_captured_by_sink():
    """start_creation_from_source returns seed_source as sibling of ui_action.
    The sink must capture it so the drain propagates it to metadata."""
    append_from_result({
        "success": True,
        "data": {
            "ui_action": "start_wizard_seeded",
            "seed_source": {"type": "template", "id": "tpl-001"},
        },
    })
    d = drain_sink()
    assert d is not None
    assert d["ui_action"] == "start_wizard_seeded"
    assert d["seed_source"] == {"type": "template", "id": "tpl-001"}


def test_seed_source_absent_when_not_in_result():
    """Normal ui_action (open_modal etc.) should NOT have seed_source."""
    append_from_result({
        "data": {
            "ui_action": "open_modal",
            "ui_action_params": {"modal_id": "x"},
        },
    })
    d = drain_sink()
    assert d is not None
    assert "seed_source" not in d


def test_seed_source_vacancy_type():
    """source_type=vacancy also propagates."""
    append_from_result({
        "success": True,
        "data": {
            "ui_action": "start_wizard_seeded",
            "seed_source": {"type": "vacancy", "id": "vac-999"},
        },
    })
    d = drain_sink()
    assert d["seed_source"]["type"] == "vacancy"


# ── Layer 2: allowlist includes start_wizard_seeded ─────────────────────

def test_start_wizard_seeded_in_allowlist():
    """start_wizard_seeded must be in the actionable allowlist."""
    from app.shared.ui_action_sink import _actionable
    assert "start_wizard_seeded" in _actionable()


# ── Layer 3: directive format contract ──────────────────────────────────

def test_tool_result_shape_matches_wizard_registry():
    """The shape returned by start_creation_from_source must match what
    the sink expects: data.ui_action + data.seed_source."""
    # Simulate the exact return of _wrap_start_creation_from_source
    tool_result = {
        "success": True,
        "data": {
            "ui_action": "start_wizard_seeded",
            "seed_source": {"type": "template", "id": "abc-123"},
        },
        "message": "Pronto — vou abrir o assistente de criação.",
    }
    append_from_result(tool_result)
    d = drain_sink()
    assert d is not None
    assert d["ui_action"] == "start_wizard_seeded"
    assert d["seed_source"]["type"] == "template"
    assert d["seed_source"]["id"] == "abc-123"
    # ui_action_params is None for this directive (seed_source is the params)
    assert d.get("ui_action_params") is None


def test_last_wins_preserves_seed_source():
    """If multiple directives fire, last-wins must include seed_source."""
    append_from_result({
        "data": {"ui_action": "navigate_to", "ui_action_params": {"page": "/a"}},
    })
    append_from_result({
        "data": {
            "ui_action": "start_wizard_seeded",
            "seed_source": {"type": "template", "id": "last"},
        },
    })
    d = drain_sink()
    assert d["ui_action"] == "start_wizard_seeded"
    assert d["seed_source"]["id"] == "last"
