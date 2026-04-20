"""CI gate: chat-capabilities audit must report 0 regressions.

Task #672 / Fase 2C P2-4. Runs ``scripts/audit_chat_capabilities.py``, parses
the JSON written to ``docs/chat_capabilities_audit.json``, and exits non-zero
if any of the regression-sensitive fields is non-zero **or** if the total
number of registered domains drops below the baseline (protects against an
``@register_domain`` being deleted by accident).

Designed to be called from ``.github/workflows/ci-audit-gate.yml`` and
reproducible locally::

    python3 scripts/ci_audit_gate.py
    python3 scripts/ci_audit_gate.py --baseline-domains 18

Exit codes:
- 0 — audit clean and baseline preserved
- 1 — at least one gap reopened or baseline violated
- 2 — auditor itself failed (import error, etc.)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIT_SCRIPT = ROOT / "scripts" / "audit_chat_capabilities.py"
REPORT_PATH = ROOT / "docs" / "chat_capabilities_audit.json"

# Fields under ``global_summary`` that must remain at zero. Any non-zero value
# is a regression that has to be fixed before merging.
ZERO_FIELDS_SUMMARY = (
    "domains_with_gaps",
    "broken_handlers",
    "actions_no_handler",
    "orphan_tools",
    "broken_mappings",
)

# Top-level field tracked separately (lives outside ``global_summary``).
ZERO_FIELD_TOPLEVEL = "agent_types_pointing_to_unknown_domain"

# Default baseline matches the count locked in by the Fase 2C audit. Bump it
# only when a new domain is intentionally added.
DEFAULT_BASELINE_DOMAINS = 18


def _run_auditor() -> None:
    print(f"[ci_audit_gate] running {AUDIT_SCRIPT.relative_to(ROOT)} …", flush=True)
    proc = subprocess.run(
        [sys.executable, str(AUDIT_SCRIPT)],
        cwd=ROOT,
        check=False,
    )
    if proc.returncode != 0:
        print(
            f"::error::audit_chat_capabilities.py exited {proc.returncode} "
            "— gate cannot evaluate report",
            flush=True,
        )
        sys.exit(2)


def _load_report() -> dict:
    if not REPORT_PATH.exists():
        print(f"::error::report not found at {REPORT_PATH}", flush=True)
        sys.exit(2)
    try:
        return json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"::error::report is not valid JSON: {exc}", flush=True)
        sys.exit(2)


def _evaluate(report: dict, baseline_domains: int) -> list[str]:
    failures: list[str] = []

    summary = report.get("global_summary") or {}
    for field in ZERO_FIELDS_SUMMARY:
        value = summary.get(field, 0)
        if value:
            failures.append(
                f"global_summary.{field} = {value} (expected 0). "
                "A previously-fixed gap was reopened."
            )

    orphan_targets = report.get(ZERO_FIELD_TOPLEVEL) or []
    if orphan_targets:
        failures.append(
            f"{ZERO_FIELD_TOPLEVEL} = {orphan_targets} (expected []). "
            "An agent-type alias is pointing to a domain that is not registered."
        )

    total_registered = summary.get("total_registered", 0)
    if total_registered < baseline_domains:
        failures.append(
            f"global_summary.total_registered = {total_registered} "
            f"< baseline {baseline_domains}. A @register_domain was likely deleted "
            "— either restore it or update the baseline intentionally via "
            "--baseline-domains."
        )

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline-domains",
        type=int,
        default=DEFAULT_BASELINE_DOMAINS,
        help=f"Minimum number of registered domains (default: {DEFAULT_BASELINE_DOMAINS})",
    )
    parser.add_argument(
        "--skip-run",
        action="store_true",
        help="Skip running the auditor; just evaluate the existing report. "
             "Useful when the report was produced by a previous CI step.",
    )
    args = parser.parse_args()

    if not args.skip_run:
        _run_auditor()

    report = _load_report()
    failures = _evaluate(report, args.baseline_domains)

    summary = report.get("global_summary") or {}
    print("[ci_audit_gate] summary:", json.dumps(summary, indent=2))
    print(
        f"[ci_audit_gate] agent_types_pointing_to_unknown_domain="
        f"{report.get(ZERO_FIELD_TOPLEVEL) or []}"
    )

    if failures:
        print("\n::error::Chat-capabilities audit gate FAILED:")
        for f in failures:
            print(f"  - {f}")
        print(
            "\nReproduce locally:\n"
            "  cd lia-agent-system\n"
            "  python3 scripts/audit_chat_capabilities.py\n"
            "  python3 scripts/ci_audit_gate.py"
        )
        return 1

    print("[ci_audit_gate] ✅ audit clean — gate PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
