import logging
import time
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_admin
from app.core.database import get_db
from app.domains.agent_studio.custom_agent_runtime import get_available_tool_names
from app.schemas.custom_agent import (
    AgentInstallationListResponse,
    AgentInstallationResponse,
    CreateCustomAgentRequest,
    CustomAgentListResponse,
    CustomAgentResponse,
    ExecuteCustomAgentRequest,
    ExecuteCustomAgentResponse,
    InstallAgentRequest,
    MarketplaceBillingResponse,
    MarketplaceListingResponse,
    MarketplaceListResponse,
    MarketplaceReviewRequest,
    PublishToMarketplaceRequest,
    TestCustomAgentRequest,
    TestCustomAgentResponse,
    UpdateCustomAgentRequest,
)
from app.services.agent_marketplace_service import agent_marketplace_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/custom-agents", tags=["Agent Studio"])


@router.get("/available-tools", summary="List available tools for custom agents")
async def list_available_tools(
    current_user=Depends(get_current_user),
):
    return {"tools": get_available_tool_names()}


@router.post("", response_model=CustomAgentResponse, status_code=status.HTTP_201_CREATED)
async def create_custom_agent(
    body: CreateCustomAgentRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.quota_enforcement import enforce_quota
    await enforce_quota("custom_agents", current_user.company_id, db)
    try:
        agent = await agent_marketplace_service.create_agent(
            db=db,
            company_id=current_user.company_id,
            created_by=str(current_user.id),
            data=body.model_dump(),
        )
        await db.commit()
        return CustomAgentResponse(**agent.to_dict())
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.error("Error creating custom agent: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create custom agent")


@router.get("", response_model=CustomAgentListResponse)
async def list_custom_agents(
    status_filter: Optional[str] = Query(None, alias="status"),
    domain: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agents, total = await agent_marketplace_service.list_agents(
        db=db,
        company_id=current_user.company_id,
        status=status_filter,
        domain=domain,
        limit=limit,
        offset=offset,
    )
    return CustomAgentListResponse(
        agents=[CustomAgentResponse(**a.to_dict()) for a in agents],
        total=total,
    )


@router.get("/{agent_id}", response_model=CustomAgentResponse)
async def get_custom_agent(
    agent_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await agent_marketplace_service.get_agent(
        db=db, agent_id=agent_id, company_id=current_user.company_id
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return CustomAgentResponse(**agent.to_dict())


@router.patch("/{agent_id}", response_model=CustomAgentResponse)
async def update_custom_agent(
    agent_id: str,
    body: UpdateCustomAgentRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        update_data = body.model_dump(exclude_unset=True)
        agent = await agent_marketplace_service.update_agent(
            db=db,
            agent_id=agent_id,
            company_id=current_user.company_id,
            data=update_data,
        )
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        await db.commit()
        return CustomAgentResponse(**agent.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error updating custom agent: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update custom agent")


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_agent(
    agent_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        deleted = await agent_marketplace_service.delete_agent(
            db=db, agent_id=agent_id, company_id=current_user.company_id
        )
        if not deleted:
            raise HTTPException(status_code=404, detail="Agent not found")
        await db.commit()
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error deleting custom agent: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete custom agent")


@router.post("/{agent_id}/test", response_model=TestCustomAgentResponse)
async def test_custom_agent(
    agent_id: str,
    body: TestCustomAgentRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await agent_marketplace_service.get_agent(
        db=db, agent_id=agent_id, company_id=current_user.company_id
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    try:
        from app.domains.agent_studio.custom_agent_runtime import get_or_create_runtime

        runtime = get_or_create_runtime(
            agent_id=str(agent.id),
            agent_name=agent.name,
            system_prompt=agent.system_prompt,
            allowed_tools=agent.allowed_tools or [],
            domain=agent.domain,
            max_steps=agent.max_steps,
            temperature=agent.temperature,
            model_override=agent.model_override,
            company_id=current_user.company_id,
            enable_memory=getattr(agent, "enable_memory", True),
            excluded_tools=getattr(agent, "excluded_tools", None),
            context_level=getattr(agent, "context_level", "full"),
        )

        start = time.time()
        output = await runtime.execute(
            message=body.message,
            user_id=str(current_user.id),
            company_id=current_user.company_id,
            context=body.context,
        )
        elapsed_ms = int((time.time() - start) * 1000)

        tool_calls = [a.params.get("tool", "") for a in (output.actions or [])]

        return TestCustomAgentResponse(
            agent_id=str(agent.id),
            message=body.message,
            response=output.message,
            confidence=output.confidence,
            tool_calls=tool_calls,
            execution_time_ms=elapsed_ms,
        )
    except Exception as e:
        logger.error("Error testing custom agent: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Test execution failed: {e}")


@router.post("/{agent_id}/execute", response_model=ExecuteCustomAgentResponse)
async def execute_custom_agent(
    agent_id: str,
    body: ExecuteCustomAgentRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await agent_marketplace_service.get_agent(
        db=db, agent_id=agent_id, company_id=current_user.company_id
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if agent.status not in ("active", "draft"):
        raise HTTPException(status_code=400, detail="Agent is not active")

    try:
        from app.domains.agent_studio.custom_agent_runtime import get_or_create_runtime

        runtime = get_or_create_runtime(
            agent_id=str(agent.id),
            agent_name=agent.name,
            system_prompt=agent.system_prompt,
            allowed_tools=agent.allowed_tools or [],
            domain=agent.domain,
            max_steps=agent.max_steps,
            temperature=agent.temperature,
            model_override=agent.model_override,
            company_id=current_user.company_id,
            enable_memory=getattr(agent, "enable_memory", True),
            excluded_tools=getattr(agent, "excluded_tools", None),
            context_level=getattr(agent, "context_level", "full"),
        )

        start = time.time()
        # GAP 2+3: Enrich context with tenant + user info
        enriched_context = dict(body.context or {})
        try:
            from app.shared.services.tenant_context_service import TenantContextService
            _tcs = TenantContextService()
            _tenant_ctx = await _tcs.get_context(company_id=current_user.company_id, db=db)
            enriched_context["tenant_context_snippet"] = _tenant_ctx.to_prompt_snippet()
        except Exception:
            pass
        enriched_context["user_name"] = getattr(current_user, "name", "") or getattr(current_user, "full_name", "") or ""
        enriched_context["user_role"] = getattr(current_user, "role", "") or ""

        output = await runtime.execute(
            message=body.message,
            user_id=str(current_user.id),
            company_id=current_user.company_id,
            session_id=body.session_id or "",
            context=enriched_context,
        )
        elapsed_ms = int((time.time() - start) * 1000)

        credits_consumed = 0
        from sqlalchemy import select, and_
        from lia_models.custom_agent import AgentInstallation
        inst_result = await db.execute(
            select(AgentInstallation).where(
                and_(
                    AgentInstallation.installed_agent_id == agent.id,
                    AgentInstallation.installer_company_id == current_user.company_id,
                    AgentInstallation.status == "active",
                )
            )
        )
        installation = inst_result.scalar_one_or_none()
        if installation and installation.listing_id:
            from lia_models.custom_agent import AgentMarketplaceListing
            listing_result = await db.execute(
                select(AgentMarketplaceListing).where(
                    AgentMarketplaceListing.id == installation.listing_id
                )
            )
            listing = listing_result.scalar_one_or_none()
            if listing and not listing.is_free:
                credits_consumed = listing.credits_per_execution

        await agent_marketplace_service.record_execution(
            db=db,
            agent_id=str(agent.id),
            company_id=current_user.company_id,
            credits_consumed=credits_consumed,
        )
        await db.commit()

        tool_calls = [a.params.get("tool", "") for a in (output.actions or [])]

        return ExecuteCustomAgentResponse(
            agent_id=str(agent.id),
            agent_name=agent.name,
            response=output.message,
            confidence=output.confidence,
            tool_calls=tool_calls,
            credits_consumed=credits_consumed,
            execution_time_ms=elapsed_ms,
            metadata=output.metadata or {},
        )
    except Exception as e:
        await db.rollback()
        logger.error("Error executing custom agent: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Execution failed: {e}")


@router.post("/{agent_id}/publish", response_model=MarketplaceListingResponse)
async def publish_to_marketplace(
    agent_id: str,
    body: PublishToMarketplaceRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        listing = await agent_marketplace_service.publish_to_marketplace(
            db=db,
            agent_id=agent_id,
            company_id=current_user.company_id,
            data=body.model_dump(),
        )
        if not listing:
            raise HTTPException(status_code=404, detail="Agent not found")
        await db.commit()
        return MarketplaceListingResponse(**listing.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error publishing to marketplace: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to publish to marketplace")


marketplace_router = APIRouter(prefix="/agent-marketplace", tags=["Agent Marketplace"])


@marketplace_router.get("", response_model=MarketplaceListResponse)
async def browse_marketplace(
    category: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    listings, total = await agent_marketplace_service.list_marketplace(
        db=db,
        category=category,
        search=search,
        limit=limit,
        offset=offset,
    )
    return MarketplaceListResponse(
        listings=[MarketplaceListingResponse(**l) for l in listings],
        total=total,
    )


@marketplace_router.post("/install", response_model=AgentInstallationResponse)
async def install_marketplace_agent(
    body: InstallAgentRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        installation = await agent_marketplace_service.install_agent(
            db=db,
            listing_id=body.listing_id,
            installer_company_id=current_user.company_id,
            installed_by=str(current_user.id),
        )
        await db.commit()
        return AgentInstallationResponse(**installation.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.error("Error installing agent: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to install agent")


@marketplace_router.get("/installations", response_model=AgentInstallationListResponse)
async def list_installations(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    installations, total = await agent_marketplace_service.list_installations(
        db=db,
        company_id=current_user.company_id,
        limit=limit,
        offset=offset,
    )
    return AgentInstallationListResponse(
        installations=[AgentInstallationResponse(**i) for i in installations],
        total=total,
    )


@marketplace_router.delete("/installations/{installation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def uninstall_agent(
    installation_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await agent_marketplace_service.uninstall_agent(
            db=db,
            installation_id=installation_id,
            company_id=current_user.company_id,
        )
        if not result:
            raise HTTPException(status_code=404, detail="Installation not found")
        await db.commit()
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error uninstalling agent: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to uninstall agent")


@marketplace_router.get("/billing", response_model=list[MarketplaceBillingResponse])
async def get_marketplace_billing(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    summaries = await agent_marketplace_service.get_billing_summary(
        db=db,
        company_id=current_user.company_id,
    )
    return [MarketplaceBillingResponse(**s) for s in summaries]


admin_marketplace_router = APIRouter(
    prefix="/admin/agent-marketplace",
    tags=["Admin - Agent Marketplace"],
)


@admin_marketplace_router.get("/pending-reviews", response_model=MarketplaceListResponse)
async def list_pending_reviews(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    listings, total = await agent_marketplace_service.get_pending_reviews(
        db=db, limit=limit, offset=offset
    )
    return MarketplaceListResponse(
        listings=[MarketplaceListingResponse(**l) for l in listings],
        total=total,
    )


@admin_marketplace_router.post("/review/{listing_id}", response_model=MarketplaceListingResponse)
async def review_listing(
    listing_id: str,
    body: MarketplaceReviewRequest,
    _user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        listing = await agent_marketplace_service.review_listing(
            db=db,
            listing_id=listing_id,
            reviewer_id=str(getattr(_user, "id", "admin")),
            action=body.action,
            review_notes=body.review_notes,
        )
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        await db.commit()
        return MarketplaceListingResponse(**listing.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error reviewing listing: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to review listing")


@router.get("/studio/consumption", summary="Get Studio agent consumption breakdown")
async def get_studio_consumption(
    days: int = Query(default=30, ge=1, le=365),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.studio_metering_service import studio_metering_service

    company_id = current_user.company_id
    try:
        consumption = await studio_metering_service.get_studio_consumption(
            db=db, company_id=company_id, days=days,
        )
        return consumption
    except Exception as e:
        logger.error("Error fetching studio consumption: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch studio consumption")


@router.get("/studio/quota", summary="Get Studio agent quota status")
async def get_studio_quota(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from lia_models.agent_quota import AgentQuota, get_limits_for_plan
    from sqlalchemy import select

    company_id = current_user.company_id
    try:
        result = await db.execute(
            select(AgentQuota).where(AgentQuota.company_id == company_id)
        )
        quota = result.scalar_one_or_none()
        if not quota:
            from app.domains.credits.services.token_budget_service import get_plan_for_company
            plan_code = await get_plan_for_company(company_id)
            limits = get_limits_for_plan(plan_code)
            return {
                "company_id": company_id,
                "plan_code": plan_code or "starter",
                **limits,
                "active_sourcing_agents": 0,
                "active_custom_agents": 0,
                "active_digital_twins": 0,
                "active_campaigns": 0,
            }
        return quota.to_dict()
    except Exception as e:
        logger.error("Error fetching studio quota: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch studio quota")


@router.get("/{agent_id}/preview-prompt")
async def preview_agent_prompt(
    agent_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Preview the composed system prompt for a custom agent.

    Returns the first 80 lines of the fully-composed prompt so the creator
    can inspect what the LLM actually sees.  Only the agent creator (same
    company) may preview.
    """
    agent = await agent_marketplace_service.get_agent(
        db=db, agent_id=agent_id, company_id=current_user.company_id
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    from app.domains.agent_studio.custom_agent_runtime import get_or_create_runtime
    from lia_agents_core.agent_interface import AgentInput

    runtime = get_or_create_runtime(
        agent_id=str(agent.id),
        agent_name=agent.name,
        system_prompt=agent.system_prompt,
        allowed_tools=agent.allowed_tools or [],
        domain=agent.domain or "general",
        max_steps=agent.max_steps or 8,
        temperature=agent.temperature or 0.7,
        model_override=agent.model_override,
        enable_memory=getattr(agent, "enable_memory", True),
        excluded_tools=getattr(agent, "excluded_tools", None),
        context_level=getattr(agent, "context_level", "full"),
        company_id=current_user.company_id,
    )

    dummy_input = AgentInput(
        message="(preview)",
        user_id=str(current_user.id),
        company_id=current_user.company_id,
        session_id="preview",
        context={},
    )
    full_prompt = runtime._get_system_prompt(dummy_input)
    lines = full_prompt.split("\n")
    preview_lines = lines[:80]

    return {
        "agent_id": agent_id,
        "context_level": getattr(agent, "context_level", "full"),
        "total_lines": len(lines),
        "preview_lines": 80,
        "prompt_preview": "\n".join(preview_lines),
    }
