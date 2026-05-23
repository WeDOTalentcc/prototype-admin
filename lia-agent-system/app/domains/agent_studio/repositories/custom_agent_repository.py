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
    "in_app": "in_app_enabled",
    "whatsapp": "whatsapp_enabled",
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
            channel: One of {voice, voip, in_app, whatsapp}.
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
