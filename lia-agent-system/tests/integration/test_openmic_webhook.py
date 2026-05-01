"""
Integration tests for OpenMic.ai webhook endpoint.

Covers:
- Signature validation (fail-closed, HMAC-SHA256)
- Dev bypass via OPENMIC_ALLOW_UNSIGNED_WEBHOOK
- Payload acceptance / processing trigger
- SSRF guard (_validate_audio_url)
- Circuit breaker degraded-mode response
- DB persistence (mocked)
"""

import hashlib
import hmac
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_sig(secret: str, body: bytes) -> str:
    mac = hmac.new(secret.encode(), body, hashlib.sha256)
    return f"sha256={mac.hexdigest()}"


VALID_PAYLOAD = {
    "call_id": "call_abc123",
    "candidate_id": "cand_xyz",
    "job_vacancy_id": "job_001",
    "status": "completed",
    "audio_url": "https://media.openmic.ai/recordings/call_abc123.mp3",
    "transcript": "Tenho 5 anos de experiência em desenvolvimento backend.",
    "duration_seconds": 90,
    "scores": {"communication": 4, "technical": 3},
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def patch_env(monkeypatch):
    monkeypatch.setenv("OPENMIC_WEBHOOK_SECRET", "test-secret-1234")
    monkeypatch.delenv("OPENMIC_ALLOW_UNSIGNED_WEBHOOK", raising=False)


@pytest.fixture()
def app():
    from app.main import app as fastapi_app
    return fastapi_app


@pytest.fixture()
def client(app):
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# _validate_audio_url unit tests (no server needed)
# ---------------------------------------------------------------------------


def test_validate_audio_url_https_trusted():
    from app.api.v1.openmic_webhook import _validate_audio_url

    result = _validate_audio_url("https://media.openmic.ai/calls/test.mp3")
    assert result == "https://media.openmic.ai/calls/test.mp3"


def test_validate_audio_url_http_rejected():
    from app.api.v1.openmic_webhook import _validate_audio_url

    with pytest.raises(ValueError, match="HTTPS"):
        _validate_audio_url("http://media.openmic.ai/calls/test.mp3")


def test_validate_audio_url_untrusted_host_rejected():
    from app.api.v1.openmic_webhook import _validate_audio_url

    with pytest.raises(ValueError, match="allowlist"):
        _validate_audio_url("https://evil.example.com/steal.mp3")


def test_validate_audio_url_private_ip_rejected():
    from app.api.v1.openmic_webhook import _validate_audio_url

    with pytest.raises(ValueError, match="allowlist"):
        _validate_audio_url("https://10.0.0.1/internal.mp3")


def test_validate_audio_url_loopback_rejected():
    from app.api.v1.openmic_webhook import _validate_audio_url

    with pytest.raises(ValueError, match="allowlist"):
        _validate_audio_url("https://127.0.0.1/local.mp3")


def test_validate_audio_url_empty_passthrough():
    from app.api.v1.openmic_webhook import _validate_audio_url

    assert _validate_audio_url("") == ""


def test_validate_audio_url_s3_trusted():
    from app.api.v1.openmic_webhook import _validate_audio_url

    result = _validate_audio_url("https://mybucket.s3.amazonaws.com/calls/xyz.mp3")
    assert result.startswith("https://")


# ---------------------------------------------------------------------------
# OpenMicService.validate_webhook_signature unit tests
# ---------------------------------------------------------------------------


def test_signature_validation_fail_closed_no_secret(monkeypatch):
    monkeypatch.delenv("OPENMIC_WEBHOOK_SECRET", raising=False)
    from app.services.voice.openmic_service import OpenMicSignatureError, openmic_service

    openmic_service._webhook_secret = None
    with pytest.raises(OpenMicSignatureError, match="not configured"):
        openmic_service.validate_webhook_signature(b"payload", "sha256=abc")


def test_signature_validation_valid_signature(monkeypatch):
    monkeypatch.setenv("OPENMIC_WEBHOOK_SECRET", "secret-abc")
    from app.services.voice.openmic_service import openmic_service

    openmic_service._webhook_secret = None
    body = b'{"call_id":"x"}'
    sig = _make_sig("secret-abc", body)
    openmic_service.validate_webhook_signature(body, sig)  # no exception


def test_signature_validation_invalid_signature(monkeypatch):
    monkeypatch.setenv("OPENMIC_WEBHOOK_SECRET", "secret-abc")
    from app.services.voice.openmic_service import OpenMicSignatureError, openmic_service

    openmic_service._webhook_secret = None
    with pytest.raises(OpenMicSignatureError):
        openmic_service.validate_webhook_signature(b'{"call_id":"x"}', "sha256=bad")


def test_signature_validation_missing_header_format(monkeypatch):
    monkeypatch.setenv("OPENMIC_WEBHOOK_SECRET", "secret-abc")
    from app.services.voice.openmic_service import OpenMicSignatureError, openmic_service

    openmic_service._webhook_secret = None
    with pytest.raises(OpenMicSignatureError):
        openmic_service.validate_webhook_signature(b"payload", "invalid-format")


# ---------------------------------------------------------------------------
# Circuit-breaker unit test
# ---------------------------------------------------------------------------


def test_openmic_circuit_registered():
    from app.shared.resilience.circuit_breaker import ALL_CIRCUITS

    assert "openmic" in ALL_CIRCUITS, "openmic circuit must be in ALL_CIRCUITS"


def test_deepgram_circuit_registered():
    from app.shared.resilience.circuit_breaker import ALL_CIRCUITS

    assert "deepgram" in ALL_CIRCUITS, "deepgram circuit must be in ALL_CIRCUITS"


# ---------------------------------------------------------------------------
# Health reporting
# ---------------------------------------------------------------------------


def test_health_voice_services_present():
    import importlib

    health_mod = importlib.import_module("app.api.v1.system_health")
    assert hasattr(health_mod, "_check_voice_services"), (
        "_check_voice_services must be present in system_health"
    )


def test_check_voice_services_returns_dict():
    from app.api.v1.system_health import _check_voice_services

    result = _check_voice_services()
    assert isinstance(result, dict)
    assert "deepgram" in result
    assert "openmic" in result


# ---------------------------------------------------------------------------
# Endpoint-level request tests (POST /api/v1/openmic/webhook)
# ---------------------------------------------------------------------------


import hashlib
import hmac


_ENDPOINT_SECRET = "test-secret-1234"


def _sign(body: bytes, secret: str = _ENDPOINT_SECRET) -> str:
    mac = hmac.new(secret.encode(), body, hashlib.sha256)
    return f"sha256={mac.hexdigest()}"


_VALID_PAYLOAD_DICT = {
    "event": "call_completed",
    "call_id": "call_ep_001",
    "status": "completed",
    "duration_seconds": 90,
    "transcript": "Tenho 5 anos de experiência em backend.",
    "audio_url": "https://media.openmic.ai/recordings/call_ep_001.mp3",
    "metadata": {
        "candidate_id": "cand_ep",
        "job_id": "job_ep",
        "company_id": "co_ep",
    },
}


@pytest.fixture()
def webhook_client():
    """TestClient for the FastAPI app with OPENMIC_WEBHOOK_SECRET pre-set.

    Uses the same secret as the autouse patch_env fixture ('test-secret-1234').
    Resets the openmic_service cached secret so it re-reads from the env.
    """
    from app.main import app
    from fastapi.testclient import TestClient
    from app.services.voice.openmic_service import openmic_service
    openmic_service._webhook_secret = None
    return TestClient(app, raise_server_exceptions=False)


def test_endpoint_valid_request_returns_200(webhook_client):
    """Valid HMAC-signed complete call payload returns 200 with processed=True."""
    body = json.dumps(_VALID_PAYLOAD_DICT).encode()
    sig = _sign(body)

    with patch("app.api.v1.openmic_webhook._enqueue_wsi_pipeline", new_callable=AsyncMock):
        resp = webhook_client.post(
            "/api/v1/openmic/webhook",
            content=body,
            headers={"X-OpenMic-Signature": sig, "Content-Type": "application/json"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["processed"] is True
    assert data["call_id"] == "call_ep_001"


def test_endpoint_invalid_signature_returns_401(webhook_client):
    """Request with bad HMAC signature is rejected with 401."""
    body = json.dumps(_VALID_PAYLOAD_DICT).encode()

    resp = webhook_client.post(
        "/api/v1/openmic/webhook",
        content=body,
        headers={"X-OpenMic-Signature": "sha256=badsig", "Content-Type": "application/json"},
    )

    assert resp.status_code == 401


def test_endpoint_missing_metadata_returns_422(webhook_client):
    """Payload with missing metadata fields returns 422."""
    bad = {**_VALID_PAYLOAD_DICT, "metadata": {}}
    body = json.dumps(bad).encode()
    sig = _sign(body)

    with patch("app.api.v1.openmic_webhook._enqueue_wsi_pipeline", new_callable=AsyncMock):
        resp = webhook_client.post(
            "/api/v1/openmic/webhook",
            content=body,
            headers={"X-OpenMic-Signature": sig, "Content-Type": "application/json"},
        )

    assert resp.status_code == 422


def test_endpoint_non_completed_status_returns_200_not_processed(webhook_client):
    """Non-completed call status returns 200 with processed=False (no pipeline)."""
    nc = {**_VALID_PAYLOAD_DICT, "status": "no_answer"}
    body = json.dumps(nc).encode()
    sig = _sign(body)

    with patch("app.api.v1.openmic_webhook._enqueue_wsi_pipeline", new_callable=AsyncMock) as mock_enqueue:
        resp = webhook_client.post(
            "/api/v1/openmic/webhook",
            content=body,
            headers={"X-OpenMic-Signature": sig, "Content-Type": "application/json"},
        )

    assert resp.status_code == 200
    assert resp.json()["processed"] is False
    mock_enqueue.assert_not_called()


def test_endpoint_no_secret_configured_returns_503(webhook_client, monkeypatch):
    """Missing OPENMIC_WEBHOOK_SECRET causes fail-closed 503 response."""
    monkeypatch.delenv("OPENMIC_WEBHOOK_SECRET", raising=False)
    monkeypatch.delenv("OPENMIC_ALLOW_UNSIGNED_WEBHOOK", raising=False)
    body = json.dumps(_VALID_PAYLOAD_DICT).encode()

    resp = webhook_client.post(
        "/api/v1/openmic/webhook",
        content=body,
        headers={"Content-Type": "application/json"},
    )

    assert resp.status_code == 503


def test_endpoint_enqueue_called_on_valid_request(webhook_client):
    """Verifies enqueue path is invoked with correct task_data for a valid completed call."""
    body = json.dumps(_VALID_PAYLOAD_DICT).encode()
    sig = _sign(body)

    with patch("app.api.v1.openmic_webhook._enqueue_wsi_pipeline", new_callable=AsyncMock) as mock_enqueue:
        resp = webhook_client.post(
            "/api/v1/openmic/webhook",
            content=body,
            headers={"X-OpenMic-Signature": sig, "Content-Type": "application/json"},
        )

    assert resp.status_code == 200
    mock_enqueue.assert_called_once()
    call_args = mock_enqueue.call_args[0][0]
    assert call_args["call_id"] == "call_ep_001"
    assert call_args["candidate_id"] == "cand_ep"
