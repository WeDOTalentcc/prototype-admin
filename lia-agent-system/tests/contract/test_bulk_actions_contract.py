"""
Contract tests for bulk actions — pins harness engineering fixes N1/N5/N7.
These are SENSOR tests (computacional, feedback) per harness-engineering taxonomy.

RED tests (TDD): written to pin fixes and prevent regression.
If a test fails, the fix description is in the assertion message.
"""
import ast
import os
import pytest

BULK_ACTIONS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "app", "api", "v1", "bulk_actions.py"
)


def _read_bulk_actions_source() -> str:
    path = os.path.normpath(BULK_ACTIONS_PATH)
    with open(path, "r") as f:
        return f.read()


# --- N7: audit log must use Depends company_id, not getattr fallback ---

def test_no_getattr_company_id_fallback_in_bulk_actions():
    """N7 sensor: getattr(current_user, 'company_id', '') is anti-pattern.
    company_id from Depends(require_company_id) is already available in every handler.

    Fix: replace getattr(current_user, 'company_id', '') with company_id
    """
    source = _read_bulk_actions_source()
    assert 'getattr(current_user, "company_id"' not in source, (
        "N7 violation: bulk_actions.py still uses getattr(current_user, 'company_id', ''). "
        "Use the company_id from Depends(require_company_id) instead."
    )
    assert "getattr(current_user, 'company_id'" not in source, (
        "N7 violation (single quotes variant): bulk_actions.py still uses "
        "getattr(current_user, 'company_id', ''). "
        "Use the company_id from Depends(require_company_id) instead."
    )


# --- N5: TriagemSessionService must be instantiated outside loop ---

def test_triagem_service_not_instantiated_in_loop():
    """N5 sensor: TriagemSessionService() inside for loop = N instantiations.
    Must be hoisted before the loop.

    Fix: move `triagem_svc = TriagemSessionService()` before `for candidate_id in ...`
    """
    source = _read_bulk_actions_source()
    lines = source.split("\n")
    in_for_loop = False
    for_indent = 0
    violation = False
    violation_line = -1

    for i, line in enumerate(lines):
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        if "for candidate_id in request.candidate_ids" in line:
            in_for_loop = True
            for_indent = indent
            continue

        if in_for_loop:
            if stripped and indent <= for_indent and not stripped.startswith("#"):
                in_for_loop = False
            elif "TriagemSessionService()" in line:
                violation = True
                violation_line = i + 1
                break

    assert not violation, (
        f"N5 violation at line {violation_line}: TriagemSessionService() is instantiated "
        "inside the for loop. Hoist it before the loop to avoid N instantiations. "
        "Move to just before `for candidate_id in request.candidate_ids:`"
    )


# --- N1: BulkDeleteRequest must have permanent field ---

def test_bulk_delete_request_has_permanent_field():
    """N1 sensor (BE side): BulkDeleteRequest schema must accept 'permanent' field.

    AST check: BulkDeleteRequest class must have an assignment to 'permanent'.
    """
    source = _read_bulk_actions_source()
    tree = ast.parse(source)

    found_class = False
    has_permanent = False

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "BulkDeleteRequest":
            found_class = True
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    if item.target.id == "permanent":
                        has_permanent = True
                        break
            break

    assert found_class, "BulkDeleteRequest class not found in bulk_actions.py"
    assert has_permanent, (
        "N1 violation: BulkDeleteRequest does not have a 'permanent' field. "
        "Add: permanent: bool = False"
    )


def test_bulk_delete_request_uses_wedo_base_model():
    """N1 bonus: BulkDeleteRequest should inherit from WeDoBaseModel (extra='forbid')."""
    source = _read_bulk_actions_source()
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "BulkDeleteRequest":
            base_names = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    base_names.append(base.id)
                elif isinstance(base, ast.Attribute):
                    base_names.append(base.attr)
            assert "WeDoBaseModel" in base_names, (
                f"BulkDeleteRequest inherits from {base_names}, not WeDoBaseModel. "
                "Use WeDoBaseModel to enforce extra='forbid' (Pydantic conventions R1)."
            )
            return

    pytest.fail("BulkDeleteRequest class not found in bulk_actions.py")
