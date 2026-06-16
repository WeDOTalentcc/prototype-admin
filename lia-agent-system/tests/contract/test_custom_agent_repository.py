"""C.5 contract: CustomAgentRepository canonical (ADR-001 extraction).

Workstream C ticket 5 (2026-05-23).

Sprint 3.7 deixou 3 sites com `select(CustomAgent)` inline + `update`
sob `# ADR-001-EXEMPT` markers porque CustomAgentRepository nao existia
(escopo Sprint 4 follow-up). C.5 consolida o pattern num repositorio
canonical e refatora os 3 endpoints para usar a abstracao.

Multi-tenancy fail-closed: todo metodo publico chama _require_company_id.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Repository declaration contract
# ---------------------------------------------------------------------------

class TestRepositoryDeclaration:
    def test_repository_module_importable(self):
        """C.5: CustomAgentRepository lives at
        app.domains.agent_studio.repositories.custom_agent_repository."""
        from app.domains.agent_studio.repositories.custom_agent_repository import (
            CustomAgentRepository,
        )
        assert CustomAgentRepository is not None

    def test_repository_constructor_takes_db(self):
        """C.5: constructor is CustomAgentRepository(db: AsyncSession)."""
        from app.domains.agent_studio.repositories.custom_agent_repository import (
            CustomAgentRepository,
        )
        db = MagicMock()
        repo = CustomAgentRepository(db)
        assert repo is not None


# ---------------------------------------------------------------------------
# Multi-tenancy contract (fail-closed)
# ---------------------------------------------------------------------------

class TestTenantIsolation:
    @pytest.mark.asyncio
    async def test_get_by_id_rejects_empty_company_id(self):
        """C.5: get_by_id raises ValueError when company_id is empty."""
        from app.domains.agent_studio.repositories.custom_agent_repository import (
            CustomAgentRepository,
        )
        db = MagicMock()
        repo = CustomAgentRepository(db)
        with pytest.raises(ValueError):
            await repo.get_by_id(agent_id="any", company_id="")

    @pytest.mark.asyncio
    async def test_get_by_id_rejects_none_company_id(self):
        """C.5: get_by_id raises ValueError when company_id is None."""
        from app.domains.agent_studio.repositories.custom_agent_repository import (
            CustomAgentRepository,
        )
        db = MagicMock()
        repo = CustomAgentRepository(db)
        with pytest.raises(ValueError):
            await repo.get_by_id(agent_id="any", company_id=None)  # type: ignore[arg-type]

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_found(self):
        """C.5: get_by_id returns None when agent missing in tenant scope."""
        from app.domains.agent_studio.repositories.custom_agent_repository import (
            CustomAgentRepository,
        )
        db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        db.execute = AsyncMock(return_value=mock_result)
        repo = CustomAgentRepository(db)

        result = await repo.get_by_id(agent_id="agent-x", company_id="company-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_returns_agent_when_present(self):
        """C.5: get_by_id returns the CustomAgent instance when found."""
        from app.domains.agent_studio.repositories.custom_agent_repository import (
            CustomAgentRepository,
        )
        sentinel = MagicMock(name="custom_agent_row")
        db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=sentinel)
        db.execute = AsyncMock(return_value=mock_result)
        repo = CustomAgentRepository(db)

        result = await repo.get_by_id(agent_id="agent-x", company_id="company-1")
        assert result is sentinel


# ---------------------------------------------------------------------------
# Update operations contract
# ---------------------------------------------------------------------------

class TestChannelToggleUpdates:
    @pytest.mark.asyncio
    async def test_update_channel_flag_voice(self):
        """C.5: update_channel_flag(voice_enabled=True) executes update + commit."""
        from app.domains.agent_studio.repositories.custom_agent_repository import (
            CustomAgentRepository,
        )
        db = MagicMock()
        db.execute = AsyncMock(return_value=MagicMock())
        db.commit = AsyncMock(return_value=None)
        repo = CustomAgentRepository(db)

        await repo.update_channel_flag(
            agent_id="agent-x", company_id="company-1",
            channel="voice", enabled=True,
        )
        db.execute.assert_awaited_once()
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_channel_flag_unknown_channel_rejected(self):
        """C.5: update_channel_flag rejects unknown channel name (defense)."""
        from app.domains.agent_studio.repositories.custom_agent_repository import (
            CustomAgentRepository,
        )
        db = MagicMock()
        repo = CustomAgentRepository(db)
        with pytest.raises(ValueError):
            await repo.update_channel_flag(
                agent_id="agent-x", company_id="company-1",
                channel="bogus", enabled=True,
            )

    @pytest.mark.asyncio
    async def test_update_channel_flag_rejects_empty_company_id(self):
        """C.5: update fail-closed on missing company_id."""
        from app.domains.agent_studio.repositories.custom_agent_repository import (
            CustomAgentRepository,
        )
        db = MagicMock()
        repo = CustomAgentRepository(db)
        with pytest.raises(ValueError):
            await repo.update_channel_flag(
                agent_id="agent-x", company_id="",
                channel="voice", enabled=True,
            )


# ---------------------------------------------------------------------------
# Sensor: no inline select(CustomAgent) under EXEMPT in the 3 endpoints
# ---------------------------------------------------------------------------

class TestEndpointsUseRepository:
    """Pin that 3 endpoints no longer carry ADR-001-EXEMPT markers."""

    def test_agent_studio_voice_has_no_adr001_exempt(self):
        from pathlib import Path
        p = Path("app/api/v1/agent_studio_voice.py")
        src = p.read_text(encoding="utf-8")
        assert "ADR-001-EXEMPT" not in src, (
            "C.5: agent_studio_voice.py must use CustomAgentRepository instead "
            "of inline select(CustomAgent) under ADR-001-EXEMPT marker."
        )

    def test_agent_studio_whatsapp_has_no_adr001_exempt(self):
        from pathlib import Path
        p = Path("app/api/v1/agent_studio_whatsapp.py")
        src = p.read_text(encoding="utf-8")
        assert "ADR-001-EXEMPT" not in src, (
            "C.5: agent_studio_whatsapp.py must use CustomAgentRepository."
        )

    def test_agent_studio_channels_uses_repository(self):
        """C.5: agent_studio_channels.py adopts CustomAgentRepository."""
        from pathlib import Path
        p = Path("app/api/v1/agent_studio_channels.py")
        src = p.read_text(encoding="utf-8")
        assert "CustomAgentRepository" in src, (
            "C.5: agent_studio_channels.py must import CustomAgentRepository."
        )
