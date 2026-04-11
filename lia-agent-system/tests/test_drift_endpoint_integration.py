"""
Integration tests — GET /api/v1/drift/status (D.2 — Model Drift Detection)

Camada 3 da pirâmide de testes (testing-patterns §5).
Usa httpx AsyncClient com ASGITransport para testar o endpoint real.

Nota: app.main tem um SyntaxError pré-existente em wizard_orchestrator_service.py
(arquivo truncado). Para isolar o teste do endpoint de drift, criamos um mini-app
apenas com o router de drift — sem depender do app.main completo.

Referência: screening-compliance §7, testing-patterns C3.
"""
import pytest
from unittest.mock import patch, AsyncMock
from uuid import uuid4

from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from app.api.v1.drift import router as drift_router
from app.shared.services.model_drift_service import DriftStatus, DriftTrigger, SCORE_DRIFT_THRESHOLD

# Mini-app isolado: apenas o drift router (sem carregar o app.main inteiro)
_test_app = FastAPI()
_test_app.include_router(drift_router, prefix="/api/v1")


COMPANY_ID = str(uuid4())
NOW_DT = __import__("datetime").datetime.utcnow()


def _mock_drift_status(drift_detected: bool = False, alert_level: str = "ok") -> DriftStatus:
    """Helper para construir um DriftStatus de teste."""
    status = DriftStatus(
        company_id=COMPANY_ID,
        evaluated_at=NOW_DT,
        recent_window_start=NOW_DT - __import__("datetime").timedelta(days=7),
        baseline_window_start=NOW_DT - __import__("datetime").timedelta(days=14),
    )
    status.drift_detected = drift_detected
    status.alert_level = alert_level
    status.triggers = [
        DriftTrigger(
            name="score_drift",
            baseline_value=70.0,
            recent_value=70.2,
            delta=0.2,
            threshold=SCORE_DRIFT_THRESHOLD,
            triggered=False,
            description="Score médio WSI: baseline=70.00 → recente=70.20 (Δ=0.20)",
        )
    ]
    return status


@pytest.mark.asyncio
class TestDriftEndpointIntegration:
    """Testes de integração para GET /api/v1/drift/status."""

    async def test_endpoint_returns_200_with_valid_company_id(self):
        """GET /api/v1/drift/status?company_id=<uuid> retorna 200 com status ok."""
        mock_status = _mock_drift_status(drift_detected=False, alert_level="ok")

        with patch(
            "app.api.v1.drift.model_drift_service.evaluate",
            new_callable=AsyncMock,
            return_value=mock_status,
        ):
            async with AsyncClient(transport=ASGITransport(app=_test_app), base_url="http://test") as client:
                response = await client.get(
                    f"/api/v1/drift/status?company_id={COMPANY_ID}"
                )

        assert response.status_code == 200
        data = response.json()
        assert data["company_id"] == COMPANY_ID
        assert data["drift_detected"] is False
        assert data["alert_level"] == "ok"

    async def test_endpoint_returns_drift_detected_when_triggered(self):
        """Quando drift detectado, response inclui drift_detected=True e alert_level apropriado."""
        mock_status = _mock_drift_status(drift_detected=True, alert_level="warning")
        mock_status.triggers = [
            DriftTrigger(
                name="score_drift",
                baseline_value=70.0,
                recent_value=72.5,
                delta=2.5,
                threshold=SCORE_DRIFT_THRESHOLD,
                triggered=True,
                description="Score médio WSI: drift detectado",
            )
        ]

        with patch(
            "app.api.v1.drift.model_drift_service.evaluate",
            new_callable=AsyncMock,
            return_value=mock_status,
        ):
            async with AsyncClient(transport=ASGITransport(app=_test_app), base_url="http://test") as client:
                response = await client.get(
                    f"/api/v1/drift/status?company_id={COMPANY_ID}"
                )

        assert response.status_code == 200
        data = response.json()
        assert data["drift_detected"] is True
        assert data["alert_level"] == "warning"
        assert len(data["triggers"]) == 1
        assert data["triggers"][0]["name"] == "score_drift"
        assert data["triggers"][0]["triggered"] is True

    async def test_endpoint_returns_422_without_company_id(self):
        """GET /api/v1/drift/status sem company_id retorna 422 (validation error)."""
        async with AsyncClient(transport=ASGITransport(app=_test_app), base_url="http://test") as client:
            response = await client.get("/api/v1/drift/status")

        assert response.status_code == 422

    async def test_endpoint_returns_422_with_invalid_uuid(self):
        """GET /api/v1/drift/status com UUID inválido retorna 422."""
        async with AsyncClient(transport=ASGITransport(app=_test_app), base_url="http://test") as client:
            response = await client.get("/api/v1/drift/status?company_id=not-a-uuid")

        assert response.status_code == 422

    async def test_response_has_required_fields(self):
        """Response deve conter todos os campos obrigatórios do schema."""
        mock_status = _mock_drift_status()

        with patch(
            "app.api.v1.drift.model_drift_service.evaluate",
            new_callable=AsyncMock,
            return_value=mock_status,
        ):
            async with AsyncClient(transport=ASGITransport(app=_test_app), base_url="http://test") as client:
                response = await client.get(
                    f"/api/v1/drift/status?company_id={COMPANY_ID}"
                )

        data = response.json()
        required = {
            "company_id", "evaluated_at", "recent_window_start",
            "baseline_window_start", "drift_detected", "alert_level", "triggers"
        }
        assert required.issubset(data.keys()), (
            f"Campos faltando na response: {required - data.keys()}"
        )

    async def test_trigger_has_required_fields(self):
        """Cada trigger na response deve ter todos os campos obrigatórios."""
        mock_status = _mock_drift_status()

        with patch(
            "app.api.v1.drift.model_drift_service.evaluate",
            new_callable=AsyncMock,
            return_value=mock_status,
        ):
            async with AsyncClient(transport=ASGITransport(app=_test_app), base_url="http://test") as client:
                response = await client.get(
                    f"/api/v1/drift/status?company_id={COMPANY_ID}"
                )

        data = response.json()
        assert len(data["triggers"]) > 0
        trigger = data["triggers"][0]
        required = {"name", "baseline_value", "recent_value", "delta", "threshold", "triggered", "description"}
        assert required.issubset(trigger.keys())

    async def test_service_error_returns_500(self):
        """Se o service lança exceção, endpoint retorna 500."""
        with patch(
            "app.api.v1.drift.model_drift_service.evaluate",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB error"),
        ):
            async with AsyncClient(transport=ASGITransport(app=_test_app), base_url="http://test") as client:
                response = await client.get(
                    f"/api/v1/drift/status?company_id={COMPANY_ID}"
                )

        assert response.status_code == 500
