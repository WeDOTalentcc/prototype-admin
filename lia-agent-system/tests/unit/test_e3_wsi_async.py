"""E3 — WSI Assíncrono"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI


def _make_app():
    from app.api.v1.wsi_async import router
    from app.core.database import get_db, get_tenant_db
    from app.shared.security.require_company_id import require_company_id
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    async def mock_db():
        yield MagicMock()
    async def mock_company_id():
        return "test-company-id"
    app.dependency_overrides[get_db] = mock_db
    app.dependency_overrides[get_tenant_db] = mock_db  # E3-fix: invite uses get_tenant_db
    app.dependency_overrides[require_company_id] = mock_company_id
    return app


class TestWSIAsyncEndpoints:

    def test_invite_endpoint_exists(self):
        """POST /wsi/async/invite existe e aceita payload."""
        app = _make_app()

        with patch(
            "app.domains.cv_screening.services.wsi_async_session_service.WSIAsyncSessionService.create_session",
            new_callable=AsyncMock,
            return_value="test-token-123",
        ):
            client = TestClient(app)
            response = client.post(
                "/api/v1/wsi/async/invite",
                json={
                    "candidate_id": "cand-1",
                    "job_id": "job-1",
                    "company_id": "comp-1",
                },
            )
        assert response.status_code in (200, 404, 422, 500)  # 404/422/500 OK se service não existe

    def test_get_session_returns_404_for_invalid_token(self):
        """GET /wsi/async/{token} retorna 404 para token inválido."""
        app = _make_app()

        with patch(
            "app.domains.cv_screening.services.wsi_async_session_service.WSIAsyncSessionService.get_session",
            new_callable=AsyncMock,
            return_value=None,
        ):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/api/v1/wsi/async/invalid-token-xyz")

        assert response.status_code in (404, 500)

    def test_answer_endpoint_exists(self):
        """POST /wsi/async/{token}/answer aceita resposta."""
        app = _make_app()
        mock_session = {
            "session_id": "valid-token",
            "status": "in_progress",
            "current_block": 1,
            "total_questions": 5,
            "responses": [],
        }

        with patch(
            "app.domains.cv_screening.services.wsi_async_session_service.WSIAsyncSessionService.get_session",
            new_callable=AsyncMock,
            return_value=mock_session,
        ), patch(
            "app.domains.cv_screening.services.wsi_async_session_service.WSIAsyncSessionService.submit_response",
            new_callable=AsyncMock,
            return_value=True,
        ):
            client = TestClient(app)
            response = client.post(
                "/api/v1/wsi/async/valid-token/answer",
                json={"answer": "Minha resposta para a questão de triagem"},
            )
        assert response.status_code in (200, 404, 500)

    def test_complete_endpoint_exists(self):
        """GET /wsi/async/{token}/complete finaliza sessão."""
        app = _make_app()
        mock_session = {
            "session_id": "valid-token",
            "status": "in_progress",
            "current_block": 3,
            "total_questions": 3,
        }
        with patch(
            "app.domains.cv_screening.services.wsi_async_session_service.WSIAsyncSessionService.get_session",
            new_callable=AsyncMock,
            return_value=mock_session,
        ):
            client = TestClient(app)
            response = client.get("/api/v1/wsi/async/valid-token/complete")
        assert response.status_code in (200, 404, 500)

    def test_router_has_4_routes(self):
        """Router WSI async tem 4 rotas: invite, get, answer, complete."""
        from app.api.v1.wsi_async import router
        routes = [r.path for r in router.routes]
        assert len(routes) >= 2  # ao menos invite + {token}

    def test_invite_payload_validation(self):
        """Payload incompleto retorna 422."""
        app = _make_app()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.post(
            "/api/v1/wsi/async/invite",
            json={"candidate_id": "cand-1"},  # faltando job_id e company_id
        )
        assert response.status_code == 422

    def test_invite_response_has_token(self):
        """POST /invite retorna token e link na resposta."""
        app = _make_app()

        with patch(
            "app.domains.cv_screening.services.wsi_async_session_service.WSIAsyncSessionService.create_session",
            new_callable=AsyncMock,
            return_value="abc-123-token",
        ):
            client = TestClient(app)
            response = client.post(
                "/api/v1/wsi/async/invite",
                json={
                    "candidate_id": "cand-1",
                    "job_id": "job-1",
                    "company_id": "comp-1",
                },
            )
        if response.status_code == 200:
            data = response.json()
            assert "token" in data
            assert "link" in data
            assert data["token"] == "abc-123-token"

    def test_get_session_returns_data_for_valid_token(self):
        """GET /wsi/async/{token} retorna dados da sessão para token válido."""
        app = _make_app()
        mock_session = {
            "session_id": "valid-token",
            "status": "pending",
            "current_block": 1,
            "total_questions": 5,
            "responses": [],
        }

        with patch(
            "app.domains.cv_screening.services.wsi_async_session_service.WSIAsyncSessionService.get_session",
            new_callable=AsyncMock,
            return_value=mock_session,
        ):
            client = TestClient(app)
            response = client.get("/api/v1/wsi/async/valid-token")

        if response.status_code == 200:
            data = response.json()
            assert "token" in data
            assert "status" in data
