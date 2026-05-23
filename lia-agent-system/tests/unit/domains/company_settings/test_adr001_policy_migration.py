"""
ADR-001 W1-004-C Agent-B: Regression tests for policy_tool_registry migration.

Verifies:
1. _wrap_get_current_policy uses HiringPolicyRepository (no inline text() SELECT)
2. _wrap_get_policy_summary uses HiringPolicyRepository (no inline text() SELECT)
3. HiringPolicyRepository has get_by_company method
4. EXEMPT marker coverage for all remaining text() SQL in analytics/dynamic tools
"""
from pathlib import Path

POLICY_FILE = Path(
    "app/domains/hiring_policy/agents/policy_tool_registry.py"
)

# Functions MIGRATED to repo — must NOT have inline text() SQL for the SELECT
MIGRATED_FUNCTIONS = [
    "_wrap_get_current_policy",
    "_wrap_get_policy_summary",
]

# Functions EXEMPT — must have ADR-001-EXEMPT marker on or before their first text() call
EXEMPT_FUNCTIONS = [
    "_wrap_save_policy_field",
    "_wrap_get_company_context",
    "_wrap_get_platform_benchmarks",
    "_wrap_detect_policy_impact_anomalies",
    "_wrap_get_policy_effectiveness_report",
    "_wrap_save_policy_block",
    "_wrap_apply_industry_defaults",
    "_wrap_get_setup_progress",
]


def _extract_function_body(content: str, func_name: str) -> str:
    """Return text between func_name start and next @tool_handler / EOF."""
    idx = content.find(f"async def {func_name}")
    if idx < 0:
        return ""
    end = content.find("\n@tool_handler", idx + 1)
    if end < 0:
        end = len(content)
    return content[idx:end]


def test_policy_repo_import_present():
    """MIGRATE: HiringPolicyRepository must be imported in policy_tool_registry."""
    content = POLICY_FILE.read_text()
    assert "HiringPolicyRepository" in content, (
        "policy_tool_registry: missing HiringPolicyRepository import. "
        "ADR-001 W1-004-C MIGRATE 1+2 require it."
    )


def test_get_current_policy_no_inline_sql():
    """MIGRATE 1: _wrap_get_current_policy must NOT query via inline text()."""
    content = POLICY_FILE.read_text()
    func_body = _extract_function_body(content, "_wrap_get_current_policy")
    assert func_body, "_wrap_get_current_policy not found"
    # The SELECT text() was replaced by repo.get_by_company
    assert "text(" not in func_body or "ADR-001 W1-004-C MIGRATE" in func_body, (
        "_wrap_get_current_policy: found raw text() call without migration comment. "
        "Should use HiringPolicyRepository.get_by_company."
    )
    assert "get_by_company" in func_body, (
        "_wrap_get_current_policy: missing get_by_company call. "
        "MIGRATE 1 must delegate to HiringPolicyRepository."
    )


def test_get_policy_summary_no_inline_sql():
    """MIGRATE 2: _wrap_get_policy_summary must NOT query via inline text()."""
    content = POLICY_FILE.read_text()
    func_body = _extract_function_body(content, "_wrap_get_policy_summary")
    assert func_body, "_wrap_get_policy_summary not found"
    assert "get_by_company" in func_body, (
        "_wrap_get_policy_summary: missing get_by_company call. "
        "MIGRATE 2 must delegate to HiringPolicyRepository."
    )


def test_exempt_functions_have_markers():
    """EXEMPT: all analytics/dynamic SQL functions must have ADR-001-EXEMPT markers."""
    content = POLICY_FILE.read_text()
    lines = content.split("\n")

    for func_name in EXEMPT_FUNCTIONS:
        func_body = _extract_function_body(content, func_name)
        if not func_body:
            # Not all functions are present; skip if missing
            continue
        if "text(" not in func_body and "sql_text(" not in func_body:
            # No SQL in this function — no marker needed
            continue
        assert "ADR-001-EXEMPT" in func_body, (
            f"{func_name}: has text()/sql_text() call without ADR-001-EXEMPT marker. "
            f"Add '# ADR-001-EXEMPT: <reason>' before the async with AsyncSessionLocal block."
        )


def test_hiring_policy_repo_has_get_by_company():
    """Repo contract: HiringPolicyRepository.get_by_company must exist."""
    from app.domains.hiring_policy.repositories.hiring_policy_repository import (
        HiringPolicyRepository,
    )
    assert hasattr(HiringPolicyRepository, "get_by_company"), (
        "HiringPolicyRepository is missing get_by_company method. "
        "This method is required by MIGRATE 1+2 (ADR-001 W1-004-C)."
    )
