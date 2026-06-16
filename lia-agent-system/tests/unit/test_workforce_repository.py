"""TDD — WorkforceRepository: 3 new analytical query methods (ADR-001 T9).

Extracted from app/domains/talent_intelligence/tools/workforce_planning_tools.py
where 3 raw SQL queries lived behind ADR-001-EXEMPT markers. Moving them to the
repository layer is the canonical fix (spirit of ADR-001):
  1. get_open_jobs_summary   — COUNT/SUM job_vacancies by status
  2. get_historical_hire_metrics — AVG time-to-fill + count of closed vacancies
  3. get_internal_employee_count — COUNT active internal candidates
"""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.repositories.workforce_repository import WorkforceRepository


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.execute = AsyncMock()
    return db


# ---------------------------------------------------------------------------
# _require_company_id guard (inherited from existing repo pattern)
# ---------------------------------------------------------------------------

class TestRequireCompanyId:
    def test_raises_on_empty_string(self):
        with pytest.raises(ValueError, match="company_id"):
            WorkforceRepository._require_company_id("")

    def test_raises_on_none(self):
        with pytest.raises(ValueError, match="company_id"):
            WorkforceRepository._require_company_id(None)  # type: ignore

    def test_passes_on_valid(self):
        # Must not raise
        WorkforceRepository._require_company_id("tenant-123")


# ---------------------------------------------------------------------------
# get_open_jobs_summary
# ---------------------------------------------------------------------------

class TestGetOpenJobsSummary:
    @pytest.mark.asyncio
    async def test_fail_closed_without_company_id(self, mock_db):
        """Multi-tenancy: empty company_id must raise before any DB call."""
        repo = WorkforceRepository(mock_db)
        with pytest.raises(ValueError, match="company_id"):
            await repo.get_open_jobs_summary(company_id="")
        mock_db.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_returns_expected_shape(self, mock_db):
        """Returns dict with correct keys and values."""
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = {
            "open_positions": 5,
            "active_count": 3,
            "pipeline_count": 2,
        }
        mock_db.execute.return_value = mock_result

        repo = WorkforceRepository(mock_db)
        result = await repo.get_open_jobs_summary(company_id="tenant-abc")

        mock_db.execute.assert_awaited_once()
        assert result["open_positions"] == 5
        assert result["active_count"] == 3
        assert result["pipeline_count"] == 2

    @pytest.mark.asyncio
    async def test_returns_zeros_when_no_rows(self, mock_db):
        """When DB returns None mapping, result falls back to zero-dict."""
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = None
        mock_db.execute.return_value = mock_result

        repo = WorkforceRepository(mock_db)
        result = await repo.get_open_jobs_summary(company_id="tenant-xyz")

        assert result["open_positions"] == 0
        assert result["active_count"] == 0
        assert result["pipeline_count"] == 0

    @pytest.mark.asyncio
    async def test_department_filter_accepted(self, mock_db):
        """Optional department param must not raise and is forwarded to DB."""
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = None
        mock_db.execute.return_value = mock_result

        repo = WorkforceRepository(mock_db)
        result = await repo.get_open_jobs_summary(
            company_id="tenant-abc", department="Engineering"
        )
        assert isinstance(result, dict)
        mock_db.execute.assert_awaited_once()


# ---------------------------------------------------------------------------
# get_historical_hire_metrics
# ---------------------------------------------------------------------------

class TestGetHistoricalHireMetrics:
    @pytest.mark.asyncio
    async def test_fail_closed_without_company_id(self, mock_db):
        repo = WorkforceRepository(mock_db)
        with pytest.raises(ValueError, match="company_id"):
            await repo.get_historical_hire_metrics(company_id="")
        mock_db.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_returns_expected_shape(self, mock_db):
        """Returns dict with correct total_hires and avg_time_to_fill values."""
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = {
            "total_hires": 12,
            "avg_time_to_fill": 38.5,
        }
        mock_db.execute.return_value = mock_result

        repo = WorkforceRepository(mock_db)
        result = await repo.get_historical_hire_metrics(company_id="tenant-abc")

        mock_db.execute.assert_awaited_once()
        assert result["total_hires"] == 12
        assert result["avg_time_to_fill"] == pytest.approx(38.5)

    @pytest.mark.asyncio
    async def test_default_avg_ttf_when_no_data(self, mock_db):
        """Falls back to 45-day benchmark when DB returns None (no hires)."""
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = None
        mock_db.execute.return_value = mock_result

        repo = WorkforceRepository(mock_db)
        result = await repo.get_historical_hire_metrics(company_id="tenant-xyz")

        assert result["total_hires"] == 0
        assert result["avg_time_to_fill"] == 45.0

    @pytest.mark.asyncio
    async def test_lookback_days_param_accepted(self, mock_db):
        """Custom lookback_days must not raise."""
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = None
        mock_db.execute.return_value = mock_result

        repo = WorkforceRepository(mock_db)
        result = await repo.get_historical_hire_metrics(
            company_id="tenant-abc", lookback_days=90, department="Sales"
        )
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# get_internal_employee_count
# ---------------------------------------------------------------------------

class TestGetInternalEmployeeCount:
    @pytest.mark.asyncio
    async def test_fail_closed_without_company_id(self, mock_db):
        repo = WorkforceRepository(mock_db)
        with pytest.raises(ValueError, match="company_id"):
            await repo.get_internal_employee_count(company_id="")
        mock_db.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_returns_int_count(self, mock_db):
        """Returns total_employees as int."""
        # Use a real dict — mappings().first() returns a dict-like RowMapping;
        # the repository calls row.get("total_employees") which matches dict.get().
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = {"total_employees": 42}
        mock_db.execute.return_value = mock_result

        repo = WorkforceRepository(mock_db)
        count = await repo.get_internal_employee_count(company_id="tenant-abc")

        mock_db.execute.assert_awaited_once()
        assert count == 42

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_rows(self, mock_db):
        """When DB returns None, employee count falls back to 0."""
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = None
        mock_db.execute.return_value = mock_result

        repo = WorkforceRepository(mock_db)
        count = await repo.get_internal_employee_count(company_id="tenant-xyz")

        assert count == 0

    @pytest.mark.asyncio
    async def test_department_filter_accepted(self, mock_db):
        """Optional department param must be forwarded without error."""
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = None
        mock_db.execute.return_value = mock_result

        repo = WorkforceRepository(mock_db)
        count = await repo.get_internal_employee_count(
            company_id="tenant-abc", department="Engineering"
        )
        assert count == 0
        mock_db.execute.assert_awaited_once()
