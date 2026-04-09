"""
LlmConfigRepository — data access for per-tenant LLM configuration.
Extracted from app/api/v1/llm_config.py as part of Phase 2 refactor.
"""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.encryption import encrypt_value, decrypt_value

logger = logging.getLogger(__name__)


class LlmConfigRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_company_id(self, company_id: str):
        """Return TenantLLMConfig for company, or None."""
        from app.models.tenant_llm_config import TenantLLMConfig

        result = await self.db.execute(
            select(TenantLLMConfig).where(TenantLLMConfig.company_id == company_id)
        )
        return result.scalar_one_or_none()

    def _encrypt_providers(self, providers_dict: dict) -> dict:
        encrypted = {}
        for name, prov in providers_dict.items():
            p = dict(prov)
            if "api_key" in p and p["api_key"]:
                raw_key = p["api_key"]
                if not raw_key.startswith("gAAAAA"):
                    p["api_key"] = encrypt_value(raw_key)
            encrypted[name] = p
        return encrypted

    def decrypt_provider_key(self, encrypted_key: str) -> str:
        if not encrypted_key:
            return encrypted_key
        return decrypt_value(encrypted_key)

    def _merge_providers(self, existing: dict | None, incoming: dict) -> dict:
        merged = dict(existing or {})
        for name, prov in incoming.items():
            if prov.get("_remove"):
                merged.pop(name, None)
            else:
                merged[name] = prov
        return merged

    async def upsert(
        self,
        company_id: str,
        primary_provider: str,
        fallback_order: list[str],
        providers_dict: dict,
        routing: dict,
        created_by: str,
    ):
        from app.models.tenant_llm_config import TenantLLMConfig

        config = await self.get_by_company_id(company_id)

        if config:
            merged = self._merge_providers(config.providers, self._encrypt_providers(providers_dict))
            config.primary_provider = primary_provider
            config.fallback_order = fallback_order
            config.providers = merged
            config.routing = routing
        else:
            encrypted_providers = self._encrypt_providers(providers_dict)
            config = TenantLLMConfig(
                company_id=company_id,
                primary_provider=primary_provider,
                fallback_order=fallback_order,
                providers=encrypted_providers,
                routing=routing,
                created_by=created_by,
            )
            self.db.add(config)
        return config
