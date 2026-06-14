"""Agent Marketplace orchestration service.

Wave C1.3 (2026-05-27): raw select calls migrated to canonical repositories:
  - CustomAgentRepository (agent lookup)
  - AgentMarketplaceListingRepository (listings)
  - AgentInstallationRepository (installs + billing)
"""
import logging
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.custom_agent import (
    AgentInstallation,
    AgentMarketplaceListing,
    AgentType,
    CustomAgent,
    CustomAgentStatus,
    MarketplaceListingStatus,
)
from lia_models.pool_agent_assignment import PoolAgentAssignment

from app.domains.agent_studio.repositories.agent_marketplace_repository import (
    AgentInstallationRepository,
    AgentMarketplaceListingRepository,
)

from app.shared.compliance.fairness_guard import FairnessGuard

_fairness_guard = FairnessGuard()

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
        talent_pool_id: Optional[str] = None,  # Sprint 7B-3b Part 2 v2
        job_id: Optional[str] = None,  # Sprint 7B-3b Part 2 v2
        agent_type: Optional[str] = None,  # first_party | custom (None = tenant-scoped default)
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[CustomAgent], int]:
        # ADR-001-EXEMPT: dynamic conditional builder with JSONB indexing +
        # talent_pool JOIN. Canonical CustomAgentRepository does not yet cover
        # the combined filter matrix used by this endpoint (Sprint 7A+7B-3b).
        # Move to repo when an `advanced_search` method is added.
        if agent_type == "first_party":
            # TENANT-FREE: first_party agents sao globais (company_id=None e
            # valido por design — ver AgentType docstring). Nao filtrar por
            # company_id aqui, senao os agentes WeDo globais nunca aparecem.
            conditions = [CustomAgent.agent_type == AgentType.first_party]
        else:
            conditions = [CustomAgent.company_id == company_id]
            # tenant listing exclui first_party (esses vivem no marketplace)
            conditions.append(CustomAgent.agent_type != AgentType.first_party)
        if status:
            conditions.append(CustomAgent.status == status)
        if domain:
            conditions.append(CustomAgent.domain == domain)
        if category:  # Sprint 7A category filter
            conditions.append(CustomAgent.category == category)

        # Sprint 7B-3b Part 2 v2: filter por talent_pool via JOIN canonical M2M
        # PoolAgentAssignment. Reuso do pattern Sub-sprint 7A (tabela canonical
        # pool_agent_assignments). Evita filter in-memory.
        use_pool_join = talent_pool_id is not None

        # Sprint 7B-3b Part 2 v2: filter por job_id via JSONB config->>job_id.
        # Reflete pattern sourcing-agents legacy onde job_id ficava em coluna
        # dedicada; em CustomAgent canonical o payload sourcing-specific vai em
        # config (vide ADR Sprint 7A unification).
        if job_id:
            conditions.append(CustomAgent.config["job_id"].astext == job_id)

        base = select(CustomAgent)
        count_base = select(func.count(CustomAgent.id))
        if use_pool_join:
            base = base.join(
                PoolAgentAssignment,
                PoolAgentAssignment.custom_agent_id == CustomAgent.id,
            ).where(PoolAgentAssignment.talent_pool_id == talent_pool_id)
            count_base = count_base.join(
                PoolAgentAssignment,
                PoolAgentAssignment.custom_agent_id == CustomAgent.id,
            ).where(PoolAgentAssignment.talent_pool_id == talent_pool_id)

        count_q = count_base.where(and_(*conditions))
        total = (await db.execute(count_q)).scalar() or 0

        q = (
            base
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

        listing_repo = AgentMarketplaceListingRepository(db)
        existing = await listing_repo.get_by_agent_id(agent_id=agent.id)
        if existing is not None:
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
        listing = await listing_repo.create(listing)
        agent.is_marketplace_published = True
        await db.flush()
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
        listing_repo = AgentMarketplaceListingRepository(db)
        rows, total = await listing_repo.list_public(
            category=category, search=search, limit=limit, offset=offset
        )

        listings = []
        for listing, agent in rows:
            data = listing.to_dict()
            data["agent_name"] = agent.name if agent else None
            data["agent_role"] = agent.role if agent else None
            data["agent_domain"] = agent.domain if agent else None
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
        listing_repo = AgentMarketplaceListingRepository(db)
        return await listing_repo.update_review(
            listing_id=listing_id,
            reviewer_id=reviewer_id,
            action=action,
            review_notes=review_notes,
        )

    async def install_agent(
        self,
        db: AsyncSession,
        listing_id: str,
        installer_company_id: str,
        installed_by: str,
    ) -> AgentInstallation:
        listing_repo = AgentMarketplaceListingRepository(db)
        install_repo = AgentInstallationRepository(db)

        row = await listing_repo.get_approved_listing_with_agent(
            listing_id=listing_id
        )
        if row is None:
            raise ValueError("Listing not found or not approved")
        listing, source_agent = row

        existing = await install_repo.get_active_installation(
            source_agent_id=source_agent.id,
            company_id=installer_company_id,
        )
        if existing is not None:
            raise ValueError("Agent already installed for this company")


        # P0-3: FairnessGuard scan - bloqueia system_prompt discriminatorio (CLT Art. 373-A)
        if source_agent.system_prompt:
            _fg_result = _fairness_guard.check(source_agent.system_prompt)
            if _fg_result.is_blocked:
                raise ValueError(
                    "Agente bloqueado por violacao de fairness no system_prompt "
                    f"(categoria: {_fg_result.category}). "
                    f"{_fg_result.educational_message}"
                )

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
        installation = await install_repo.create(installation)

        await listing_repo.increment_install_count(listing=listing)

        await listing_repo.activate_module_if_required(
            installation=installation,
            listing=listing,
        )

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
        install_repo = AgentInstallationRepository(db)
        installation = await install_repo.get_by_id(
            installation_id=installation_id, company_id=company_id
        )
        if installation is None:
            return False

        await install_repo.mark_uninstalled(installation=installation)

        if installation.installed_agent_id:
            installed_agent = await install_repo.get_installed_agent_by_id(
                installed_agent_id=installation.installed_agent_id
            )
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
        install_repo = AgentInstallationRepository(db)
        rows, total = await install_repo.list_by_company(
            company_id=company_id, limit=limit, offset=offset
        )

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

        # Bump agent-level counters via direct ORM (single-tenant lookup OK here
        # because record_execution is invoked from in-tenant agent runners that
        # already passed the company gate). Future: extend CustomAgentRepository
        # with bump_execution_counters.
        # ADR-001-EXEMPT: counter increment on already-validated agent; lifted to
        # repo when CustomAgentRepository.bump_executions lands.
        result = await db.execute(
            select(CustomAgent).where(CustomAgent.id == agent_uuid)
        )
        agent = result.scalar_one_or_none()
        if agent:
            agent.total_executions = (agent.total_executions or 0) + 1
            agent.last_executed_at = datetime.utcnow()

        if credits_consumed > 0:
            install_repo = AgentInstallationRepository(db)
            installation = await install_repo.get_active_for_installed_agent(
                installed_agent_id=agent_uuid,
                company_id=company_id,
            )
            if installation:
                await install_repo.bump_execution_counters(
                    installation=installation,
                    credits_consumed=credits_consumed,
                )

        await db.flush()

    async def get_billing_summary(
        self,
        db: AsyncSession,
        company_id: str,
    ) -> list[dict[str, Any]]:
        install_repo = AgentInstallationRepository(db)
        rows = await install_repo.list_billing_summary(company_id=company_id)

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
        listing_repo = AgentMarketplaceListingRepository(db)
        rows, total = await listing_repo.list_pending_reviews(
            limit=limit, offset=offset
        )

        listings = []
        for listing, agent in rows:
            data = listing.to_dict()
            data["agent_name"] = agent.name if agent else None
            data["agent_role"] = agent.role if agent else None
            data["agent_domain"] = agent.domain if agent else None
            data["system_prompt_preview"] = (agent.system_prompt or "")[:200] if agent else None
            listings.append(data)

        return listings, total

    async def _get_agent(
        self,
        db: AsyncSession,
        agent_id: str,
        company_id: str,
    ) -> Optional[CustomAgent]:
        """Canonical agent lookup — delegates to CustomAgentRepository."""
        from app.domains.agent_studio.repositories.custom_agent_repository import (
            CustomAgentRepository,
        )
        try:
            uuid.UUID(agent_id)
        except (ValueError, AttributeError, TypeError):
            return None
        repo = CustomAgentRepository(db)
        return await repo.get_by_id(agent_id=agent_id, company_id=company_id)


agent_marketplace_service = AgentMarketplaceService()
