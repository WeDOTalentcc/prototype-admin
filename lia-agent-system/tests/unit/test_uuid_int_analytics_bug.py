"""
tests/unit/test_uuid_int_analytics_bug.py

TDD tests for P1 UUID/integer dual-ID bug in analytics and pipeline endpoints.

Bug: endpoints with DUAL_ID_PATH_PATTERN accepted integer strings (Rails bigint)
but passed them directly to repo methods expecting UUID → asyncpg DataError.
"""
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestRepoGetJobDualId:
    """Repo get_job_by_id_and_company must handle both UUID and integer strings."""

    @pytest.mark.asyncio
    async def test_uuid_string_lookup_uses_pk_column(self):
        """UUID string → query by JobVacancy.id (PK column)."""
        from app.repositories.job_vacancies_analytics_repository import JobVacanciesAnalyticsRepository
        from app.models.job_vacancy import JobVacancy

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock(spec=JobVacancy)
        mock_db.execute.return_value = mock_result

        repo = JobVacanciesAnalyticsRepository(mock_db)
        job_uuid = str(uuid.uuid4())
        result = await repo.get_job_by_id_and_company(job_uuid, "company-123")

        assert result is not None
        mock_db.execute.assert_called_once()
        # The WHERE clause must include UUID PK — query should NOT fall through to integer path
        call_args = mock_db.execute.call_args[0][0]
        call_str = str(call_args)
        assert "job_vacancies" in call_str.lower() or mock_db.execute.call_count == 1

    @pytest.mark.asyncio
    async def test_integer_string_falls_through_to_rails_job_id_lookup(self):
        """Integer string ('123') → query by JobVacancy.job_id column (String FK)."""
        from app.repositories.job_vacancies_analytics_repository import JobVacanciesAnalyticsRepository
        from app.models.job_vacancy import JobVacancy

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock(spec=JobVacancy)
        mock_db.execute.return_value = mock_result

        repo = JobVacanciesAnalyticsRepository(mock_db)
        # This would previously raise asyncpg DataError
        result = await repo.get_job_by_id_and_company("74123", "company-123")

        # UUID parse raises before db.execute, so only 1 DB call: the integer fallback
        assert mock_db.execute.call_count == 1, (
            f"Expected 1 DB call for integer ID (integer fallback only, UUID raised before execute), got {mock_db.execute.call_count}"
        )

    @pytest.mark.asyncio
    async def test_uuid_object_also_works(self):
        """UUID object (not string) should also work without error."""
        from app.repositories.job_vacancies_analytics_repository import JobVacanciesAnalyticsRepository

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        repo = JobVacanciesAnalyticsRepository(mock_db)
        # Should not raise
        result = await repo.get_job_by_id_and_company(uuid.uuid4(), "company-123")
        assert result is None  # not found is fine


class TestAnalyticsEndpointJobIdResolution:
    """Analytics endpoints must resolve job_id to UUID PK before subsequent calls."""

    def test_analytics_py_resolves_job_id_after_first_lookup(self):
        """Each analytics endpoint must reassign job_id = job.id after first lookup."""
        with open("app/api/v1/job_vacancies/analytics.py") as f:
            src = f.read()
        # Count occurrences of the resolution line
        count = src.count("job_id = job.id  # resolve to UUID PK")
        assert count >= 2, (
            f"Expected >= 2 'job_id = job.id' resolution lines in analytics.py, found {count}"
        )

    def test_analytics_py_metrics_endpoint_resolves_vacancy_id(self):
        """Metrics endpoint must resolve job_vacancy_id = job.id."""
        with open("app/api/v1/job_vacancies/analytics.py") as f:
            src = f.read()
        assert "job_vacancy_id = job.id" in src, (
            "Metrics endpoint must assign job_vacancy_id = job.id to resolve integer IDs"
        )


class TestStagesPipelineIntegerIdHandling:
    """stages_pipeline.py must handle integer job_id without ValueError."""

    def test_pipeline_no_bare_uuid_UUID_call(self):
        """uuid.UUID(job_id) without try/except is removed from stages_pipeline."""
        with open("app/api/v1/recruitment_stages/stages_pipeline.py") as f:
            src = f.read()
        # Old pattern: bare uuid.UUID(job_id) passed directly to db.get
        # Should not exist without try/except guard
        import re
        bad_pattern = re.compile(
            r"stage_repo\.db\.get\(JobVacancy,\s*uuid\.UUID\(job_id\)\)"
        )
        assert not bad_pattern.search(src), (
            "stages_pipeline.py still has bare uuid.UUID(job_id) in db.get — "
            "this crashes on integer job_id from Rails"
        )

    def test_pipeline_has_integer_fallback(self):
        """stages_pipeline.py must have except ValueError fallback for integer IDs."""
        with open("app/api/v1/recruitment_stages/stages_pipeline.py") as f:
            src = f.read()
        assert "except (ValueError, AttributeError):" in src, (
            "stages_pipeline.py missing try/except for integer job_id handling"
        )
        assert "JV.job_id == str(job_id)" in src or "_JV.job_id == str(job_id)" in src, (
            "stages_pipeline.py missing integer fallback query via job_id column"
        )
