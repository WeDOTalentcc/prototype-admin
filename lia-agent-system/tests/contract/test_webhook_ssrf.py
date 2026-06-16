"""
Contract tests for webhook SSRF prevention.

P0-W3-06: CreateWebhookRequest / UpdateWebhookRequest (app/schemas/webhook.py) — SSRF
P0-W3-07: WebhookRegisterRequest / WebhookUpdateRequest (app/api/v1/job_status_webhooks.py) — SSRF

These tests verify that both webhook schemas block private IPs, loopback,
link-local, and cloud metadata endpoints, and accept legitimate HTTPS URLs.
"""
import pytest
from pydantic import ValidationError


class TestSafeOutboundUrlDirect:
    """Tests for the canonical URL validator (app/shared/security/url_validator.py)."""

    def test_blocks_loopback_ip(self):
        from app.shared.security.url_validator import safe_outbound_url, UnsafeOutboundURLError
        with pytest.raises(UnsafeOutboundURLError, match="blocked"):
            safe_outbound_url("https://127.0.0.1/webhook", require_https=True)

    def test_blocks_private_ip_192(self):
        from app.shared.security.url_validator import safe_outbound_url, UnsafeOutboundURLError
        with pytest.raises(UnsafeOutboundURLError, match="blocked"):
            safe_outbound_url("https://192.168.1.1/webhook", require_https=True)

    def test_blocks_private_ip_10(self):
        from app.shared.security.url_validator import safe_outbound_url, UnsafeOutboundURLError
        with pytest.raises(UnsafeOutboundURLError, match="blocked"):
            safe_outbound_url("https://10.0.0.1/webhook", require_https=True)

    def test_blocks_aws_metadata(self):
        from app.shared.security.url_validator import safe_outbound_url, UnsafeOutboundURLError
        with pytest.raises(UnsafeOutboundURLError, match="blocked"):
            safe_outbound_url("https://169.254.169.254/latest/meta-data/", require_https=True)

    def test_blocks_localhost_hostname(self):
        from app.shared.security.url_validator import safe_outbound_url, UnsafeOutboundURLError
        with pytest.raises(UnsafeOutboundURLError, match="blocked"):
            safe_outbound_url("https://localhost/webhook", require_https=True)

    def test_blocks_http_scheme(self):
        from app.shared.security.url_validator import safe_outbound_url, UnsafeOutboundURLError
        with pytest.raises(UnsafeOutboundURLError, match="HTTPS"):
            safe_outbound_url("http://example.com/webhook", require_https=True)

    def test_accepts_valid_https_url(self):
        from app.shared.security.url_validator import safe_outbound_url
        result = safe_outbound_url("https://hooks.example.com/webhook", require_https=True)
        assert result == "https://hooks.example.com/webhook"

    def test_blocks_google_metadata_hostname(self):
        from app.shared.security.url_validator import safe_outbound_url, UnsafeOutboundURLError
        with pytest.raises(UnsafeOutboundURLError, match="blocked"):
            safe_outbound_url("https://metadata.google.internal/computeMetadata/v1/", require_https=True)

    def test_blocks_private_ip_172(self):
        from app.shared.security.url_validator import safe_outbound_url, UnsafeOutboundURLError
        with pytest.raises(UnsafeOutboundURLError, match="blocked"):
            safe_outbound_url("https://172.16.0.1/webhook", require_https=True)


class TestCreateWebhookRequestSSRF:
    """Tests for P0-W3-06: app/schemas/webhook.py CreateWebhookRequest."""

    def test_rejects_private_ip_127(self):
        from app.schemas.webhook import CreateWebhookRequest
        with pytest.raises(ValidationError) as exc_info:
            CreateWebhookRequest(
                name="test-webhook",
                url="https://127.0.0.1/webhook",
                events=["agent.execution.completed"]
            )
        assert "seguranca" in str(exc_info.value).lower() or "blocked" in str(exc_info.value).lower()

    def test_rejects_private_ip_192(self):
        from app.schemas.webhook import CreateWebhookRequest
        with pytest.raises(ValidationError):
            CreateWebhookRequest(
                name="test-webhook",
                url="https://192.168.1.100/webhook",
                events=["agent.execution.completed"]
            )

    def test_rejects_private_ip_10(self):
        from app.schemas.webhook import CreateWebhookRequest
        with pytest.raises(ValidationError):
            CreateWebhookRequest(
                name="test-webhook",
                url="https://10.0.0.1/webhook",
                events=["agent.execution.completed"]
            )

    def test_rejects_aws_metadata(self):
        from app.schemas.webhook import CreateWebhookRequest
        with pytest.raises(ValidationError):
            CreateWebhookRequest(
                name="test-webhook",
                url="https://169.254.169.254/latest/meta-data/",
                events=["agent.execution.completed"]
            )

    def test_accepts_valid_https_url(self):
        from app.schemas.webhook import CreateWebhookRequest
        req = CreateWebhookRequest(
            name="test-webhook",
            url="https://hooks.example.com/my-webhook",
            events=["agent.execution.completed"]
        )
        assert req.url == "https://hooks.example.com/my-webhook"


class TestWebhookRegisterRequestSSRF:
    """Tests for P0-W3-07: app/api/v1/job_status_webhooks.py WebhookRegisterRequest."""

    def test_rejects_loopback_ip(self):
        from app.api.v1.job_status_webhooks import WebhookRegisterRequest
        with pytest.raises(ValidationError):
            WebhookRegisterRequest(
                name="test",
                url="https://127.0.0.1:8080/hook"
            )

    def test_rejects_private_ip_192(self):
        from app.api.v1.job_status_webhooks import WebhookRegisterRequest
        with pytest.raises(ValidationError):
            WebhookRegisterRequest(
                name="test",
                url="https://192.168.100.1/hook"
            )

    def test_rejects_aws_metadata(self):
        from app.api.v1.job_status_webhooks import WebhookRegisterRequest
        with pytest.raises(ValidationError):
            WebhookRegisterRequest(
                name="test",
                url="https://169.254.169.254/metadata"
            )

    def test_accepts_valid_https_url(self):
        from app.api.v1.job_status_webhooks import WebhookRegisterRequest
        req = WebhookRegisterRequest(
            name="test",
            url="https://api.example.com/webhooks/receive"
        )
        assert req.url.startswith("https://")

    def test_update_request_rejects_private_ip(self):
        from app.api.v1.job_status_webhooks import WebhookUpdateRequest
        with pytest.raises(ValidationError):
            WebhookUpdateRequest(url="https://10.1.2.3/hook")

    def test_update_request_accepts_none(self):
        from app.api.v1.job_status_webhooks import WebhookUpdateRequest
        req = WebhookUpdateRequest(url=None)
        assert req.url is None

    def test_update_request_accepts_valid_url(self):
        from app.api.v1.job_status_webhooks import WebhookUpdateRequest
        req = WebhookUpdateRequest(url="https://hooks.example.com/updated")
        assert req.url == "https://hooks.example.com/updated"
