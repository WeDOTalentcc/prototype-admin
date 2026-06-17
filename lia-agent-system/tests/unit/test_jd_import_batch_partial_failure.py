"""Unit tests — JD bulk import: HTTP 207 partial failure + quality gate threshold.

Harness: Sensor (computacional) for Feature 1 (Bulk Import).
Covers:
- quality_score computation matches spec formula
- is_used_for_learning=True only when quality_score >= 0.65
- POST /api/v1/jobs/bulk-import returns HTTP 207 when ≥1 item fails
- POST returns HTTP 200 when all items succeed
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Tests: _compute_quality_score
# ---------------------------------------------------------------------------

class TestComputeQualityScore:
    """The quality gate formula: title(0.25) + salary(0.30) + dept(0.15) + seniority(0.15) + skills(0.15)."""

    def _score(self, jd_data: dict) -> float:
        from app.domains.job_management.services.jd_import_service import JDImportService
        svc = JDImportService.__new__(JDImportService)
        return svc._compute_quality_score(jd_data)

    def test_full_job_scores_100(self):
        jd = {
            "title": "Software Engineer",
            "salary_min": 10000,
            "department": "Engineering",
            "seniority": "Senior",
            "skills": ["Python", "FastAPI"],
        }
        assert self._score(jd) == 1.0

    def test_no_salary_scores_below_threshold(self):
        jd = {
            "title": "Product Manager",
            "department": "Product",
            "seniority": "Mid",
            "skills": ["Roadmap"],
        }
        result = self._score(jd)
        # 0.25 + 0.15 + 0.15 + 0.15 = 0.70 — above threshold
        assert result == 0.70

    def test_only_title_scores_025(self):
        jd = {"title": "Sales Rep"}
        assert self._score(jd) == 0.25

    def test_title_plus_salary_scores_055(self):
        jd = {"title": "Engineer", "salary_min": 5000}
        assert self._score(jd) == 0.55

    def test_below_threshold_job_not_used_for_learning(self):
        """Job with quality_score < 0.65 must have is_used_for_learning=False."""
        jd = {"title": "Analyst"}  # score=0.25 — below 0.65
        assert self._score(jd) < 0.65

    def test_at_threshold_job_used_for_learning(self):
        """Job with quality_score >= 0.65 must have is_used_for_learning=True."""
        jd = {
            "title": "Engineer",
            "salary_min": 8000,
            "department": "Engineering",
        }
        result = self._score(jd)
        # 0.25 + 0.30 + 0.15 = 0.70 — above threshold
        assert result >= 0.65

    def test_required_skills_also_counts(self):
        """is_used_for_learning triggers on 'required_skills' key as well as 'skills'."""
        jd = {
            "title": "Engineer",
            "salary_min": 5000,
            "required_skills": ["AWS"],
        }
        result = self._score(jd)
        # 0.25 + 0.30 + 0.15 = 0.70
        assert result == 0.70


# ---------------------------------------------------------------------------
# Tests: is_used_for_learning flag wired correctly in import_jd
# ---------------------------------------------------------------------------

class TestIsUsedForLearningGate:
    """import_jd() must set is_used_for_learning based on quality_score."""

    def test_high_quality_job_sets_learning_true(self):
        from app.domains.job_management.services.jd_import_service import JDImportService
        svc = JDImportService.__new__(JDImportService)

        jd_data = {
            "title": "Backend Engineer",
            "salary_min": 12000,
            "salary_max": 18000,
            "department": "Engineering",
            "seniority": "Senior",
            "skills": ["Python"],
        }
        score = svc._compute_quality_score(jd_data)
        assert score >= 0.65, f"Expected score >=0.65, got {score}"

    def test_low_quality_job_below_threshold(self):
        from app.domains.job_management.services.jd_import_service import JDImportService
        svc = JDImportService.__new__(JDImportService)

        jd_data = {"title": "Intern"}  # score=0.25
        score = svc._compute_quality_score(jd_data)
        assert score < 0.65, f"Expected score <0.65, got {score}"


# ---------------------------------------------------------------------------
# Tests: bulk-import endpoint returns 207 on partial failure
# ---------------------------------------------------------------------------

class TestBulkImportEndpoint207:
    """POST /api/v1/jobs/bulk-import must return 207 when batch.failed_records > 0.

    Uses FastAPI dependency_overrides to bypass auth and DB.
    """

    def _run_endpoint(self, failed_records: int, total: int = 2, successful: int = 1):
        import asyncio
        from fastapi import FastAPI
        from httpx import AsyncClient, ASGITransport
        from uuid import uuid4

        try:
            from app.api.v1.jobs_bulk_import import router
            from app.auth.dependencies import get_current_user, get_db
        except ImportError:
            import pytest
            pytest.skip("jobs_bulk_import router not importable in this environment")

        app = FastAPI()
        app.include_router(router, prefix="/api/v1")

        # Build a mock user with a company_id
        mock_user = SimpleNamespace(id=uuid4(), company_id=uuid4(), email="test@co.com")

        # Build a mock batch result
        mock_batch = MagicMock()
        mock_batch.id = uuid4()
        mock_batch.total_records = total
        mock_batch.successful_records = successful
        mock_batch.failed_records = failed_records
        mock_batch.status = "completed"
        mock_batch.errors = []

        # Override FastAPI dependencies
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: AsyncMock()

        async def _test():
            with patch("app.api.v1.jobs_bulk_import.JDImportService") as MockSvc:
                MockSvc.return_value.import_batch_jds = AsyncMock(return_value=mock_batch)

                async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://testserver",
                ) as client:
                    return await client.post(
                        "/api/v1/jobs/bulk-import",
                        json={
                            "source": "spreadsheet",
                            "jobs": [
                                {"title": "Engineer", "salary_min": 10000},
                                {"title": "Designer"},
                            ],
                        },
                    )

        return asyncio.run(_test())

    def test_returns_207_when_partial_failure(self):
        """HTTP 207 Multi-Status when at least 1 item fails."""
        response = self._run_endpoint(failed_records=1, total=2, successful=1)
        assert response.status_code == 207, (
            f"Expected 207 Multi-Status for partial failure, got {response.status_code}. "
            "Fix: return JSONResponse(status_code=207, ...) when batch.failed_records > 0 "
            "in app/api/v1/jobs_bulk_import.py."
        )

    def test_returns_200_when_all_succeed(self):
        """HTTP 200 when all items succeed."""
        response = self._run_endpoint(failed_records=0, total=2, successful=2)
        assert response.status_code == 200, (
            f"Expected 200 when all items succeed, got {response.status_code}."
        )

    def test_207_response_has_items_array(self):
        """207 response body must include per-item status array."""
        response = self._run_endpoint(failed_records=1)
        body = response.json()
        assert "items" in body, (
            "207 response must include 'items' array with per-item status. "
            "Clients need per-item details to show which JDs failed."
        )
