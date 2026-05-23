"""
TDD tests for W1-004-B Commit 4: talent_tool_registry SQL migration.

Verifies:
1. No inline SQL blocks remain in talent_tool_registry.py
2. CandidateRepository has all new W1-004-B methods
3. VacancyCandidateRepository has all new W1-004-B methods
4. _require_company_id raises on empty/None company_id
5. Behavioral tests: tool wrappers call repo with correct args
6. LGPD: gender not used in ORDER BY or WHERE in repo methods
"""
import ast
import re
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

WORKSPACE = Path("/home/runner/workspace/lia-agent-system")
REGISTRY_PATH = (
    WORKSPACE
    / "app/domains/recruiter_assistant/agents/talent_tool_registry.py"
)
CANDIDATE_REPO_PATH = (
    WORKSPACE
    / "app/domains/candidates/repositories/candidate_repository.py"
)
VC_REPO_PATH = (
    WORKSPACE
    / "app/domains/candidates/repositories/vacancy_candidate_repository.py"
)


class TestNoInlineSQLInRegistry:
    """ADR-001: no inline SQL blocks must remain in registry."""

    def test_no_raw_text_triple_quote_in_registry(self):
        """Registry must not contain text(triple_quote SQL blocks."""
        content = REGISTRY_PATH.read_text()
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

    def test_no_company_id_bypass_pattern(self):
        """Registry must not contain OR :company_id = \'\' cross-tenant bypass."""
        content = REGISTRY_PATH.read_text()
        matches = re.findall(r"OR :company_id\s*=\s*['\']\s*['\']", content)
        assert matches == [], (
            f"Found {len(matches)} cross-tenant bypass(es) in {REGISTRY_PATH.name}. "
            "Use fail-closed _require_company_id instead."
        )

    def test_registry_syntax_valid(self):
        content = REGISTRY_PATH.read_text()
        try:
            ast.parse(content)
        except SyntaxError as e:
            pytest.fail(f"Syntax error in {REGISTRY_PATH.name}: {e}")

    def test_candidate_repo_syntax_valid(self):
        content = CANDIDATE_REPO_PATH.read_text()
        try:
            ast.parse(content)
        except SyntaxError as e:
            pytest.fail(f"Syntax error in {CANDIDATE_REPO_PATH.name}: {e}")

    def test_vc_repo_syntax_valid(self):
        content = VC_REPO_PATH.read_text()
        try:
            ast.parse(content)
        except SyntaxError as e:
            pytest.fail(f"Syntax error in {VC_REPO_PATH.name}: {e}")


class TestCandidateRepositoryHasNewMethods:
    """CandidateRepository must expose all ADR-001 W1-004-B methods."""

    REQUIRED_METHODS = [
        "_require_company_id",
        "search_by_skills_and_experience",
        "get_full_profile",
        "list_for_recommendations",
        "list_for_report",
        "get_skill_set",
        "get_applications_summary",
    ]

    def _get_method_names(self):
        content = CANDIDATE_REPO_PATH.read_text()
        tree = ast.parse(content)
        methods = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in ast.walk(node):
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.add(item.name)
        return methods

    @pytest.mark.parametrize("method_name", REQUIRED_METHODS)
    def test_candidate_repo_method_exists(self, method_name):
        methods = self._get_method_names()
        assert method_name in methods, (
            f"Method '{method_name}' not found in CandidateRepository. "
            "ADR-001 W1-004-B requires this method."
        )


class TestVacancyCandidateRepositoryHasNewMethods:
    """VacancyCandidateRepository must expose all ADR-001 W1-004-B methods."""

    REQUIRED_METHODS = [
        "_require_company_id",
        "list_for_talent_funnel",
        "rank_for_job",
        "update_match_percentage",
        "get_pool_benchmarks",
        "get_pool_health",
    ]

    def _get_method_names(self):
        content = VC_REPO_PATH.read_text()
        tree = ast.parse(content)
        methods = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in ast.walk(node):
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.add(item.name)
        return methods

    @pytest.mark.parametrize("method_name", REQUIRED_METHODS)
    def test_vc_repo_method_exists(self, method_name):
        methods = self._get_method_names()
        assert method_name in methods, (
            f"Method '{method_name}' not found in VacancyCandidateRepository. "
            "ADR-001 W1-004-B requires this method."
        )


class TestRequireCompanyId:
    """_require_company_id must raise ValueError on empty/None inputs."""

    def test_candidate_repo_raises_on_empty_string(self):
        from app.domains.candidates.repositories.candidate_repository import (
            CandidateRepository,
        )
        with pytest.raises(ValueError, match="company_id"):
            CandidateRepository._require_company_id("")

    def test_candidate_repo_raises_on_none(self):
        from app.domains.candidates.repositories.candidate_repository import (
            CandidateRepository,
        )
        with pytest.raises(ValueError, match="company_id"):
            CandidateRepository._require_company_id(None)

    def test_candidate_repo_returns_value_on_valid(self):
        from app.domains.candidates.repositories.candidate_repository import (
            CandidateRepository,
        )
        result = CandidateRepository._require_company_id("test-company-123")
        assert result == "test-company-123"

    def test_vc_repo_raises_on_empty_string(self):
        from app.domains.candidates.repositories.vacancy_candidate_repository import (
            VacancyCandidateRepository,
        )
        with pytest.raises(ValueError, match="company_id"):
            VacancyCandidateRepository._require_company_id("")

    def test_vc_repo_raises_on_none(self):
        from app.domains.candidates.repositories.vacancy_candidate_repository import (
            VacancyCandidateRepository,
        )
        with pytest.raises(ValueError, match="company_id"):
            VacancyCandidateRepository._require_company_id(None)

    def test_vc_repo_returns_value_on_valid(self):
        from app.domains.candidates.repositories.vacancy_candidate_repository import (
            VacancyCandidateRepository,
        )
        result = VacancyCandidateRepository._require_company_id("company-xyz")
        assert result == "company-xyz"


class TestGenderNotUsedInRanking:
    """LGPD ADR-LGPD-001: gender must not appear in ORDER BY or WHERE in repo methods."""

    def _check_no_gender_in_ranking_clauses(self, content: str) -> list[str]:
        """Return lines where gender appears in ORDER BY or WHERE context."""
        violations = []
        lines = content.split("\n")
        in_order_by = False
        in_where = False
        for i, line in enumerate(lines, start=1):
            stripped = line.upper()
            if "ORDER BY" in stripped:
                in_order_by = True
            if "WHERE" in stripped:
                in_where = True
            if in_order_by or in_where:
                if "gender" in line.lower():
                    violations.append(f"Line {i}: {line.strip()}")
            # Reset on new method/blank
            if line.strip() == "" or "async def " in line or "def " in line:
                in_order_by = False
                in_where = False
        return violations

    def test_gender_not_in_ranking_clauses_candidate_repo(self):
        content = CANDIDATE_REPO_PATH.read_text()
        violations = self._check_no_gender_in_ranking_clauses(content)
        assert violations == [], (
            f"LGPD violation: gender found in ORDER BY/WHERE in CandidateRepository:\n"
            + "\n".join(violations)
        )

    def test_gender_not_in_ranking_clauses_vc_repo(self):
        content = VC_REPO_PATH.read_text()
        violations = self._check_no_gender_in_ranking_clauses(content)
        assert violations == [], (
            f"LGPD violation: gender found in ORDER BY/WHERE in VacancyCandidateRepository:\n"
            + "\n".join(violations)
        )


@pytest.mark.asyncio
class TestToolWrappersDelegateToRepo:
    """Tool wrappers must call repo methods with correct arguments."""

    async def test_wrap_search_candidates_calls_repo(self):
        from unittest.mock import patch

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=None)

        mock_repo = AsyncMock()
        mock_repo.search_by_skills_and_experience = AsyncMock(
            return_value={"results": [], "total": 0}
        )

        with (
            patch(
                "app.domains.recruiter_assistant.agents.talent_tool_registry.AsyncSessionLocal",
                return_value=mock_db,
            ),
            patch(
                "app.domains.recruiter_assistant.agents.talent_tool_registry.CandidateRepository",
                return_value=mock_repo,
            ),
        ):
            from app.domains.recruiter_assistant.agents.talent_tool_registry import (
                _wrap_search_candidates,
            )
            result = await _wrap_search_candidates(
                company_id="company-abc",
                query="python",
                filters={"location": "sao paulo", "min_experience": 3},
                limit=10,
            )

        assert result["success"] is True
        mock_repo.search_by_skills_and_experience.assert_called_once_with(
            company_id="company-abc",
            query="python",
            location="sao paulo",
            min_experience=3,
            limit=10,
        )

    async def test_wrap_list_candidates_calls_vc_repo(self):
        from unittest.mock import patch

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=None)

        mock_vc_repo = AsyncMock()
        mock_vc_repo.list_for_talent_funnel = AsyncMock(
            return_value={"candidates": [], "total": 0}
        )

        with (
            patch(
                "app.domains.recruiter_assistant.agents.talent_tool_registry.AsyncSessionLocal",
                return_value=mock_db,
            ),
            patch(
                "app.domains.recruiter_assistant.agents.talent_tool_registry.VacancyCandidateRepository",
                return_value=mock_vc_repo,
            ),
        ):
            from app.domains.recruiter_assistant.agents.talent_tool_registry import (
                _wrap_list_candidates,
            )
            result = await _wrap_list_candidates(
                company_id="company-xyz",
                status="active",
                vacancy_id="vac-001",
                limit=20,
            )

        assert result["success"] is True
        mock_vc_repo.list_for_talent_funnel.assert_called_once_with(
            company_id="company-xyz",
            status="active",
            vacancy_id="vac-001",
            limit=20,
        )

    async def test_wrap_view_candidate_profile_not_found(self):
        from unittest.mock import patch

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=None)

        mock_repo = AsyncMock()
        mock_repo.get_full_profile = AsyncMock(return_value=None)

        with (
            patch(
                "app.domains.recruiter_assistant.agents.talent_tool_registry.AsyncSessionLocal",
                return_value=mock_db,
            ),
            patch(
                "app.domains.recruiter_assistant.agents.talent_tool_registry.CandidateRepository",
                return_value=mock_repo,
            ),
        ):
            from app.domains.recruiter_assistant.agents.talent_tool_registry import (
                _wrap_view_candidate_profile,
            )
            result = await _wrap_view_candidate_profile(
                company_id="company-abc",
                candidate_id="nonexistent-id",
            )

        assert result["success"] is False
        assert "nao encontrado" in result["message"]

    async def test_wrap_rank_candidates_calls_vc_repo(self):
        from unittest.mock import patch

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=None)

        mock_vc_repo = AsyncMock()
        mock_vc_repo.rank_for_job = AsyncMock(return_value=[
            {"position": 1, "candidate_id": "cand-1", "lia_score": 4.5}
        ])

        with (
            patch(
                "app.domains.recruiter_assistant.agents.talent_tool_registry.AsyncSessionLocal",
                return_value=mock_db,
            ),
            patch(
                "app.domains.recruiter_assistant.agents.talent_tool_registry.VacancyCandidateRepository",
                return_value=mock_vc_repo,
            ),
        ):
            from app.domains.recruiter_assistant.agents.talent_tool_registry import (
                _wrap_rank_candidates,
            )
            result = await _wrap_rank_candidates(
                company_id="company-abc",
                vacancy_id="vac-001",
                criteria="skills",
            )

        assert result["success"] is True
        assert result["data"]["ranked_count"] == 1
        mock_vc_repo.rank_for_job.assert_called_once_with(
            vacancy_id="vac-001",
            company_id="company-abc",
            criteria="skills",
        )

    async def test_wrap_generate_report_calls_candidate_repo(self):
        from unittest.mock import patch

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=None)

        mock_repo = AsyncMock()
        mock_repo.get_applications_summary = AsyncMock(
            return_value={"total_applications": 42, "approved": 10, "rejected": 5}
        )

        with (
            patch(
                "app.domains.recruiter_assistant.agents.talent_tool_registry.AsyncSessionLocal",
                return_value=mock_db,
            ),
            patch(
                "app.domains.recruiter_assistant.agents.talent_tool_registry.CandidateRepository",
                return_value=mock_repo,
            ),
        ):
            from app.domains.recruiter_assistant.agents.talent_tool_registry import (
                _wrap_generate_report,
            )
            result = await _wrap_generate_report(
                company_id="company-abc",
                report_type="summary",
                period="month",
            )

        assert result["success"] is True
        assert result["data"]["summary"]["total_applications"] == 42
        mock_repo.get_applications_summary.assert_called_once_with(
            company_id="company-abc",
            period_days=30,
        )

    async def test_wrap_get_talent_pool_benchmarks_calls_vc_repo(self):
        from unittest.mock import patch

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=None)

        mock_vc_repo = AsyncMock()
        mock_vc_repo.get_pool_benchmarks = AsyncMock(
            return_value={"pool_size": 25, "avg_score": 3.8, "stage_distribution": {"triagem": 10}}
        )

        with (
            patch(
                "app.domains.recruiter_assistant.agents.talent_tool_registry.AsyncSessionLocal",
                return_value=mock_db,
            ),
            patch(
                "app.domains.recruiter_assistant.agents.talent_tool_registry.VacancyCandidateRepository",
                return_value=mock_vc_repo,
            ),
        ):
            from app.domains.recruiter_assistant.agents.talent_tool_registry import (
                _wrap_get_talent_pool_benchmarks,
            )
            result = await _wrap_get_talent_pool_benchmarks(
                company_id="company-abc",
                vacancy_id="vac-001",
            )

        assert result["success"] is True
        assert result["data"]["pool_size"] == 25
        mock_vc_repo.get_pool_benchmarks.assert_called_once_with(
            company_id="company-abc",
            vacancy_id="vac-001",
        )
