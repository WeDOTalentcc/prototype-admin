"""
LlmConfigRepository — data access for per-tenant LLM configuration.
Extracted from app/api/v1/llm_config.py as part of Phase 2 refactor.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


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

    async def upsert(
        self,
        company_id: str,
        primary_provider: str,
        fallback_order: list[str],
        providers_dict: dict,
        routing: dict,
        created_by: str,
    ):
        """Create or update TenantLLMConfig; return instance (no flush — caller commits)."""
        from app.models.tenant_llm_config import TenantLLMConfig

        config = await self.get_by_company_id(company_id)
        if config:
            config.primary_provider = primary_provider
            config.fallback_order = fallback_order
            config.providers = providers_dict
            config.routing = routing
        else:
            config = TenantLLMConfig(
                company_id=company_id,
                primary_provider=primary_provider,
                fallback_order=fallback_order,
                providers=providers_dict,
                routing=routing,
                created_by=created_by,
            )
            self.db.add(config)
        return config
