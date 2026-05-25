import logging
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.custom_agent import (
    AgentInstallation,
    AgentMarketplaceListing,
    CustomAgent,
    CustomAgentStatus,
    MarketplaceListingStatus,
)

logger = logging.getLogger(__name__)


class AgentMarketplaceService:

    async def create_agent(
        self,
        db: AsyncSession,
        company_id: str,
        created_by: str,
        data: dict[str, Any],
    ) -> CustomAgent:
        agent = CustomAgent(
            company_id=company_id,
            created_by=created_by,
            name=data["name"],
            role=data["role"],
            description=data.get("description"),
            system_prompt=data["system_prompt"],
            allowed_tools=data.get("allowed_tools", []),
            domain=data.get("domain", "general"),
            icon=data.get("icon", "🤖"),
            config=data.get("config", {}),
            max_steps=data.get("max_steps", 8),
            temperature=data.get("temperature", 0.7),
            model_override=data.get("model_override"),
            status=CustomAgentStatus.DRAFT.value,
        )
        db.add(agent)
        await db.flush()
        await db.refresh(agent)
        logger.info("[AgentMarketplace] Created agent=%s company=%s", agent.id, company_id)
        return agent

    async def update_agent(
        self,
        db: AsyncSession,
        agent_id: str,
        company_id: str,
        data: dict[str, Any],
    ) -> Optional[CustomAgent]:
        agent = await self._get_agent(db, agent_id, company_id)
        if not agent:
            return None

        for field, value in data.items():
            if value is not None and hasattr(agent, field):
                setattr(agent, field, value)

        agent.updated_at = datetime.utcnow()
        agent.version = (agent.version or 1) + 1
        await db.flush()
        await db.refresh(agent)
        return agent

    async def get_agent(
        self,
        db: AsyncSession,
        agent_id: str,
        company_id: str,
    ) -> Optional[CustomAgent]:
        return await self._get_agent(db, agent_id, company_id)

    async def list_agents(
        self,
        db: AsyncSession,
        company_id: str,
        status: Optional[str] = None,
        domain: Optional[str] = None,
        category: Optional[str] = None,  # Sprint 7A category filter
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[CustomAgent], int]:
        conditions = [CustomAgent.company_id == company_id]
        if status:
            conditions.append(CustomAgent.status == status)
        if domain:
            conditions.append(CustomAgent.domain == domain)
        if category:  # Sprint 7A category filter
            conditions.append(CustomAgent.category == category)

        count_q = select(func.count(CustomAgent.id)).where(and_(*conditions))
        total = (await db.execute(count_q)).scalar() or 0

        q = (
            select(CustomAgent)
            .where(and_(*conditions))
            .order_by(CustomAgent.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(q)
        return list(result.scalars().all()), total

    async def delete_agent(
        self,
        db: AsyncSession,
        agent_id: str,
        company_id: str,
    ) -> bool:
        agent = await self._get_agent(db, agent_id, company_id)
        if not agent:
            return False
        await db.delete(agent)
        await db.flush()
        return True

    async def publish_to_marketplace(
        self,
        db: AsyncSession,
        agent_id: str,
        company_id: str,
        data: dict[str, Any],
    ) -> Optional[AgentMarketplaceListing]:
        agent = await self._get_agent(db, agent_id, company_id)
        if not agent:
            return None

        if agent.status != CustomAgentStatus.ACTIVE.value:
            raise ValueError("Agent must be active before publishing to marketplace")

        existing = await db.execute(
            select(AgentMarketplaceListing).where(
                AgentMarketplaceListing.agent_id == agent.id
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Agent already has a marketplace listing")

        listing = AgentMarketplaceListing(
            agent_id=agent.id,
            publisher_company_id=company_id,
            title=data["title"],
            short_description=data.get("short_description"),
            long_description=data.get("long_description"),
            category=data.get("category", "general"),
            tags=data.get("tags", []),
            icon_url=data.get("icon_url"),
            credits_per_execution=data.get("credits_per_execution", 1),
            is_free=data.get("is_free", False),
            status=MarketplaceListingStatus.PENDING_REVIEW.value,
        )
        db.add(listing)
        agent.is_marketplace_published = True
        await db.flush()
        await db.refresh(listing)
        logger.info("[AgentMarketplace] Published listing=%s agent=%s", listing.id, agent_id)
        return listing

    async def list_marketplace(
        self,
        db: AsyncSession,
        category: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
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

        count_q = select(func.count(AgentMarketplaceListing.id)).where(and_(*conditions))
        total = (await db.execute(count_q)).scalar() or 0

        q = (
            select(AgentMarketplaceListing, CustomAgent)
            .join(CustomAgent, AgentMarketplaceListing.agent_id == CustomAgent.id)
            .where(and_(*conditions))
            .order_by(AgentMarketplaceListing.install_count.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(q)
        rows = result.all()

        listings = []
        for listing, agent in rows:
            data = listing.to_dict()
            data["agent_name"] = agent.name
            data["agent_role"] = agent.role
            data["agent_domain"] = agent.domain
            listings.append(data)

        return listings, total

    async def review_listing(
        self,
        db: AsyncSession,
        listing_id: str,
        reviewer_id: str,
        action: str,
        review_notes: Optional[str] = None,
    ) -> Optional[AgentMarketplaceListing]:
        try:
            listing_uuid = uuid.UUID(listing_id)
        except (ValueError, AttributeError):
            return None
        result = await db.execute(
            select(AgentMarketplaceListing).where(
                AgentMarketplaceListing.id == listing_uuid
            )
        )
        listing = result.scalar_one_or_none()
        if not listing:
            return None

        if action == "approve":
            listing.status = MarketplaceListingStatus.APPROVED.value
            listing.published_at = datetime.utcnow()
        elif action == "reject":
            listing.status = MarketplaceListingStatus.REJECTED.value

        listing.reviewed_by = reviewer_id
        listing.reviewed_at = datetime.utcnow()
        listing.review_notes = review_notes
        await db.flush()
        await db.refresh(listing)
        return listing

    async def install_agent(
        self,
        db: AsyncSession,
        listing_id: str,
        installer_company_id: str,
        installed_by: str,
    ) -> AgentInstallation:
        try:
            listing_uuid = uuid.UUID(listing_id)
        except (ValueError, AttributeError):
            raise ValueError("Invalid listing ID format")
        result = await db.execute(
            select(AgentMarketplaceListing, CustomAgent)
            .join(CustomAgent, AgentMarketplaceListing.agent_id == CustomAgent.id)
            .where(
                and_(
                    AgentMarketplaceListing.id == listing_uuid,
                    AgentMarketplaceListing.status == MarketplaceListingStatus.APPROVED.value,
                )
            )
        )
        row = result.one_or_none()
        if not row:
            raise ValueError("Listing not found or not approved")

        listing, source_agent = row

        existing = await db.execute(
            select(AgentInstallation).where(
                and_(
                    AgentInstallation.source_agent_id == source_agent.id,
                    AgentInstallation.installer_company_id == installer_company_id,
                    AgentInstallation.status == "active",
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Agent already installed for this company")

        installed_agent = CustomAgent(
            company_id=installer_company_id,
            created_by=installed_by,
            name=f"{source_agent.name} (Marketplace)",
            role=source_agent.role,
            description=source_agent.description,
            system_prompt=source_agent.system_prompt,
            allowed_tools=source_agent.allowed_tools,
            domain=source_agent.domain,
            icon=source_agent.icon,
            config=source_agent.config,
            max_steps=source_agent.max_steps,
            temperature=source_agent.temperature,
            model_override=source_agent.model_override,
            status=CustomAgentStatus.ACTIVE.value,
        )
        db.add(installed_agent)
        await db.flush()
        await db.refresh(installed_agent)

        installation = AgentInstallation(
            source_agent_id=source_agent.id,
            listing_id=listing.id,
            installer_company_id=installer_company_id,
            installed_agent_id=installed_agent.id,
            installed_by=installed_by,
            version_at_install=source_agent.version,
        )
        db.add(installation)

        listing.install_count = (listing.install_count or 0) + 1

        await db.flush()
        await db.refresh(installation)
        logger.info(
            "[AgentMarketplace] Installed agent=%s from listing=%s company=%s",
            source_agent.id,
            listing_id,
            installer_company_id,
        )
        return installation

    async def uninstall_agent(
        self,
        db: AsyncSession,
        installation_id: str,
        company_id: str,
    ) -> bool:
        try:
            inst_uuid = uuid.UUID(installation_id)
        except (ValueError, AttributeError):
            return False
        result = await db.execute(
            select(AgentInstallation).where(
                and_(
                    AgentInstallation.id == inst_uuid,
                    AgentInstallation.installer_company_id == company_id,
                    AgentInstallation.status == "active",
                )
            )
        )
        installation = result.scalar_one_or_none()
        if not installation:
            return False

        installation.status = "uninstalled"
        installation.uninstalled_at = datetime.utcnow()

        if installation.installed_agent_id:
            agent_result = await db.execute(
                select(CustomAgent).where(CustomAgent.id == installation.installed_agent_id)
            )
            installed_agent = agent_result.scalar_one_or_none()
            if installed_agent:
                installed_agent.status = CustomAgentStatus.ARCHIVED.value

        await db.flush()
        return True

    async def list_installations(
        self,
        db: AsyncSession,
        company_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        conditions = [
            AgentInstallation.installer_company_id == company_id,
            AgentInstallation.status == "active",
        ]

        count_q = select(func.count(AgentInstallation.id)).where(and_(*conditions))
        total = (await db.execute(count_q)).scalar() or 0

        q = (
            select(AgentInstallation, CustomAgent)
            .join(CustomAgent, AgentInstallation.source_agent_id == CustomAgent.id)
            .where(and_(*conditions))
            .order_by(AgentInstallation.installed_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(q)
        rows = result.all()

        installations = []
        for inst, agent in rows:
            data = inst.to_dict()
            data["agent_name"] = agent.name
            installations.append(data)

        return installations, total

    async def record_execution(
        self,
        db: AsyncSession,
        agent_id: str,
        company_id: str,
        credits_consumed: int = 0,
        tokens_input: int = 0,
        tokens_output: int = 0,
        pricing_tier: str = "pro",
    ) -> None:
        """Wave 4 W4-4 audit 2026-05-22: credits_consumed agora suporta calculo
        real via tokens × price quando tokens > 0. Backward-compat: credits_consumed
        explicito ainda funciona (passado por agentes free/listing constants).

        Args:
            credits_consumed: se >0, usa esse valor diretamente (override).
            tokens_input + tokens_output: se ambos >0 E credits_consumed=0,
                                          computa via compute_credits canonical.
            pricing_tier: free/pro/enterprise. Default 'pro'.
        """
        # Wave 4 W4-4: compute credits from tokens if not explicitly provided
        if credits_consumed == 0 and (tokens_input > 0 or tokens_output > 0):
            try:
                from app.services.agent_pricing import compute_credits
                credits_consumed = compute_credits(
                    tokens_input=tokens_input,
                    tokens_output=tokens_output,
                    tier=pricing_tier,
                )
            except Exception as e:
                logger.warning("[agent_pricing] compute_credits failed: %s", e)
                credits_consumed = 0
        try:
            agent_uuid = uuid.UUID(agent_id)
        except (ValueError, AttributeError):
            return

        result = await db.execute(
            select(CustomAgent).where(CustomAgent.id == agent_uuid)
        )
        agent = result.scalar_one_or_none()
        if agent:
            agent.total_executions = (agent.total_executions or 0) + 1
            agent.last_executed_at = datetime.utcnow()

        if credits_consumed > 0:
            inst_result = await db.execute(
                select(AgentInstallation).where(
                    and_(
                        AgentInstallation.installed_agent_id == agent_uuid,
                        AgentInstallation.installer_company_id == company_id,
                        AgentInstallation.status == "active",
                    )
                )
            )
            installation = inst_result.scalar_one_or_none()
            if installation:
                installation.total_executions = (installation.total_executions or 0) + 1
                installation.total_credits_consumed = (
                    installation.total_credits_consumed or 0
                ) + credits_consumed

        await db.flush()

    async def get_billing_summary(
        self,
        db: AsyncSession,
        company_id: str,
    ) -> list[dict[str, Any]]:
        q = (
            select(AgentInstallation, CustomAgent)
            .join(CustomAgent, AgentInstallation.source_agent_id == CustomAgent.id)
            .where(
                and_(
                    AgentInstallation.installer_company_id == company_id,
                    AgentInstallation.status == "active",
                )
            )
        )
        result = await db.execute(q)
        rows = result.all()

        summaries = []
        for inst, agent in rows:
            summaries.append({
                "agent_id": str(agent.id),
                "agent_name": agent.name,
                "total_executions": inst.total_executions or 0,
                "total_credits_consumed": inst.total_credits_consumed or 0,
            })
        return summaries

    async def get_pending_reviews(
        self,
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        conditions = [
            AgentMarketplaceListing.status == MarketplaceListingStatus.PENDING_REVIEW.value
        ]

        count_q = select(func.count(AgentMarketplaceListing.id)).where(and_(*conditions))
        total = (await db.execute(count_q)).scalar() or 0

        q = (
            select(AgentMarketplaceListing, CustomAgent)
            .join(CustomAgent, AgentMarketplaceListing.agent_id == CustomAgent.id)
            .where(and_(*conditions))
            .order_by(AgentMarketplaceListing.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(q)
        rows = result.all()

        listings = []
        for listing, agent in rows:
            data = listing.to_dict()
            data["agent_name"] = agent.name
            data["agent_role"] = agent.role
            data["agent_domain"] = agent.domain
            data["system_prompt_preview"] = (agent.system_prompt or "")[:200]
            listings.append(data)

        return listings, total

    async def _get_agent(
        self,
        db: AsyncSession,
        agent_id: str,
        company_id: str,
    ) -> Optional[CustomAgent]:
        try:
            agent_uuid = uuid.UUID(agent_id)
        except (ValueError, AttributeError):
            return None
        result = await db.execute(
            select(CustomAgent).where(
                and_(
                    CustomAgent.id == agent_uuid,
                    CustomAgent.company_id == company_id,
                )
            )
        )
        return result.scalar_one_or_none()


agent_marketplace_service = AgentMarketplaceService()
