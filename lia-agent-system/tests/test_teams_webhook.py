"""
Integration tests for Teams → WhatsApp Screening webhook endpoint.

Tests cover:
- Endpoint routing and response structure
- Action parsing (approve, reject, schedule)
- WhatsApp screening initiation on approve
- Signature verification security
- Audit logging

Migração G.3: TestClient → AsyncClient + mini-app isolado para evitar
conflito de event loop entre asyncpg e o loop de teste.
"""
import pytest
import hmac
import hashlib
import json
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from app.api.v1.teams import router as teams_router
from app.core.database import get_db

# ---------------------------------------------------------------------------
# Mini-app isolado — apenas o router de teams
# ---------------------------------------------------------------------------
_test_app = FastAPI()
_test_app.include_router(teams_router, prefix="/api/v1")


async def _mock_db():
    """Mock async DB session — evita conexão real ao PostgreSQL."""
    mock = AsyncMock()
    mock.add = MagicMock()
    mock.commit = AsyncMock()
    # execute retorna resultado vazio por padrão
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_result.scalar.return_value = 0
    mock_result.fetchall.return_value = []
    mock.execute = AsyncMock(return_value=mock_result)
    yield mock


_test_app.dependency_overrides[get_db] = _mock_db


def _generate_signature(payload: dict, secret: str) -> str:
    """Generate HMAC-SHA256 signature for testing."""
    payload_bytes = json.dumps(payload).encode("utf-8")
    signature = hmac.new(
        secret.encode("utf-8"),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()
    return f"sha256={signature}"


BASE_URL = "http://test"


@pytest.mark.asyncio
class TestTeamsWebhookEndpoint:
    """Integration tests for /api/v1/teams/webhook endpoint."""

    @pytest.fixture
    def approve_payload(self):
        return {
            "action": "approve",
            "candidate_id": "cand_test_123",
            "candidate_name": "João Silva",
            "candidate_phone": "+5511999999999",
            "vacancy_id": "vac_test_456",
            "vacancy_title": "Desenvolvedor Python Senior",
            "company_id": "comp_test_789",
            "recruiter_id": "user_001",
            "recruiter_name": "Maria Santos",
        }

    @pytest.fixture
    def reject_payload(self):
        return {
            "action": "reject",
            "candidate_id": "cand_test_123",
            "candidate_name": "João Silva",
            "vacancy_id": "vac_test_456",
            "recruiter_id": "user_001",
            "recruiter_name": "Maria Santos",
            "notes": "Perfil não alinhado com requisitos técnicos",
        }

    @pytest.fixture
    def schedule_payload(self):
        return {
            "action": "schedule",
            "candidate_id": "cand_test_123",
            "candidate_name": "João Silva",
            "vacancy_id": "vac_test_456",
            "recruiter_id": "user_001",
            "recruiter_name": "Maria Santos",
            "scheduled_date": "2026-02-15T10:00:00Z",
        }

    @patch("app.api.v1.teams.settings.TEAMS_WEBHOOK_SECRET", None)
    @patch(
        "app.domains.communication.services.communication_dispatcher.communication_dispatcher.send_whatsapp"
    )
    @patch(
        "app.domains.communication.services.communication_history_service.communication_history_service.log_communication",
        new_callable=AsyncMock,
    )
    async def test_approve_action_initiates_screening(
        self, mock_log_comm, mock_send_whatsapp, approve_payload
    ):
        """Test that approve action initiates WhatsApp screening."""
        mock_send_whatsapp.return_value = {
            "success": True,
            "message_id": "msg_test_001",
            "mock": True,
        }

        async with AsyncClient(
            transport=ASGITransport(app=_test_app), base_url=BASE_URL
        ) as client:
            response = await client.post(
                "/api/v1/teams/webhook", json=approve_payload
            )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["action"] == "approve"
        assert data["screening_initiated"] is True
        assert data["candidate_id"] == approve_payload["candidate_id"]
        assert "audit_id" in data
        assert data["audit_id"] is not None

        mock_send_whatsapp.assert_called_once()
        call_args = mock_send_whatsapp.call_args
        assert approve_payload["candidate_phone"] in call_args.kwargs.get(
            "to_phone", ""
        )

    @patch("app.api.v1.teams.settings.TEAMS_WEBHOOK_SECRET", None)
    async def test_approve_action_without_phone_returns_error(self, approve_payload):
        """Test that approve without phone number returns error."""
        del approve_payload["candidate_phone"]

        async with AsyncClient(
            transport=ASGITransport(app=_test_app), base_url=BASE_URL
        ) as client:
            response = await client.post(
                "/api/v1/teams/webhook", json=approve_payload
            )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is False
        assert data["action"] == "approve"
        assert data["screening_initiated"] is False
        assert (
            "telefone" in data["message"].lower() or "phone" in data["message"].lower()
        )

    @patch("app.api.v1.teams.settings.TEAMS_WEBHOOK_SECRET", None)
    async def test_reject_action_returns_success(self, reject_payload):
        """Test that reject action is processed correctly."""
        async with AsyncClient(
            transport=ASGITransport(app=_test_app), base_url=BASE_URL
        ) as client:
            response = await client.post(
                "/api/v1/teams/webhook", json=reject_payload
            )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["action"] == "reject"
        assert data["screening_initiated"] is False
        assert data["candidate_id"] == reject_payload["candidate_id"]
        assert "audit_id" in data

    @patch("app.api.v1.teams.settings.TEAMS_WEBHOOK_SECRET", None)
    async def test_schedule_action_returns_success(self, schedule_payload):
        """Test that schedule action is processed correctly."""
        async with AsyncClient(
            transport=ASGITransport(app=_test_app), base_url=BASE_URL
        ) as client:
            response = await client.post(
                "/api/v1/teams/webhook", json=schedule_payload
            )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["action"] == "schedule"
        assert data["candidate_id"] == schedule_payload["candidate_id"]
        assert "audit_id" in data

    @patch("app.api.v1.teams.settings.TEAMS_WEBHOOK_SECRET", None)
    async def test_invalid_action_returns_400(self):
        """Test that invalid action returns 400 error."""
        payload = {"action": "invalid_action", "candidate_id": "cand_test_123"}

        async with AsyncClient(
            transport=ASGITransport(app=_test_app), base_url=BASE_URL
        ) as client:
            response = await client.post("/api/v1/teams/webhook", json=payload)

        assert response.status_code == 400
        assert (
            "invalid_action" in response.text.lower()
            or "não suportada" in response.text.lower()
        )

    @patch("app.api.v1.teams.settings.TEAMS_WEBHOOK_SECRET", "test_secret_123")
    async def test_missing_signature_returns_401_when_secret_configured(
        self, approve_payload
    ):
        """Test that missing signature returns 401 when secret is configured."""
        async with AsyncClient(
            transport=ASGITransport(app=_test_app), base_url=BASE_URL
        ) as client:
            response = await client.post(
                "/api/v1/teams/webhook", json=approve_payload
            )

        assert response.status_code == 401
        assert "signature" in response.text.lower()

    @patch("app.api.v1.teams.settings.TEAMS_WEBHOOK_SECRET", "test_secret_123")
    async def test_invalid_signature_returns_401(self, approve_payload):
        """Test that invalid signature returns 401."""
        async with AsyncClient(
            transport=ASGITransport(app=_test_app), base_url=BASE_URL
        ) as client:
            response = await client.post(
                "/api/v1/teams/webhook",
                json=approve_payload,
                headers={"X-Teams-Signature": "sha256=invalid_signature"},
            )

        assert response.status_code == 401

    @patch("app.api.v1.teams.settings.TEAMS_WEBHOOK_SECRET", "test_secret_123")
    @patch(
        "app.domains.communication.services.communication_dispatcher.communication_dispatcher.send_whatsapp"
    )
    @patch(
        "app.domains.communication.services.communication_history_service.communication_history_service.log_communication",
        new_callable=AsyncMock,
    )
    async def test_valid_signature_allows_request(
        self, mock_log_comm, mock_send_whatsapp, approve_payload
    ):
        """Test that valid signature allows request to proceed."""
        mock_send_whatsapp.return_value = {
            "success": True,
            "message_id": "msg_test_001",
            "mock": True,
        }

        payload_bytes = json.dumps(approve_payload).encode("utf-8")
        signature = hmac.new(
            "test_secret_123".encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()

        async with AsyncClient(
            transport=ASGITransport(app=_test_app), base_url=BASE_URL
        ) as client:
            response = await client.post(
                "/api/v1/teams/webhook",
                content=payload_bytes,
                headers={
                    "X-Teams-Signature": f"sha256={signature}",
                    "Content-Type": "application/json",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @patch("app.api.v1.teams.settings.TEAMS_WEBHOOK_SECRET", None)
    async def test_request_info_action_returns_success(self):
        """Test that request_info action is processed correctly."""
        payload = {
            "action": "request_info",
            "candidate_id": "cand_test_123",
            "candidate_name": "João Silva",
            "recruiter_id": "user_001",
            "recruiter_name": "Maria Santos",
            "notes": "Por favor, envie certificações atualizadas",
        }

        async with AsyncClient(
            transport=ASGITransport(app=_test_app), base_url=BASE_URL
        ) as client:
            response = await client.post("/api/v1/teams/webhook", json=payload)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["action"] == "request_info"
        assert "audit_id" in data

    @patch("app.api.v1.teams.settings.TEAMS_WEBHOOK_SECRET", None)
    async def test_reschedule_action_returns_success(self):
        """Test that reschedule action is processed correctly."""
        payload = {
            "action": "reschedule",
            "candidate_id": "cand_test_123",
            "candidate_name": "João Silva",
            "vacancy_id": "vac_test_456",
            "recruiter_id": "user_001",
            "recruiter_name": "Maria Santos",
            "scheduled_date": "2026-02-20T14:00:00Z",
        }

        async with AsyncClient(
            transport=ASGITransport(app=_test_app), base_url=BASE_URL
        ) as client:
            response = await client.post("/api/v1/teams/webhook", json=payload)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["action"] == "reschedule"

    async def test_invalid_json_returns_400(self):
        """Test that invalid JSON returns 400 error."""
        async with AsyncClient(
            transport=ASGITransport(app=_test_app), base_url=BASE_URL
        ) as client:
            response = await client.post(
                "/api/v1/teams/webhook",
                content=b"not valid json",
                headers={"Content-Type": "application/json"},
            )

        assert response.status_code == 400 or response.status_code == 422

    @patch("app.api.v1.teams.settings.TEAMS_WEBHOOK_SECRET", None)
    async def test_missing_required_action_field_returns_422(self):
        """Test that missing required action field returns 422."""
        payload = {"candidate_id": "cand_test_123"}

        async with AsyncClient(
            transport=ASGITransport(app=_test_app), base_url=BASE_URL
        ) as client:
            response = await client.post("/api/v1/teams/webhook", json=payload)

        assert response.status_code == 400 or response.status_code == 422


@pytest.mark.asyncio
class TestTeamsWebhookAuditLogs:
    """Tests for Teams webhook audit logging functionality."""

    @patch("app.api.v1.teams.settings.TEAMS_WEBHOOK_SECRET", None)
    async def test_audit_logs_endpoint_returns_logs(self):
        """Test that audit logs endpoint returns logged actions."""
        reject_payload = {
            "action": "reject",
            "candidate_id": "cand_audit_test",
            "candidate_name": "Ana Costa",
            "recruiter_id": "user_002",
            "recruiter_name": "Pedro Lima",
        }

        async with AsyncClient(
            transport=ASGITransport(app=_test_app), base_url=BASE_URL
        ) as client:
            await client.post("/api/v1/teams/webhook", json=reject_payload)
            response = await client.get("/api/v1/teams/webhook/audit-logs")

        assert response.status_code == 200
        data = response.json()

        assert "logs" in data
        assert "count" in data
        assert "total" in data
        assert isinstance(data["logs"], list)

    @patch("app.api.v1.teams.settings.TEAMS_WEBHOOK_SECRET", None)
    async def test_audit_logs_filter_by_action(self):
        """Test that audit logs can be filtered by action."""
        async with AsyncClient(
            transport=ASGITransport(app=_test_app), base_url=BASE_URL
        ) as client:
            response = await client.get(
                "/api/v1/teams/webhook/audit-logs", params={"action": "reject"}
            )

        assert response.status_code == 200
        data = response.json()

        for log in data["logs"]:
            assert log["action"] == "reject"

    @patch("app.api.v1.teams.settings.TEAMS_WEBHOOK_SECRET", None)
    async def test_audit_logs_filter_by_candidate(self):
        """Test that audit logs can be filtered by candidate_id."""
        async with AsyncClient(
            transport=ASGITransport(app=_test_app), base_url=BASE_URL
        ) as client:
            response = await client.get(
                "/api/v1/teams/webhook/audit-logs",
                params={"candidate_id": "cand_audit_test"},
            )

        assert response.status_code == 200
        data = response.json()

        for log in data["logs"]:
            assert log["candidate_id"] == "cand_audit_test"

    @patch("app.api.v1.teams.settings.TEAMS_WEBHOOK_SECRET", None)
    async def test_audit_logs_respects_limit(self):
        """Test that audit logs respects limit parameter."""
        async with AsyncClient(
            transport=ASGITransport(app=_test_app), base_url=BASE_URL
        ) as client:
            response = await client.get(
                "/api/v1/teams/webhook/audit-logs", params={"limit": 5}
            )

        assert response.status_code == 200
        data = response.json()

        assert len(data["logs"]) <= 5


@pytest.mark.asyncio
class TestTeamsWebhookPayloadValidation:
    """Tests for payload validation in Teams webhook."""

    @patch("app.api.v1.teams.settings.TEAMS_WEBHOOK_SECRET", None)
    async def test_action_is_case_insensitive(self):
        """Test that action field is case-insensitive."""
        for action in ["APPROVE", "Approve", "aPpRoVe"]:
            payload = {
                "action": action,
                "candidate_id": "cand_test_123",
                "candidate_name": "Test User",
            }

            async with AsyncClient(
                transport=ASGITransport(app=_test_app), base_url=BASE_URL
            ) as client:
                response = await client.post("/api/v1/teams/webhook", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["action"] == "approve"

    @patch("app.api.v1.teams.settings.TEAMS_WEBHOOK_SECRET", None)
    async def test_company_id_from_header(self):
        """Test that company_id can come from X-Company-ID header."""
        payload = {
            "action": "reject",
            "candidate_id": "cand_test_123",
            "candidate_name": "Test User",
        }

        async with AsyncClient(
            transport=ASGITransport(app=_test_app), base_url=BASE_URL
        ) as client:
            response = await client.post(
                "/api/v1/teams/webhook",
                json=payload,
                headers={"X-Company-ID": "comp_from_header"},
            )

        assert response.status_code == 200

    @patch("app.api.v1.teams.settings.TEAMS_WEBHOOK_SECRET", None)
    async def test_metadata_field_is_optional(self):
        """Test that metadata field is optional."""
        payload = {
            "action": "reject",
            "candidate_id": "cand_test_123",
            "candidate_name": "Test User",
        }

        async with AsyncClient(
            transport=ASGITransport(app=_test_app), base_url=BASE_URL
        ) as client:
            response = await client.post("/api/v1/teams/webhook", json=payload)

        assert response.status_code == 200

    @patch("app.api.v1.teams.settings.TEAMS_WEBHOOK_SECRET", None)
    async def test_metadata_field_with_extra_data(self):
        """Test that metadata field accepts extra data."""
        payload = {
            "action": "reject",
            "candidate_id": "cand_test_123",
            "candidate_name": "Test User",
            "metadata": {
                "source": "teams_notification",
                "channel_id": "19:abc123",
                "custom_field": "custom_value",
            },
        }

        async with AsyncClient(
            transport=ASGITransport(app=_test_app), base_url=BASE_URL
        ) as client:
            response = await client.post("/api/v1/teams/webhook", json=payload)

        assert response.status_code == 200
