"""
SENSOR (harness-engineering): HITL approval via REST canonical wiring.

Detects regressions where the REST `/api/v1/wizard/smart-orchestrate`
endpoint bypasses `wizard_gate_service.resume_gate(...)` when a frontend
client submits an approval/rejection of a wizard gate.

Mirrors the WS pattern in agent_chat_ws.py:683-687 — same canonical
service, same idempotency guarantees, same audit trail.

Sentinels (3 sufficient — symmetric cases dropped to avoid TestClient
asyncio cleanup races):
  - approval_decision="approved" → resume_gate called, process_message NOT
  - approval_decision without pending_id → handler-level 422 with
    LLM-readable message naming both fields
  - resume_gate ValueError → HTTP 200 with error field populated (never 500)

Run:
  pytest tests/integration/test_wizard_hitl_approval_rest.py -v
"""
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app  # type: ignore


REAL_USER_ID = "13cf82fb-f1f6-4205-9377-758e59040148"
REAL_COMPANY = "00000000-0000-4000-a000-000000000001"


def _make_token() -> str:
    from datetime import timedelta

    from app.auth.security import create_access_token

    return create_access_token(
        subject=REAL_USER_ID,
        role="recruiter",
        company_id=REAL_COMPANY,
        expires_delta=timedelta(hours=1),
    )


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_make_token()}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_approval_decision_calls_resume_gate(client: TestClient) -> None:
    """approval_decision='approved' MUST call wizard_gate_service.resume_gate
    and MUST NOT call WizardSessionService.process_message.
    """
    fake_gate_result = {
        "status": "ok",
        "message": "Aprovado! Avançando para a próxima etapa.",
        "gate_id": "gate:thread-abc:pending-xyz",
        "cached": False,
        "decision": "approved",
    }
    with patch(
        "app.domains.job_creation.services.wizard_gate_service.wizard_gate_service.resume_gate",
        new=AsyncMock(return_value=fake_gate_result),
    ) as mock_resume, patch(
        "app.domains.job_creation.services.wizard_session_service.WizardSessionService.process_message",
        new=AsyncMock(return_value=("should-not-be-called", {}, 0)),
    ) as mock_process:
        response = client.post(
            "/api/v1/wizard/smart-orchestrate",
            headers=_headers(),
            json={
                "message": "ignored when approval_decision set",
                "approval_decision": "approved",
                "pending_id": "test-pending-uuid",
                "conversation_id": "test-conv-hitl",
            },
        )

    assert response.status_code == 200
    body = response.json()
    data = body.get("data", body)
    assert data["success"] is True
    assert data["intent"] == "hitl_approved"
    assert data["awaiting_confirmation"] is False
    assert "Aprovado" in data["lia_message"]
    mock_resume.assert_awaited_once()
    mock_process.assert_not_called()


def test_approval_without_pending_id_returns_422(client: TestClient) -> None:
    """Handler-level guard MUST reject approval_decision without pending_id.

    The error response body must contain 'approval_decision' AND 'pending_id'
    keywords — that's the LLM-optimized message harness-engineering requires
    so future agents can self-correct when seeing this error.
    """
    response = client.post(
        "/api/v1/wizard/smart-orchestrate",
        headers=_headers(),
        json={
            "approval_decision": "approved",
            # missing pending_id intentionally
            "conversation_id": "test-conv-422",
        },
    )
    assert response.status_code == 422
    body = response.json()
    detail_str = str(body).lower()
    assert "approval_decision" in detail_str
    assert "pending_id" in detail_str


def test_resume_gate_value_error_returns_structured_error(client: TestClient) -> None:
    """When resume_gate raises ValueError (invalid gate_id mismatch, etc),
    the endpoint MUST return HTTP 200 with structured error field — never
    500, so the frontend can show a graceful message.
    """
    with patch(
        "app.domains.job_creation.services.wizard_gate_service.wizard_gate_service.resume_gate",
        new=AsyncMock(side_effect=ValueError("gate_id mismatch")),
    ):
        response = client.post(
            "/api/v1/wizard/smart-orchestrate",
            headers=_headers(),
            json={
                "message": "ignored",
                "approval_decision": "rejected",
                "pending_id": "bad-pending-id",
                "conversation_id": "test-conv-error",
            },
        )

    assert response.status_code == 200
    body = response.json()
    data = body.get("data", body)
    assert data["success"] is False
    assert "inválido" in data["lia_message"].lower() or "invalid" in (data.get("error") or "").lower()
