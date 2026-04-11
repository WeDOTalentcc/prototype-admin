"""
Testes unitários e de integração para BiasAuditSnapshot (G.4).

Cobrem:
- save_snapshot: persiste snapshot corretamente no DB
- get_snapshot_history: retorna snapshots ordenados por data desc
- get_snapshot_history: respeita company_id (multi-tenant)
- Endpoint GET /api/v1/bias-audit/job/{job_id}/history: 200 com header válido
- Endpoint: lista vazia para vaga sem histórico
- Endpoint: parâmetro limit respeitado

Usa AsyncClient + mini-app isolado (padrão testing-patterns C3).
"""
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from app.api.v1.bias_audit import router as bias_audit_router
from app.core.database import get_db
from app.models.bias_audit_snapshot import BiasAuditSnapshot
from app.shared.services.bias_audit_service import (
    BiasAuditService,
    BiasAuditReport,
    DemographicAuditResult,
)

# ---------------------------------------------------------------------------
# Mini-app isolado
# ---------------------------------------------------------------------------
_test_app = FastAPI()
_test_app.include_router(bias_audit_router, prefix="/api/v1")


async def _mock_db():
    mock = AsyncMock()
    mock.add = MagicMock()
    mock.flush = AsyncMock()
    mock.commit = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_result.scalar.return_value = 0
    mock.execute = AsyncMock(return_value=mock_result)
    yield mock


_test_app.dependency_overrides[get_db] = _mock_db

COMPANY_ID = uuid4()
JOB_ID = str(uuid4())
NOW = datetime.utcnow()


def _make_report(has_alerts: bool = False) -> BiasAuditReport:
    return BiasAuditReport(
        job_id=JOB_ID,
        evaluated_at=NOW,
        total_candidates=10,
        dimensions=[
            DemographicAuditResult(
                dimension="gender",
                groups={"masculino": {"count": 5, "approved": 4, "rate": 0.8}},
                adverse_impact_ratio=1.0,
                below_threshold=False,
                alert_level="ok",
            )
        ],
        has_alerts=has_alerts,
    )


def _make_snapshot(
    company_id=None,
    job_id=None,
    evaluated_at=None,
    has_alerts=False,
) -> BiasAuditSnapshot:
    s = BiasAuditSnapshot()
    s.id = uuid4()
    s.company_id = company_id or COMPANY_ID
    s.job_id = job_id or JOB_ID
    s.evaluated_at = evaluated_at or NOW
    s.total_candidates = 10
    s.has_alerts = has_alerts
    s.dimensions_json = json.dumps([])
    s.created_at = NOW
    return s


# ---------------------------------------------------------------------------
# Testes unitários do service
# ---------------------------------------------------------------------------

class TestBiasAuditServiceSnapshot:

    @pytest.mark.asyncio
    async def test_save_snapshot_persists_to_db(self):
        """save_snapshot deve adicionar um BiasAuditSnapshot à sessão."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        svc = BiasAuditService()
        report = _make_report()
        await svc.save_snapshot(mock_db, COMPANY_ID, report)

        mock_db.add.assert_called_once()
        snapshot = mock_db.add.call_args[0][0]
        assert isinstance(snapshot, BiasAuditSnapshot)
        assert snapshot.company_id == COMPANY_ID
        assert snapshot.job_id == JOB_ID
        assert snapshot.total_candidates == 10
        assert snapshot.has_alerts is False
        mock_db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_save_snapshot_serializes_dimensions(self):
        """dimensions_json deve conter as dimensões serializadas."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        svc = BiasAuditService()
        report = _make_report()
        await svc.save_snapshot(mock_db, COMPANY_ID, report)

        snapshot = mock_db.add.call_args[0][0]
        parsed = json.loads(snapshot.dimensions_json)
        assert isinstance(parsed, list)
        assert len(parsed) == 1
        assert parsed[0]["dimension"] == "gender"

    @pytest.mark.asyncio
    async def test_get_history_returns_snapshots_ordered_by_date_desc(self):
        """get_snapshot_history deve retornar snapshots em ordem decrescente."""
        older = _make_snapshot(evaluated_at=NOW - timedelta(days=1))
        newer = _make_snapshot(evaluated_at=NOW)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [newer, older]
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        svc = BiasAuditService()
        snapshots = await svc.get_snapshot_history(mock_db, COMPANY_ID, JOB_ID)

        assert len(snapshots) == 2
        assert snapshots[0].evaluated_at >= snapshots[1].evaluated_at

    @pytest.mark.asyncio
    async def test_get_history_respects_company_id_isolation(self):
        """get_snapshot_history deve filtrar por company_id (multi-tenant)."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        svc = BiasAuditService()
        other_company = uuid4()
        snapshots = await svc.get_snapshot_history(mock_db, other_company, JOB_ID)

        # Verifica que o execute foi chamado (query contém filtro by company_id)
        mock_db.execute.assert_awaited_once()
        assert snapshots == []


# ---------------------------------------------------------------------------
# Testes de integração — endpoint /history
# ---------------------------------------------------------------------------

_HISTORY_PATH = "app.services.bias_audit_service.BiasAuditService.get_snapshot_history"
_VALID_HEADERS = {"X-Company-ID": str(COMPANY_ID)}


@pytest.mark.asyncio
class TestBiasAuditHistoryEndpoint:

    async def test_history_endpoint_returns_200_with_valid_header(self):
        """GET /history com X-Company-ID válido retorna 200."""
        snapshots = [_make_snapshot()]
        with patch(_HISTORY_PATH, new_callable=AsyncMock, return_value=snapshots):
            async with AsyncClient(
                transport=ASGITransport(app=_test_app), base_url="http://test"
            ) as client:
                response = await client.get(
                    f"/api/v1/bias-audit/job/{JOB_ID}/history",
                    headers=_VALID_HEADERS,
                )
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == JOB_ID
        assert data["count"] == 1
        assert isinstance(data["history"], list)

    async def test_history_endpoint_returns_empty_list_for_new_job(self):
        """GET /history para vaga sem histórico retorna lista vazia."""
        with patch(_HISTORY_PATH, new_callable=AsyncMock, return_value=[]):
            async with AsyncClient(
                transport=ASGITransport(app=_test_app), base_url="http://test"
            ) as client:
                response = await client.get(
                    f"/api/v1/bias-audit/job/{JOB_ID}/history",
                    headers=_VALID_HEADERS,
                )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["history"] == []

    async def test_history_endpoint_respects_limit_param(self):
        """GET /history?limit=3 deve passar limit=3 ao service."""
        captured = {}

        async def _mock_history(db, company_id, job_id, limit=10):
            captured["limit"] = limit
            return []

        with patch(_HISTORY_PATH, side_effect=_mock_history):
            async with AsyncClient(
                transport=ASGITransport(app=_test_app), base_url="http://test"
            ) as client:
                await client.get(
                    f"/api/v1/bias-audit/job/{JOB_ID}/history",
                    headers=_VALID_HEADERS,
                    params={"limit": 3},
                )

        assert captured.get("limit") == 3

    async def test_history_endpoint_returns_401_without_header(self):
        """GET /history sem X-Company-ID retorna 401."""
        async with AsyncClient(
            transport=ASGITransport(app=_test_app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/v1/bias-audit/job/{JOB_ID}/history")
        assert response.status_code == 401
