"""
D9 — Análise Comparativa Visual

Testa endpoint POST /api/v1/candidates/compare:
- Compara candidatos com sucesso
- Valida payload (min 2, max 4 candidatos)
- Retorna 500 em caso de erro do service
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
from fastapi.testclient import TestClient
from fastapi import FastAPI


def _make_app():
    from app.api.v1.candidate_compare import router
    from app.core.database import get_db
    from app.shared.security.require_company_id import require_company_id

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    async def mock_db():
        yield MagicMock()

    async def mock_company_id():
        return COMPANY_ID

    app.dependency_overrides[get_db] = mock_db
    app.dependency_overrides[require_company_id] = mock_company_id
    return app


COMPANY_ID = str(uuid4())


class TestCandidateCompareEndpoint:

    def test_compare_two_candidates_success(self):
        """POST /compare com 2 candidatos retorna resultado."""
        app = _make_app()
        c1, c2 = str(uuid4()), str(uuid4())

        mock_result = {
            "comparison_id": "cmp-1",
            "winner": c1,
            "winner_name": "Alice",
            "confidence": 0.85,
            "scenario": "B",
            "scenario_description": "CV comparison",
            "candidate_scores": {c1: 82.0, c2: 65.0},
            "dimension_comparison": {},
            "analysis": "Alice se destaca em experiência técnica.",
            "generated_at": "2026-03-15T10:00:00",
        }

        with patch(
            "app.domains.candidates.services.candidate_comparison_service.CandidateComparisonService.compare_candidates",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            client = TestClient(app)
            response = client.post(
                "/api/v1/candidates/compare",
                json={"candidate_ids": [c1, c2]},
                headers={"X-Company-ID": COMPANY_ID},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["winner"] == c1
        assert data["confidence"] == 0.85

    def test_compare_requires_at_least_2(self):
        """Payload com apenas 1 candidato retorna 422."""
        app = _make_app()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.post(
            "/api/v1/candidates/compare",
            json={"candidate_ids": [str(uuid4())]},
            headers={"X-Company-ID": COMPANY_ID},
        )
        assert response.status_code == 422

    def test_compare_rejects_more_than_4(self):
        """Payload com 5 candidatos retorna 422."""
        app = _make_app()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.post(
            "/api/v1/candidates/compare",
            json={"candidate_ids": [str(uuid4()) for _ in range(5)]},
            headers={"X-Company-ID": COMPANY_ID},
        )
        assert response.status_code == 422

    def test_compare_requires_company_header(self):
        """Sem X-Company-ID retorna 401."""
        app = _make_app()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.post(
            "/api/v1/candidates/compare",
            json={"candidate_ids": [str(uuid4()), str(uuid4())]},
        )
        assert response.status_code == 401

    def test_compare_service_error_returns_500(self):
        """Erro no service retorna 500."""
        app = _make_app()

        with patch(
            "app.domains.candidates.services.candidate_comparison_service.CandidateComparisonService.compare_candidates",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB unavailable"),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post(
                "/api/v1/candidates/compare",
                json={"candidate_ids": [str(uuid4()), str(uuid4())]},
                headers={"X-Company-ID": COMPANY_ID},
            )
        assert response.status_code == 500

    def test_compare_accepts_optional_job_id(self):
        """job_id opcional é aceito no payload."""
        app = _make_app()
        c1, c2 = str(uuid4()), str(uuid4())
        job_id = str(uuid4())

        mock_result = {
            "comparison_id": "cmp-2",
            "winner": c1,
            "winner_name": "Bob",
            "confidence": 0.9,
            "scenario": "A",
            "scenario_description": "WSI comparison",
            "candidate_scores": {c1: 90.0, c2: 70.0},
            "dimension_comparison": {},
            "analysis": "Bob lidera em screening.",
            "generated_at": "2026-03-15T10:00:00",
        }

        with patch(
            "app.domains.candidates.services.candidate_comparison_service.CandidateComparisonService.compare_candidates",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            client = TestClient(app)
            response = client.post(
                "/api/v1/candidates/compare",
                json={"candidate_ids": [c1, c2], "job_id": job_id},
                headers={"X-Company-ID": COMPANY_ID},
            )

        assert response.status_code == 200
