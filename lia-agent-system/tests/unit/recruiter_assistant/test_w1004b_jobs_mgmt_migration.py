"""
TDD tests for W1-004-B Commit 3: jobs_mgmt_tool_registry SQL migration.

Verifies:
1. No inline SQL blocks remain in jobs_mgmt_tool_registry.py
2. JobVacancyCRUDRepository has all 10+ new methods
3. _require_company_id raises on empty/None company_id
4. Behavioral tests: tool wrappers call repo with correct args
"""
import ast
import re
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

WORKSPACE = Path("/home/runner/workspace/lia-agent-system")
REGISTRY_PATH = (
    WORKSPACE
    / "app/domains/recruiter_assistant/agents/jobs_mgmt_tool_registry.py"
)
REPO_PATH = (
    WORKSPACE
    / "app/domains/job_management/repositories/job_vacancy_crud_repository.py"
)


class TestNoInlineSQLInRegistry:
    """ADR-001: no inline SQL blocks must remain in registry."""

    def test_no_raw_text_triple_quote_in_registry(self):
        """Registry must not contain text(triple_quote SQL blocks."""
        content = REGISTRY_PATH.read_text()
        # Pattern: text( followed by triple double-quotes
        matches = re.findall(r'text\s*\(\s*"""', content)
        assert matches == [], (
            f"Found {len(matches)} inline SQL block(s) in {REGISTRY_PATH.name}. "
            "All SQL must live in repository methods."
        )

    def test_no_raw_text_f_triple_quote_in_registry(self):
        """Registry must not contain text(f triple_quote SQL blocks."""
        content = REGISTRY_PATH.read_text()
        matches = re.findall(r'text\s*\(\s*f"""', content)
        assert matches == [], (
            f"Found {len(matches)} inline f-SQL block(s) in {REGISTRY_PATH.name}. "
            "All SQL must live in repository methods."
        )

    def test_registry_syntax_valid(self):
        content = REGISTRY_PATH.read_text()
        try:
            ast.parse(content)
        except SyntaxError as e:
            pytest.fail(f"Syntax error in {REGISTRY_PATH.name}: {e}")

    def test_repo_syntax_valid(self):
        content = REPO_PATH.read_text()
        try:
            ast.parse(content)
        except SyntaxError as e:
            pytest.fail(f"Syntax error in {REPO_PATH.name}: {e}")


class TestRepositoryHasNewMethods:
    """JobVacancyCRUDRepository must expose all ADR-001 W1-004-B methods."""

    REQUIRED_METHODS = [
        "_require_company_id",
        "get_recruitment_benchmarks",
        "list_jobs_with_candidate_count",
        "get_job_details_with_days_open",
        "get_portfolio_metrics",
        "compare_jobs_by_ids",
        "get_sla_status",
        "get_bottleneck_analysis",
        "get_report_summary",
        "update_priority",
        "update_status",
    ]

    def _get_method_names(self):
        content = REPO_PATH.read_text()
        tree = ast.parse(content)
        methods = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in ast.walk(node):
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.add(item.name)
        return methods

    @pytest.mark.parametrize("method_name", REQUIRED_METHODS)
    def test_method_exists(self, method_name):
        methods = self._get_method_names()
        assert method_name in methods, (
            f"Method '{method_name}' not found in JobVacancyCRUDRepository. "
            "ADR-001 W1-004-B requires this method."
        )


class TestRequireCompanyId:
    """_require_company_id must raise ValueError on empty/None inputs."""

    def test_raises_on_empty_string(self):
        from app.domains.job_management.repositories.job_vacancy_crud_repository import (
            JobVacancyCRUDRepository,
        )
        with pytest.raises(ValueError, match="company_id"):
            JobVacancyCRUDRepository._require_company_id("")

    def test_raises_on_none(self):
        from app.domains.job_management.repositories.job_vacancy_crud_repository import (
            JobVacancyCRUDRepository,
        )
        with pytest.raises(ValueError, match="company_id"):
            JobVacancyCRUDRepository._require_company_id(None)

    def test_returns_value_on_valid(self):
        from app.domains.job_management.repositories.job_vacancy_crud_repository import (
            JobVacancyCRUDRepository,
        )
        result = JobVacancyCRUDRepository._require_company_id("test-company-123")
        assert result == "test-company-123"


@pytest.mark.asyncio
class TestToolWrappersDelegateToRepo:
    """Tool wrappers must call repo methods with correct arguments."""

    async def test_wrap_list_jobs_calls_repo(self):
        from unittest.mock import patch

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=None)

        mock_repo = AsyncMock()
        mock_repo.list_jobs_with_candidate_count = AsyncMock(
            return_value={"jobs": [], "total": 0}
        )

        with (
            patch(
                "app.domains.recruiter_assistant.agents.jobs_mgmt_tool_registry.AsyncSessionLocal",
                return_value=mock_db,
            ),
            patch(
                "app.domains.recruiter_assistant.agents.jobs_mgmt_tool_registry.JobVacancyCrudRepository",
                return_value=mock_repo,
            ),
        ):
            from app.domains.recruiter_assistant.agents.jobs_mgmt_tool_registry import (
                _wrap_list_jobs,
            )
            result = await _wrap_list_jobs(
                company_id="company-abc",
                status="active",
                department="engineering",
                limit=10,
            )

        assert result["success"] is True
        mock_repo.list_jobs_with_candidate_count.assert_called_once_with(
            company_id="company-abc",
            status="active",
            department="engineering",
            limit=10,
        )

    async def test_wrap_update_priority_maps_english_to_portuguese(self):
        from unittest.mock import patch

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=None)

        mock_repo = AsyncMock()
        mock_repo.update_priority = AsyncMock(
            return_value={"previous_priority": "baixa", "new_priority": "alta"}
        )

        with (
            patch(
                "app.domains.recruiter_assistant.agents.jobs_mgmt_tool_registry.AsyncSessionLocal",
                return_value=mock_db,
            ),
            patch(
                "app.domains.recruiter_assistant.agents.jobs_mgmt_tool_registry.JobVacancyCrudRepository",
                return_value=mock_repo,
            ),
        ):
            from app.domains.recruiter_assistant.agents.jobs_mgmt_tool_registry import (
                _wrap_update_priority,
            )
            result = await _wrap_update_priority(
                company_id="company-xyz",
                job_id="job-001",
                priority="high",
            )

        assert result["success"] is True
        assert result["data"]["new_priority"] == "alta"
        mock_repo.update_priority.assert_called_once_with(
            job_id="job-001",
            company_id="company-xyz",
            priority="alta",
        )

    async def test_wrap_pause_job_uses_update_status(self):
        from unittest.mock import patch

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=None)

        mock_repo = AsyncMock()
        mock_repo.update_status = AsyncMock(return_value=True)

        with (
            patch(
                "app.domains.recruiter_assistant.agents.jobs_mgmt_tool_registry.AsyncSessionLocal",
                return_value=mock_db,
            ),
            patch(
                "app.domains.recruiter_assistant.agents.jobs_mgmt_tool_registry.JobVacancyCrudRepository",
                return_value=mock_repo,
            ),
        ):
            from app.domains.recruiter_assistant.agents.jobs_mgmt_tool_registry import (
                _wrap_pause_job,
            )
            result = await _wrap_pause_job(
                company_id="company-abc",
                job_id="job-999",
                reason="Orcamento suspenso",
            )

        assert result["success"] is True
        assert result["data"]["new_status"] == "Pausada"
        mock_repo.update_status.assert_called_once_with(
            job_id="job-999",
            company_id="company-abc",
            new_status="Pausada",
        )

    async def test_wrap_view_job_details_not_found_returns_failure(self):
        from unittest.mock import patch

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=None)

        mock_repo = AsyncMock()
        mock_repo.get_job_details_with_days_open = AsyncMock(return_value=None)

        with (
            patch(
                "app.domains.recruiter_assistant.agents.jobs_mgmt_tool_registry.AsyncSessionLocal",
                return_value=mock_db,
            ),
            patch(
                "app.domains.recruiter_assistant.agents.jobs_mgmt_tool_registry.JobVacancyCrudRepository",
                return_value=mock_repo,
            ),
        ):
            from app.domains.recruiter_assistant.agents.jobs_mgmt_tool_registry import (
                _wrap_view_job_details,
            )
            result = await _wrap_view_job_details(
                company_id="company-abc",
                job_id="nonexistent-job",
            )

        assert result["success"] is False
        assert "nao encontrada" in result["message"]
