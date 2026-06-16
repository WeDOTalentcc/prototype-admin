"""Sensor (warn-only) — Wizard canonical doc freshness.

Ensures `/tmp/WIZARD_ARCHITECTURE_CANONICAL.md` (canonical reference for the wizard
agentic pipeline — ADR-WIZARD-002) exists and was modified within the last 30 days.

Rationale: drift between code (`graph.py`, `state.py`, `wizard_session_service.py`,
`wizard_smart_orchestrator.py`, `api_client.py`) and the canonical doc is a
classic harness failure — code moves forward, doc lags, next agent reads stale doc
and reintroduces fixed bugs. This sensor surfaces the lag explicitly.

Currently warn-only (pytest.skip with reason) so it doesn't break local dev when
the doc lives on Mac and not on Replit. Promote to BLOCKING once the doc has a
canonical Replit-pinned location (under version control) and the team is aware
of the contract.
"""

from __future__ import annotations

import datetime as _dt
import os
import pathlib

import pytest

# Canonical locations (Replit /tmp + Mac local, kept in sync by maintainer).
_CANONICAL_PATHS = (
    "/tmp/WIZARD_ARCHITECTURE_CANONICAL.md",
    str(pathlib.Path.home() / "Documents/Python/WIZARD_ARCHITECTURE_CANONICAL.md"),
)

_STALENESS_THRESHOLD_DAYS = 30


def _resolve_canonical_path() -> str | None:
    for candidate in _CANONICAL_PATHS:
        if os.path.exists(candidate):
            return candidate
    return None


def test_wizard_canonical_doc_exists() -> None:
    """Canonical doc must be readable in at least one of the known locations."""
    path = _resolve_canonical_path()
    if path is None:
        pytest.skip(
            "WIZARD_ARCHITECTURE_CANONICAL.md not found at any known location. "
            "Expected one of: " + ", ".join(_CANONICAL_PATHS) + ". "
            "See ADR-WIZARD-002 in lia-agent-system/CLAUDE.md."
        )

    assert os.path.getsize(path) > 0, (
        f"Canonical wizard doc at {path} is empty. "
        "Restore from git history or Mac local copy. See ADR-WIZARD-002."
    )


def test_wizard_canonical_doc_freshness() -> None:
    """Canonical doc must have been touched in the last 30 days.

    Warn-only: if stale, emit a skip(reason=...) instead of failing. Promote
    to assert when the doc has a canonical version-controlled location.
    """
    path = _resolve_canonical_path()
    if path is None:
        pytest.skip("Doc not found — see ADR-WIZARD-002.")

    mtime = _dt.datetime.fromtimestamp(os.path.getmtime(path))
    age = _dt.datetime.now() - mtime
    if age.days > _STALENESS_THRESHOLD_DAYS:
        pytest.skip(
            f"WIZARD_ARCHITECTURE_CANONICAL.md at {path} is {age.days} days old "
            f"(> {_STALENESS_THRESHOLD_DAYS}d threshold). Review whether recent "
            "changes to graph.py / wizard_session_service.py / state.py / "
            "wizard_smart_orchestrator.py / api_client.py are reflected. "
            "ADR-WIZARD-002 binds these files to the doc."
        )


def test_adr_wizard_002_present_in_claude_md() -> None:
    """ADR-WIZARD-002 marker must exist in lia-agent-system/CLAUDE.md."""
    claude_md = pathlib.Path(__file__).resolve().parents[2] / "CLAUDE.md"
    if not claude_md.exists():
        pytest.skip(f"CLAUDE.md not found at {claude_md}")

    body = claude_md.read_text(encoding="utf-8")
    assert "ADR-WIZARD-002" in body, (
        "ADR-WIZARD-002 marker missing from lia-agent-system/CLAUDE.md. "
        "Was the ADR removed? Restore it — it pins the canonical wizard doc."
    )
