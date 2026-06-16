"""Sprint R.3 sensor — uvicorn --reload em dev workflow.

Validates that the `.replit` config keeps `--reload` enabled for the
`lia-backend` workflow uvicorn command. Without this, file changes
during dev require manual kill + nohup respawn (recurring incident
across sprints F, L, M, N).

Pattern: read workspace-root `.replit`, locate the lia-backend uvicorn
shell command, assert reload flags present.

Rationale: prod deploy (Anderson/team via GitHub canonical) does NOT
use `--reload`. This sensor protects only the dev workflow .replit.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


# .replit lives at workspace root, two levels above this test file:
#   <workspace>/.replit
#   <workspace>/lia-agent-system/tests/sensors/test_replit_workflow_uvicorn_reload.py
WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
REPLIT_CONFIG = WORKSPACE_ROOT / ".replit"


@pytest.fixture(scope="module")
def replit_content() -> str:
    assert REPLIT_CONFIG.exists(), (
        f".replit not found at {REPLIT_CONFIG}. Sensor cannot verify "
        "uvicorn --reload config."
    )
    return REPLIT_CONFIG.read_text()


def _extract_lia_backend_args(content: str) -> str:
    """Find the `args = ...` line of the lia-backend uvicorn task.

    Locates the `[[workflows.workflow]]` block whose `name = "lia-backend"`
    and returns the `args = "..."` string of its uvicorn-bearing
    `shell.exec` task.
    """
    # Split on workflow blocks
    blocks = re.split(r"\[\[workflows\.workflow\]\]", content)
    for block in blocks:
        if not re.search(r'^\s*name\s*=\s*"lia-backend"', block, re.MULTILINE):
            continue
        # Find shell.exec args containing "uvicorn"
        for m in re.finditer(r'args\s*=\s*"([^"]+)"', block):
            if "uvicorn" in m.group(1):
                return m.group(1)
    pytest.fail(
        "Could not locate `args = \"...uvicorn...\"` inside the "
        "`[[workflows.workflow]]` block named lia-backend in .replit"
    )


def test_lia_backend_uvicorn_has_reload_flag(replit_content: str) -> None:
    """`--reload` must be present so file changes auto-restart uvicorn."""
    args = _extract_lia_backend_args(replit_content)
    assert "--reload" in args, (
        "lia-backend uvicorn command in .replit is missing `--reload`. "
        "Dev workflow needs auto-restart on .py file changes. "
        f"Current args: {args!r}"
    )


def test_lia_backend_uvicorn_reload_dir_scoped(replit_content: str) -> None:
    """`--reload-dir lia-agent-system` must scope the watcher.

    Without `--reload-dir`, watchfiles monitors the whole CWD which on
    Replit means monorepo-wide noise (plataforma-lia/, .git/, node_modules/).
    """
    args = _extract_lia_backend_args(replit_content)
    assert "--reload-dir" in args and "lia-agent-system" in args, (
        "lia-backend uvicorn `--reload` must be scoped via "
        "`--reload-dir lia-agent-system` to avoid monorepo-wide watch noise. "
        f"Current args: {args!r}"
    )


def test_lia_backend_uvicorn_still_binds_8001(replit_content: str) -> None:
    """Sanity guard: don't accidentally break the port binding."""
    args = _extract_lia_backend_args(replit_content)
    assert "--port 8001" in args, (
        "lia-backend uvicorn must bind 0.0.0.0:8001 (waitForPort in workflow). "
        f"Current args: {args!r}"
    )
