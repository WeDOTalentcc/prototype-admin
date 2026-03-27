"""
Email Providers Package.

Provides a unified interface for different email sending services
with factory pattern for provider selection.

Supported providers:
- resend: Resend API (default)
- sendgrid: SendGrid API

Usage:
    from app.services.email_providers import get_email_provider, EmailProvider
    
    # Get provider based on environment/client config
    provider = get_email_provider()
    
    # Or specify provider explicitly
    provider = get_email_provider("sendgrid")
    
    # Send email
    result = await provider.send_email(
        to="user@example.com",
        subject="Hello",
        html_content="<h1>Hello World</h1>"
    )

Environment Variables:
- EMAIL_PROVIDER: Default provider to use (resend|sendgrid)
- RESEND_API_KEY: Resend API key
- SENDGRID_API_KEY: SendGrid API key
"""
import os
import logging
from typing import Dict, Optional, Type

from .base import EmailProvider, EmailMessage, EmailResult
from .resend_provider import ResendProvider
from .sendgrid_provider import SendGridProvider

logger = logging.getLogger(__name__)

__all__ = [
    "EmailProvider",
    "EmailMessage", 
    "EmailResult",
    "ResendProvider",
    "SendGridProvider",
    "get_email_provider",
    "get_provider_for_client",
    "AVAILABLE_PROVIDERS"
]

AVAILABLE_PROVIDERS: Dict[str, Type[EmailProvider]] = {
    "resend": ResendProvider,
    "sendgrid": SendGridProvider,
}

_provider_instances: Dict[str, EmailProvider] = {}


def get_email_provider(
    provider_name: Optional[str] = None,
    api_key: Optional[str] = None,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None,
    use_cache: bool = True
) -> EmailProvider:
    """
    Factory function to get an email provider instance.
    
    Args:
        provider_name: Provider to use ('resend' or 'sendgrid'). 
                      Defaults to EMAIL_PROVIDER env var or 'resend'.
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
        provider_name = os.getenv("EMAIL_PROVIDER", "resend").lower()
    
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
    
    logger.info(f"Created email provider: {provider_name}")
    return provider


def get_provider_for_client(
    client_id: str,
    client_config: Optional[Dict] = None
) -> EmailProvider:
    """
    Get email provider configured for a specific client.
    
    This allows different clients to use different email providers
    based on their configuration.
    
    Args:
        client_id: Client identifier
        client_config: Optional client configuration dict with:
            - email_provider: Provider name (resend|sendgrid)
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
    
    logger.info(f"Created email provider for client {client_id}: {provider.provider_name}")
    return provider


def clear_provider_cache():
    """Clear all cached provider instances."""
    _provider_instances.clear()
    logger.info("Cleared email provider cache")


def get_all_providers_status() -> Dict[str, Dict]:
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
