#!/usr/bin/env python3
"""
Lint check: block forbidden import paths that cause duplicate SQLAlchemy
class registrations.

Forbidden paths:
  - from libs.models.lia_models.*
  - from libs.messaging.lia_messaging.*
  - import libs.models.lia_models.*
  - import libs.messaging.lia_messaging.*
  - from app.models(.*)? / import app.models(.*)?  (removed shim layer — task #242)

Correct alternatives:
  - from lia_models.* …
  - from lia_messaging.* …

See ADR-012 in ARCHITECTURE.md for rationale.

Run:  python scripts/check_forbidden_imports.py
Exit: 0 = clean, 1 = violations found
"""
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
WORKSPACE_ROOT = ROOT.parent

FORBIDDEN_PATTERNS = [
    re.compile(r"\bfrom\s+libs\.models\.lia_models\b"),
    re.compile(r"\bimport\s+libs\.models\.lia_models\b"),
    re.compile(r"\bfrom\s+libs\.messaging\.lia_messaging\b"),
    re.compile(r"\bimport\s+libs\.messaging\.lia_messaging\b"),
    # task #242: app/models/ shim layer was deleted. The canonical path is
    # `lia_models.*`. A second import path created duplicate SQLAlchemy class
    # registrations (e.g. SourcingAgentSignal) and 500s.
    re.compile(r"\bfrom\s+app\.models\b"),
    re.compile(r"\bimport\s+app\.models\b"),
    # task #350: app.shared.global_tool_registry was deleted (had no
    # production callers). Reintroducing it would resurrect a dead code path.
    # Tool routing goes through app.tools.registry + tool_permissions.yaml.
    re.compile(r"\bfrom\s+app\.shared\.global_tool_registry\b"),
    re.compile(r"\bimport\s+app\.shared\.global_tool_registry\b"),
    # task #343: legacy observability paths were collapsed into
    # app.shared.observability.*. The 11 files (tracing, structured_logging,
    # callbacks, agent_monitoring_service, agent_health_alert_service,
    # model_drift_service, drift_alert_service, token_tracking_service,
    # token_budget_service, wsi_observability, langsmith) and 5 re-export
    # shims were deleted to leave a single source of truth.
    re.compile(r"\bfrom\s+app\.shared\.tracing\b"),
    re.compile(r"\bimport\s+app\.shared\.tracing\b"),
    re.compile(r"\bfrom\s+app\.shared\.structured_logging\b"),
    re.compile(r"\bimport\s+app\.shared\.structured_logging\b"),
    re.compile(r"\bfrom\s+app\.shared\.llm\.callbacks\b"),
    re.compile(r"\bimport\s+app\.shared\.llm\.callbacks\b"),
    re.compile(r"\bfrom\s+app\.shared\.governance\.agent_monitoring_service\b"),
    re.compile(r"\bimport\s+app\.shared\.governance\.agent_monitoring_service\b"),
    re.compile(r"\bfrom\s+app\.shared\.services\.agent_health_alert_service\b"),
    re.compile(r"\bimport\s+app\.shared\.services\.agent_health_alert_service\b"),
    re.compile(r"\bfrom\s+app\.shared\.services\.model_drift_service\b"),
    re.compile(r"\bimport\s+app\.shared\.services\.model_drift_service\b"),
    re.compile(r"\bfrom\s+app\.shared\.services\.drift_alert_service\b"),
    re.compile(r"\bimport\s+app\.shared\.services\.drift_alert_service\b"),
    re.compile(r"\bfrom\s+app\.shared\.services\.token_tracking_service\b"),
    re.compile(r"\bimport\s+app\.shared\.services\.token_tracking_service\b"),
    re.compile(r"\bfrom\s+app\.shared\.services\.token_budget_service\b"),
    re.compile(r"\bimport\s+app\.shared\.services\.token_budget_service\b"),
    re.compile(r"\bfrom\s+app\.domains\.ai\.services\.model_drift_service\b"),
    re.compile(r"\bimport\s+app\.domains\.ai\.services\.model_drift_service\b"),
    re.compile(r"\bfrom\s+app\.domains\.lgpd\.services\.drift_alert_service\b"),
    re.compile(r"\bimport\s+app\.domains\.lgpd\.services\.drift_alert_service\b"),
    re.compile(r"\bfrom\s+app\.domains\.analytics\.services\.token_tracking_service\b"),
    re.compile(r"\bimport\s+app\.domains\.analytics\.services\.token_tracking_service\b"),
    re.compile(r"\bfrom\s+app\.domains\.analytics\.services\.wsi_observability\b"),
    re.compile(r"\bimport\s+app\.domains\.analytics\.services\.wsi_observability\b"),
    re.compile(r"\bfrom\s+app\.domains\.analytics\.services\.agent_monitoring_service\b"),
    re.compile(r"\bimport\s+app\.domains\.analytics\.services\.agent_monitoring_service\b"),
    re.compile(r"\bfrom\s+app\.domains\.credits\.services\.token_budget_service\b"),
    re.compile(r"\bimport\s+app\.domains\.credits\.services\.token_budget_service\b"),
    re.compile(r"\bfrom\s+app\.config\.langsmith\b"),
    re.compile(r"\bimport\s+app\.config\.langsmith\b"),
]

SCAN_DIRS = ["app", "scripts", "tests", "libs", "alembic"]

SELF = Path(__file__).resolve()


def _scan_string_literals(
    source: str, py_file: Path, base: Path, violations: list[str]
) -> None:
    """Parse the file as Python and search inside every string literal for
    forbidden import patterns. This catches patch/codegen scripts that emit
    Python source via ``write_text(...)`` or string templates — the line
    scanner above only sees the surrounding quotes, not the embedded import.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
            continue
        text = node.value
        if not text or "import" not in text:
            continue
        node_lineno = getattr(node, "lineno", 1) or 1
        for offset, line in enumerate(text.splitlines()):
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            for pattern in FORBIDDEN_PATTERNS:
                if pattern.search(line):
                    rel = py_file.relative_to(base)
                    lineno = node_lineno + offset
                    violations.append(
                        f"  {rel}:{lineno} (inside string literal): {line.strip()}"
                    )
                    break


def _check_file(py_file: Path, base: Path, violations: list[str]) -> None:
    if py_file.resolve() == SELF:
        return
    try:
        source = py_file.read_text(encoding="utf-8")
    except Exception:
        return
    for lineno, line in enumerate(source.splitlines(), 1):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.search(line):
                rel = py_file.relative_to(base)
                violations.append(f"  {rel}:{lineno}: {line.rstrip()}")
                break
    _scan_string_literals(source, py_file, base, violations)


def main() -> int:
    violations: list[str] = []

    for scan_dir in SCAN_DIRS:
        target = ROOT / scan_dir
        if not target.exists():
            continue
        for py_file in target.rglob("*.py"):
            _check_file(py_file, ROOT, violations)

    for py_file in ROOT.glob("*.py"):
        _check_file(py_file, ROOT, violations)

    for py_file in WORKSPACE_ROOT.glob("*.py"):
        _check_file(py_file, WORKSPACE_ROOT, violations)

    if violations:
        print(
            "FAIL — forbidden import paths found (ADR-012):\n"
            + "\n".join(violations)
            + "\n\n"
            "These paths cause duplicate SQLAlchemy class registrations.\n"
            "Use the short-form imports instead:\n"
            "  from libs.models.lia_models.X  →  from lia_models.X\n"
            "  from libs.messaging.lia_messaging.X  →  from lia_messaging.X\n"
            "\n"
            "See ADR-012 in ARCHITECTURE.md for details."
        )
        return 1

    print("OK — no forbidden import paths (ADR-012).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
