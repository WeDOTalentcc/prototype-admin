"""
ATS Provider Factory

Factory for creating and caching ATS client instances.
Supports environment-variable-based configuration and provider status reporting.
"""
import logging
import os


from app.domains.ats_integration.services.ats_clients.base import ATSClient, ATSClientConfig
from app.domains.ats_integration.services.ats_clients.gupy import GupyClient
from app.domains.ats_integration.services.ats_clients.merge import MergeClient
from app.domains.ats_integration.services.ats_clients.pandape import PandapeClient

logger = logging.getLogger(__name__)

PROVIDER_CLASSES: dict[str, type] = {
    "gupy": GupyClient,
    "pandape": PandapeClient,
    "merge": MergeClient,
}


class ATSProviderFactory:
    _cache: dict[str, ATSClient] = {}

    @classmethod
    def get_provider(cls, provider_name: str, config: ATSClientConfig | None = None) -> ATSClient:
        provider_name = provider_name.lower()

        if provider_name in cls._cache:
            return cls._cache[provider_name]

        if config is None:
            config = cls._build_config_from_env(provider_name)

        client_cls = PROVIDER_CLASSES.get(provider_name)
        if client_cls is None:
            raise ValueError(
                f"Unknown ATS provider: {provider_name}. "
                f"Available: {', '.join(PROVIDER_CLASSES.keys())}"
            )

        client = client_cls(config)
        cls._cache[provider_name] = client
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Created ATS client for provider: {provider_name}")
        return client

    @classmethod
    def get_provider_from_env(cls, provider_name: str) -> ATSClient:
        config = cls._build_config_from_env(provider_name)
        return cls.get_provider(provider_name, config)

    @classmethod
    def _build_config_from_env(cls, provider_name: str) -> ATSClientConfig:
        prefix = f"ATS_{provider_name.upper()}"
        api_key = os.getenv(f"{prefix}_API_KEY", "")
        api_secret = os.getenv(f"{prefix}_API_SECRET")
        base_url = os.getenv(f"{prefix}_BASE_URL")
        company_id = os.getenv(f"{prefix}_COMPANY_ID")
        webhook_url = os.getenv(f"{prefix}_WEBHOOK_URL")

        return ATSClientConfig(
            api_key=api_key,
            api_secret=api_secret,
            base_url=base_url,
            company_id=company_id,
            webhook_url=webhook_url,
        )

    @classmethod
    def get_all_providers_status(cls) -> dict[str, dict]:
        status: dict[str, dict] = {}
        for name in PROVIDER_CLASSES:
            prefix = f"ATS_{name.upper()}"
            api_key = os.getenv(f"{prefix}_API_KEY", "")
            status[name] = {
                "provider": name,
                "configured": bool(api_key),
                "cached": name in cls._cache,
            }
        return status

    @classmethod
    def clear_cache(cls) -> None:
        cls._cache.clear()
