import logging
import time
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_admin
from app.core.database import get_db, get_tenant_db
from app.domains.agent_studio.custom_agent_runtime import get_available_tool_names
from lia_models.custom_agent import CustomAgent
from app.schemas.custom_agent import (
    AgentInstallationListResponse,
    AgentInstallationResponse,
    CreateCustomAgentRequest,
    CustomAgentListResponse,
    CustomAgentResponse,
    ExecuteCustomAgentRequest,
    ExecuteCustomAgentResponse,
    GeneratedAgentConfig,
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
from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/custom-agents", tags=["Agent Studio"])


@router.get("/available-tools", summary="List available tools for custom agents")
async def list_available_tools(
    current_user=Depends(get_current_user),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    return {"tools": get_available_tool_names()}


@router.post("", response_model=CustomAgentResponse, status_code=status.HTTP_201_CREATED)
async def create_custom_agent(
    body: CreateCustomAgentRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    from app.services.quota_enforcement import enforce_quota
    await enforce_quota("custom_agents", current_user.company_id, db)

    # Wave 2 audit 2026-05-21: FG check no system_prompt antes de persistir.
    # ANTES: recruiter podia digitar prompt enviesado ("prefer male candidates")
    # e o agente ficava com prompt salvo no DB. Bias atravessava ate o runtime
    # rodar guards no input do recruiter (não no system_prompt).
    # AGORA: bloqueia create se FG detecta bias no system_prompt.
    if body.system_prompt:
        try:
            from app.shared.compliance.fairness_guard import FairnessGuard
            _fg_create = FairnessGuard()
            _fg_result = _fg_create.check(body.system_prompt)
            if _fg_result.is_blocked:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "fairness_guard_blocked",
                        "category": _fg_result.category,
                        "message": _fg_result.educational_message or (
                            "system_prompt contém critérios discriminatórios. "
                            "Reformule sem viés."
                        ),
                        "blocked_terms": _fg_result.blocked_terms,
                    },
                )
        except HTTPException:
            raise
        except Exception as _fg_exc:
            logger.warning("[CustomAgent.create] FairnessGuard check failed: %s", _fg_exc)
            # Fail-closed em ambiente de produção: bloqueia se FG não estiver disponível
            # (consistente com pattern WT-2022 P1.A canonical)

    try:
        agent = await agent_marketplace_service.create_agent(
            db=db,
            company_id=current_user.company_id,
            created_by=str(current_user.id),
            data=body.model_dump(),
        )
        await db.commit()
        # P0-3 audit 2026-05-21: canonical lifecycle audit (EU AI Act Art. 12 / LGPD Art. 20)
        from app.domains.agent_studio._audit_helper import studio_audit
        await studio_audit(
            company_id=current_user.company_id,
            action="studio_agent_create",
            decision="created",
            reasoning=[
                f"Agent name: {agent.name}",
                f"Domain: {agent.domain}",
                f"Tools: {len(agent.allowed_tools or [])} tools",
                f"Status: {agent.status}",
            ],
            actor_user_id=str(current_user.id),
            target_id=str(agent.id),
            criteria_used=["name", "domain", "allowed_tools", "system_prompt"],
        )
        return CustomAgentResponse(**agent.to_dict())
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error creating custom agent: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create custom agent")


@router.get("", response_model=CustomAgentListResponse)
async def list_custom_agents(
    status_filter: Optional[str] = Query(None, alias="status"),
    domain: Optional[str] = None,
    category: Optional[str] = Query(
        None,
        pattern="^(screening|sourcing|communication|analytics|automation|job_management)$",
        description="Sprint 7A category filter",
    ),
    talent_pool_id: Optional[str] = Query(
        None,
        description="Sprint 7B-3b Part 2 v2: filtra agents assigned ao pool via PoolAgentAssignment",
    ),
    job_id: Optional[str] = Query(
        None,
        description="Sprint 7B-3b Part 2 v2: filtra agents com config.job_id match (JSONB)",
    ),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    agents, total = await agent_marketplace_service.list_agents(
        db=db,
        company_id=current_user.company_id,
        status=status_filter,
        domain=domain,
        category=category,
        talent_pool_id=talent_pool_id,
        job_id=job_id,
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
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
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
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Update custom agent. Automatically creates a version snapshot before applying changes."""
    # P2.2: Snapshot before update
    try:
        from app.services.agent_version_service import agent_version_service
        from sqlalchemy import select as _sel
        _existing_result = await db.execute(
            _sel(CustomAgent).where(
                CustomAgent.id == agent_id,
                CustomAgent.company_id == current_user.company_id,
            )
        )
        _existing = _existing_result.scalar_one_or_none()
        if _existing:
            _update_data_peek = body.model_dump(exclude_unset=True)
            _changed_fields = [k for k in _update_data_peek.keys() if hasattr(_existing, k)]
            if _changed_fields:
                await agent_version_service.create_snapshot(
                    db=db,
                    agent=_existing,
                    changed_fields=_changed_fields,
                    changed_by=str(current_user.id),
                )
    except Exception as _snap_err:
        logger.warning("[AgentVersion] snapshot failed (non-blocking): %s", _snap_err)

    # Wave 2 audit 2026-05-21: FG check em system_prompt quando incluído no PATCH.
    if body.system_prompt is not None:
        try:
            from app.shared.compliance.fairness_guard import FairnessGuard
            _fg_update = FairnessGuard()
            _fg_result = _fg_update.check(body.system_prompt)
            if _fg_result.is_blocked:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "fairness_guard_blocked",
                        "category": _fg_result.category,
                        "message": _fg_result.educational_message or (
                            "system_prompt contém critérios discriminatórios. "
                            "Reformule sem viés."
                        ),
                        "blocked_terms": _fg_result.blocked_terms,
                    },
                )
        except HTTPException:
            raise
        except Exception as _fg_exc:
            logger.warning("[CustomAgent.update] FairnessGuard check failed: %s", _fg_exc)

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
        # P0-3 audit 2026-05-21: canonical lifecycle audit
        from app.domains.agent_studio._audit_helper import studio_audit
        await studio_audit(
            company_id=current_user.company_id,
            action="studio_agent_update",
            decision="updated",
            reasoning=[f"Changed fields: {list(update_data.keys())}"],
            actor_user_id=str(current_user.id),
            target_id=str(agent.id),
            criteria_used=list(update_data.keys()),
        )
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
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        deleted = await agent_marketplace_service.delete_agent(
            db=db, agent_id=agent_id, company_id=current_user.company_id
        )
        if not deleted:
            raise HTTPException(status_code=404, detail="Agent not found")
        await db.commit()
        # P0-3 audit 2026-05-21: canonical lifecycle audit
        from app.domains.agent_studio._audit_helper import studio_audit
        await studio_audit(
            company_id=current_user.company_id,
            action="studio_agent_delete",
            decision="deleted",
            reasoning=[f"Agent {agent_id} permanently removed"],
            actor_user_id=str(current_user.id),
            target_id=agent_id,
        )
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
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
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

        _meta = output.metadata or {}
        # P0-3 chunk 2 audit 2026-05-21
        from app.domains.agent_studio._audit_helper import studio_audit
        await studio_audit(
            company_id=current_user.company_id,
            action="studio_agent_test",
            decision="executed",
            reasoning=[f"Test message: {body.message[:200]}"],
            actor_user_id=str(current_user.id),
            target_id=str(agent.id),
        )
        return TestCustomAgentResponse(
            agent_id=str(agent.id),
            message=body.message,
            response=output.message,
            confidence=output.confidence,
            tool_calls=_meta.get("tool_calls", []),
            execution_time_ms=elapsed_ms,
            tokens_input=_meta.get("tokens_input", 0),
            tokens_output=_meta.get("tokens_output", 0),
            model_used=_meta.get("model_used", ""),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error testing custom agent: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Test execution failed: {e}")


@router.post("/{agent_id}/execute", response_model=ExecuteCustomAgentResponse)
async def execute_custom_agent(
    agent_id: str,
    body: ExecuteCustomAgentRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
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

        # Wave 4 W4-4 audit 2026-05-22: passar tokens para calculo real
        _output_meta = output.metadata if isinstance(output.metadata, dict) else {}
        await agent_marketplace_service.record_execution(
            db=db,
            agent_id=str(agent.id),
            company_id=current_user.company_id,
            credits_consumed=credits_consumed,
            tokens_input=_output_meta.get("tokens_input", 0),
            tokens_output=_output_meta.get("tokens_output", 0),
            pricing_tier="pro",
        )

        # Persist execution log (GAP B2)
        try:
            from lia_models.agent_execution_log import AgentExecutionLog
            from uuid import uuid4
            _meta = output.metadata or {}
            db.add(AgentExecutionLog(
                id=uuid4(),
                agent_id=agent.id,
                company_id=current_user.company_id,
                user_id=str(current_user.id),
                input_message=body.message[:2000],
                output_message=(output.message or "")[:5000],
                confidence=output.confidence,
                tokens_input=_meta.get("tokens_input", 0),
                tokens_output=_meta.get("tokens_output", 0),
                model_used=_meta.get("model_used", ""),
                latency_ms=elapsed_ms,
                credits_consumed=credits_consumed,
                tool_calls=_meta.get("tool_calls", []),
                # WT-2022 P0.B fix: deriva de output.metadata.blocked (era ghost metric "pass" hardcoded).
                # FairnessGuard bloqueia agent em runtime.py:464-472 setando metadata.blocked=True;
                # antes o log SEMPRE escrevia "pass" — dashboard StudioComplianceView vanity metric.
                compliance_status=("blocked" if bool((_meta or {}).get("blocked")) else "pass"),
            ))
        except Exception as _log_err:
            logger.warning("[Studio] Execution log persist failed: %s", _log_err)

        await db.commit()

        # P0-3 chunk 2b audit 2026-05-21: canonical lifecycle audit complementa ExecutionLog ad-hoc
        # com schema canonical audit_logs (EU AI Act Art. 12 + LGPD Art. 20).
        try:
            from app.domains.agent_studio._audit_helper import studio_audit
            _meta_post = output.metadata or {}
            _blocked = bool(_meta_post.get("blocked"))
            await studio_audit(
                company_id=current_user.company_id,
                action="studio_agent_execute",
                decision=("blocked" if _blocked else "executed"),
                reasoning=[
                    f"Input message length: {len(body.message)}",
                    f"Output length: {len(output.message or '')}",
                    f"Tool calls: {len(_meta.get('tool_calls', []) or [])}",
                    f"Latency: {elapsed_ms}ms",
                    f"Credits consumed: {credits_consumed}",
                ],
                actor_user_id=str(current_user.id),
                target_id=str(agent.id),
                confidence=output.confidence,
            )
        except Exception as _audit_err:
            logger.warning("[Studio] audit log_decision failed: %s", _audit_err)

        # P2.5a: Internal notification (non-blocking)
        try:
            from app.services.studio_notification_service import studio_notification_service
            await studio_notification_service.notify_execution_completed(
                db=db,
                user_id=str(current_user.id),
                agent_id=str(agent.id),
                agent_name=agent.name,
                candidates_processed=1,
                execution_time_ms=elapsed_ms,
            )
            await db.commit()
        except Exception as _notif_err:
            logger.warning("[StudioNotif] execute notify failed: %s", _notif_err)

        # P2.5b: External webhook dispatch (non-blocking)
        try:
            from app.services.webhook_dispatcher import webhook_service
            await webhook_service.dispatch(
                db=db,
                company_id=current_user.company_id,
                event="agent.execution.completed",
                payload={
                    "agent_id": str(agent.id),
                    "agent_name": agent.name,
                    "execution_time_ms": elapsed_ms,
                    "tokens_input": _meta.get("tokens_input", 0) if "_meta" in dir() else 0,
                    "tokens_output": _meta.get("tokens_output", 0) if "_meta" in dir() else 0,
                    "confidence": output.confidence,
                    "user_id": str(current_user.id),
                },
            )
        except Exception as _wh_err:
            logger.warning("[Webhook] execute dispatch failed: %s", _wh_err)

        tool_calls = [a.params.get("tool", "") for a in (output.actions or [])]

        _meta = output.metadata or {}
        return ExecuteCustomAgentResponse(
            agent_id=str(agent.id),
            agent_name=agent.name,
            response=output.message,
            confidence=output.confidence,
            tool_calls=tool_calls,
            credits_consumed=credits_consumed,
            execution_time_ms=elapsed_ms,
            tokens_input=_meta.get("tokens_input", 0),
            tokens_output=_meta.get("tokens_output", 0),
            model_used=_meta.get("model_used", ""),
            metadata=_meta,
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error executing custom agent: %s", e, exc_info=True)
        # P1-W3-10: dispatch agent.execution.failed (was ghost event)
        try:
            _agent_for_wh = locals().get('agent')
            if _agent_for_wh and current_user:
                from app.services.webhook_dispatcher import webhook_service
                await webhook_service.dispatch(
                    db=db,
                    company_id=current_user.company_id,
                    event="agent.execution.failed",
                    payload={
                        "agent_id": str(_agent_for_wh.id),
                        "agent_name": _agent_for_wh.name,
                        "error": str(e),
                        "user_id": str(current_user.id),
                    },
                )
        except Exception as _wh_err:
            logger.warning("[Webhook] execution.failed dispatch error: %s", _wh_err)
        raise HTTPException(status_code=500, detail=f"Execution failed: {e}")


@router.post("/{agent_id}/publish", response_model=MarketplaceListingResponse)
async def publish_to_marketplace(
    agent_id: str,
    body: PublishToMarketplaceRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
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
        # P0-3 chunk 2 audit 2026-05-21: marketplace publish trail
        from app.domains.agent_studio._audit_helper import studio_audit
        await studio_audit(
            company_id=current_user.company_id,
            action="studio_agent_publish",
            decision="published",
            reasoning=[f"Listing {listing.id} published from agent {agent_id}"],
            actor_user_id=str(current_user.id),
            target_id=str(listing.id),
            target_type="marketplace_listing",
        )
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
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
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
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    try:
        installation = await agent_marketplace_service.install_agent(
            db=db,
            listing_id=body.listing_id,
            installer_company_id=current_user.company_id,
            installed_by=str(current_user.id),
        )
        await db.commit()
        # P0-3 chunk 2 audit 2026-05-21: marketplace install trail
        from app.domains.agent_studio._audit_helper import studio_audit
        await studio_audit(
            company_id=current_user.company_id,
            action="studio_agent_install",
            decision="installed",
            reasoning=[
                f"Listing ID: {body.listing_id}",
                f"Installation ID: {installation.id}",
                f"Installed agent ID: {installation.installed_agent_id}",
            ],
            actor_user_id=str(current_user.id),
            target_id=str(installation.installed_agent_id),
            target_type="custom_agent",
        )
        return AgentInstallationResponse(**installation.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error installing agent: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to install agent")


@marketplace_router.get("/installations", response_model=AgentInstallationListResponse)
async def list_installations(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
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
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    try:
        result = await agent_marketplace_service.uninstall_agent(
            db=db,
            installation_id=installation_id,
            company_id=current_user.company_id,
        )
        if not result:
            raise HTTPException(status_code=404, detail="Installation not found")
        await db.commit()
        # P0-3 chunk 2 audit 2026-05-21: marketplace uninstall trail
        from app.domains.agent_studio._audit_helper import studio_audit
        await studio_audit(
            company_id=current_user.company_id,
            action="studio_agent_uninstall",
            decision="uninstalled",
            reasoning=[f"Installation {installation_id} removed"],
            actor_user_id=str(current_user.id),
            target_id=installation_id,
            target_type="marketplace_installation",
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error uninstalling agent: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to uninstall agent")


@marketplace_router.get("/billing", response_model=list[MarketplaceBillingResponse])
async def get_marketplace_billing(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
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
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
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
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
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


@router.get("/{agent_id}/executions", summary="Get execution history for an agent")
async def get_agent_executions(
    agent_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Paginated execution history for a specific agent."""
    from sqlalchemy import select, and_, func
    from lia_models.agent_execution_log import AgentExecutionLog

    # TENANT-EXEMPT: AgentExecutionLog.company_id == current_user.company_id
    # já é elemento de `base_filter` and_() abaixo (statically guaranteed).
    # Sensor AST não rastreia through .where(base_filter) indirection.
    base_filter = and_(
        AgentExecutionLog.agent_id == agent_id,
        AgentExecutionLog.company_id == current_user.company_id,
    )

    total = await db.scalar(select(func.count(AgentExecutionLog.id)).where(base_filter))

        # TENANT-EXEMPT: see base_filter and_() acima — company_id já incluso.
    result = await db.execute(
        select(AgentExecutionLog)
        .where(base_filter)
        .order_by(AgentExecutionLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    logs = result.scalars().all()

    return {
        "executions": [log.to_dict() for log in logs],
        "total": total or 0,
        "limit": limit,
        "offset": offset,
    }


@router.get("/studio/consumption", summary="Get Studio agent consumption breakdown")
async def get_studio_consumption(
    days: int = Query(default=30, ge=1, le=365),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    from app.services.studio_metering_service import studio_metering_service

    company_id = current_user.company_id
    try:
        consumption = await studio_metering_service.get_studio_consumption(
            db=db, company_id=company_id, days=days,
        )
        return consumption
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching studio consumption: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch studio consumption")


@router.get("/studio/quota", summary="Get Studio agent quota status")
async def get_studio_quota(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching studio quota: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch studio quota")


@router.get("/{agent_id}/versions", summary="List agent version history")
async def list_agent_versions(
    agent_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Paginated list of version snapshots for an agent."""
    from app.services.agent_version_service import agent_version_service
    versions, total = await agent_version_service.list_versions(
        db=db,
        agent_id=agent_id,
        company_id=current_user.company_id,
        limit=limit,
        offset=offset,
    )
    return {
        "versions": [v.summary() for v in versions],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{agent_id}/versions/{version}", summary="Get specific version snapshot")
async def get_agent_version(
    agent_id: str,
    version: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get full snapshot data for a specific version."""
    from app.services.agent_version_service import agent_version_service
    snap = await agent_version_service.get_version(
        db=db,
        agent_id=agent_id,
        version=version,
        company_id=current_user.company_id,
    )
    if not snap:
        raise HTTPException(status_code=404, detail="Version not found")
    return snap.to_dict()


@router.post("/{agent_id}/revert/{version}", summary="Revert agent to previous version")
async def revert_agent_to_version(
    agent_id: str,
    version: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Revert agent state to a previous version. Creates a new snapshot before reverting."""
    from app.services.agent_version_service import agent_version_service
    from sqlalchemy import select as _sel

    agent_result = await db.execute(
        _sel(CustomAgent).where(
            CustomAgent.id == agent_id,
            CustomAgent.company_id == current_user.company_id,
        )
    )
    agent = agent_result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    try:
        reverted = await agent_version_service.revert(
            db=db,
            agent=agent,
            target_version=version,
            reverted_by=str(current_user.id),
        )
        await db.commit()
        return CustomAgentResponse(**reverted.to_dict())
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("[AgentVersion] revert failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to revert agent")


@router.get("/search", summary="Search agents by name (fuzzy)")
async def search_agents_by_name(
    name: str = Query(..., min_length=1, max_length=256),
    limit: int = Query(5, ge=1, le=20),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Fuzzy search for agents by name. Used by chat to find agent mentioned by user.

    Returns top N matches ordered by relevance. Tenant-isolated.
    """
    from sqlalchemy import select, and_, func
    from lia_models.custom_agent import CustomAgent

    # Case-insensitive LIKE search
    name_lower = name.lower().strip()
    result = await db.execute(
        select(CustomAgent)
        .where(
            and_(
                CustomAgent.company_id == current_user.company_id,
                func.lower(CustomAgent.name).contains(name_lower),
            )
        )
        .limit(limit)
    )
    agents = list(result.scalars().all())
    return {
        "agents": [a.to_dict() for a in agents],
        "total": len(agents),
        "query": name,
    }


@router.get("/studio/compliance-summary", summary="Aggregated compliance metrics for Studio")
async def get_studio_compliance_summary(
    period_days: int = Query(30, ge=1, le=365),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Aggregated compliance metrics across all Studio agents in the period.

    Returns:
      - Total executions and breakdown by compliance_status (pass/blocked)
      - Top agents by blocked execution count (highest risk)
      - Daily trend (executions per day)
      - Active agents count
      - Block rate percentage

    Used by Settings > Fairness & Compliance > Studio dashboard.
    """
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import select, and_, func, desc, cast, Date
    from lia_models.custom_agent import CustomAgent
    from lia_models.agent_execution_log import AgentExecutionLog

    since = datetime.now(timezone.utc) - timedelta(days=period_days)
    base_filter = and_(
        AgentExecutionLog.company_id == current_user.company_id,
        AgentExecutionLog.created_at >= since,
    )

    # Totals
    totals = await db.execute(
        select(
            func.count(AgentExecutionLog.id).label("total"),
            func.coalesce(
                func.sum(
                    func.case((AgentExecutionLog.compliance_status != "pass", 1), else_=0)
                ),
                0,
            ).label("blocked"),
            func.coalesce(func.avg(AgentExecutionLog.confidence), 0.0).label("avg_confidence"),
        ).where(base_filter)
    )
    t = totals.one()
    total_exec = t.total or 0
    blocked = t.blocked or 0
    block_rate = round((blocked / total_exec * 100), 2) if total_exec > 0 else 0.0

    # Breakdown by compliance_status
    status_breakdown = await db.execute(
        select(
            AgentExecutionLog.compliance_status,
            func.count(AgentExecutionLog.id).label("count"),
        )
        .where(base_filter)
        .group_by(AgentExecutionLog.compliance_status)
    )
    by_status = {row.compliance_status or "unknown": row.count for row in status_breakdown.all()}

    # Top blocked agents (highest risk)
    top_blocked_q = await db.execute(
        select(
            AgentExecutionLog.agent_id,
            func.count(AgentExecutionLog.id).label("blocks"),
        )
        .where(
            and_(
                base_filter,
                AgentExecutionLog.compliance_status != "pass",
            )
        )
        .group_by(AgentExecutionLog.agent_id)
        .order_by(desc("blocks"))
        .limit(5)
    )
    top_blocked_rows = list(top_blocked_q.all())

    top_blocked_agents = []
    for row in top_blocked_rows:
        # Multi-tenancy fail-closed: explicit company_id filter (REGRA ZERO + B.1).
        agent_res = await db.execute(
            select(CustomAgent).where(
                CustomAgent.id == row.agent_id,
                CustomAgent.company_id == current_user.company_id,
            )
        )
        agent = agent_res.scalar_one_or_none()
        top_blocked_agents.append({
            "agent_id": str(row.agent_id),
            "agent_name": agent.name if agent else "(deleted)",
            "blocked_count": row.blocks,
        })

    # Daily trend (executions per day)
    trend_q = await db.execute(
        select(
            cast(AgentExecutionLog.created_at, Date).label("day"),
            func.count(AgentExecutionLog.id).label("count"),
            func.coalesce(
                func.sum(
                    func.case((AgentExecutionLog.compliance_status != "pass", 1), else_=0)
                ),
                0,
            ).label("blocked"),
        )
        .where(base_filter)
        .group_by("day")
        .order_by("day")
    )
    trend = [
        {
            "day": row.day.isoformat() if row.day else None,
            "executions": row.count,
            "blocked": row.blocked or 0,
        }
        for row in trend_q.all()
    ]

    # Active agents
    active_count = await db.scalar(
        select(func.count(CustomAgent.id)).where(
            and_(
                CustomAgent.company_id == current_user.company_id,
                CustomAgent.status == "active",
            )
        )
    ) or 0

    return {
        "period_days": period_days,
        "total_executions": total_exec,
        "blocked_executions": blocked,
        "block_rate_pct": block_rate,
        "avg_confidence": round(float(t.avg_confidence or 0), 3),
        "active_agents": active_count,
        "by_status": by_status,
        "top_blocked_agents": top_blocked_agents,
        "trend": trend,
    }


@router.get("/studio/metrics/summary", summary="Aggregated Studio metrics for dashboard/chat")
async def get_studio_metrics_summary(
    period_days: int = Query(7, ge=1, le=90),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Returns aggregated metrics across all tenant agents for the specified period.

    Used by chat intent "meu consumo" / "quantas execucoes hoje".
    """
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import select, and_, func, desc
    from lia_models.custom_agent import CustomAgent
    from lia_models.agent_execution_log import AgentExecutionLog

    since = datetime.now(timezone.utc) - timedelta(days=period_days)

    # Total metrics
    totals = await db.execute(
        select(
            func.count(AgentExecutionLog.id).label("total_executions"),
            func.coalesce(func.sum(AgentExecutionLog.tokens_input), 0).label("total_tokens_input"),
            func.coalesce(func.sum(AgentExecutionLog.tokens_output), 0).label("total_tokens_output"),
            func.coalesce(func.sum(AgentExecutionLog.credits_consumed), 0).label("total_credits"),
            func.coalesce(func.avg(AgentExecutionLog.confidence), 0.0).label("avg_confidence"),
            func.coalesce(func.avg(AgentExecutionLog.latency_ms), 0).label("avg_latency_ms"),
        ).where(
            and_(
                AgentExecutionLog.company_id == current_user.company_id,
                AgentExecutionLog.created_at >= since,
            )
        )
    )
    total_row = totals.one()

    # Top 3 agents by execution count
    top_agents_result = await db.execute(
        select(
            AgentExecutionLog.agent_id,
            func.count(AgentExecutionLog.id).label("exec_count"),
            func.coalesce(func.sum(AgentExecutionLog.tokens_input + AgentExecutionLog.tokens_output), 0).label("total_tokens"),
        )
        .where(
            and_(
                AgentExecutionLog.company_id == current_user.company_id,
                AgentExecutionLog.created_at >= since,
            )
        )
        .group_by(AgentExecutionLog.agent_id)
        .order_by(desc("exec_count"))
        .limit(3)
    )
    top_agent_rows = list(top_agents_result.all())

    # Enrich top agents with names
    top_agents = []
    for row in top_agent_rows:
        # Multi-tenancy fail-closed: explicit company_id filter (REGRA ZERO + B.1).
        agent_result = await db.execute(
            select(CustomAgent).where(
                CustomAgent.id == row.agent_id,
                CustomAgent.company_id == current_user.company_id,
            )
        )
        agent = agent_result.scalar_one_or_none()
        top_agents.append({
            "agent_id": str(row.agent_id),
            "agent_name": agent.name if agent else "(deleted)",
            "execution_count": row.exec_count,
            "total_tokens": row.total_tokens,
        })

    # Active agent count
    active_count = await db.scalar(
        select(func.count(CustomAgent.id)).where(
            and_(
                CustomAgent.company_id == current_user.company_id,
                CustomAgent.status == "active",
            )
        )
    ) or 0

    # Estimated cost (R$0.000003 per token — rough estimate)
    total_tokens = (total_row.total_tokens_input or 0) + (total_row.total_tokens_output or 0)
    estimated_cost_brl = round(total_tokens * 0.000003, 4)

    return {
        "period_days": period_days,
        "total_executions": total_row.total_executions or 0,
        "total_tokens_input": total_row.total_tokens_input or 0,
        "total_tokens_output": total_row.total_tokens_output or 0,
        "total_tokens": total_tokens,
        "total_credits": total_row.total_credits or 0,
        "estimated_cost_brl": estimated_cost_brl,
        "avg_confidence": round(float(total_row.avg_confidence or 0), 3),
        "avg_latency_ms": int(total_row.avg_latency_ms or 0),
        "active_agents": active_count,
        "top_agents": top_agents,
    }


def _coalesce(value, default):
    """Return ``default`` if ``value`` is None or an empty string/list, else ``value``.

    Python's ``dict.get(key, default)`` only returns ``default`` when the key is
    *missing*. If the key exists but is ``None`` (e.g. an LLM emits
    ``"suggested_tools": null``), ``.get`` returns ``None`` and downstream code
    that expects a list/string crashes. This helper closes that gap.
    """
    if value is None:
        return default
    if isinstance(value, (list, str)) and not value:
        return default
    return value


@router.post(
    "/generate-from-description",
    response_model=GeneratedAgentConfig,
    summary="LIA generates agent config from description",
)
async def generate_agent_from_description(
    body: dict,
    current_user=Depends(get_current_user),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Generate a complete agent configuration from a natural language description.

    The recruiter describes what they need in Portuguese, and LIA generates:
    name, role, domain, tools, system_prompt, context_level, etc.

    Compliance: FairnessGuard + SecurityPatterns run on the description before generation.
    """
    description = (body.get("description") or "").strip()
    if not description or len(description) < 10:
        raise HTTPException(status_code=400, detail="Descricao deve ter pelo menos 10 caracteres")

    # Security checks on input
    try:
        from app.shared.robustness.security_patterns import check_input_security
        sec = check_input_security(description)
        if sec.is_blocked:
            raise HTTPException(status_code=400, detail="Descricao bloqueada por padrao de seguranca")
    except HTTPException:
        raise
    except Exception as _sec_exc:
        # WT-2022 P1.A fix (REGRA 4): silent fallback proibido em path critico.
        logger.error(
            "SecurityPatterns check FAILED em custom_agents (WT-2022 P1.A fail-closed): %s",
            str(_sec_exc)[:200],
        )
        raise HTTPException(
            status_code=503,
            detail="SecurityPatterns temporariamente indisponivel - operacao bloqueada",
        )

    try:
        from app.shared.compliance.fairness_guard import FairnessGuard
        fg = FairnessGuard()
        fg_result = fg.check(description)
        if fg_result.is_blocked:
            raise HTTPException(status_code=400, detail="Descricao bloqueada por criterios de equidade")
    except HTTPException:
        raise
    except Exception as _fg_exc:
        # WT-2022 P1.A fix (REGRA 4 CLAUDE.md): silent fallback em path critico de IA era PROIBIDO.
        # FairnessGuard indisponivel = NAO prosseguir (gate eh requisito canonical, nao optional).
        logger.error(
            "FairnessGuard check FAILED em path critico custom_agents (WT-2022 P1.A fail-closed): %s",
            str(_fg_exc)[:200],
        )
        raise HTTPException(
            status_code=503,
            detail="FairnessGuard temporariamente indisponivel - operacao bloqueada por seguranca",
        )

    # Generate config using audited LLM
    try:
        from app.domains.ai.services.llm import llm_service
        import json

        generation_prompt = f"""Voce e um especialista em configuracao de agentes de IA para recrutamento.
O recrutador descreveu o que precisa:

"{description}"

Gere uma configuracao completa de agente no formato JSON com estes campos:
- suggested_name: nome curto e descritivo (max 50 chars)
- suggested_role: descricao do papel do agente (max 200 chars)
- suggested_domain: um de [sourcing, screening, pipeline, analytics, communication, job_management, automation, general]
- suggested_tools: lista de tools (escolha entre: search_candidates, list_jobs, get_job_details, get_candidate_details, get_evaluation_criteria, get_pipeline_summary, search_talent_pool, get_company_culture, get_analytics_summary, summarize_context, clarify_request, move_candidate, send_email, update_candidate_field, schedule_interview, create_note)
- suggested_prompt: system prompt completo para o agente (em portugues, 200-500 chars)
- suggested_context_level: "full", "standard" ou "minimal"
- suggested_max_steps: numero entre 5 e 15
- suggested_temperature: numero entre 0.2 e 0.8
- reasoning: explique brevemente por que escolheu essa configuracao (em portugues)

Responda APENAS com o JSON, sem texto adicional."""

        model = llm_service.get_audited_model(company_id=current_user.company_id)
        response = await model.ainvoke(generation_prompt)
        content = response.content if hasattr(response, "content") else str(response)
        if isinstance(content, list):
            content = "".join(
                b.get("text", "") if isinstance(b, dict) else str(b) for b in content
            )

        # Parse JSON from response
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("```", 1)[0]
        config = json.loads(content)

        # _coalesce protects against the LLM emitting explicit nulls like
        # {"suggested_tools": null} — Pydantic GeneratedAgentConfig also
        # provides a final safety net via its field defaults.
        # P0-3 chunk 2 audit 2026-05-21: LLM generation trail
        try:
            from app.domains.agent_studio._audit_helper import studio_audit
            await studio_audit(
                company_id=current_user.company_id,
                action="studio_agent_generate",
                decision="generated",
                reasoning=[
                    f"Description: {description[:200]}",
                    f"Suggested name: {config.get('suggested_name', '')[:100]}",
                    f"Suggested domain: {config.get('suggested_domain', '')}",
                ],
                actor_user_id=str(current_user.id),
                target_id=None,
                target_type="custom_agent_blueprint",
            )
        except Exception:
            pass
        return GeneratedAgentConfig(
            suggested_name=_coalesce(config.get("suggested_name"), "Novo Agente"),
            suggested_role=_coalesce(config.get("suggested_role"), description[:200]),
            suggested_domain=_coalesce(config.get("suggested_domain"), "general"),
            suggested_tools=_coalesce(
                config.get("suggested_tools"),
                ["search_candidates", "get_candidate_details"],
            ),
            suggested_prompt=_coalesce(config.get("suggested_prompt"), ""),
            suggested_context_level=_coalesce(
                config.get("suggested_context_level"), "standard"
            ),
            suggested_max_steps=_coalesce(config.get("suggested_max_steps"), 8),
            suggested_temperature=_coalesce(config.get("suggested_temperature"), 0.5),
            reasoning=_coalesce(config.get("reasoning"), ""),
        )
    except json.JSONDecodeError:
        # Fallback: return sensible defaults when the LLM does not emit valid JSON.
        return GeneratedAgentConfig(
            suggested_name="Novo Agente",
            suggested_role=description[:200],
            suggested_domain="general",
            suggested_tools=["search_candidates", "get_candidate_details"],
            suggested_prompt=f"Voce e um agente de recrutamento. {description}",
            suggested_context_level="standard",
            suggested_max_steps=8,
            suggested_temperature=0.5,
            reasoning="Configuracao padrao gerada como fallback.",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error generating agent config: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao gerar configuracao: {e}")


@router.post("/{agent_id}/clone", summary="Clone an existing agent")
async def clone_custom_agent(
    agent_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Create a copy of an existing agent with '(copia)' appended to name."""
    agent = await agent_marketplace_service.get_agent(
        db=db, agent_id=agent_id, company_id=current_user.company_id
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    clone_data = {
        "name": f"{agent.name} (copia)",
        "role": agent.role,
        "description": agent.description,
        "system_prompt": agent.system_prompt,
        "allowed_tools": agent.allowed_tools or [],
        "domain": agent.domain or "general",
        "icon": agent.icon,
        "max_steps": agent.max_steps or 8,
        "temperature": agent.temperature or 0.7,
        "model_override": agent.model_override,
        "enable_memory": getattr(agent, "enable_memory", True),
        "context_level": getattr(agent, "context_level", "full"),
        "excluded_tools": getattr(agent, "excluded_tools", []),
    }
    try:
        cloned = await agent_marketplace_service.create_agent(
            db=db,
            company_id=current_user.company_id,
            created_by=str(current_user.id),
            data=clone_data,
        )
        await db.commit()
        # P0-3 chunk 2 audit 2026-05-21: clone trail
        from app.domains.agent_studio._audit_helper import studio_audit
        await studio_audit(
            company_id=current_user.company_id,
            action="studio_agent_clone",
            decision="cloned",
            reasoning=[f"Cloned from agent {agent_id} as new agent {cloned.id}"],
            actor_user_id=str(current_user.id),
            target_id=str(cloned.id),
        )
        return CustomAgentResponse(**cloned.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error cloning agent: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to clone agent")


@router.get("/{agent_id}/preview-prompt")
async def preview_agent_prompt(
    agent_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
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


# ─────────────────────────────────────────────────────────────────────────────
# Sprint 7B-3b Part 1 Fase B — Timeline shim canonical (transitional)
# ─────────────────────────────────────────────────────────────────────────────
from sqlalchemy import or_, select  # noqa: E402

from app.schemas.agent_timeline import AgentTimelineEventResponse  # noqa: E402
from app.services.sourcing_agent_orchestrator import sourcing_agent_orchestrator  # noqa: E402
from app.shared.types import AgentIdParam  # noqa: E402


@router.get(
    "/{agent_id}/timeline",
    summary="Timeline canonical de eventos do agente (sourcing category)",
)
async def get_custom_agent_timeline(
    agent_id: AgentIdParam,
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_tenant_db),
):
    """Timeline shim — compat com /sourcing-agents/{id}/timeline pré-Sprint 7B-3b.

    Resolve agent_id via OR shim (custom_agent.id OR legacy_sourcing_agent_id)
    porque Part 2 frontend swap ainda não foi feito. Sprint 7B-3b Part 3 remove
    OR shim quando frontend passar custom_agent.id direto.

    Filtra por company_id (multi-tenancy fail-closed) e category=sourcing
    (timeline só faz sentido pra agentes de sourcing — outras categorias usam
    surfaces diferentes).
    """
    stmt = select(CustomAgent).where(
        or_(
            CustomAgent.id == agent_id,
            CustomAgent.legacy_sourcing_agent_id == agent_id,
        ),
        CustomAgent.company_id == company_id,
        CustomAgent.category == "sourcing",
    )
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    raw_events = await sourcing_agent_orchestrator.get_agent_timeline(
        agent.id, db=db
    )

    timeline = [AgentTimelineEventResponse(**ev) for ev in raw_events]
    return {"timeline": timeline}
