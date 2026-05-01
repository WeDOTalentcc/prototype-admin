"""
Integration tests — GET /api/v1/bias-audit/job/{job_id} (E.2 — Bias Audit API)

Camada 3 da pirâmide de testes (testing-patterns §5).
Usa httpx AsyncClient com ASGITransport e mini-app FastAPI isolado.

Isolação: não importa app.main (evita SyntaxError pré-existente).
Referências: dei-fairness §4, testing-patterns C3.
"""
import pytest
from datetime import datetime
from unittest.mock import patch, AsyncMock
from uuid import uuid4

from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from app.api.v1.bias_audit import router as bias_audit_router
from app.shared.services.bias_audit_service import (
    BiasAuditReport,
    DemographicAuditResult,
)

# Mini-app isolado: apenas o bias-audit router
_test_app = FastAPI()
_test_app.include_router(bias_audit_router, prefix="/api/v1")

COMPANY_ID = str(uuid4())
JOB_ID = str(uuid4())
NOW_DT = datetime.utcnow()


def _mock_report(
    total_candidates: int = 30,
    has_alerts: bool = False,
) -> BiasAuditReport:
    """Helper para construir um BiasAuditReport de teste."""
    dimensions = [
        DemographicAuditResult(
            dimension="gender",
            groups={
                "masculino": {"count": 15, "approved": 12, "rate": 0.8},
                "feminino": {"count": 15, "approved": 13, "rate": 0.8667},
            },
            adverse_impact_ratio=0.923,
            below_threshold=False,
            alert_level="ok",
        ),
        DemographicAuditResult(
            dimension="age_group",
            groups={
                "<30": {"count": 10, "approved": 9, "rate": 0.9},
                "30-44": {"count": 15, "approved": 12, "rate": 0.8},
                "45+": {"count": 5, "approved": 4, "rate": 0.8},
            },
            adverse_impact_ratio=0.889,
            below_threshold=False,
            alert_level="ok",
        ),
        DemographicAuditResult(
            dimension="disability",
            groups={
                "pcd": {"count": 5, "approved": 3, "rate": 0.6},
                "sem pcd": {"count": 25, "approved": 22, "rate": 0.88},
            },
            adverse_impact_ratio=0.682 if has_alerts else 0.85,
            below_threshold=has_alerts,
            alert_level="warning" if has_alerts else "ok",
        ),
        DemographicAuditResult(
            dimension="region",
            groups={
                "SP": {"count": 20, "approved": 17, "rate": 0.85},
                "RJ": {"count": 10, "approved": 8, "rate": 0.8},
            },
            adverse_impact_ratio=0.941,
            below_threshold=False,
            alert_level="ok",
        ),
    ]
    return BiasAuditReport(
        job_id=JOB_ID,
        evaluated_at=NOW_DT,
        total_candidates=total_candidates,
        dimensions=dimensions,
        has_alerts=has_alerts,
    )


_MOCK_PATH = "app.api.v1.bias_audit.bias_audit_service.get_adverse_impact_by_job"
_VALID_HEADERS = {"X-Company-ID": COMPANY_ID}


@pytest.mark.asyncio
class TestBiasAuditEndpointIntegration:
    """Testes de integração para GET /api/v1/bias-audit/job/{job_id}."""

    async def test_returns_200_with_valid_x_company_id(self):
        """GET com X-Company-ID UUID válido retorna 200."""
        mock_report = _mock_report()
        with patch(_MOCK_PATH, new_callable=AsyncMock, return_value=mock_report):
            async with AsyncClient(
                transport=ASGITransport(app=_test_app), base_url="http://test"
            ) as client:
                response = await client.get(
                    f"/api/v1/bias-audit/job/{JOB_ID}",
                    headers=_VALID_HEADERS,
                )
        assert response.status_code == 200

    async def test_returns_401_without_x_company_id_header(self):
        """GET sem X-Company-ID header retorna 401."""
        async with AsyncClient(
            transport=ASGITransport(app=_test_app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/v1/bias-audit/job/{JOB_ID}")
        assert response.status_code == 401
        assert "X-Company-ID" in response.json().get("detail", "")

    async def test_returns_401_with_invalid_uuid_company_id(self):
        """GET com X-Company-ID não-UUID retorna 401."""
        async with AsyncClient(
            transport=ASGITransport(app=_test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/v1/bias-audit/job/{JOB_ID}",
                headers={"X-Company-ID": "nao-e-uuid"},
            )
        assert response.status_code == 401

    async def test_empty_job_returns_zero_candidates(self):
        """Job sem candidatos avaliados retorna total_candidates=0 e dimensions=[]."""
        empty_report = BiasAuditReport(
            job_id=JOB_ID,
            evaluated_at=NOW_DT,
            total_candidates=0,
            dimensions=[],
            has_alerts=False,
        )
        with patch(_MOCK_PATH, new_callable=AsyncMock, return_value=empty_report):
            async with AsyncClient(
                transport=ASGITransport(app=_test_app), base_url="http://test"
            ) as client:
                response = await client.get(
                    f"/api/v1/bias-audit/job/{JOB_ID}",
                    headers=_VALID_HEADERS,
                )
        assert response.status_code == 200
        data = response.json()
        assert data["total_candidates"] == 0
        assert data["dimensions"] == []

    async def test_response_has_required_fields(self):
        """Response deve conter todos os campos obrigatórios do schema."""
        mock_report = _mock_report()
        with patch(_MOCK_PATH, new_callable=AsyncMock, return_value=mock_report):
            async with AsyncClient(
                transport=ASGITransport(app=_test_app), base_url="http://test"
            ) as client:
                response = await client.get(
                    f"/api/v1/bias-audit/job/{JOB_ID}",
                    headers=_VALID_HEADERS,
                )
        data = response.json()
        required = {"job_id", "evaluated_at", "total_candidates", "dimensions", "has_alerts"}
        assert required.issubset(data.keys()), (
            f"Campos faltando: {required - data.keys()}"
        )

    async def test_dimensions_count_is_four(self):
        """Report com candidatos deve ter exatamente 4 dimensões."""
        mock_report = _mock_report()
        with patch(_MOCK_PATH, new_callable=AsyncMock, return_value=mock_report):
            async with AsyncClient(
                transport=ASGITransport(app=_test_app), base_url="http://test"
            ) as client:
                response = await client.get(
                    f"/api/v1/bias-audit/job/{JOB_ID}",
                    headers=_VALID_HEADERS,
                )
        data = response.json()
        assert len(data["dimensions"]) == 4
        dimension_names = {d["dimension"] for d in data["dimensions"]}
        assert dimension_names == {"gender", "age_group", "disability", "region"}

    async def test_service_error_returns_500(self):
        """Se o service lança exceção, endpoint retorna 500."""
        with patch(
            _MOCK_PATH,
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB error"),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=_test_app), base_url="http://test"
            ) as client:
                response = await client.get(
                    f"/api/v1/bias-audit/job/{JOB_ID}",
                    headers=_VALID_HEADERS,
                )
        assert response.status_code == 500

    async def test_alert_level_values_are_ok_or_warning(self):
        """alert_level de cada dimensão deve ser 'ok' ou 'warning'."""
        mock_report = _mock_report(has_alerts=True)
        with patch(_MOCK_PATH, new_callable=AsyncMock, return_value=mock_report):
            async with AsyncClient(
                transport=ASGITransport(app=_test_app), base_url="http://test"
            ) as client:
                response = await client.get(
                    f"/api/v1/bias-audit/job/{JOB_ID}",
                    headers=_VALID_HEADERS,
                )
        data = response.json()
        assert data["has_alerts"] is True
        for dim in data["dimensions"]:
            assert dim["alert_level"] in {"ok", "warning"}, (
                f"alert_level inválido: {dim['alert_level']}"
            )
