"""P0-4: reviewer nao pode ser do mesmo tenant que criou o agente.

Anti self-review no marketplace - previne conflito de interesse.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock


def _make_listing(publisher_company_id: str):
    listing = MagicMock()
    listing.id = "listing-001"
    listing.publisher_company_id = publisher_company_id
    listing.status = "approved"
    listing.reviewed_by = None
    listing.reviewed_at = None
    listing.review_notes = None
    listing.to_dict = MagicMock(return_value={})
    return listing


@pytest.mark.asyncio
async def test_self_review_blocked():
    """reviewer do mesmo tenant que publicou o agente deve ser bloqueado."""
    from app.services.agent_marketplace_service import AgentMarketplaceService

    svc = AgentMarketplaceService()
    db = AsyncMock()

    publisher_company = "company-abc"
    listing = _make_listing(publisher_company_id=publisher_company)

    with pytest.MonkeyPatch.context() as mp:
        from app.domains.agent_studio.repositories import agent_marketplace_repository as repo_mod

        async def fake_get_by_id(*, listing_id):
            return listing

        async def fake_update_review(**kwargs):
            return listing

        mock_repo_instance = MagicMock()
        mock_repo_instance.get_by_id = fake_get_by_id
        mock_repo_instance.update_review = fake_update_review

        import app.services.agent_marketplace_service as svc_mod
        original_cls = svc_mod.AgentMarketplaceListingRepository
        svc_mod.AgentMarketplaceListingRepository = lambda db: mock_repo_instance

        try:
            with pytest.raises((ValueError, Exception)) as exc_info:
                await svc.review_listing(
                    db=db,
                    listing_id="listing-001",
                    reviewer_id="user-admin",
                    action="approve",
                    reviewer_company_id=publisher_company,  # mesmo tenant!
                )
        finally:
            svc_mod.AgentMarketplaceListingRepository = original_cls

    err_msg = str(exc_info.value).lower()
    assert any(
        kw in err_msg
        for kw in ("auto-review", "self-review", "mesmo tenant", "bloqueado", "blocked", "conflict")
    ), f"Esperava mensagem de self-review bloqueado, got: {exc_info.value}"


@pytest.mark.asyncio
async def test_different_tenant_review_allowed():
    """reviewer de tenant diferente pode aprovar sem bloqueio."""
    from app.services.agent_marketplace_service import AgentMarketplaceService

    svc = AgentMarketplaceService()
    db = AsyncMock()

    publisher_company = "company-publisher"
    reviewer_company = "wedotalent-admin"  # diferente
    listing = _make_listing(publisher_company_id=publisher_company)

    import app.services.agent_marketplace_service as svc_mod
    original_cls = svc_mod.AgentMarketplaceListingRepository

    async def fake_get_by_id(*, listing_id):
        return listing

    async def fake_update_review(**kwargs):
        return listing

    mock_repo_instance = MagicMock()
    mock_repo_instance.get_by_id = fake_get_by_id
    mock_repo_instance.update_review = fake_update_review

    svc_mod.AgentMarketplaceListingRepository = lambda db: mock_repo_instance
    try:
        result = await svc.review_listing(
            db=db,
            listing_id="listing-001",
            reviewer_id="user-wedotalent",
            action="approve",
            reviewer_company_id=reviewer_company,
        )
    finally:
        svc_mod.AgentMarketplaceListingRepository = original_cls

    assert result is not None


@pytest.mark.asyncio
async def test_review_without_reviewer_company_id_still_works():
    """Chamada sem reviewer_company_id (backward compat) nao bloqueia."""
    from app.services.agent_marketplace_service import AgentMarketplaceService

    svc = AgentMarketplaceService()
    db = AsyncMock()

    publisher_company = "company-abc"
    listing = _make_listing(publisher_company_id=publisher_company)

    import app.services.agent_marketplace_service as svc_mod
    original_cls = svc_mod.AgentMarketplaceListingRepository

    async def fake_update_review(**kwargs):
        return listing

    mock_repo_instance = MagicMock()
    mock_repo_instance.update_review = fake_update_review

    svc_mod.AgentMarketplaceListingRepository = lambda db: mock_repo_instance
    try:
        result = await svc.review_listing(
            db=db,
            listing_id="listing-001",
            reviewer_id="user-admin",
            action="approve",
            # reviewer_company_id NOT passed - backward compat
        )
    finally:
        svc_mod.AgentMarketplaceListingRepository = original_cls

    assert result is not None
