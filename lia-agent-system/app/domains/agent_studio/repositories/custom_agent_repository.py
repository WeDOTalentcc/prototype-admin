"""CustomAgent repository — canonical ADR-001 abstraction.

C.5 ticket (2026-05-23). Consolidates the inline `select(CustomAgent)` +
`update(CustomAgent)` calls that Sprint 3.7 left scattered across three
endpoint modules under `# ADR-001-EXEMPT` markers:

  - app/api/v1/agent_studio_voice.py:_load_agent_for_company
  - app/api/v1/agent_studio_whatsapp.py:_load_agent_for_company
  - app/api/v1/agent_studio_channels.py:_load_agent_for_company

Multi-tenancy fail-closed: every public method calls _require_company_id.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.custom_agent import CustomAgent


def _require_company_id(company_id: Any) -> None:
    """Fail-closed guard mirrored from VoiceSessionRedisRepository."""
    if not isinstance(company_id, str) or not company_id.strip():
        raise ValueError(
            "CustomAgentRepository: company_id is required (multi-tenancy "
            "fail-closed)."
        )


# Canonical channel column allowlist. Update both:
# (a) libs/models/lia_models/custom_agent.py columns
# (b) this set
# (c) tests/contract/test_custom_agent_repository.py
# when adding new channel flags.
_CHANNEL_COLUMN_MAP = {
    "voice": "voice_enabled",
    "voip": "voip_enabled",
    "whatsapp": "whatsapp_enabled",
    # Workstream A 2026-05-23: 4o toggle — capability "convite triagem candidato".
    # Diferente dos 3 canais diretos, este e capability (cria token + URL publica).
    "triagem_invite": "triagem_invite_enabled",
}


class CustomAgentRepository:
    """ADR-001 canonical reads/writes for CustomAgent rows.

    Replaces ad-hoc `select(CustomAgent)` + `update(CustomAgent)` in
    agent_studio_voice / agent_studio_whatsapp / agent_studio_channels.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(
        self, *, agent_id: str, company_id: str
    ) -> CustomAgent | None:
        """Load a CustomAgent scoped to the tenant.

        Returns None if no row matches. Caller decides on 404 surfacing.
        """
        _require_company_id(company_id)
        stmt = select(CustomAgent).where(
            CustomAgent.id == agent_id,
            CustomAgent.company_id == company_id,
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_channel_flag(
        self,
        *,
        agent_id: str,
        company_id: str,
        channel: str,
        enabled: bool,
    ) -> None:
        """Toggle one canonical channel flag on a CustomAgent row.

        Args:
            channel: One of {voice, voip, whatsapp, triagem_invite}.
        """
        _require_company_id(company_id)
        if channel not in _CHANNEL_COLUMN_MAP:
            raise ValueError(
                f"CustomAgentRepository.update_channel_flag: unknown channel "
                f"{channel!r}. Valid: {sorted(_CHANNEL_COLUMN_MAP.keys())}"
            )
        column_name = _CHANNEL_COLUMN_MAP[channel]
        stmt = (
            update(CustomAgent)
            .where(
                CustomAgent.id == agent_id,
                CustomAgent.company_id == company_id,
            )
            .values({column_name: bool(enabled)})
        )
        await self._db.execute(stmt)
        await self._db.commit()

    async def list_first_party_agents(self) -> list[CustomAgent]:
        """Returns all active first-party (WeDo global) Studio agents.

        # TENANT-FREE: first_party agents have company_id=None — intentional.
        # No _require_company_id guard: these agents are explicitly global
        # (Fase A decision). Scoped agents use get_by_id().
        """
        from lia_models.custom_agent import AgentType  # local to avoid circular at module level

        stmt = select(CustomAgent).where(
            CustomAgent.agent_type == AgentType.first_party,
            CustomAgent.status == "active",
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def update_first_party_manifest(
        self,
        *,
        agent_id: str,
        domains: list[str],
        allowed_tools: list[str],
    ) -> None:
        """Update domains + allowed_tools on a first-party agent and invalidate cache.

        # TENANT-FREE: no company_id guard — first_party agents are global.
        """
        from lia_models.custom_agent import AgentType
        from app.orchestrator.studio_scope_extension import invalidate_studio_scope_cache

        stmt = (
            update(CustomAgent)
            .where(
                CustomAgent.id == agent_id,
                CustomAgent.agent_type == AgentType.first_party,
            )
            .values(domains=domains, allowed_tools=allowed_tools)
        )
        await self._db.execute(stmt)
        await self._db.commit()
        # Invalidate the shared scope cache so the next request rebuilds it.
        invalidate_studio_scope_cache()

    async def list_active_for_context(
        self,
        *,
        company_id: str | None,
        domain: str,
        include_first_party: bool = True,
    ) -> list:
        """Return active Studio agents covering domain for a tenant context.

        Priority:
          1. Tenant-scoped custom agents (company_id match + domain).
          2. First-party global agents (company_id=None) when include_first_party=True.

        TENANT-AWARE: first_party agents have company_id=None by design (global).
        Returns empty list (not an error) when no agents match.
        """
        from lia_models.custom_agent import AgentType
        from sqlalchemy import and_

        # Tenant-scoped custom agents with matching domain (JSONB contains check).
        tenant_agents: list = []
        if company_id:
            tenant_stmt = select(CustomAgent).where(
                and_(
                    CustomAgent.status == "active",
                    CustomAgent.agent_type == AgentType.custom,
                    CustomAgent.company_id == company_id,
                    CustomAgent.domains.contains([domain]),
                )
            ).order_by(CustomAgent.name)
            result = await self._db.execute(tenant_stmt)
            tenant_agents = list(result.scalars().all())

        if tenant_agents:
            return tenant_agents  # tenant deployment wins over global

        if not include_first_party:
            return []

        # Global first-party agents as fallback (TENANT-FREE: company_id=None).
        fp_stmt = select(CustomAgent).where(
            CustomAgent.agent_type == AgentType.first_party,
            CustomAgent.status == "active",
            CustomAgent.domains.contains([domain]),
        ).order_by(CustomAgent.name)
        fp_result = await self._db.execute(fp_stmt)
        return list(fp_result.scalars().all())
