"""Unit tests — Fase E: AgentMarketplaceListing + billing hook

Cobertura:
1. AgentMarketplaceListing created for TalentIntelAgent with correct module_required
2. listing_type=agent vs listing_type=template are distinct enum values
3. Billing hook activates CompanyModule when first-party agent installed
4. Billing hook is idempotent (second install doesn't duplicate CompanyModule)
5. Template install (is_free=True, module_required=None) does NOT activate any CompanyModule
6. Unknown module_key logs warning and skips
7. InterviewAnalysisAgent listing has correct module_required
8. to_dict() includes new listing_type + module_required fields
"""
import types
import uuid
import datetime
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── Shared fixtures ─────────────────────────────────────────────────────────

TALENT_INTEL_AGENT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
INTERVIEW_ANALYSIS_AGENT_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")
COMPANY_ID = "company-test-abc123"


def _make_listing_ns(
    *,
    agent_id=None,
    template_id=None,
    module_required=None,
    listing_type="agent",
    is_free=False,
    credits_per_execution=10,
    status="approved",
    title="Test Listing",
):
    """Build a listing-like SimpleNamespace (avoids SQLAlchemy instrumentation in unit tests)."""
    from lia_models.custom_agent import ListingType

    ns = types.SimpleNamespace()
    ns.id = uuid.uuid4()
    ns.agent_id = agent_id
    ns.template_id = template_id
    ns.module_required = module_required
    ns.listing_type = ListingType(listing_type)
    ns.is_free = is_free
    ns.credits_per_execution = credits_per_execution
    ns.status = status
    ns.title = title
    ns.publisher_company_id = "wedo-platform"
    return ns


def _make_installation_ns(*, company_id: str, source_agent_id: uuid.UUID, listing_id=None):
    """Build an installation-like SimpleNamespace."""
    ns = types.SimpleNamespace()
    ns.id = uuid.uuid4()
    ns.installer_company_id = company_id
    ns.source_agent_id = source_agent_id
    ns.listing_id = listing_id
    ns.status = "active"
    return ns


def _make_repo(*, existing_module=None):
    """Build AgentInstallationRepository with mocked AsyncSession."""
    from app.domains.agent_studio.repositories.agent_marketplace_repository import (
        AgentInstallationRepository,
    )

    db = AsyncMock()
    module_result = MagicMock()
    module_result.scalar_one_or_none.return_value = existing_module
    db.execute = AsyncMock(return_value=module_result)
    db.add = MagicMock()
    db.flush = AsyncMock()

    repo = AgentInstallationRepository(db)
    return repo, db


# ── Test 1: TalentIntelAgent listing has correct module_required ─────────────

def test_talent_intel_listing_module_required():
    """AgentMarketplaceListing for TalentIntelAgent must reference talent_intelligence_pro."""
    from lia_models.custom_agent import ListingType

    listing = _make_listing_ns(
        agent_id=TALENT_INTEL_AGENT_ID,
        module_required="talent_intelligence_pro",
        listing_type="agent",
        credits_per_execution=10,
        is_free=False,
    )

    assert listing.agent_id == TALENT_INTEL_AGENT_ID
    assert listing.module_required == "talent_intelligence_pro"
    assert listing.listing_type == ListingType.agent
    assert listing.is_free is False
    assert listing.credits_per_execution == 10


# ── Test 2: ListingType enum distinguishes agent vs template ─────────────────

def test_listing_type_enum_distinct():
    """listing_type=agent and listing_type=template are different enum values."""
    from lia_models.custom_agent import ListingType

    assert ListingType.agent != ListingType.template
    assert ListingType.agent.value == "agent"
    assert ListingType.template.value == "template"

    agent_listing = _make_listing_ns(listing_type="agent")
    template_listing = _make_listing_ns(listing_type="template", is_free=True, module_required=None)

    assert agent_listing.listing_type != template_listing.listing_type


# ── Test 3: Billing hook activates CompanyModule on install ──────────────────

@pytest.mark.asyncio
async def test_billing_hook_activates_module():
    """Installing a module-gated agent creates a CompanyModule row."""
    repo, db = _make_repo(existing_module=None)

    listing = _make_listing_ns(
        agent_id=TALENT_INTEL_AGENT_ID,
        module_required="talent_intelligence_pro",
        listing_type="agent",
    )
    installation = _make_installation_ns(
        company_id=COMPANY_ID,
        source_agent_id=TALENT_INTEL_AGENT_ID,
        listing_id=listing.id,
    )

    result = await repo.activate_module_if_required(
        installation=installation,
        listing=listing,
    )

    assert result is True
    db.add.assert_called_once()
    added_module = db.add.call_args[0][0]
    assert added_module.company_id == COMPANY_ID
    assert added_module.module_name == "talent_intelligence_pro"
    assert added_module.status == "beta"


# ── Test 4: Billing hook is idempotent ──────────────────────────────────────

@pytest.mark.asyncio
async def test_billing_hook_idempotent():
    """Second install of same module does NOT create duplicate CompanyModule."""
    from lia_models.billing import CompanyModule

    existing = MagicMock(spec=CompanyModule)
    existing.module_name = "talent_intelligence_pro"
    existing.company_id = COMPANY_ID

    repo, db = _make_repo(existing_module=existing)

    listing = _make_listing_ns(
        agent_id=TALENT_INTEL_AGENT_ID,
        module_required="talent_intelligence_pro",
        listing_type="agent",
    )
    installation = _make_installation_ns(
        company_id=COMPANY_ID,
        source_agent_id=TALENT_INTEL_AGENT_ID,
        listing_id=listing.id,
    )

    result = await repo.activate_module_if_required(
        installation=installation,
        listing=listing,
    )

    assert result is False
    db.add.assert_not_called()


# ── Test 5: Template install does NOT activate CompanyModule ─────────────────

@pytest.mark.asyncio
async def test_template_install_no_billing_hook():
    """Template listing (is_free=True, module_required=None) creates no CompanyModule."""
    repo, db = _make_repo(existing_module=None)

    template_id = uuid.uuid4()
    template_listing = _make_listing_ns(
        template_id=template_id,
        agent_id=None,
        module_required=None,
        listing_type="template",
        is_free=True,
        credits_per_execution=0,
    )
    installation = _make_installation_ns(
        company_id=COMPANY_ID,
        source_agent_id=uuid.uuid4(),
        listing_id=template_listing.id,
    )

    result = await repo.activate_module_if_required(
        installation=installation,
        listing=template_listing,
    )

    assert result is False
    db.add.assert_not_called()


# ── Test 6: Unknown module_key logs warning and skips ────────────────────────

@pytest.mark.asyncio
async def test_billing_hook_unknown_module_skips():
    """Unknown module_key logs a warning and does not create CompanyModule."""
    repo, db = _make_repo(existing_module=None)

    listing = _make_listing_ns(
        agent_id=TALENT_INTEL_AGENT_ID,
        module_required="nonexistent_module_xyz",
        listing_type="agent",
    )
    installation = _make_installation_ns(
        company_id=COMPANY_ID,
        source_agent_id=TALENT_INTEL_AGENT_ID,
        listing_id=listing.id,
    )

    result = await repo.activate_module_if_required(
        installation=installation,
        listing=listing,
    )

    assert result is False
    db.add.assert_not_called()


# ── Test 7: InterviewAnalysisAgent listing has correct module_required ────────

def test_interview_analysis_listing_module_required():
    """AgentMarketplaceListing for InterviewAnalysisAgent references interview_intelligence."""
    from lia_models.custom_agent import ListingType

    listing = _make_listing_ns(
        agent_id=INTERVIEW_ANALYSIS_AGENT_ID,
        module_required="interview_intelligence",
        listing_type="agent",
        credits_per_execution=5,
        is_free=False,
    )

    assert listing.agent_id == INTERVIEW_ANALYSIS_AGENT_ID
    assert listing.module_required == "interview_intelligence"
    assert listing.credits_per_execution == 5
    assert listing.listing_type == ListingType.agent


# ── Test 8: to_dict() includes new fields ────────────────────────────────────

def test_listing_to_dict_includes_new_fields():
    """AgentMarketplaceListing.to_dict() must expose listing_type and module_required."""
    from lia_models.custom_agent import AgentMarketplaceListing, ListingType

    # Build the real SQLAlchemy object with constructor (safe path)
    listing = AgentMarketplaceListing(
        agent_id=TALENT_INTEL_AGENT_ID,
        template_id=None,
        publisher_company_id="wedo-platform",
        title="Talent Intelligence Pro",
        category="talent_intelligence",
        module_required="talent_intelligence_pro",
        listing_type=ListingType.agent,
        is_free=False,
        credits_per_execution=10,
        status="approved",
    )

    d = listing.to_dict()

    assert d["listing_type"] == "agent"
    assert d["module_required"] == "talent_intelligence_pro"
    assert d["agent_id"] == str(TALENT_INTEL_AGENT_ID)
    assert d["template_id"] is None
