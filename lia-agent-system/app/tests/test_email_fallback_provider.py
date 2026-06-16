"""
Unit tests for Mailgun→Resend automatic fallback email provider.

Tests:
- Mailgun success path (no fallback needed)
- Mailgun failure triggers automatic Resend fallback
- MAILGUN_CIRCUIT open routes immediately to Resend
- Both circuits open returns failure without sending
- get_status reflects both providers
"""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.communication.services.email_providers.fallback_provider import FallbackEmailProvider
from app.services.email_providers.base import EmailResult


def _make_provider(name: str, success: bool, error: str = None) -> MagicMock:
    provider = MagicMock()
    provider.provider_name = name
    provider.get_status.return_value = {
        "provider": name,
        "configured": True,
        "healthy": True,
    }
    result = EmailResult(
        success=success,
        message_id=f"{name}-msg-id" if success else None,
        provider=name,
        status="sent" if success else "failed",
        error=error,
        sent_at=datetime.utcnow() if success else None,
    )
    provider.send_email = AsyncMock(return_value=result)
    return provider


COMMON_SEND_KWARGS = dict(
    to="user@example.com",
    subject="Test",
    html_content="<h1>Hello</h1>",
    text_content="Hello",
)


class TestFallbackEmailProvider:

    @pytest.mark.asyncio
    async def test_primary_success_no_fallback(self):
        """When Mailgun succeeds, Resend must not be called."""
        mailgun = _make_provider("mailgun", success=True)
        resend = _make_provider("resend", success=True)

        with patch(
            "app.domains.communication.services.email_providers.fallback_provider.MAILGUN_CIRCUIT"
        ) as mg_cb, patch(
            "app.domains.communication.services.email_providers.fallback_provider.RESEND_CIRCUIT"
        ) as rs_cb:
            from app.shared.resilience.circuit_breaker import CircuitState
            mg_cb.state = CircuitState.CLOSED
            rs_cb.state = CircuitState.CLOSED

            provider = FallbackEmailProvider(primary=mailgun, fallback=resend)
            result = await provider.send_email(**COMMON_SEND_KWARGS)

        assert result.success is True
        assert result.provider == "mailgun"
        mailgun.send_email.assert_awaited_once()
        resend.send_email.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_primary_failure_triggers_fallback(self):
        """When Mailgun returns failure, Resend fallback must be used."""
        mailgun = _make_provider("mailgun", success=False, error="Mailgun 500 error")
        resend = _make_provider("resend", success=True)

        with patch(
            "app.domains.communication.services.email_providers.fallback_provider.MAILGUN_CIRCUIT"
        ) as mg_cb, patch(
            "app.domains.communication.services.email_providers.fallback_provider.RESEND_CIRCUIT"
        ) as rs_cb:
            from app.shared.resilience.circuit_breaker import CircuitState
            mg_cb.state = CircuitState.CLOSED
            rs_cb.state = CircuitState.CLOSED

            provider = FallbackEmailProvider(primary=mailgun, fallback=resend)
            result = await provider.send_email(**COMMON_SEND_KWARGS)

        assert result.success is True
        assert result.provider == "resend"
        mailgun.send_email.assert_awaited_once()
        resend.send_email.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_mailgun_circuit_open_routes_to_resend(self):
        """When MAILGUN_CIRCUIT is OPEN, Mailgun is skipped and Resend is used."""
        mailgun = _make_provider("mailgun", success=True)
        resend = _make_provider("resend", success=True)

        with patch(
            "app.domains.communication.services.email_providers.fallback_provider.MAILGUN_CIRCUIT"
        ) as mg_cb, patch(
            "app.domains.communication.services.email_providers.fallback_provider.RESEND_CIRCUIT"
        ) as rs_cb:
            from app.shared.resilience.circuit_breaker import CircuitState
            mg_cb.state = CircuitState.OPEN
            rs_cb.state = CircuitState.CLOSED

            provider = FallbackEmailProvider(primary=mailgun, fallback=resend)
            result = await provider.send_email(**COMMON_SEND_KWARGS)

        assert result.success is True
        assert result.provider == "resend"
        mailgun.send_email.assert_not_awaited()
        resend.send_email.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_both_circuits_open_returns_failure(self):
        """When both circuits are OPEN, no send occurs and failure is returned."""
        mailgun = _make_provider("mailgun", success=True)
        resend = _make_provider("resend", success=True)

        with patch(
            "app.domains.communication.services.email_providers.fallback_provider.MAILGUN_CIRCUIT"
        ) as mg_cb, patch(
            "app.domains.communication.services.email_providers.fallback_provider.RESEND_CIRCUIT"
        ) as rs_cb:
            from app.shared.resilience.circuit_breaker import CircuitState
            mg_cb.state = CircuitState.OPEN
            rs_cb.state = CircuitState.OPEN

            provider = FallbackEmailProvider(primary=mailgun, fallback=resend)
            result = await provider.send_email(**COMMON_SEND_KWARGS)

        assert result.success is False
        assert "OPEN" in result.error
        mailgun.send_email.assert_not_awaited()
        resend.send_email.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_primary_exception_triggers_fallback(self):
        """When Mailgun raises an exception, Resend fallback must be used."""
        mailgun = _make_provider("mailgun", success=True)
        mailgun.send_email = AsyncMock(side_effect=ConnectionError("Mailgun unreachable"))
        resend = _make_provider("resend", success=True)

        with patch(
            "app.domains.communication.services.email_providers.fallback_provider.MAILGUN_CIRCUIT"
        ) as mg_cb, patch(
            "app.domains.communication.services.email_providers.fallback_provider.RESEND_CIRCUIT"
        ) as rs_cb:
            from app.shared.resilience.circuit_breaker import CircuitState
            mg_cb.state = CircuitState.CLOSED
            rs_cb.state = CircuitState.CLOSED

            provider = FallbackEmailProvider(primary=mailgun, fallback=resend)
            result = await provider.send_email(**COMMON_SEND_KWARGS)

        assert result.success is True
        assert result.provider == "resend"
        resend.send_email.assert_awaited_once()

    def test_get_status_reflects_both_providers(self):
        """get_status() must include both primary and fallback provider status."""
        mailgun = _make_provider("mailgun", success=True)
        resend = _make_provider("resend", success=True)

        provider = FallbackEmailProvider(primary=mailgun, fallback=resend)
        status = provider.get_status()

        assert status["provider"] == "mailgun_with_resend_fallback"
        assert "primary" in status
        assert "fallback" in status
        assert status["primary"]["provider"] == "mailgun"
        assert status["fallback"]["provider"] == "resend"
        assert status["healthy"] is True
