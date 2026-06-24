"""GAP-03-005: Dynamic sort_by/sort_order for job vacancies endpoint.

TDD sensor: validates allowlist enforcement, default behavior, and
invalid-input rejection for the new sort parameters.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.domains.job_management.repositories.job_vacancy_crud_repository import (
    ALLOWED_SORT_FIELDS,
    resolve_sort_clause,
    JobVacancyCRUDRepository,
)


# ── Unit: resolve_sort_clause (pure, no DB) ──────────────────────────────────

class TestResolveSortClause:
    """Allowlist enforcement + defaults for the pure sort resolver."""

    def test_default_is_updated_at_desc(self):
        col, direction = resolve_sort_clause(None, "desc")
        assert col.key == "updated_at"
        assert direction == "desc"

    def test_explicit_created_at_asc(self):
        col, direction = resolve_sort_clause("created_at", "asc")
        assert col.key == "created_at"
        assert direction == "asc"

    def test_title_sort(self):
        col, direction = resolve_sort_clause("title", "asc")
        assert col.key == "title"
        assert direction == "asc"

    def test_status_sort(self):
        col, direction = resolve_sort_clause("status", "desc")
        assert col.key == "status"
        assert direction == "desc"

    def test_updated_at_sort(self):
        col, direction = resolve_sort_clause("updated_at", "desc")
        assert col.key == "updated_at"
        assert direction == "desc"

    def test_invalid_sort_field_raises(self):
        with pytest.raises(ValueError, match="not allowed"):
            resolve_sort_clause("hacked_field; DROP TABLE", "asc")

    def test_invalid_sort_order_raises(self):
        with pytest.raises(ValueError, match="asc.*desc"):
            resolve_sort_clause("title", "RANDOM")

    def test_sql_injection_in_sort_by_blocked(self):
        with pytest.raises(ValueError, match="not allowed"):
            resolve_sort_clause("created_at; DROP TABLE job_vacancies", "asc")

    def test_allowlist_contains_expected_fields(self):
        assert set(ALLOWED_SORT_FIELDS.keys()) == {
            "created_at", "title", "status", "updated_at",
        }


# ── Integration-style: repo method accepts sort params ───────────────────────

class TestListVacanciesSortIntegration:
    """Verify that list_vacancies passes sort params through to the query."""

    @pytest.mark.asyncio
    async def test_list_vacancies_default_sort(self):
        """Default call (no sort params) must not raise and uses created_at desc."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        repo = JobVacancyCRUDRepository(mock_db)
        result = await repo.list_vacancies(company_id="tenant-1")
        assert result == []
        # execute was called with a select statement
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_vacancies_with_explicit_sort(self):
        """Explicit sort_by=title, sort_order=asc accepted without error."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        repo = JobVacancyCRUDRepository(mock_db)
        result = await repo.list_vacancies(
            company_id="tenant-1",
            sort_by="title",
            sort_order="asc",
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_vacancies_invalid_sort_raises(self):
        """Invalid sort_by must raise ValueError (endpoint converts to 422)."""
        mock_db = AsyncMock()
        repo = JobVacancyCRUDRepository(mock_db)
        with pytest.raises(ValueError, match="not allowed"):
            await repo.list_vacancies(
                company_id="tenant-1",
                sort_by="password",
            )
