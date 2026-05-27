"""Agent marketplace repositories — canonical ADR-001 abstractions.

Wave C1.2 (2026-05-27). Two repositories backing
`agent_marketplace_service.py`:

  - AgentMarketplaceListingRepository — handles listing CRUD, public listing
    search, review workflow, install_count bump.
  - AgentInstallationRepository — handles installer-side install records,
    list/uninstall/billing aggregation.

Both fail-closed on `company_id` for any operation that scopes to a tenant
(LGPD Art. 6 II — multi-tenancy invariant). Listing-side cross-tenant reads
(public marketplace listing) explicitly do NOT take `company_id` — those are
intentionally public (status = APPROVED).

Replaces the 18 inline `select(...)` calls in
`app/services/agent_marketplace_service.py` (Wave C1.3 service refactor).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.custom_agent import (
    AgentInstallation,
    AgentMarketplaceListing,
    CustomAgent,
    MarketplaceListingStatus,
)


def _require_company_id(company_id: Any) -> None:
    """Fail-closed guard — multi-tenancy invariant."""
    if not isinstance(company_id, str) or not company_id.strip():
        raise ValueError(
            "AgentMarketplace*Repository: company_id is required (multi-tenancy "
            "fail-closed)."
        )


def _to_uuid(value: str) -> uuid.UUID | None:
    """Parse a UUID, returning None for invalid input (caller decides on 404)."""
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError, TypeError):
        return None


# ---------------- AgentMarketplaceListingRepository ----------------


class AgentMarketplaceListingRepository:
    """Canonical reads/writes for `agent_marketplace_listings`."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, listing: AgentMarketplaceListing) -> AgentMarketplaceListing:
        """Persist a new listing instance. Caller commits."""
        self._db.add(listing)
        await self._db.flush()
        await self._db.refresh(listing)
        return listing

    async def get_by_id(
        self, *, listing_id: str
    ) -> AgentMarketplaceListing | None:
        """Load a listing by id (no tenant filter — listings are cross-tenant)."""
        listing_uuid = _to_uuid(listing_id)
        if listing_uuid is None:
            return None
        stmt = select(AgentMarketplaceListing).where(
            AgentMarketplaceListing.id == listing_uuid
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_approved_listing_with_agent(
        self, *, listing_id: str
    ) -> tuple[AgentMarketplaceListing, CustomAgent] | None:
        """Load an approved listing + its source agent (for install flow)."""
        listing_uuid = _to_uuid(listing_id)
        if listing_uuid is None:
            return None
        stmt = (
            select(AgentMarketplaceListing, CustomAgent)
            .join(CustomAgent, AgentMarketplaceListing.agent_id == CustomAgent.id)
            .where(
                and_(
                    AgentMarketplaceListing.id == listing_uuid,
                    AgentMarketplaceListing.status
                    == MarketplaceListingStatus.APPROVED.value,
                )
            )
        )
        result = await self._db.execute(stmt)
        row = result.one_or_none()
        if row is None:
            return None
        return row[0], row[1]

    async def get_by_agent_id(
        self, *, agent_id: uuid.UUID | str
    ) -> AgentMarketplaceListing | None:
        """Check whether an agent already has a marketplace listing."""
        stmt = select(AgentMarketplaceListing).where(
            AgentMarketplaceListing.agent_id == agent_id
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_public(
        self,
        *,
        category: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[tuple[AgentMarketplaceListing, CustomAgent]], int]:
        """Public catalog: listings with status=APPROVED + their source agent.

        Cross-tenant by design — marketplace is global.
        """
        conditions = [
            AgentMarketplaceListing.status == MarketplaceListingStatus.APPROVED.value
        ]
        if category:
            conditions.append(AgentMarketplaceListing.category == category)
        if search:
            search_filter = or_(
                AgentMarketplaceListing.title.ilike(f"%{search}%"),
                AgentMarketplaceListing.short_description.ilike(f"%{search}%"),
            )
            conditions.append(search_filter)

        count_stmt = select(func.count(AgentMarketplaceListing.id)).where(
            and_(*conditions)
        )
        total = (await self._db.execute(count_stmt)).scalar() or 0

        stmt = (
            select(AgentMarketplaceListing, CustomAgent)
            .join(CustomAgent, AgentMarketplaceListing.agent_id == CustomAgent.id)
            .where(and_(*conditions))
            .order_by(AgentMarketplaceListing.install_count.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._db.execute(stmt)
        rows = [(row[0], row[1]) for row in result.all()]
        return rows, int(total)

    async def list_pending_reviews(
        self, *, limit: int = 50, offset: int = 0
    ) -> tuple[list[tuple[AgentMarketplaceListing, CustomAgent]], int]:
        """Admin queue: listings awaiting review."""
        conditions = [
            AgentMarketplaceListing.status
            == MarketplaceListingStatus.PENDING_REVIEW.value
        ]

        count_stmt = select(func.count(AgentMarketplaceListing.id)).where(
            and_(*conditions)
        )
        total = (await self._db.execute(count_stmt)).scalar() or 0

        stmt = (
            select(AgentMarketplaceListing, CustomAgent)
            .join(CustomAgent, AgentMarketplaceListing.agent_id == CustomAgent.id)
            .where(and_(*conditions))
            .order_by(AgentMarketplaceListing.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._db.execute(stmt)
        rows = [(row[0], row[1]) for row in result.all()]
        return rows, int(total)

    async def update_review(
        self,
        *,
        listing_id: str,
        reviewer_id: str,
        action: str,
        review_notes: str | None = None,
    ) -> AgentMarketplaceListing | None:
        """Apply approve/reject review decision to a listing."""
        listing = await self.get_by_id(listing_id=listing_id)
        if listing is None:
            return None

        if action == "approve":
            listing.status = MarketplaceListingStatus.APPROVED.value
            listing.published_at = datetime.utcnow()
        elif action == "reject":
            listing.status = MarketplaceListingStatus.REJECTED.value

        listing.reviewed_by = reviewer_id
        listing.reviewed_at = datetime.utcnow()
        listing.review_notes = review_notes
        await self._db.flush()
        await self._db.refresh(listing)
        return listing

    async def increment_install_count(
        self, *, listing: AgentMarketplaceListing
    ) -> None:
        """Bump install_count on a listing (already loaded)."""
        listing.install_count = (listing.install_count or 0) + 1
        await self._db.flush()

    async def count_by_publisher(self, *, company_id: str) -> int:
        """Count listings published by a tenant."""
        _require_company_id(company_id)
        stmt = select(func.count(AgentMarketplaceListing.id)).where(
            AgentMarketplaceListing.publisher_company_id == company_id
        )
        result = await self._db.execute(stmt)
        return int(result.scalar() or 0)


# ---------------- AgentInstallationRepository ----------------


class AgentInstallationRepository:
    """Canonical reads/writes for `agent_installations`."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, installation: AgentInstallation) -> AgentInstallation:
        """Persist a new installation. Caller commits."""
        self._db.add(installation)
        await self._db.flush()
        await self._db.refresh(installation)
        return installation

    async def get_active_installation(
        self,
        *,
        source_agent_id: uuid.UUID | str,
        company_id: str,
    ) -> AgentInstallation | None:
        """Find an active installation of `source_agent_id` for a tenant."""
        _require_company_id(company_id)
        stmt = select(AgentInstallation).where(
            and_(
                AgentInstallation.source_agent_id == source_agent_id,
                AgentInstallation.installer_company_id == company_id,
                AgentInstallation.status == "active",
            )
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(
        self,
        *,
        installation_id: str,
        company_id: str,
    ) -> AgentInstallation | None:
        """Load an installation row scoped to the installer tenant."""
        _require_company_id(company_id)
        inst_uuid = _to_uuid(installation_id)
        if inst_uuid is None:
            return None
        stmt = select(AgentInstallation).where(
            and_(
                AgentInstallation.id == inst_uuid,
                AgentInstallation.installer_company_id == company_id,
                AgentInstallation.status == "active",
            )
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_installed_agent_by_id(
        self, *, installed_agent_id: uuid.UUID | str
    ) -> CustomAgent | None:
        """Load the CustomAgent row created during install (uninstall path)."""
        stmt = select(CustomAgent).where(CustomAgent.id == installed_agent_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_company(
        self,
        *,
        company_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[tuple[AgentInstallation, CustomAgent]], int]:
        """List active installations for a tenant + their source agents."""
        _require_company_id(company_id)
        conditions = [
            AgentInstallation.installer_company_id == company_id,
            AgentInstallation.status == "active",
        ]

        count_stmt = select(func.count(AgentInstallation.id)).where(
            and_(*conditions)
        )
        total = (await self._db.execute(count_stmt)).scalar() or 0

        stmt = (
            select(AgentInstallation, CustomAgent)
            .join(CustomAgent, AgentInstallation.source_agent_id == CustomAgent.id)
            .where(and_(*conditions))
            .order_by(AgentInstallation.installed_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._db.execute(stmt)
        rows = [(row[0], row[1]) for row in result.all()]
        return rows, int(total)

    async def list_billing_summary(
        self, *, company_id: str
    ) -> list[tuple[AgentInstallation, CustomAgent]]:
        """List active installs + source agents for billing aggregation."""
        _require_company_id(company_id)
        stmt = (
            select(AgentInstallation, CustomAgent)
            .join(CustomAgent, AgentInstallation.source_agent_id == CustomAgent.id)
            .where(
                and_(
                    AgentInstallation.installer_company_id == company_id,
                    AgentInstallation.status == "active",
                )
            )
        )
        result = await self._db.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def get_active_for_installed_agent(
        self,
        *,
        installed_agent_id: uuid.UUID | str,
        company_id: str,
    ) -> AgentInstallation | None:
        """Find the active installation that produced `installed_agent_id`."""
        _require_company_id(company_id)
        stmt = select(AgentInstallation).where(
            and_(
                AgentInstallation.installed_agent_id == installed_agent_id,
                AgentInstallation.installer_company_id == company_id,
                AgentInstallation.status == "active",
            )
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_uninstalled(
        self, *, installation: AgentInstallation
    ) -> None:
        """Soft-uninstall an installation (already loaded + tenant-scoped)."""
        installation.status = "uninstalled"
        installation.uninstalled_at = datetime.utcnow()
        await self._db.flush()

    async def bump_execution_counters(
        self,
        *,
        installation: AgentInstallation,
        credits_consumed: int,
    ) -> None:
        """Increment per-install execution + credits counters."""
        installation.total_executions = (installation.total_executions or 0) + 1
        installation.total_credits_consumed = (
            installation.total_credits_consumed or 0
        ) + credits_consumed
        await self._db.flush()

    async def count_by_company(self, *, company_id: str) -> int:
        """Count active installations for a tenant."""
        _require_company_id(company_id)
        stmt = select(func.count(AgentInstallation.id)).where(
            and_(
                AgentInstallation.installer_company_id == company_id,
                AgentInstallation.status == "active",
            )
        )
        result = await self._db.execute(stmt)
        return int(result.scalar() or 0)
