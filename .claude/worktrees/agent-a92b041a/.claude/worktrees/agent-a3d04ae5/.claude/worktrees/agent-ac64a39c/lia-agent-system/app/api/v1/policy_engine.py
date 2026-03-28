"""
Policy Engine API Endpoints.

Provides endpoints for:
- Listing and managing business rules
- Listing and managing rate limit rules
- Listing and managing escalation rules
- Evaluating policies
- Seeding default rules
"""
from fastapi import APIRouter, HTTPException, Query, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from typing import Optional, List
from datetime import datetime
import logging
from uuid import UUID

from app.core.database import get_db
from app.models.policy import (
    BusinessRule, RateLimitRule, EscalationRule,
    PolicyEvaluationLog, EscalationLog
)
from app.schemas.policy import (
    BusinessRuleCreate, BusinessRuleUpdate, BusinessRuleResponse,
    RateLimitRuleCreate, RateLimitRuleUpdate, RateLimitRuleResponse,
    EscalationRuleCreate, EscalationRuleUpdate, EscalationRuleResponse,
    PolicyEvaluateRequest, PolicyEvaluateResponse,
    RateLimitCheckRequest, RateLimitCheckResponse,
    EscalationTriggerRequest, EscalationTriggerResponse,
    PolicyListResponse, PolicySeedResponse,
    PolicyEvaluationLogResponse, EscalationLogResponse,
    PolicyEvaluationResultEnum
)
from app.services.policy_engine_service import PolicyEngineService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/policy-engine", tags=["policy-engine"])


def get_company_id_from_header(
    x_company_id: Optional[str] = Header(None, alias="X-Company-ID")
) -> Optional[str]:
    """Extract company ID from header if present."""
    if x_company_id:
        try:
            UUID(x_company_id)
            return x_company_id
        except ValueError:
            pass
    return None


def get_user_id_from_header(
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> Optional[str]:
    """Extract user ID from header if present."""
    if x_user_id:
        try:
            UUID(x_user_id)
            return x_user_id
        except ValueError:
            pass
    return None


@router.get("", response_model=PolicyListResponse, summary="List all policies")
async def list_policies(
    rule_type: Optional[str] = Query(None, description="Filter business rules by type"),
    target_type: Optional[str] = Query(None, description="Filter rate limit rules by target type"),
    trigger_type: Optional[str] = Query(None, description="Filter escalation rules by trigger type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    company_id: Optional[str] = Depends(get_company_id_from_header),
    db: AsyncSession = Depends(get_db)
):
    """List all policy rules (business, rate limit, escalation)."""
    try:
        business_conditions = [BusinessRule.is_active == True] if is_active is None else [BusinessRule.is_active == is_active]
        if rule_type:
            business_conditions.append(BusinessRule.rule_type == rule_type)
        if company_id:
            business_conditions.append(
                or_(BusinessRule.company_id == None, BusinessRule.company_id == UUID(company_id))
            )
        
        business_query = select(BusinessRule).where(and_(*business_conditions)).order_by(BusinessRule.priority.asc())
        business_result = await db.execute(business_query)
        business_rules = business_result.scalars().all()
        
        rate_conditions = [RateLimitRule.is_active == True] if is_active is None else [RateLimitRule.is_active == is_active]
        if target_type:
            rate_conditions.append(RateLimitRule.target_type == target_type)
        if company_id:
            rate_conditions.append(
                or_(RateLimitRule.company_id == None, RateLimitRule.company_id == UUID(company_id))
            )
        
        rate_query = select(RateLimitRule).where(and_(*rate_conditions))
        rate_result = await db.execute(rate_query)
        rate_limit_rules = rate_result.scalars().all()
        
        esc_conditions = [EscalationRule.is_active == True] if is_active is None else [EscalationRule.is_active == is_active]
        if trigger_type:
            esc_conditions.append(EscalationRule.trigger_type == trigger_type)
        if company_id:
            esc_conditions.append(
                or_(EscalationRule.company_id == None, EscalationRule.company_id == UUID(company_id))
            )
        
        esc_query = select(EscalationRule).where(and_(*esc_conditions)).order_by(EscalationRule.priority.asc())
        esc_result = await db.execute(esc_query)
        escalation_rules = esc_result.scalars().all()
        
        return PolicyListResponse(
            business_rules=[BusinessRuleResponse(**r.to_dict()) for r in business_rules],
            rate_limit_rules=[RateLimitRuleResponse(**r.to_dict()) for r in rate_limit_rules],
            escalation_rules=[EscalationRuleResponse(**r.to_dict()) for r in escalation_rules],
            total_business_rules=len(business_rules),
            total_rate_limit_rules=len(rate_limit_rules),
            total_escalation_rules=len(escalation_rules)
        )
    except Exception as e:
        logger.error(f"Error listing policies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/business-rules", response_model=BusinessRuleResponse, summary="Create business rule")
async def create_business_rule(
    data: BusinessRuleCreate,
    company_id: Optional[str] = Depends(get_company_id_from_header),
    user_id: Optional[str] = Depends(get_user_id_from_header),
    db: AsyncSession = Depends(get_db)
):
    """Create a new business rule."""
    try:
        rule = BusinessRule(
            company_id=UUID(data.company_id or company_id) if (data.company_id or company_id) else None,
            name=data.name,
            description=data.description,
            rule_type=data.rule_type.value,
            conditions=data.conditions,
            actions=data.actions,
            priority=data.priority,
            approval_config=data.approval_config,
            is_active=data.is_active,
            rule_metadata=data.rule_metadata,
            created_by=UUID(user_id) if user_id else None
        )
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        
        return BusinessRuleResponse(**rule.to_dict())
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating business rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/business-rules/{rule_id}", response_model=BusinessRuleResponse, summary="Get business rule")
async def get_business_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific business rule."""
    try:
        rule_uuid = UUID(rule_id)
        query = select(BusinessRule).where(BusinessRule.id == rule_uuid)
        result = await db.execute(query)
        rule = result.scalar_one_or_none()
        
        if not rule:
            raise HTTPException(status_code=404, detail="Business rule not found")
        
        return BusinessRuleResponse(**rule.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid rule ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting business rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/business-rules/{rule_id}", response_model=BusinessRuleResponse, summary="Update business rule")
async def update_business_rule(
    rule_id: str,
    data: BusinessRuleUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a business rule."""
    try:
        rule_uuid = UUID(rule_id)
        query = select(BusinessRule).where(BusinessRule.id == rule_uuid)
        result = await db.execute(query)
        rule = result.scalar_one_or_none()
        
        if not rule:
            raise HTTPException(status_code=404, detail="Business rule not found")
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "rule_type" and value:
                value = value.value
            setattr(rule, field, value)
        
        await db.commit()
        await db.refresh(rule)
        
        return BusinessRuleResponse(**rule.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid rule ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating business rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/business-rules/{rule_id}", summary="Delete business rule")
async def delete_business_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a business rule."""
    try:
        rule_uuid = UUID(rule_id)
        query = select(BusinessRule).where(BusinessRule.id == rule_uuid)
        result = await db.execute(query)
        rule = result.scalar_one_or_none()
        
        if not rule:
            raise HTTPException(status_code=404, detail="Business rule not found")
        
        await db.delete(rule)
        await db.commit()
        
        return {"message": "Business rule deleted successfully"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid rule ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting business rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rate-limit-rules", response_model=RateLimitRuleResponse, summary="Create rate limit rule")
async def create_rate_limit_rule(
    data: RateLimitRuleCreate,
    company_id: Optional[str] = Depends(get_company_id_from_header),
    db: AsyncSession = Depends(get_db)
):
    """Create a new rate limit rule."""
    try:
        rule = RateLimitRule(
            company_id=UUID(data.company_id or company_id) if (data.company_id or company_id) else None,
            name=data.name,
            description=data.description,
            target_type=data.target_type.value,
            target_id=data.target_id,
            action_pattern=data.action_pattern,
            limit_value=data.limit_value,
            window_seconds=data.window_seconds,
            burst_limit=data.burst_limit,
            is_active=data.is_active
        )
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        
        return RateLimitRuleResponse(**rule.to_dict())
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating rate limit rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/rate-limit-rules/{rule_id}", response_model=RateLimitRuleResponse, summary="Update rate limit rule")
async def update_rate_limit_rule(
    rule_id: str,
    data: RateLimitRuleUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a rate limit rule."""
    try:
        rule_uuid = UUID(rule_id)
        query = select(RateLimitRule).where(RateLimitRule.id == rule_uuid)
        result = await db.execute(query)
        rule = result.scalar_one_or_none()
        
        if not rule:
            raise HTTPException(status_code=404, detail="Rate limit rule not found")
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "target_type" and value:
                value = value.value
            setattr(rule, field, value)
        
        await db.commit()
        await db.refresh(rule)
        
        return RateLimitRuleResponse(**rule.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid rule ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating rate limit rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/escalation-rules", response_model=EscalationRuleResponse, summary="Create escalation rule")
async def create_escalation_rule(
    data: EscalationRuleCreate,
    company_id: Optional[str] = Depends(get_company_id_from_header),
    db: AsyncSession = Depends(get_db)
):
    """Create a new escalation rule."""
    try:
        rule = EscalationRule(
            company_id=UUID(data.company_id or company_id) if (data.company_id or company_id) else None,
            name=data.name,
            description=data.description,
            trigger_type=data.trigger_type.value,
            condition=data.condition,
            escalate_to=data.escalate_to,
            escalation_action=data.escalation_action.value,
            notification_template=data.notification_template,
            cooldown_seconds=data.cooldown_seconds,
            priority=data.priority,
            is_active=data.is_active
        )
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        
        return EscalationRuleResponse(**rule.to_dict())
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating escalation rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/escalation-rules/{rule_id}", response_model=EscalationRuleResponse, summary="Update escalation rule")
async def update_escalation_rule(
    rule_id: str,
    data: EscalationRuleUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an escalation rule."""
    try:
        rule_uuid = UUID(rule_id)
        query = select(EscalationRule).where(EscalationRule.id == rule_uuid)
        result = await db.execute(query)
        rule = result.scalar_one_or_none()
        
        if not rule:
            raise HTTPException(status_code=404, detail="Escalation rule not found")
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "trigger_type" and value:
                value = value.value
            elif field == "escalation_action" and value:
                value = value.value
            setattr(rule, field, value)
        
        await db.commit()
        await db.refresh(rule)
        
        return EscalationRuleResponse(**rule.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid rule ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating escalation rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate", response_model=PolicyEvaluateResponse, summary="Evaluate policy")
async def evaluate_policy(
    data: PolicyEvaluateRequest,
    company_id: Optional[str] = Depends(get_company_id_from_header),
    user_id: Optional[str] = Depends(get_user_id_from_header)
):
    """Evaluate whether an action is allowed by policies."""
    try:
        service = PolicyEngineService()
        result = await service.evaluate(
            action=data.action,
            context=data.context,
            agent_name=data.agent_name,
            company_id=data.company_id or company_id,
            user_id=data.user_id or user_id,
            check_rate_limit=data.check_rate_limit,
            dry_run=data.dry_run
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
            rules_evaluated=result.rules_evaluated
        )
    except Exception as e:
        logger.error(f"Error evaluating policy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-rate-limit", response_model=RateLimitCheckResponse, summary="Check rate limit")
async def check_rate_limit(
    data: RateLimitCheckRequest,
    company_id: Optional[str] = Depends(get_company_id_from_header)
):
    """Check rate limit for a specific target and action."""
    try:
        service = PolicyEngineService()
        result = await service.check_rate_limit(
            target_type=data.target_type.value,
            target_id=data.target_id,
            action=data.action,
            company_id=data.company_id or company_id,
            increment=data.increment
        )
        
        return RateLimitCheckResponse(**result.to_dict())
    except Exception as e:
        logger.error(f"Error checking rate limit: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger-escalation", response_model=EscalationTriggerResponse, summary="Trigger escalation")
async def trigger_escalation(
    data: EscalationTriggerRequest,
    company_id: Optional[str] = Depends(get_company_id_from_header)
):
    """Trigger an escalation based on a rule or trigger type."""
    try:
        service = PolicyEngineService()
        result = await service.trigger_escalation(
            rule_id=data.rule_id,
            trigger_type=data.trigger_type.value if data.trigger_type else None,
            context=data.context,
            company_id=data.company_id or company_id
        )
        
        return EscalationTriggerResponse(**result.to_dict())
    except Exception as e:
        logger.error(f"Error triggering escalation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/apply-sector/{company_id}",
    summary="Aplica defaults setoriais Alpha 1 para uma empresa",
)
async def apply_sector_defaults(
    company_id: str,
    sector: str = Query(..., description="Setor: tech | varejo | logistica | financeiro | saude | rpo"),
    db: AsyncSession = Depends(get_db),
):
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
            detail=f"Setor '{sector}' não reconhecido. Válidos: {sorted(valid_sectors)}"
        )

    try:
        service = PolicyEngineService()
        result = await service.save_policy_block(
            company_id=company_id,
            sector=sector_key,
            db=db,
        )
        return result
    except Exception as e:
        logger.error(f"Error applying sector defaults for {company_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/seed", response_model=PolicySeedResponse, summary="Seed default policies")
async def seed_default_policies():
    """Seed the database with default policy rules."""
    try:
        service = PolicyEngineService()
        stats = await service.load_default_rules()
        
        total_created = (
            stats["business_rules_created"] +
            stats["rate_limit_rules_created"] +
            stats["escalation_rules_created"]
        )
        total_skipped = (
            stats["business_rules_skipped"] +
            stats["rate_limit_rules_skipped"] +
            stats["escalation_rules_skipped"]
        )
        
        return PolicySeedResponse(
            business_rules_created=stats["business_rules_created"],
            business_rules_skipped=stats["business_rules_skipped"],
            rate_limit_rules_created=stats["rate_limit_rules_created"],
            rate_limit_rules_skipped=stats["rate_limit_rules_skipped"],
            escalation_rules_created=stats["escalation_rules_created"],
            escalation_rules_skipped=stats["escalation_rules_skipped"],
            message=f"Seeded {total_created} rules, skipped {total_skipped} existing rules"
        )
    except Exception as e:
        logger.error(f"Error seeding policies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evaluation-logs", response_model=List[PolicyEvaluationLogResponse], summary="Get evaluation logs")
async def get_evaluation_logs(
    action: Optional[str] = Query(None, description="Filter by action"),
    result: Optional[str] = Query(None, description="Filter by result"),
    agent_name: Optional[str] = Query(None, description="Filter by agent name"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    company_id: Optional[str] = Depends(get_company_id_from_header),
    db: AsyncSession = Depends(get_db)
):
    """Get policy evaluation logs."""
    try:
        conditions = []
        if company_id:
            conditions.append(PolicyEvaluationLog.company_id == UUID(company_id))
        if action:
            conditions.append(PolicyEvaluationLog.action == action)
        if result:
            conditions.append(PolicyEvaluationLog.result == result)
        if agent_name:
            conditions.append(PolicyEvaluationLog.agent_name == agent_name)
        
        query = select(PolicyEvaluationLog)
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(desc(PolicyEvaluationLog.created_at)).limit(limit).offset(offset)
        
        db_result = await db.execute(query)
        logs = db_result.scalars().all()
        
        return [PolicyEvaluationLogResponse(**log.to_dict()) for log in logs]
    except Exception as e:
        logger.error(f"Error getting evaluation logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/escalation-logs", response_model=List[EscalationLogResponse], summary="Get escalation logs")
async def get_escalation_logs(
    resolved: Optional[bool] = Query(None, description="Filter by resolved status"),
    action_taken: Optional[str] = Query(None, description="Filter by action taken"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    company_id: Optional[str] = Depends(get_company_id_from_header),
    db: AsyncSession = Depends(get_db)
):
    """Get escalation logs."""
    try:
        conditions = []
        if company_id:
            conditions.append(EscalationLog.company_id == UUID(company_id))
        if resolved is not None:
            conditions.append(EscalationLog.resolved == resolved)
        if action_taken:
            conditions.append(EscalationLog.action_taken == action_taken)
        
        query = select(EscalationLog)
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(desc(EscalationLog.created_at)).limit(limit).offset(offset)
        
        db_result = await db.execute(query)
        logs = db_result.scalars().all()
        
        return [EscalationLogResponse(**log.to_dict()) for log in logs]
    except Exception as e:
        logger.error(f"Error getting escalation logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/escalation-logs/{log_id}/resolve", summary="Resolve an escalation")
async def resolve_escalation(
    log_id: str,
    resolution_notes: Optional[str] = Query(None, description="Resolution notes"),
    user_id: Optional[str] = Depends(get_user_id_from_header),
    db: AsyncSession = Depends(get_db)
):
    """Mark an escalation as resolved."""
    try:
        log_uuid = UUID(log_id)
        query = select(EscalationLog).where(EscalationLog.id == log_uuid)
        result = await db.execute(query)
        log = result.scalar_one_or_none()
        
        if not log:
            raise HTTPException(status_code=404, detail="Escalation log not found")
        
        log.resolved = True
        log.resolved_at = datetime.utcnow()
        log.resolved_by = UUID(user_id) if user_id else None
        log.resolution_notes = resolution_notes
        
        await db.commit()
        await db.refresh(log)
        
        return {"message": "Escalation resolved successfully", "log": log.to_dict()}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid log ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error resolving escalation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
