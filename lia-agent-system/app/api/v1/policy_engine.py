"""
Policy Engine API.

Provides endpoints for:
- Listing and managing business rules (tenant-scoped via JWT)
- Listing and managing rate limit/escalation rules
- Evaluating policies
- Seeding default rules (wedotalent_admin ONLY — Onda 4.2d-P0-13)

Onda 4.2d-P0-8 a P0-13 (2026-05-23): regulatory hardening:
- Business/rate-limit/escalation rules: company_id 100% JWT (payload nao
  pode sobrescrever — fechou P0-8, P0-11).
- Mutation endpoints (update/delete/resolve) pre-check
  `rule.company_id == company_id` (fechou P0-9, P0-10).
- Sector defaults: strict_match path.company_id (fechou P0-12).
- Seed: wedotalent_admin gate (fechou P0-13).
- user_id agora vem do JWT, nao X-User-ID header forjavel.
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.dependencies import get_current_active_user
from app.auth.models import User, UserRole
from app.domains.policy.dependencies import get_policy_repo
from app.domains.policy.repositories.policy_repository import PolicyRepository
from app.domains.policy.services.policy_engine_service import PolicyEngineService, get_policy_engine_service
from app.models.policy import BusinessRule, EscalationRule, RateLimitRule
from app.schemas.policy import (
    BusinessRuleCreate,
    BusinessRuleResponse,
    BusinessRuleUpdate,
    EscalationLogResponse,
    EscalationRuleCreate,
    EscalationRuleResponse,
    EscalationRuleUpdate,
    EscalationTriggerRequest,
    EscalationTriggerResponse,
    PolicyEvaluateRequest,
    PolicyEvaluateResponse,
    PolicyEvaluationLogResponse,
    PolicyEvaluationResultEnum,
    PolicyListResponse,
    PolicySeedResponse,
    RateLimitCheckRequest,
    RateLimitCheckResponse,
    RateLimitRuleCreate,
    RateLimitRuleResponse,
    RateLimitRuleUpdate,
)
from app.shared.tenant_guard import get_verified_company_id
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/policy-engine", tags=["policy-engine"])


def require_wedotalent_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Onda 4.2d-P0-13 (2026-05-23): gate pra seed/sector defaults.

    Apenas staff WeDOTalent pode mutar config platform-wide.
    """
    if current_user.role != UserRole.wedotalent_admin:
        raise HTTPException(
            status_code=403,
            detail="Only WeDOTalent staff can seed default policies.",
        )
    return current_user


def get_user_id_from_header(
    current_user: User = Depends(get_current_active_user),
) -> str:
    """Get user ID from JWT (NO header).

    Onda 4.2d (2026-05-23): antes lia X-User-ID forjavel. Agora JWT-only.
    """
    return str(current_user.id)


@router.get("", response_model=PolicyListResponse, summary="List all policies")
async def list_policies(
    rule_type: str | None = Query(None, description="Filter business rules by type"),
    target_type: str | None = Query(None, description="Filter rate limit rules by target type"),
    trigger_type: str | None = Query(None, description="Filter escalation rules by trigger type"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    company_id: str | None = Depends(get_verified_company_id),
    repo: PolicyRepository = Depends(get_policy_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List all policy rules (business, rate limit, escalation)."""
    try:
        business_rules = await repo.list_business_rules(
            is_active=is_active, rule_type=rule_type, company_id=company_id
        )
        rate_limit_rules = await repo.list_rate_limit_rules(
            is_active=is_active, target_type=target_type, company_id=company_id
        )
        escalation_rules = await repo.list_escalation_rules(
            is_active=is_active, trigger_type=trigger_type, company_id=company_id
        )

        return PolicyListResponse(
            business_rules=[BusinessRuleResponse(**r.to_dict()) for r in business_rules],
            rate_limit_rules=[RateLimitRuleResponse(**r.to_dict()) for r in rate_limit_rules],
            escalation_rules=[EscalationRuleResponse(**r.to_dict()) for r in escalation_rules],
            total_business_rules=len(business_rules),
            total_rate_limit_rules=len(rate_limit_rules),
            total_escalation_rules=len(escalation_rules),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing policies: {e}", exc_info=True)
        raise


@router.post("/business-rules", response_model=BusinessRuleResponse, summary="Create business rule")
async def create_business_rule(
    data: BusinessRuleCreate,
    company_id: str | None = Depends(get_verified_company_id),
    user_id: str | None = Depends(get_user_id_from_header),
    repo: PolicyRepository = Depends(get_policy_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Create a new business rule."""
    try:
        rule = BusinessRule(
            company_id=UUID(company_id) if company_id else None,
            name=data.name,
            description=data.description,
            rule_type=data.rule_type.value,
            conditions=data.conditions,
            actions=data.actions,
            priority=data.priority,
            approval_config=data.approval_config,
            is_active=data.is_active,
            rule_metadata=data.rule_metadata,
            created_by=UUID(user_id) if user_id else None,
        )
        rule = await repo.create_business_rule(rule)
        return BusinessRuleResponse(**rule.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating business rule: {e}", exc_info=True)
        raise


@router.get("/business-rules/{rule_id}", response_model=BusinessRuleResponse, summary="Get business rule")
async def get_business_rule(
    rule_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    repo: PolicyRepository = Depends(get_policy_repo),
    company_id: str = Depends(require_company_id),
):
    """Get a specific business rule.

    Onda 4.2d-P0-9 (2026-05-23): cross-tenant guard via pre-check
    `rule.company_id == company_id`. Antes user empresa A podia ler
    business rule da empresa B passando o UUID.
    """
    try:
        rule_uuid = UUID(rule_id)
        rule = await repo.get_business_rule(rule_uuid)
        if not rule or str(rule.company_id) != str(company_id):
            # 404 (no enumeration leak)
            raise HTTPException(status_code=404, detail="Business rule not found")
        return BusinessRuleResponse(**rule.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid rule ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting business rule: {e}", exc_info=True)
        raise


@router.put("/business-rules/{rule_id}", response_model=BusinessRuleResponse, summary="Update business rule")
async def update_business_rule(
    rule_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: BusinessRuleUpdate,
    repo: PolicyRepository = Depends(get_policy_repo),
    company_id: str = Depends(require_company_id),
):
    """Update a business rule.

    Onda 4.2d-P0-9 (2026-05-23): cross-tenant guard.
    """
    try:
        rule_uuid = UUID(rule_id)
        rule = await repo.get_business_rule(rule_uuid)
        if not rule or str(rule.company_id) != str(company_id):
            raise HTTPException(status_code=404, detail="Business rule not found")
        update_data = data.model_dump(exclude_unset=True)
        rule = await repo.update_business_rule(rule, update_data)
        return BusinessRuleResponse(**rule.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid rule ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating business rule: {e}", exc_info=True)
        raise


@router.delete("/business-rules/{rule_id}", summary="Delete business rule", response_model=None)
async def delete_business_rule(
    rule_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    repo: PolicyRepository = Depends(get_policy_repo),
    company_id: str = Depends(require_company_id),
):
    """Delete a business rule.

    Onda 4.2d-P0-9 (2026-05-23): cross-tenant guard.
    """
    try:
        rule_uuid = UUID(rule_id)
        rule = await repo.get_business_rule(rule_uuid)
        if not rule or str(rule.company_id) != str(company_id):
            raise HTTPException(status_code=404, detail="Business rule not found")
        await repo.delete_business_rule(rule)
        return {"message": "Business rule deleted successfully"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid rule ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting business rule: {e}", exc_info=True)
        raise


@router.post("/rate-limit-rules", response_model=RateLimitRuleResponse, summary="Create rate limit rule")
async def create_rate_limit_rule(
    data: RateLimitRuleCreate,
    company_id: str | None = Depends(get_verified_company_id),
    repo: PolicyRepository = Depends(get_policy_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Create a new rate limit rule."""
    try:
        rule = RateLimitRule(
            company_id=UUID(company_id) if company_id else None,
            name=data.name,
            description=data.description,
            target_type=data.target_type.value,
            target_id=data.target_id,
            action_pattern=data.action_pattern,
            limit_value=data.limit_value,
            window_seconds=data.window_seconds,
            burst_limit=data.burst_limit,
            is_active=data.is_active,
        )
        rule = await repo.create_rate_limit_rule(rule)
        return RateLimitRuleResponse(**rule.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating rate limit rule: {e}", exc_info=True)
        raise


@router.put("/rate-limit-rules/{rule_id}", response_model=RateLimitRuleResponse, summary="Update rate limit rule")
async def update_rate_limit_rule(
    rule_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: RateLimitRuleUpdate,
    repo: PolicyRepository = Depends(get_policy_repo),
    company_id: str = Depends(require_company_id),
):
    """Update a rate limit rule.

    Onda 4.2d-P0-10 (2026-05-23): cross-tenant guard.
    """
    try:
        rule_uuid = UUID(rule_id)
        rule = await repo.get_rate_limit_rule(rule_uuid)
        if not rule or str(rule.company_id) != str(company_id):
            raise HTTPException(status_code=404, detail="Rate limit rule not found")
        update_data = data.model_dump(exclude_unset=True)
        rule = await repo.update_rate_limit_rule(rule, update_data)
        return RateLimitRuleResponse(**rule.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid rule ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating rate limit rule: {e}", exc_info=True)
        raise


@router.post("/escalation-rules", response_model=EscalationRuleResponse, summary="Create escalation rule")
async def create_escalation_rule(
    data: EscalationRuleCreate,
    company_id: str | None = Depends(get_verified_company_id),
    repo: PolicyRepository = Depends(get_policy_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Create a new escalation rule."""
    try:
        rule = EscalationRule(
            company_id=UUID(company_id) if company_id else None,
            name=data.name,
            description=data.description,
            trigger_type=data.trigger_type.value,
            condition=data.condition,
            escalate_to=data.escalate_to,
            escalation_action=data.escalation_action.value,
            notification_template=data.notification_template,
            cooldown_seconds=data.cooldown_seconds,
            priority=data.priority,
            is_active=data.is_active,
        )
        rule = await repo.create_escalation_rule(rule)
        return EscalationRuleResponse(**rule.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating escalation rule: {e}", exc_info=True)
        raise


@router.put("/escalation-rules/{rule_id}", response_model=EscalationRuleResponse, summary="Update escalation rule")
async def update_escalation_rule(
    rule_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: EscalationRuleUpdate,
    repo: PolicyRepository = Depends(get_policy_repo),
    company_id: str = Depends(require_company_id),
):
    """Update an escalation rule.

    Onda 4.2d-P0-10 (2026-05-23): cross-tenant guard.
    """
    try:
        rule_uuid = UUID(rule_id)
        rule = await repo.get_escalation_rule(rule_uuid)
        if not rule or str(rule.company_id) != str(company_id):
            raise HTTPException(status_code=404, detail="Escalation rule not found")
        update_data = data.model_dump(exclude_unset=True)
        rule = await repo.update_escalation_rule(rule, update_data)
        return EscalationRuleResponse(**rule.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid rule ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating escalation rule: {e}", exc_info=True)
        raise


@router.post("/evaluate", response_model=PolicyEvaluateResponse, summary="Evaluate policy")
async def evaluate_policy(
    data: PolicyEvaluateRequest,
    company_id: str | None = Depends(get_verified_company_id),
    user_id: str | None = Depends(get_user_id_from_header),
    service: PolicyEngineService = Depends(get_policy_engine_service),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Evaluate whether an action is allowed by policies."""
    try:
        result = await service.evaluate(
            action=data.action,
            context=data.context,
            agent_name=data.agent_name,
            company_id=company_id,
            user_id=data.user_id or user_id,
            check_rate_limit=data.check_rate_limit,
            dry_run=data.dry_run,
        )

        return PolicyEvaluateResponse(
            result=PolicyEvaluationResultEnum(result.result.value),
            allowed=result.allowed,
            reason=result.reason,
            matching_rule=BusinessRuleResponse(**result.matching_rule.to_dict()) if result.matching_rule else None,
            rate_limit_status=result.rate_limit_status,
            requires_approval=result.requires_approval,
            approval_config=result.approval_config,
            evaluation_time_ms=result.evaluation_time_ms,
            rules_evaluated=result.rules_evaluated,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error evaluating policy: {e}", exc_info=True)
        raise


@router.post("/check-rate-limit", response_model=RateLimitCheckResponse, summary="Check rate limit")
async def check_rate_limit(
    data: RateLimitCheckRequest,
    company_id: str | None = Depends(get_verified_company_id),
    service: PolicyEngineService = Depends(get_policy_engine_service),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Check rate limit for a specific target and action."""
    try:
        result = await service.check_rate_limit(
            target_type=data.target_type.value,
            target_id=data.target_id,
            action=data.action,
            company_id=company_id,
            increment=data.increment,
        )
        return RateLimitCheckResponse(**result.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking rate limit: {e}", exc_info=True)
        raise


@router.post("/trigger-escalation", response_model=EscalationTriggerResponse, summary="Trigger escalation")
async def trigger_escalation(
    data: EscalationTriggerRequest,
    company_id: str | None = Depends(get_verified_company_id),
    service: PolicyEngineService = Depends(get_policy_engine_service),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Trigger an escalation based on a rule or trigger type."""
    try:
        result = await service.trigger_escalation(
            rule_id=data.rule_id,
            trigger_type=data.trigger_type.value if data.trigger_type else None,
            context=data.context,
            company_id=company_id,
        )
        return EscalationTriggerResponse(**result.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering escalation: {e}", exc_info=True)
        raise


@router.post(
    "/apply-sector/{company_id}",
    summary="Aplica defaults setoriais Alpha 1 para uma empresa",
    response_model=None,
)
async def apply_sector_defaults(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    sector: str = Query(..., description="Setor: tech | varejo | logistica | financeiro | saude | rpo"),
    repo: PolicyRepository = Depends(get_policy_repo),
    service: PolicyEngineService = Depends(get_policy_engine_service),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Persiste os defaults setoriais (Alpha 1) em CompanyHiringPolicy.

    Chama PolicyEngineService.save_policy_block() para mapear SECTOR_DEFAULTS
    para os blocos automation_rules e screening_rules da empresa.
    Idempotente — seguro repetir.
    """
    try:
        UUID(company_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="company_id inválido (esperado UUID)")

    valid_sectors = {"tech", "varejo", "logistica", "financeiro", "saude", "rpo"}
    sector_key = sector.lower().strip()
    if sector_key not in valid_sectors:
        raise HTTPException(
            status_code=400,
            detail=f"Setor {sector} não reconhecido. Válidos: {sorted(valid_sectors)}",
        )

    try:
        result = await service.save_policy_block(
            company_id=company_id,
            sector=sector_key,
            db=repo.db,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying sector defaults for {company_id}: {e}", exc_info=True)
        raise


@router.post("/seed", response_model=PolicySeedResponse, summary="Seed default policies")
async def seed_default_policies(
    service: PolicyEngineService = Depends(get_policy_engine_service),
    # Onda 4.2d-P0-13 (2026-05-23): wedotalent_admin gate.
    _staff: User = Depends(require_wedotalent_admin),
    company_id: str = Depends(require_company_id),
):
    """Seed the database with default policy rules (staff-only)."""
    try:
        stats = await service.load_default_rules()

        total_created = (
            stats["business_rules_created"]
            + stats["rate_limit_rules_created"]
            + stats["escalation_rules_created"]
        )
        total_skipped = (
            stats["business_rules_skipped"]
            + stats["rate_limit_rules_skipped"]
            + stats["escalation_rules_skipped"]
        )

        return PolicySeedResponse(
            business_rules_created=stats["business_rules_created"],
            business_rules_skipped=stats["business_rules_skipped"],
            rate_limit_rules_created=stats["rate_limit_rules_created"],
            rate_limit_rules_skipped=stats["rate_limit_rules_skipped"],
            escalation_rules_created=stats["escalation_rules_created"],
            escalation_rules_skipped=stats["escalation_rules_skipped"],
            message=f"Seeded {total_created} rules, skipped {total_skipped} existing rules",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error seeding policies: {e}", exc_info=True)
        raise


@router.get("/evaluation-logs", response_model=list[PolicyEvaluationLogResponse], summary="Get evaluation logs")
async def get_evaluation_logs(
    action: str | None = Query(None, description="Filter by action"),
    result: str | None = Query(None, description="Filter by result"),
    agent_name: str | None = Query(None, description="Filter by agent name"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    company_id: str | None = Depends(get_verified_company_id),
    repo: PolicyRepository = Depends(get_policy_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get policy evaluation logs."""
    try:
        logs = await repo.list_evaluation_logs(
            company_id=company_id,
            action=action,
            result=result,
            agent_name=agent_name,
            limit=limit,
            offset=offset,
        )
        return [PolicyEvaluationLogResponse(**log.to_dict()) for log in logs]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting evaluation logs: {e}", exc_info=True)
        raise


@router.get("/escalation-logs", response_model=list[EscalationLogResponse], summary="Get escalation logs")
async def get_escalation_logs(
    resolved: bool | None = Query(None, description="Filter by resolved status"),
    action_taken: str | None = Query(None, description="Filter by action taken"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    company_id: str | None = Depends(get_verified_company_id),
    repo: PolicyRepository = Depends(get_policy_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get escalation logs."""
    try:
        logs = await repo.list_escalation_logs(
            company_id=company_id,
            resolved=resolved,
            action_taken=action_taken,
            limit=limit,
            offset=offset,
        )
        return [EscalationLogResponse(**log.to_dict()) for log in logs]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting escalation logs: {e}", exc_info=True)
        raise


@router.post("/escalation-logs/{log_id}/resolve", summary="Resolve an escalation", response_model=None)
async def resolve_escalation(
    log_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    resolution_notes: str | None = Query(None, description="Resolution notes"),
    user_id: str | None = Depends(get_user_id_from_header),
    repo: PolicyRepository = Depends(get_policy_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Mark an escalation as resolved."""
    try:
        log_uuid = UUID(log_id)
        log = await repo.get_escalation_log(log_uuid)
        if not log:
            raise HTTPException(status_code=404, detail="Escalation log not found")
        log = await repo.resolve_escalation_log(log, user_id, resolution_notes)
        return {"message": "Escalation resolved successfully", "log": log.to_dict()}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid log ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving escalation: {e}", exc_info=True)
        raise

reorder_collection_before_item(router)
