"""CI gate: run the chat capabilities auditor and fail on any global gap.

This test wraps `scripts/audit_chat_capabilities.py` so the same checks the
script enforces when run manually are now executed on every PR. If any of
`broken_mappings`, `orphan_tools`, `actions_no_handler`, or `broken_handlers`
is non-zero — or `domains_with_gaps` rises above zero — the suite fails and
blocks merge, surfacing the offending domains in the assertion message.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest


_REPO_ROOT = Path(__file__).resolve().parent.parent
_AUDIT_SCRIPT = _REPO_ROOT / "scripts" / "audit_chat_capabilities.py"


def _load_auditor():
    """Load the auditor module by file path (scripts/ has no __init__.py)."""
    os.environ.setdefault("LIA_ALLOW_NON_COMPLIANT_DOMAINS", "1")
    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://stub:stub@localhost/stub")
    os.environ.setdefault("LIA_SKIP_DB", "1")
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))

    spec = importlib.util.spec_from_file_location(
        "lia_audit_chat_capabilities", _AUDIT_SCRIPT
    )
    assert spec and spec.loader, f"Cannot load auditor at {_AUDIT_SCRIPT}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def audit_report() -> dict:
    auditor = _load_auditor()
    auditor.audit()
    report = auditor.REPORT
    assert report.get("global_summary"), "Auditor produced no global_summary."
    return report


def _gap_detail(report: dict, key: str) -> str:
    """Build a human-readable list of offending (domain, item) entries."""
    detail: list[str] = []
    for domain_id, info in report.get("registered_domains", {}).items():
        gaps = (info or {}).get("gaps") or {}
        items = gaps.get(key) or []
        if items:
            detail.append(f"  - {domain_id}: {items}")
    return "\n".join(detail) if detail else "  (no per-domain detail available)"


def test_audit_has_zero_broken_mappings(audit_report: dict) -> None:
    summary = audit_report["global_summary"]
    assert summary["broken_mappings"] == 0, (
        f"{summary['broken_mappings']} action->tool mappings reference "
        f"missing tools:\n{_gap_detail(audit_report, 'action_tool_map_broken')}"
    )


def test_audit_has_zero_orphan_tools(audit_report: dict) -> None:
    summary = audit_report["global_summary"]
    assert summary["orphan_tools"] == 0, (
        f"{summary['orphan_tools']} tools are registered but unreachable "
        f"(no action mapped to them):\n"
        f"{_gap_detail(audit_report, 'tools_orphaned_no_action')}"
    )


def test_audit_has_zero_actions_without_handler(audit_report: dict) -> None:
    summary = audit_report["global_summary"]
    assert summary["actions_no_handler"] == 0, (
        f"{summary['actions_no_handler']} actions have neither a tool "
        f"mapping nor a handler:\n"
        f"{_gap_detail(audit_report, 'actions_without_tool_or_handler')}"
    )


def test_audit_has_zero_broken_handlers(audit_report: dict) -> None:
    summary = audit_report["global_summary"]
    assert summary["broken_handlers"] == 0, (
        f"{summary['broken_handlers']} tool handlers fail to import or "
        f"are not callable:\n{_gap_detail(audit_report, 'handlers_failing_import')}"
    )


def test_audit_has_zero_domains_with_gaps(audit_report: dict) -> None:
    summary = audit_report["global_summary"]
    assert summary["domains_with_gaps"] == 0, (
        f"{summary['domains_with_gaps']} domain(s) have at least one gap. "
        f"See the per-category assertions above for details."
    )
