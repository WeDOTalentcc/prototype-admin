"""Meta-sensor — pins `.github/workflows/wizard-nightly.yml` shape.

Sprint R.4 — guarantees the canonical bateria 9 nightly workflow stays
discoverable and properly configured. If someone deletes the cron, flips
`LIA_E2E_SENSORS_ENABLED`, or renames the pytest target, this test fails.

Skip when running outside the Replit workspace (file may not exist in
local clones of other agents).
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

# Workflow lives at the workspace root, NOT inside lia-agent-system/.
# Resolve by walking up from this file: tests/sensors/<this> → tests → lia-agent-system → workspace root.
_HERE = Path(__file__).resolve()
_WORKFLOW_PATH = (
    _HERE.parent.parent.parent.parent  # workspace root
    / ".github"
    / "workflows"
    / "wizard-nightly.yml"
)

pytestmark = pytest.mark.skipif(
    not _WORKFLOW_PATH.exists(),
    reason=(
        f"wizard-nightly.yml not found at {_WORKFLOW_PATH} — "
        "skip when running outside the canonical workspace"
    ),
)


@pytest.fixture(scope="module")
def workflow_text() -> str:
    return _WORKFLOW_PATH.read_text(encoding="utf-8")


def test_workflow_has_cron_schedule(workflow_text: str) -> None:
    """Sensor: nightly cron MUST be present, else regression goes undetected."""
    assert "schedule:" in workflow_text, (
        "wizard-nightly.yml lost its `schedule:` block — nightly regression "
        "batch will never run. Restore the cron trigger."
    )
    assert "cron:" in workflow_text, (
        "wizard-nightly.yml lost its `cron:` line — restore "
        '`- cron: "0 6 * * *"` under `schedule:`.'
    )


def test_workflow_enables_e2e_sensors_env(workflow_text: str) -> None:
    """Sensor: LIA_E2E_SENSORS_ENABLED MUST be 'true' or the tests skip silently."""
    assert "LIA_E2E_SENSORS_ENABLED" in workflow_text, (
        "wizard-nightly.yml is missing LIA_E2E_SENSORS_ENABLED env var. "
        "Without it, tests/wizard/test_canonical_e2e_sensors.py auto-skips "
        "(pytestmark.skipif gate) and the nightly becomes a green no-op."
    )
    # Accept either "true" or 'true' YAML literal forms.
    assert (
        'LIA_E2E_SENSORS_ENABLED: "true"' in workflow_text
        or "LIA_E2E_SENSORS_ENABLED: 'true'" in workflow_text
        or "LIA_E2E_SENSORS_ENABLED: true" in workflow_text
    ), (
        "LIA_E2E_SENSORS_ENABLED is set but NOT to 'true' — the bateria 9 "
        "skipif gate will trigger and the workflow will green-pass without "
        "actually running the sensors. Set it to \"true\"."
    )


def test_workflow_runs_canonical_sensor_file(workflow_text: str) -> None:
    """Sensor: pytest invocation MUST target the canonical bateria 9 file."""
    assert "test_canonical_e2e_sensors.py" in workflow_text, (
        "wizard-nightly.yml does not invoke tests/wizard/test_canonical_e2e_sensors.py. "
        "If you moved/renamed the canonical bateria 9 file, update the workflow "
        "step name 'Wizard E2E sensors (bateria 9)' pytest argument."
    )
    assert "pytest" in workflow_text, (
        "wizard-nightly.yml has no `pytest` step — restore the invocation."
    )


def test_workflow_allows_manual_dispatch(workflow_text: str) -> None:
    """Sensor: workflow_dispatch MUST be present for ad-hoc pre-deploy runs."""
    assert "workflow_dispatch" in workflow_text, (
        "wizard-nightly.yml lost `workflow_dispatch:` trigger — operators "
        "cannot run the bateria 9 manually from the GitHub Actions UI before "
        "a release. Restore the trigger."
    )
