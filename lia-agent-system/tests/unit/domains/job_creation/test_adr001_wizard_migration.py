"""
ADR-001 W1-004-C Agent-B: Regression tests for wizard_tool_registry migration.

Verifies:
1. _load_vacancy_or_error uses JobVacancyCrudRepository (no inline select())
2. JobVacancyCrudRepository has get_by_id_strict_company method
3. EXEMPT marker coverage for salary benchmark and report aggregation SQL
"""
from pathlib import Path


WIZARD_FILE = Path(
    "app/domains/job_management/agents/wizard_tool_registry.py"
)


def test_wizard_no_inline_select_jobvacancy():
    """MIGRATE 1: _load_vacancy_or_error must NOT use sa_select(JobVacancy)."""
    content = WIZARD_FILE.read_text()
    assert "sa_select(JobVacancy).where(" not in content, (
        "wizard_tool_registry: inline sa_select(JobVacancy) found in "
        "_load_vacancy_or_error. Should use JobVacancyCrudRepository.get_by_id_strict_company."
    )


def test_wizard_load_uses_repo():
    """MIGRATE 1: _load_vacancy_or_error must reference the repo method."""
    content = WIZARD_FILE.read_text()
    assert "JobVacancyCrudRepository" in content, (
        "wizard_tool_registry: missing JobVacancyCrudRepository import/usage. "
        "MIGRATE 1 should route _load_vacancy_or_error through the repo."
    )
    assert "get_by_id_strict_company" in content, (
        "wizard_tool_registry: missing get_by_id_strict_company call. "
        "_load_vacancy_or_error must delegate to the existing repo method."
    )


def test_wizard_salary_benchmark_has_exempt():
    """EXEMPT: _wrap_get_salary_benchmarks must have ADR-001-EXEMPT marker."""
    content = WIZARD_FILE.read_text()
    lines = content.split("\n")
    in_salary_func = False
    for i, line in enumerate(lines):
        if "async def _wrap_get_salary_benchmarks" in line:
            in_salary_func = True
        if in_salary_func and ("sql_text(" in line or "query = sql_text" in line):
            # Check the preceding 8 lines for EXEMPT marker (marker may be several lines up)
            context = "\n".join(lines[max(0, i - 8):i])
            assert "ADR-001-EXEMPT" in context, (
                f"Line {i+1}: sql_text() in _wrap_get_salary_benchmarks without "
                "ADR-001-EXEMPT marker in preceding 8 lines. Add the marker."
            )
            break


def test_wizard_generate_report_has_exempt():
    """EXEMPT: _wrap_generate_report sql_text must have ADR-001-EXEMPT marker."""
    content = WIZARD_FILE.read_text()
    lines = content.split("\n")
    in_report_func = False
    for i, line in enumerate(lines):
        if "async def _wrap_generate_report" in line:
            in_report_func = True
        if in_report_func and "sql_text(" in line:
            context = "\n".join(lines[max(0, i - 8):i])
            assert "ADR-001-EXEMPT" in context, (
                f"Line {i+1}: sql_text() in _wrap_generate_report without "
                "ADR-001-EXEMPT marker in preceding 8 lines. Add the marker."
            )
            break


def test_job_vacancy_crud_repo_has_get_by_id_strict():
    """Repo contract: JobVacancyCrudRepository.get_by_id_strict_company must exist."""
    from app.domains.job_management.repositories.job_vacancy_crud_repository import (
        JobVacancyCrudRepository,
    )
    assert hasattr(JobVacancyCrudRepository, "get_by_id_strict_company"), (
        "JobVacancyCrudRepository is missing get_by_id_strict_company method. "
        "This method is required by _load_vacancy_or_error (ADR-001 W1-004-C MIGRATE 1)."
    )
