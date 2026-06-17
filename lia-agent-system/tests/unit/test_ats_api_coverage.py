"""
Unit tests for ATS API endpoints — targeting app/api/v1/ats.py.
Covers: _validate_api_endpoint, request models, endpoint shapes.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone
from fastapi import HTTPException


# ---------------------------------------------------------------------------
# _validate_api_endpoint (pure logic, SSRF protection)
# ---------------------------------------------------------------------------

class TestValidateApiEndpoint:
    def test_none_returns_none(self):
        from app.api.v1.ats import _validate_api_endpoint
        assert _validate_api_endpoint("gupy", None) is None

    def test_valid_gupy_endpoint(self):
        from app.api.v1.ats import _validate_api_endpoint
        result = _validate_api_endpoint("gupy", "https://api.gupy.io/v1/jobs")
        assert result == "https://api.gupy.io/v1/jobs"

    def test_valid_pandape_endpoint(self):
        from app.api.v1.ats import _validate_api_endpoint
        result = _validate_api_endpoint("pandape", "https://api.pandape.com/v1")
        assert result == "https://api.pandape.com/v1"

    def test_valid_merge_endpoint(self):
        from app.api.v1.ats import _validate_api_endpoint
        result = _validate_api_endpoint("merge", "https://api.merge.dev/api/ats")
        assert result == "https://api.merge.dev/api/ats"

    def test_invalid_domain_raises_400(self):
        from app.api.v1.ats import _validate_api_endpoint
        with pytest.raises(HTTPException) as exc:
            _validate_api_endpoint("gupy", "https://evil.com/api")
        assert exc.value.status_code == 400
        assert "Invalid API endpoint" in str(exc.value.detail)

    def test_http_instead_of_https_raises_400(self):
        from app.api.v1.ats import _validate_api_endpoint
        with pytest.raises(HTTPException) as exc:
            _validate_api_endpoint("gupy", "http://api.gupy.io/v1/jobs")
        assert exc.value.status_code == 400
        assert "HTTPS" in str(exc.value.detail)

    def test_unknown_provider_rejects_all_domains(self):
        from app.api.v1.ats import _validate_api_endpoint
        with pytest.raises(HTTPException):
            _validate_api_endpoint("unknown", "https://anything.com/api")

    def test_pandape_alternative_domain(self):
        from app.api.v1.ats import _validate_api_endpoint
        result = _validate_api_endpoint("pandape", "https://api-pandape.infojobs.com.br/v1")
        assert "infojobs" in result


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class TestATSRequestModels:
    def test_create_connection_request(self):
        from app.api.v1.ats import CreateATSConnectionRequest
        req = CreateATSConnectionRequest(
            provider="gupy",
            provider_name="Gupy",
            api_key="key-123",
            api_secret="secret-456",
        )
        assert req.provider == "gupy"
        assert req.api_key == "key-123"

    def test_create_connection_request_optional_fields(self):
        from app.api.v1.ats import CreateATSConnectionRequest
        req = CreateATSConnectionRequest(
            provider="pandape",
            provider_name="Pandape",
            api_key="key-123",
        )
        assert req.api_secret is None

    def test_test_connection_request(self):
        from app.api.v1.ats import TestATSConnectionRequest
        req = TestATSConnectionRequest(
            provider="merge",
            api_key="key-abc",
        )
        assert req.provider == "merge"

    def test_save_field_mappings_request(self):
        from app.api.v1.ats import SaveFieldMappingsRequest
        req = SaveFieldMappingsRequest(
            connection_id="conn-1",
            mappings=[{"source": "name", "target": "full_name"}],
        )
        assert req.connection_id == "conn-1"

    def test_trigger_sync_request(self):
        from app.api.v1.ats import TriggerSyncRequest
        req = TriggerSyncRequest(
            sync_type="full",
            filters={},
        )
        assert req.sync_type == "full"


# ---------------------------------------------------------------------------
# _test_provider_connection
# ---------------------------------------------------------------------------

class TestProviderConnection:
    @pytest.mark.asyncio
    async def test_gupy_connection_test(self):
        from app.api.v1.ats import _test_provider_connection
        mock_service = AsyncMock()
        mock_service.test_connection = AsyncMock(return_value=True)
        with patch("app.api.v1.ats.GupyService", return_value=mock_service):
            result = await _test_provider_connection("gupy", "key-123")
            assert result is True

    @pytest.mark.asyncio
    async def test_pandape_connection_test(self):
        from app.api.v1.ats import _test_provider_connection
        mock_service = AsyncMock()
        mock_service.test_connection = AsyncMock(return_value=True)
        with patch("app.api.v1.ats.PandapeService", return_value=mock_service):
            result = await _test_provider_connection("pandape", "key-123", "https://api.pandape.com/v1")
            assert result is True

    @pytest.mark.asyncio
    async def test_merge_connection_test_success(self):
        from app.api.v1.ats import _test_provider_connection
        import httpx
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_resp)
        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await _test_provider_connection("merge", "key-123")
            assert result is True

    @pytest.mark.asyncio
    async def test_merge_connection_test_failure(self):
        from app.api.v1.ats import _test_provider_connection
        import httpx
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=Exception("timeout"))
        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await _test_provider_connection("merge", "key-123")
            assert result is False

    @pytest.mark.asyncio
    async def test_unknown_provider_returns_false(self):
        from app.api.v1.ats import _test_provider_connection
        result = await _test_provider_connection("unknown_ats", "key-123")
        assert result is False


# ---------------------------------------------------------------------------
# SUPPORTED_PROVIDERS and ALLOWED_ATS_DOMAINS
# ---------------------------------------------------------------------------

class TestATSConstants:
    def test_supported_providers(self):
        from app.api.v1.ats import SUPPORTED_PROVIDERS
        assert "gupy" in SUPPORTED_PROVIDERS
        assert "pandape" in SUPPORTED_PROVIDERS
        assert "merge" in SUPPORTED_PROVIDERS

    def test_allowed_domains_per_provider(self):
        from app.api.v1.ats import ALLOWED_ATS_DOMAINS
        assert "api.gupy.io" in ALLOWED_ATS_DOMAINS["gupy"]
        assert "api.merge.dev" in ALLOWED_ATS_DOMAINS["merge"]


# ---------------------------------------------------------------------------
# Webhook processing (using mock request)
# ---------------------------------------------------------------------------

class TestWebhookProcessing:
    @pytest.mark.asyncio
    async def test_process_webhook_event_dispatches_gupy(self):
        from app.api.v1.ats import _process_webhook_event
        mock_repo = AsyncMock()
        conn_id = uuid4()
        with patch("app.api.v1.ats._process_gupy_webhook", new_callable=AsyncMock, return_value=True) as mock_gupy:
            result = await _process_webhook_event("gupy", "candidate.created", {"data": {}}, mock_repo, connection_id=conn_id)
            mock_gupy.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_webhook_event_dispatches_pandape(self):
        from app.api.v1.ats import _process_webhook_event
        mock_repo = AsyncMock()
        conn_id = uuid4()
        with patch("app.api.v1.ats._process_pandape_webhook", new_callable=AsyncMock, return_value=True) as mock_pp:
            result = await _process_webhook_event("pandape", "candidate.updated", {"data": {}}, mock_repo, connection_id=conn_id)
            mock_pp.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_webhook_event_dispatches_merge(self):
        from app.api.v1.ats import _process_webhook_event
        mock_repo = AsyncMock()
        conn_id = uuid4()
        with patch("app.api.v1.ats._process_merge_webhook", new_callable=AsyncMock, return_value=True) as mock_merge:
            result = await _process_webhook_event("merge", "sync.complete", {"data": {}}, mock_repo, connection_id=conn_id)
            mock_merge.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_webhook_event_no_connection_returns_false(self):
        from app.api.v1.ats import _process_webhook_event
        mock_repo = AsyncMock()
        result = await _process_webhook_event("gupy", "candidate.created", {}, mock_repo, connection_id=None)
        assert result is False

    @pytest.mark.asyncio
    async def test_process_webhook_event_unknown_provider_returns_false(self):
        from app.api.v1.ats import _process_webhook_event
        mock_repo = AsyncMock()
        result = await _process_webhook_event("unknown", "event", {}, mock_repo, connection_id=uuid4())
        assert result is False
