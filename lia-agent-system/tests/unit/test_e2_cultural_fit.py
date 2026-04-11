"""E2 — Fit Cultural com Dados de Entrevista"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from uuid import uuid4


COMPANY_ID = str(uuid4())
CANDIDATE_ID = str(uuid4())
JOB_ID = str(uuid4())


class TestCulturalFitService:

    @pytest.mark.asyncio
    async def test_compute_integrated_fit_returns_result(self):
        from app.shared.services.cultural_fit_integration_service import (
            CulturalFitIntegrationService, CulturalFitResult
        )
        svc = CulturalFitIntegrationService()
        db = MagicMock()

        with patch.object(svc, "_get_wsi_score", new_callable=AsyncMock, return_value=75.0):
            with patch.object(svc, "_get_interview_score", new_callable=AsyncMock, return_value=80.0):
                with patch.object(svc, "_get_culture_alignment", new_callable=AsyncMock, return_value=70.0):
                    result = await svc.compute_integrated_fit(
                        CANDIDATE_ID, JOB_ID, COMPANY_ID, db
                    )

        assert isinstance(result, CulturalFitResult)
        assert 0 <= result.overall_score <= 100

    @pytest.mark.asyncio
    async def test_weights_sum_to_1(self):
        from app.shared.services.cultural_fit_integration_service import WSI_WEIGHT, INTERVIEW_WEIGHT, CULTURE_WEIGHT
        total = WSI_WEIGHT + INTERVIEW_WEIGHT + CULTURE_WEIGHT
        assert abs(total - 1.0) < 0.001

    @pytest.mark.asyncio
    async def test_fail_open_on_db_error(self):
        from app.shared.services.cultural_fit_integration_service import CulturalFitIntegrationService
        svc = CulturalFitIntegrationService()
        db = MagicMock()

        with patch.object(svc, "_get_wsi_score", new_callable=AsyncMock, side_effect=RuntimeError("DB error")):
            result = await svc.compute_integrated_fit(CANDIDATE_ID, JOB_ID, COMPANY_ID, db)

        assert result.overall_score == 50.0
        assert result.error is not None

    def test_cultural_fit_result_to_dict(self):
        from app.shared.services.cultural_fit_integration_service import CulturalFitResult
        from datetime import datetime

        r = CulturalFitResult(
            candidate_id=CANDIDATE_ID,
            job_id=JOB_ID,
            overall_score=72.5,
            wsi_contribution=75.0,
            interview_contribution=70.0,
            culture_alignment=65.0,
            computed_at=datetime(2026, 3, 15),
        )
        d = r.to_dict()
        assert d["overall_score"] == 72.5
        assert "2026-03-15" in d["computed_at"]

    @pytest.mark.asyncio
    async def test_wsi_score_fallback_returns_50(self):
        from app.shared.services.cultural_fit_integration_service import CulturalFitIntegrationService
        svc = CulturalFitIntegrationService()
        db = MagicMock()
        db.execute = AsyncMock(side_effect=RuntimeError("no table"))

        score = await svc._get_wsi_score(CANDIDATE_ID, JOB_ID, db)
        assert score == 50.0

    @pytest.mark.asyncio
    async def test_interview_score_fallback_returns_50(self):
        from app.shared.services.cultural_fit_integration_service import CulturalFitIntegrationService
        svc = CulturalFitIntegrationService()
        db = MagicMock()
        db.execute = AsyncMock(side_effect=RuntimeError("no table"))

        score = await svc._get_interview_score(CANDIDATE_ID, JOB_ID, db)
        assert score == 50.0

    @pytest.mark.asyncio
    async def test_culture_alignment_fallback_returns_50(self):
        from app.shared.services.cultural_fit_integration_service import CulturalFitIntegrationService
        svc = CulturalFitIntegrationService()
        db = MagicMock()

        with patch("app.services.culture_analyzer_service.CultureAnalyzerService", side_effect=ImportError):
            score = await svc._get_culture_alignment(CANDIDATE_ID, JOB_ID, COMPANY_ID, db)

        assert score == 50.0

    def test_endpoint_requires_company_header(self):
        from fastapi import FastAPI
        from app.api.v1.cultural_fit import router
        from app.core.database import get_db

        app = FastAPI()
        app.include_router(router, prefix="/api/v1")

        async def mock_db():
            yield MagicMock()

        app.dependency_overrides[get_db] = mock_db
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get(f"/api/v1/candidates/{CANDIDATE_ID}/cultural-fit?job_id={JOB_ID}")
        assert response.status_code == 401

    def test_endpoint_with_valid_header_returns_result(self):
        from fastapi import FastAPI
        from app.api.v1.cultural_fit import router
        from app.core.database import get_db
        from app.shared.services.cultural_fit_integration_service import CulturalFitResult
        from datetime import datetime

        app = FastAPI()
        app.include_router(router, prefix="/api/v1")

        async def mock_db():
            yield MagicMock()

        app.dependency_overrides[get_db] = mock_db

        mock_result = CulturalFitResult(
            candidate_id=CANDIDATE_ID,
            job_id=JOB_ID,
            overall_score=75.0,
            wsi_contribution=80.0,
            interview_contribution=70.0,
            culture_alignment=65.0,
            computed_at=datetime.utcnow(),
        )

        with patch(
            "app.services.cultural_fit_integration_service.CulturalFitIntegrationService.compute_integrated_fit",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            client = TestClient(app)
            response = client.get(
                f"/api/v1/candidates/{CANDIDATE_ID}/cultural-fit?job_id={JOB_ID}",
                headers={"X-Company-ID": COMPANY_ID},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["overall_score"] == 75.0
