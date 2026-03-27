"""
Integration tests — POST /api/v1/drift/run-batch (E.3 — Drift Batch Job)

Camada 3 da pirâmide de testes (testing-patterns §5).
Usa httpx AsyncClient com ASGITransport e mini-app FastAPI isolado.

Isolação: não importa app.main (evita SyntaxError pré-existente).
Referências: screening-compliance §7, testing-patterns C3.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4

from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from app.api.v1.drift import router as drift_router
from app.auth.dependencies import require_admin
from app.auth.models import UserRole

# ---------------------------------------------------------------------------
# Mini-apps — um com admin mockado, um sem override (para testar 401)
# ---------------------------------------------------------------------------

def _make_mock_admin():
    """Cria um mock de User admin sem precisar de SQLAlchemy."""
    user = MagicMock()
    user.id = uuid4()
    user.email = "admin@test.com"
    user.role = UserRole.admin
    user.is_active = True
    return user


_mock_admin = _make_mock_admin()

# App com override de require_admin (usuário admin mock)
_test_app = FastAPI()
_test_app.dependency_overrides[require_admin] = lambda: _mock_admin
_test_app.include_router(drift_router, prefix="/api/v1")

# App sem override (para testar 401 sem autenticação)
_unauth_app = FastAPI()
_unauth_app.include_router(drift_router, prefix="/api/v1")


_BATCH_PATH = "app.api.v1.drift.run_drift_check_all_companies"


@pytest.mark.asyncio
class TestDriftBatchEndpointIntegration:
    """Testes de integração para POST /api/v1/drift/run-batch."""

    async def test_batch_returns_200_with_admin_auth(self):
        """POST com admin mockado retorna 200."""
        with patch(_BATCH_PATH, new_callable=AsyncMock, return_value={"checked": 3, "drifted": 0, "errors": 0}):
            async with AsyncClient(
                transport=ASGITransport(app=_test_app), base_url="http://test"
            ) as client:
                response = await client.post("/api/v1/drift/run-batch")
        assert response.status_code == 200

    async def test_batch_response_has_status_checked_drifted_errors(self):
        """Response deve conter campos status, checked, drifted, errors."""
        with patch(_BATCH_PATH, new_callable=AsyncMock, return_value={"checked": 5, "drifted": 1, "errors": 0}):
            async with AsyncClient(
                transport=ASGITransport(app=_test_app), base_url="http://test"
            ) as client:
                response = await client.post("/api/v1/drift/run-batch")
        data = response.json()
        required = {"status", "checked", "drifted", "errors"}
        assert required.issubset(data.keys()), (
            f"Campos faltando: {required - data.keys()}"
        )

    async def test_batch_status_is_completed(self):
        """Campo status da response deve ser 'completed'."""
        with patch(_BATCH_PATH, new_callable=AsyncMock, return_value={"checked": 2, "drifted": 0, "errors": 0}):
            async with AsyncClient(
                transport=ASGITransport(app=_test_app), base_url="http://test"
            ) as client:
                response = await client.post("/api/v1/drift/run-batch")
        assert response.json()["status"] == "completed"

    async def test_batch_with_no_companies_returns_zero_counts(self):
        """Quando não há empresas, checked=0, drifted=0, errors=0."""
        with patch(_BATCH_PATH, new_callable=AsyncMock, return_value={"checked": 0, "drifted": 0, "errors": 0}):
            async with AsyncClient(
                transport=ASGITransport(app=_test_app), base_url="http://test"
            ) as client:
                response = await client.post("/api/v1/drift/run-batch")
        data = response.json()
        assert data["checked"] == 0
        assert data["drifted"] == 0
        assert data["errors"] == 0

    async def test_batch_with_notify_user_id_query_param(self):
        """Query param notify_user_id é aceito sem erro."""
        user_id = str(uuid4())
        with patch(_BATCH_PATH, new_callable=AsyncMock, return_value={"checked": 1, "drifted": 0, "errors": 0}):
            async with AsyncClient(
                transport=ASGITransport(app=_test_app), base_url="http://test"
            ) as client:
                response = await client.post(
                    f"/api/v1/drift/run-batch?notify_user_id={user_id}"
                )
        assert response.status_code == 200

    async def test_batch_drifted_count_in_response(self):
        """drifted count reflete o retorno do service."""
        with patch(_BATCH_PATH, new_callable=AsyncMock, return_value={"checked": 4, "drifted": 2, "errors": 0}):
            async with AsyncClient(
                transport=ASGITransport(app=_test_app), base_url="http://test"
            ) as client:
                response = await client.post("/api/v1/drift/run-batch")
        assert response.json()["drifted"] == 2
        assert response.json()["checked"] == 4

    async def test_service_error_returns_500(self):
        """Se o service lança exceção, endpoint retorna 500."""
        with patch(
            _BATCH_PATH,
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB error"),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=_test_app), base_url="http://test"
            ) as client:
                response = await client.post("/api/v1/drift/run-batch")
        assert response.status_code == 500

    async def test_batch_401_without_auth(self):
        """POST sem autenticação retorna 401 (HTTPBearer exige token)."""
        async with AsyncClient(
            transport=ASGITransport(app=_unauth_app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/drift/run-batch")
        # Sem auth Bearer, FastAPI retorna 403 (HTTPBearer auto_error=True)
        assert response.status_code in {401, 403}
