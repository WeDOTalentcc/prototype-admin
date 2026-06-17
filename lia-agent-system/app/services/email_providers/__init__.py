"""
Email Providers Package.

Provides a unified interface for different email sending services
with factory pattern for provider selection.

Supported providers:
- mailgun: Mailgun API (primary)
- resend: Resend API (fallback)

Usage:
    from app.services.email_providers import get_email_provider, EmailProvider

    # Get provider based on environment/client config
    provider = get_email_provider()

    # Or specify provider explicitly
    provider = get_email_provider("mailgun")

    # Send email
    result = await provider.send_email(
        to="user@example.com",
        subject="Hello",
        html_content="<h1>Hello World</h1>"
    )

Environment Variables:
- EMAIL_PROVIDER: Default provider to use (mailgun|resend)
- MAILGUN_API_KEY: Mailgun API key (required for Mailgun)
- MAILGUN_DOMAIN: Mailgun sending domain (required for Mailgun)
- RESEND_API_KEY: Resend API key (required for Resend fallback)
"""
import logging
import os
from typing import Dict, Optional, Type

from fastapi import status

from .base import EmailMessage, EmailProvider, EmailResult
from .mailgun_provider import MailgunProvider
from .resend_provider import ResendProvider

logger = logging.getLogger(__name__)

__all__ = [
    "EmailProvider",
    "EmailMessage",
    "EmailResult",
    "ResendProvider",
    "MailgunProvider",
    "get_email_provider",
    "get_provider_for_client",
    "AVAILABLE_PROVIDERS"
]

AVAILABLE_PROVIDERS: dict[str, type[EmailProvider]] = {
    "mailgun": MailgunProvider,
    "resend": ResendProvider,
}

_provider_instances: dict[str, EmailProvider] = {}


def get_email_provider(
    provider_name: str | None = None,
    api_key: str | None = None,
    from_email: str | None = None,
    from_name: str | None = None,
    use_cache: bool = True
) -> EmailProvider:
    """
    Factory function to get an email provider instance.

    Args:
        provider_name: Provider to use ('mailgun' or 'resend').
                      Defaults to EMAIL_PROVIDER env var or 'mailgun'.
        api_key: Optional API key override
        from_email: Optional sender email override
        from_name: Optional sender name override
        use_cache: Whether to cache and reuse provider instances

    Returns:
        Configured EmailProvider instance

    Raises:
        ValueError: If provider_name is not supported
    """
    if provider_name is None:
        provider_name = os.getenv("EMAIL_PROVIDER", "mailgun").lower()

    provider_name = provider_name.lower()

    if provider_name not in AVAILABLE_PROVIDERS:
        raise ValueError(
            f"Unknown email provider: {provider_name}. "
            f"Available: {list(AVAILABLE_PROVIDERS.keys())}"
        )

    cache_key = f"{provider_name}:{api_key or 'default'}"

    if use_cache and cache_key in _provider_instances:
        return _provider_instances[cache_key]

    provider_class = AVAILABLE_PROVIDERS[provider_name]

    kwargs = {}
    if api_key:
        kwargs["api_key"] = api_key
    if from_email:
        kwargs["from_email"] = from_email
    if from_name:
        kwargs["from_name"] = from_name

    provider = provider_class(**kwargs)

    if use_cache:
        _provider_instances[cache_key] = provider

    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"Created email provider: {provider_name}")
    return provider


def get_provider_for_client(
    client_id: str,
    client_config: dict | None = None
) -> EmailProvider:
    """
    Get email provider configured for a specific client.

    This allows different clients to use different email providers
    based on their configuration.

    Args:
        client_id: Client identifier
        client_config: Optional client configuration dict with:
            - email_provider: Provider name (mailgun|resend)
            - email_api_key: Provider-specific API key
            - email_from: Sender email
            - email_from_name: Sender name

    Returns:
        Configured EmailProvider for the client
    """
    if client_config is None:
        client_config = {}

    provider_name = client_config.get("email_provider")
    api_key = client_config.get("email_api_key")
    from_email = client_config.get("email_from")
    from_name = client_config.get("email_from_name")

    cache_key = f"client:{client_id}"

    if cache_key in _provider_instances:
        return _provider_instances[cache_key]

    provider = get_email_provider(
        provider_name=provider_name,
        api_key=api_key,
        from_email=from_email,
        from_name=from_name,
        use_cache=False
    )

    _provider_instances[cache_key] = provider

    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"Created email provider for client {client_id}: {provider.provider_name}")
    return provider


def clear_provider_cache():
    """Clear all cached provider instances."""
    _provider_instances.clear()
    logger.info("Cleared email provider cache")


def get_all_providers_status() -> dict[str, dict]:
    """Get status of all available providers."""
    status = {}
    for name in AVAILABLE_PROVIDERS:
        try:
            provider = get_email_provider(name, use_cache=True)
            status[name] = provider.get_status()
        except Exception as e:
            status[name] = {
                "provider": name,
                "configured": False,
                "healthy": False,
                "error": str(e)
            }
    return status
