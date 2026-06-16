"""
LlmConfigRepository — data access for per-tenant LLM configuration.
Extracted from app/api/v1/llm_config.py as part of Phase 2 refactor.
API keys are encrypted at-rest using Fernet symmetric encryption.
"""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.encryption import encrypt_value, decrypt_value

logger = logging.getLogger(__name__)

def _encrypt_provider_keys(providers: dict) -> dict:
    encrypted = {}
    for name, prov in providers.items():
        if prov.get("_remove"):
            continue
        p = dict(prov) if isinstance(prov, dict) else {}
        if "api_key" in p and p["api_key"] and not p["api_key"].startswith("gAAAAA"):
            p["api_key"] = encrypt_value(p["api_key"])
        encrypted[name] = p
    return encrypted


def _decrypt_provider_keys(providers: dict) -> dict:
    decrypted = {}
    for name, prov in (providers or {}).items():
        p = dict(prov) if isinstance(prov, dict) else {}
        if "api_key" in p and p["api_key"]:
            p["api_key"] = decrypt_value(p["api_key"])
        decrypted[name] = p
    return decrypted


class _Snapshot:
    """Detached snapshot of TenantLLMConfig to prevent ORM dirty-flush of decrypted keys."""
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class LlmConfigRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_company_id(self, company_id: str):
        """Return a detached snapshot of TenantLLMConfig for company, or None.
        API keys are decrypted for internal use.
        Returns a detached snapshot to avoid ORM dirty-flush of decrypted keys."""
        from app.models.tenant_llm_config import TenantLLMConfig

        result = await self.db.execute(
            select(TenantLLMConfig).where(TenantLLMConfig.company_id == company_id)
        )
        config = result.scalar_one_or_none()
        if not config:
            return None

        return _Snapshot(
            id=config.id,
            company_id=config.company_id,
            primary_provider=config.primary_provider,
            fallback_order=list(config.fallback_order) if config.fallback_order else [],
            providers=_decrypt_provider_keys(config.providers) if config.providers else {},
            routing=dict(config.routing) if config.routing else {},
            config=dict(config.config) if hasattr(config, 'config') and config.config else {},
            is_active=config.is_active,
            created_at=config.created_at,
            updated_at=config.updated_at,
            created_by=getattr(config, 'created_by', None),
        )

    @staticmethod
    def decrypt_provider_key(value: str) -> str:
        """Decrypt a single provider key value."""
        return decrypt_value(value)

    def _merge_providers(self, existing: dict | None, incoming: dict) -> dict:
        """Merge incoming providers into existing ones, handling _remove flag."""
        merged = dict(existing or {})
        for name, prov in incoming.items():
            if prov.get("_remove"):
                merged.pop(name, None)
            else:
                p = dict(prov)
                if "api_key" in p and p["api_key"] and not p["api_key"].startswith("gAAAAA"):
                    p["api_key"] = encrypt_value(p["api_key"])
                merged[name] = p
        return merged

    async def upsert(
        self,
        company_id: str,
        primary_provider: str,
        fallback_order: list[str],
        providers_dict: dict,
        routing: dict,
        created_by: str,
        region: str | None = None,
    ):
        """Create or update TenantLLMConfig; return instance (no flush — caller commits).
        API keys are encrypted before persisting. Handles provider removal."""
        from app.models.tenant_llm_config import TenantLLMConfig

        result = await self.db.execute(
            select(TenantLLMConfig).where(TenantLLMConfig.company_id == company_id)
        )
        config = result.scalar_one_or_none()

        if config:
            config.providers = self._merge_providers(config.providers, providers_dict)
            config.primary_provider = primary_provider
            config.fallback_order = fallback_order
            config.routing = routing
            # W2-012-B (2026-05-23): region update path
            if region is not None:
                config.region = region
        else:
            encrypted_providers = _encrypt_provider_keys(providers_dict)
            config = TenantLLMConfig(
                company_id=company_id,
                primary_provider=primary_provider,
                fallback_order=fallback_order,
                providers=encrypted_providers,
                routing=routing,
                created_by=created_by,
                region=region,  # W2-012-B (2026-05-23): LGPD Art 33 region pinning
            )
            self.db.add(config)

        logger.info(
            "[LlmConfigRepo] upsert company_id=%s by=%s provider=%s",
            company_id, created_by, primary_provider,
        )
        return config
