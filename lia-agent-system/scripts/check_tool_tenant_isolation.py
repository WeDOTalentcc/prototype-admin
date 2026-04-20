"""
CI guard — Tool tenant isolation (Task #673 / closes #361, ADR-018).

For every public function defined under ``app/domains/*/tools/``, exactly one of
the following must hold:

  1. The function is decorated with ``@tool_handler(...)`` (canonical path —
     fail-closed `company_id` check + module gating + audit shape).
  2. The owning module declares ``# tenant-isolation: manual: <reason>`` in its
     header (first ~2 KB) AND the file is listed in ``MANUAL_ALLOWLIST`` below.
     This grandfathers the legacy hand-rolled ``_extract_context(kwargs)`` path
     that pre-dates the decorator. **No new entries are accepted** — each item
     should disappear as the file is migrated.
  3. The function is a ``register_*_tools`` / ``get_*_tools`` aggregator helper,
     or a private helper (``_`` prefix) — neither reads tenant data directly.

Exit code:
    0 — every public handler is protected.
    1 — at least one unprotected handler. The output names file:line and the
        offending function so the contributor can pick (1) or (2) above.

Run::

    python3 scripts/check_tool_tenant_isolation.py
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS_GLOB = "app/domains/*/tools/**/*.py"

MODULE_ANNOTATION = "tenant-isolation: manual"

# Legacy files that pre-date `@tool_handler`. Each entry is grandfathered ONLY
# while the module header carries the `# tenant-isolation: manual: <reason>`
# annotation explaining how `company_id` is read. New files are NOT accepted
# here — they must use `@tool_handler`.
MANUAL_ALLOWLIST: frozenset[str] = frozenset({
    "app/domains/analytics/tools/analytics_query_tools/_base.py",
    "app/domains/analytics/tools/analytics_query_tools/activity_metrics.py",
    "app/domains/analytics/tools/analytics_query_tools/financial_trends.py",
    "app/domains/analytics/tools/analytics_query_tools/intelligence.py",
    "app/domains/analytics/tools/analytics_query_tools/pipeline_analytics.py",
    "app/domains/analytics/tools/analytics_query_tools/quality_metrics.py",
    "app/domains/analytics/tools/analytics_query_tools/recruiter_performance.py",
    "app/domains/analytics/tools/analytics_query_tools/registry.py",
    "app/domains/analytics/tools/analytics_query_tools/workload_analysis.py",
    "app/domains/analytics/tools/query_tools.py",
    "app/domains/automation/tools/automation_tools.py",
    "app/domains/communication/tools/communication_tools.py",
    "app/domains/company_settings/tools/import_tools.py",
    "app/domains/cv_screening/tools/candidate_tools.py",
    "app/domains/cv_screening/tools/cv_match_tool.py",
    "app/domains/cv_screening/tools/cv_upload_tool.py",
    "app/domains/job_management/tools/job_tools.py",
    "app/domains/job_management/tools/job_wizard_tools.py",
    "app/domains/job_management/tools/query_tools.py",
    "app/domains/recruiter_assistant/tools/pipeline_tools.py",
    "app/domains/sourcing/tools/enrichment_tools.py",
    "app/domains/sourcing/tools/query_tools.py",
    "app/domains/talent_intelligence/tools/registry.py",
})


def _func_decorators(node: ast.AST) -> list[str]:
    out: list[str] = []
    for d in getattr(node, "decorator_list", []) or []:
        try:
            out.append(ast.unparse(d))
        except Exception:
            out.append("")
    return out


def _scan_file(path: Path, rel: str) -> list[str]:
    """Return list of human-readable violations for `path`."""
    try:
        source = path.read_text(encoding="utf-8")
    except Exception:
        return []
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [f"{rel}: SyntaxError {exc}"]

    module_manual = MODULE_ANNOTATION in source[:2000]
    is_allowlisted = rel in MANUAL_ALLOWLIST

    if module_manual and not is_allowlisted:
        return [
            f"{rel}: module declares '# tenant-isolation: manual' but is NOT in "
            f"MANUAL_ALLOWLIST. Either add `@tool_handler` to each function OR "
            f"add the file to the allowlist with a reason."
        ]
    if is_allowlisted and not module_manual:
        return [
            f"{rel}: file is in MANUAL_ALLOWLIST but is missing the "
            f"`# tenant-isolation: manual: <reason>` header annotation."
        ]

    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            continue
        name = node.name
        if name.startswith("_"):
            continue
        if name.startswith("register_") and name.endswith("_tools"):
            continue
        if name.startswith("get_") and name.endswith("_tools"):
            continue
        decorators = _func_decorators(node)
        if any("tool_handler" in d for d in decorators):
            continue
        if module_manual and is_allowlisted:
            continue
        violations.append(
            f"{rel}:{node.lineno}: function '{name}' is missing `@tool_handler` "
            f"and the module is not annotated `# tenant-isolation: manual`."
        )
    return violations


def main() -> int:
    violations: list[str] = []
    for py in sorted(ROOT.glob(TOOLS_GLOB)):
        if py.name == "__init__.py":
            continue
        rel = str(py.relative_to(ROOT))
        violations.extend(_scan_file(py, rel))

    if violations:
        print("[#673] FAIL — tool tenant-isolation guard:", file=sys.stderr)
        for v in violations:
            print(f"  {v}", file=sys.stderr)
        print(
            "\nFix: add `@tool_handler(domain=..., module=...)` to the function, "
            "OR (legacy only) add the module-level header "
            "`# tenant-isolation: manual: <how company_id is read>` AND list the "
            "file in `MANUAL_ALLOWLIST` inside this script.",
            file=sys.stderr,
        )
        return 1
    print("[#673] OK — every tool function in app/domains/*/tools/ is protected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
