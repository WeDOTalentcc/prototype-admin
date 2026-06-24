"""
ATS-Fairness Policy API — REST endpoints for policy management.

Endpoints:
  GET  /fairness-policies           — list rules
  POST /fairness-policies           — create draft rule
  POST /fairness-policies/{id}/publish — publish draft
  POST /fairness-activations        — activate rule for domain
  GET  /fairness-effective-policy   — resolve effective policy (debug)
  GET  /fairness-violations         — list violations (tenant)
  POST /fairness-policies/seed-defaults — seed DEFAULT_PLATFORM_GENERAL_RULES

Compliance: LGPD Art.6/11 + EU AI Act Annex III item 4
"""
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/fairness", tags=["fairness-policies"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class FairnessRuleCreate(BaseModel):
    scope: str
    domain: str | None = None
    rule_type: str
    is_locked: bool = True
    body_json: dict
    description: str | None = None

    model_config = {"extra": "forbid"}


class FairnessActivationCreate(BaseModel):
    rule_id: str
    domain: str

    model_config = {"extra": "forbid"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_admin_or_platform(current_user: Any, allow_tenant: bool = False) -> None:
    role = getattr(current_user, "role", None) or ""
    if role == "wedotalent_admin":
        return
    if allow_tenant and role in ("tenant_admin", "recruiter"):
        return
    raise HTTPException(status_code=403, detail="Permissão insuficiente para gerenciar políticas de fairness")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/fairness-policies")
async def list_fairness_policies(
    scope: str | None = Query(None),
    domain: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_active_user),
):
    """List fairness policy rules. Platform admin sees all; tenant admin sees own + platform."""
    _require_admin_or_platform(current_user, allow_tenant=True)
    from sqlalchemy import select
    from lia_models.fairness_policies import FairnessPolicyRule

    stmt = select(FairnessPolicyRule)
    role = getattr(current_user, "role", "")
    if role != "wedotalent_admin":
        company_id = getattr(current_user, "company_id", None)
        from sqlalchemy import or_
        stmt = stmt.where(
            or_(
                FairnessPolicyRule.company_id.is_(None),
                FairnessPolicyRule.company_id == company_id,
            )
        )
    if scope:
        stmt = stmt.where(FairnessPolicyRule.scope == scope)
    if domain:
        stmt = stmt.where(FairnessPolicyRule.domain == domain)

    rows = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": str(r.id),
            "scope": r.scope,
            "domain": r.domain,
            "rule_type": r.rule_type,
            "status": r.status,
            "is_locked": r.is_locked,
            "description": r.description,
            "body_json": r.body_json,
            "version": r.version,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.post("/fairness-policies", status_code=201)
async def create_fairness_policy(
    payload: FairnessRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_active_user),
):
    """Create a draft fairness policy rule."""
    role = getattr(current_user, "role", "")
    company_id = getattr(current_user, "company_id", None)

    # Platform scope requires platform admin
    if payload.scope in ("platform_general", "platform_domain") and role != "wedotalent_admin":
        raise HTTPException(403, "Apenas wedotalent_admin pode criar regras de plataforma")

    _require_admin_or_platform(current_user, allow_tenant=True)

    from lia_models.fairness_policies import FairnessPolicyRule

    rule_company_id = None
    if payload.scope == "tenant":
        rule_company_id = company_id

    rule = FairnessPolicyRule(
        id=uuid.uuid4(),
        company_id=rule_company_id,
        scope=payload.scope,
        domain=payload.domain,
        rule_type=payload.rule_type,
        is_locked=payload.is_locked,
        body_json=payload.body_json,
        description=payload.description,
        status="draft",
        version=1,
        created_by=getattr(current_user, "id", None),
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)

    logger.info(
        "[FairnessPolicies] Created rule %s scope=%s rule_type=%s by user=%s",
        rule.id, rule.scope, rule.rule_type, current_user.id,
    )
    return {"id": str(rule.id), "status": rule.status}


@router.post("/fairness-policies/{rule_id}/publish")
async def publish_fairness_policy(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_active_user),
):
    """Promote a draft rule to published status. Platform admin only."""
    _require_admin_or_platform(current_user, allow_tenant=False)
    from sqlalchemy import select
    from lia_models.fairness_policies import FairnessPolicyRule

    stmt = select(FairnessPolicyRule).where(FairnessPolicyRule.id == uuid.UUID(rule_id))
    rule = (await db.execute(stmt)).scalar_one_or_none()
    if not rule:
        raise HTTPException(404, f"Regra {rule_id} não encontrada")
    if rule.status != "draft":
        raise HTTPException(400, f"Apenas regras em status 'draft' podem ser publicadas (atual: {rule.status})")

    rule.status = "published"
    await db.commit()

    logger.info("[FairnessPolicies] Published rule %s by user=%s", rule_id, current_user.id)
    return {"id": rule_id, "status": "published"}


@router.post("/fairness-activations", status_code=201)
async def create_fairness_activation(
    payload: FairnessActivationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_active_user),
):
    """Activate a published fairness rule for a domain."""
    _require_admin_or_platform(current_user, allow_tenant=True)
    from sqlalchemy import select
    from lia_models.fairness_policies import FairnessPolicyRule, FairnessPolicyActivation

    # Verify rule exists and is published
    stmt = select(FairnessPolicyRule).where(FairnessPolicyRule.id == uuid.UUID(payload.rule_id))
    rule = (await db.execute(stmt)).scalar_one_or_none()
    if not rule:
        raise HTTPException(404, f"Regra {payload.rule_id} não encontrada")
    if rule.status not in ("published", "active"):
        raise HTTPException(400, "Apenas regras publicadas podem ser ativadas")

    company_id = getattr(current_user, "company_id", None)
    activation = FairnessPolicyActivation(
        id=uuid.uuid4(),
        company_id=company_id,
        domain=payload.domain,
        rule_id=uuid.UUID(payload.rule_id),
        activated_by=getattr(current_user, "id", None),
        is_current=True,
    )
    db.add(activation)
    await db.commit()

    return {"id": str(activation.id), "is_current": True}


@router.get("/fairness-effective-policy")
async def get_effective_policy(
    domain: str = Query(..., description="Domínio alvo, ex: screening"),
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_active_user),
):
    """Returns the composed effective fairness policy for the current tenant and domain."""
    _require_admin_or_platform(current_user, allow_tenant=True)
    company_id = str(getattr(current_user, "company_id", None) or "")

    from app.shared.compliance.fairness_policy_service import FairnessPolicyService
    service = FairnessPolicyService()
    policy = await service.load_effective_policy(company_id or None, domain, db)
    return {"domain": domain, "tenant_id": company_id, "effective_policy": policy}


@router.get("/fairness-violations")
async def list_fairness_violations(
    domain: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_active_user),
):
    """List fairness violations for the current tenant."""
    _require_admin_or_platform(current_user, allow_tenant=True)
    from sqlalchemy import select
    from lia_models.fairness_policies import FairnessPolicyViolation

    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        raise HTTPException(400, "company_id requerido")

    stmt = select(FairnessPolicyViolation).where(
        FairnessPolicyViolation.company_id == company_id
    )
    if domain:
        stmt = stmt.where(FairnessPolicyViolation.domain == domain)
    stmt = stmt.order_by(FairnessPolicyViolation.detected_at.desc()).offset(offset).limit(limit)

    rows = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": str(v.id),
            "domain": v.domain,
            "rule_type": v.rule_type,
            "violation_type": v.violation_type,
            "was_blocked": v.was_blocked,
            "detected_at": v.detected_at.isoformat() if v.detected_at else None,
            "correlation_id": v.correlation_id,
        }
        for v in rows
    ]


@router.post("/fairness-policies/seed-defaults", status_code=201)
async def seed_default_rules(
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_active_user),
):
    """Seed DEFAULT_PLATFORM_GENERAL_RULES. wedotalent_admin only."""
    role = getattr(current_user, "role", "")
    if role != "wedotalent_admin":
        raise HTTPException(403, "Apenas wedotalent_admin pode fazer seed de regras padrão")

    from lia_models.fairness_policies import FairnessPolicyRule, DEFAULT_PLATFORM_GENERAL_RULES

    created = 0
    for rule_def in DEFAULT_PLATFORM_GENERAL_RULES:
        rule = FairnessPolicyRule(
            id=uuid.uuid4(),
            company_id=None,
            scope=rule_def["scope"],
            domain=rule_def.get("domain"),
            rule_type=rule_def["rule_type"],
            is_locked=rule_def.get("is_locked", True),
            body_json=rule_def["body_json"],
            description=rule_def.get("description"),
            status="published",
            version=1,
            created_by=getattr(current_user, "id", None),
        )
        db.add(rule)
        created += 1

    await db.commit()
    logger.info("[FairnessPolicies] Seeded %d default rules by user=%s", created, current_user.id)
    return {"seeded": created}
