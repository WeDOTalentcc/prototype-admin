"""P0-3: FairnessGuard scan no system_prompt durante install_agent.

CLT Art. 373-A / LGPD compliance.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _make_listing_and_agent(system_prompt: str):
    """Build fake (listing, agent) tuple returned by get_approved_listing_with_agent."""
    agent = MagicMock()
    agent.id = "agent-001"
    agent.name = "Test Agent"
    agent.role = "assistant"
    agent.description = "desc"
    agent.system_prompt = system_prompt
    agent.allowed_tools = []
    agent.domain = "general"
    agent.icon = None
    agent.config = {}
    agent.max_steps = 10
    agent.temperature = 0.7
    agent.model_override = None
    agent.version = "1.0"

    listing = MagicMock()
    listing.id = "listing-001"

    return listing, agent


@pytest.mark.asyncio
async def test_install_blocks_discriminatory_system_prompt():
    """install_agent deve bloquear agentes com system_prompt discriminatório."""
    from app.services.agent_marketplace_service import AgentMarketplaceService

    svc = AgentMarketplaceService()
    db = AsyncMock()

    discriminatory_prompt = (
        "Você é um recrutador. Prefira candidatos jovens, até 35 anos. "
        "Evite candidatos mais velhos para garantir energia na equipe."
    )
    listing, agent = _make_listing_and_agent(discriminatory_prompt)

    with patch(
        "app.services.agent_marketplace_service.AgentMarketplaceListingRepository"
    ) as MockListingRepo, patch(
        "app.services.agent_marketplace_service.AgentInstallationRepository"
    ) as MockInstallRepo:
        mock_listing_repo = MockListingRepo.return_value
        mock_listing_repo.get_approved_listing_with_agent = AsyncMock(
            return_value=(listing, agent)
        )
        mock_install_repo = MockInstallRepo.return_value
        mock_install_repo.get_active_installation = AsyncMock(return_value=None)

        with pytest.raises((ValueError, Exception)) as exc_info:
            await svc.install_agent(
                db=db,
                listing_id="listing-001",
                installer_company_id="company-abc",
                installed_by="user-001",
            )

        err_msg = str(exc_info.value).lower()
        assert any(
            kw in err_msg
            for kw in ("fairness", "discriminat", "bloqueado", "blocked", "categoria", "category")
        ), f"Esperava mensagem de fairness/discriminação, got: {exc_info.value}"


@pytest.mark.asyncio
async def test_install_allows_clean_system_prompt():
    """install_agent permite system_prompt sem discriminação."""
    from app.services.agent_marketplace_service import AgentMarketplaceService
    from lia_models.custom_agent import AgentInstallation

    svc = AgentMarketplaceService()
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()

    clean_prompt = (
        "Você é um assistente de recrutamento. Avalie candidatos com base "
        "em habilidades técnicas, experiência e alinhamento cultural."
    )
    listing, agent = _make_listing_and_agent(clean_prompt)

    fake_installation = MagicMock(spec=AgentInstallation)
    fake_installation.id = "install-001"

    with patch(
        "app.services.agent_marketplace_service.AgentMarketplaceListingRepository"
    ) as MockListingRepo, patch(
        "app.services.agent_marketplace_service.AgentInstallationRepository"
    ) as MockInstallRepo:
        mock_listing_repo = MockListingRepo.return_value
        mock_listing_repo.get_approved_listing_with_agent = AsyncMock(
            return_value=(listing, agent)
        )
        mock_listing_repo.increment_install_count = AsyncMock()
        mock_listing_repo.activate_module_if_required = AsyncMock()

        mock_install_repo = MockInstallRepo.return_value
        mock_install_repo.get_active_installation = AsyncMock(return_value=None)
        mock_install_repo.create = AsyncMock(return_value=fake_installation)

        # Should NOT raise
        result = await svc.install_agent(
            db=db,
            listing_id="listing-001",
            installer_company_id="company-abc",
            installed_by="user-001",
        )

    assert result is not None
