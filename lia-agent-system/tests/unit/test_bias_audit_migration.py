"""UC-P0-13: bias audit API and RAG pipeline route through rails_adapter, not deprecated service.

These tests verify the migration path is in place and no caller directly
imports (at runtime) from app.shared.services.bias_audit_service.
"""
import ast
from pathlib import Path

WORKSPACE = Path("/home/runner/workspace/lia-agent-system")


def _runtime_imports_from(source: str) -> list[tuple[int, str]]:
    """Return (lineno, module) for all ImportFrom nodes NOT guarded by TYPE_CHECKING.

    A node is considered TYPE_CHECKING-guarded if it appears inside an
    'if TYPE_CHECKING:' block (ast.If where the test is ast.Name(id='TYPE_CHECKING')).
    """
    tree = ast.parse(source)

    # Collect lineno ranges of TYPE_CHECKING blocks
    type_checking_ranges: list[tuple[int, int]] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.If)
            and isinstance(node.test, ast.Name)
            and node.test.id == "TYPE_CHECKING"
        ):
            end = max((n.end_lineno for n in ast.walk(node) if hasattr(n, 'end_lineno')), default=node.lineno)
            type_checking_ranges.append((node.lineno, end))

    def in_type_checking(lineno: int) -> bool:
        return any(start <= lineno <= end for start, end in type_checking_ranges)

    results = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if not in_type_checking(node.lineno):
                results.append((node.lineno, node.module))
    return results


def test_bias_audit_api_does_not_import_deprecated_service():
    """bias_audit.py must not import (at runtime) from app.shared.services.bias_audit_service.

    TYPE_CHECKING-only imports are permitted (type annotations only, not executed at runtime).
    Fix if failing: wrap the import in 'if TYPE_CHECKING:' or remove it entirely. (UC-P0-13)
    """
    source = (WORKSPACE / "app/api/v1/bias_audit.py").read_text()
    runtime_imports = _runtime_imports_from(source)
    for lineno, mod in runtime_imports:
        assert "shared.services.bias_audit_service" not in mod, (
            f"bias_audit.py line {lineno}: runtime import from deprecated service found. "
            "Fix: wrap in 'if TYPE_CHECKING:' or use rails_adapter delegate instead. "
            "(UC-P0-13)"
        )


def test_bias_audit_api_uses_rails_adapter():
    """bias_audit.py must reference rails_adapter for actual runtime calls."""
    source = (WORKSPACE / "app/api/v1/bias_audit.py").read_text()
    assert "rails_adapter" in source or "_bias_adapter" in source, (
        "bias_audit.py does not reference rails_adapter or _bias_adapter. "
        "Fix: import RailsAdapter from integrations_hub.services.rails_adapter "
        "and route get_adverse_impact_by_job through it. (UC-P0-13)"
    )


def test_rag_pipeline_does_not_import_deprecated_service_at_module_level():
    """rag_pipeline_service.py must not have a module-level import of the deprecated service.

    Lazy inline imports (inside functions, indented) are allowed.
    """
    source = (WORKSPACE / "app/domains/ai/services/rag_pipeline_service.py").read_text()
    lines = source.splitlines()
    for i, line in enumerate(lines, 1):
        stripped = line.lstrip()
        if stripped.startswith("from app.shared.services.bias_audit_service"):
            indent = len(line) - len(stripped)
            assert indent > 0, (
                f"rag_pipeline_service.py line {i}: module-level import of deprecated "
                "bias_audit_service found. Fix: use rails_adapter.audit_ranking_results() "
                "instead. (UC-P0-13)"
            )


def test_compliance_duplicate_deleted():
    """app/shared/compliance/bias_audit_service.py (duplicate) must not exist."""
    duplicate = WORKSPACE / "app/shared/compliance/bias_audit_service.py"
    assert not duplicate.exists(), (
        "Duplicate bias_audit_service.py still exists at app/shared/compliance/. "
        "Fix: delete it — it has no callers. (UC-P0-13)"
    )


def test_rails_adapter_has_bias_audit_methods():
    """rails_adapter.py must expose get_adverse_impact_by_job and audit_ranking_results."""
    source = (WORKSPACE / "app/domains/integrations_hub/services/rails_adapter.py").read_text()
    assert "def get_adverse_impact_by_job" in source, (
        "rails_adapter.py is missing get_adverse_impact_by_job. "
        "Fix: add the method as a Python delegate (UC-P0-13 Scenario B)."
    )
    assert "def audit_ranking_results" in source, (
        "rails_adapter.py is missing audit_ranking_results. "
        "Fix: add the method as a Python delegate (UC-P0-13 Scenario B)."
    )
    assert "def get_bias_audit_snapshot_history" in source, (
        "rails_adapter.py is missing get_bias_audit_snapshot_history. "
        "Fix: add the method as a Python delegate (UC-P0-13 Scenario B)."
    )
