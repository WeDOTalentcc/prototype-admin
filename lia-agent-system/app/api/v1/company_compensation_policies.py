"""
Company Compensation Policies API — Políticas de Remuneração Variável (PRV).

Schema: 1:1 com Rails canonical (23 colunas) + updated_by (auditabilidade).
Multi-tenancy: company_id scoped via JWT + RLS no DB.

LGPD/Fairness:
- approved_by / created_by / updated_by armazenados como user_id (UUID-like string).
- Elegibilidade por atributo protegido BLOQUEADA (fairness guard computacional).
- // TODO(LGPD:001) — masking de approved_by em logs de offer (Fase 4).
- // TODO(FAIRNESS:001) — validador de termos discriminatórios em applicable_*[]
  implementado neste arquivo (CLAUDE.md non-negotiable rule #3).
- // TODO(WIZARD-INT:001) — Wizard LIA consultar policies por seniority/dept da vaga.

Refs:
- Plan: ~/.claude/plans/vams-conectar-ao-replit-effervescent-fairy.md (Fase 2.4)
- Best practices: docs/COMPENSATION_BEST_PRACTICES.md
- Rails canonical: ats-api-copia/db/migrate/20250715000009_create_compensation_policies.rb (READ-ONLY)
"""
import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import (
    get_current_user_or_demo,
    get_user_company_id,
    validate_company_access,
)
from app.auth.models import User
from app.core.database import get_db, get_tenant_db
from app.domains.company.repositories.compensation_policy_repository import (
    CompensationPolicyRepository,
)
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match

router = APIRouter(
    prefix="/company/compensation-policies", tags=["compensation-policies"]
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Fairness guard — CLAUDE.md non-negotiable rule #3
# Elegibilidade de PRV NÃO pode usar atributo protegido.
# ---------------------------------------------------------------------------
PROHIBITED_ELIGIBILITY_TERMS = frozenset({
    # PT-BR
    "raca", "raça", "genero", "gênero", "religiao", "religião", "etnia",
    "estado_civil", "estado civil", "casado", "solteiro", "divorciado",
    "idade", "anos", "menor_de", "maior_de", "jovem", "idoso",
    "saude", "saúde", "doenca", "doença", "deficiencia", "deficiência",
    "gravidez", "gestante", "maternidade",
    "homem", "mulher", "masculino", "feminino", "lgbt", "lgbtqia",
    "branco", "negro", "pardo", "amarelo", "indigena", "indígena",
    "catolico", "evangelico", "judeu", "muculmano", "ateu",
    # EN
    "race", "gender", "religion", "ethnicity", "marital", "single", "married",
    "age", "elderly", "young", "youth",
    "health", "disease", "disability", "pregnancy", "pregnant", "maternity",
    "male", "female", "white", "black", "asian", "hispanic",
})


def _check_prv_fairness(values: list[str] | None, field_name: str) -> None:
    """Raise ValueError se algum termo for atributo protegido. Computacional, fail-loud."""
    if not values:
        return
    for v in values:
        normalized = str(v).lower().strip()
        for prohibited in PROHIBITED_ELIGIBILITY_TERMS:
            if prohibited in normalized:
                raise ValueError(
                    f"Termo discriminatório detectado em {field_name}: '{v}'. "
                    f"Políticas de remuneração NÃO podem ter elegibilidade por atributo "
                    f"protegido (raça, gênero, idade, religião, etnia, estado civil, "
                    f"saúde, deficiência, gravidez). LGPD + non-negotiable rule (CLAUDE.md). "
                    f"Use critérios neutros: cargo, senioridade, departamento, tipo de contrato."
                )


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class CompensationPolicyBase(BaseModel):
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    policy_type: str | None = None  # hierarchical_bands | mixed | variable_only
    currency: str | None = Field(None, max_length=10)

    # Estrutura jsonb
    salary_bands: list[dict] | None = Field(default_factory=list)
    bonus_structure: dict[str, Any] | None = Field(default_factory=dict)
    equity_rules: dict[str, Any] | None = Field(default_factory=dict)
    benefits_package: dict[str, Any] | None = Field(default_factory=dict)
    variable_compensation: dict[str, Any] | None = Field(default_factory=dict)

    # Elegibilidade (arrays)
    applicable_departments: list[str] | None = Field(default_factory=list)
    applicable_seniority: list[str] | None = Field(default_factory=list)
    applicable_roles: list[str] | None = Field(default_factory=list)

    # Estado
    is_active: bool | None = True
    is_default: bool | None = False

    # Vigência + Aprovação
    effective_from: str | None = None
    effective_until: str | None = None
    approved_by: str | None = None  # user_id — // TODO(LGPD:001) maskar em logs
    approved_at: str | None = None


class CompensationPolicyCreate(CompensationPolicyBase):
    """Create exige `name`. Valida fairness em elegibilidade."""

    name: str = Field(..., min_length=1, max_length=255)

    @field_validator("applicable_departments", "applicable_seniority", "applicable_roles")
    @classmethod
    def _no_discriminatory_terms(
        cls, v: list[str] | None, info
    ) -> list[str] | None:
        _check_prv_fairness(v, info.field_name)
        return v

    @model_validator(mode="after")
    def _validate_variable_compensation_kinds(self) -> "CompensationPolicyCreate":
        vc = self.variable_compensation or {}
        items = vc.get("items", [])
        valid_kinds = {"plr", "ppr", "bonus", "commission", "spot_bonus", "equity"}
        for item in items:
            kind = item.get("kind", "")
            if not kind or kind not in valid_kinds:
                raise ValueError(
                    f"variable_compensation item kind inválido: '{kind}'. "
                    f"Válidos: {sorted(valid_kinds)}."
                )
        return self


class CompensationPolicyUpdate(CompensationPolicyBase):
    """Update parcial. Fairness guard aplicado nos campos de elegibilidade."""

    @field_validator("applicable_departments", "applicable_seniority", "applicable_roles")
    @classmethod
    def _no_discriminatory_terms(
        cls, v: list[str] | None, info
    ) -> list[str] | None:
        _check_prv_fairness(v, info.field_name)
        return v


class CompensationPolicyResponse(BaseModel):
    id: str
    company_id: str

    name: str
    description: str | None = None
    policy_type: str | None = None
    currency: str = "BRL"

    salary_bands: list[dict] = Field(default_factory=list)
    bonus_structure: dict[str, Any] = Field(default_factory=dict)
    equity_rules: dict[str, Any] = Field(default_factory=dict)
    benefits_package: dict[str, Any] = Field(default_factory=dict)
    variable_compensation: dict[str, Any] = Field(default_factory=dict)

    applicable_departments: list[str] = Field(default_factory=list)
    applicable_seniority: list[str] = Field(default_factory=list)
    applicable_roles: list[str] = Field(default_factory=list)

    is_active: bool = True
    is_default: bool = False

    effective_from: str | None = None
    effective_until: str | None = None
    approved_by: str | None = None
    approved_at: str | None = None

    version: int = 1
    revision_history: list[dict] = Field(default_factory=list)
    created_by: str | None = None
    updated_by: str | None = None

    created_at: str | None = None
    updated_at: str | None = None

    class Config:
        from_attributes = True


def _to_response(p) -> CompensationPolicyResponse:
    def _dt(v) -> str | None:
        return v.isoformat() if v else None

    return CompensationPolicyResponse(
        id=str(p.id),
        company_id=str(p.company_id),
        name=p.name,
        description=p.description,
        policy_type=p.policy_type,
        currency=p.currency or "BRL",
        salary_bands=p.salary_bands or [],
        bonus_structure=p.bonus_structure or {},
        equity_rules=p.equity_rules or {},
        benefits_package=p.benefits_package or {},
        variable_compensation=p.variable_compensation or {},
        applicable_departments=p.applicable_departments or [],
        applicable_seniority=p.applicable_seniority or [],
        applicable_roles=p.applicable_roles or [],
        is_active=p.is_active,
        is_default=p.is_default,
        effective_from=_dt(p.effective_from),
        effective_until=_dt(p.effective_until),
        approved_by=p.approved_by,
        approved_at=_dt(p.approved_at),
        version=p.version or 1,
        revision_history=p.revision_history or [],
        created_by=p.created_by,
        updated_by=p.updated_by,
        created_at=_dt(p.created_at),
        updated_at=_dt(p.updated_at),
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/", response_model=list[CompensationPolicyResponse])
async def list_policies(
    company_id: str | None = Query(None),
    policy_type: str | None = Query(None),
    active_only: bool = Query(True),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
gated_company_id: str = Depends(require_company_id_strict_match("query.company_id"))):
    """List PRV policies for a company."""
    try:
        effective_company_id = gated_company_id  # canonical client_account_id from JWT gate (auto-resolves company_profile_id) — same fix pattern as company_benefits.py
        validate_company_access(current_user, effective_company_id)
        repo = CompensationPolicyRepository(db)
        policies = await repo.list_for_company(
            effective_company_id,
            active_only=active_only,
            policy_type=policy_type,
            search=search,
        )
        return [_to_response(p) for p in policies]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing compensation policies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=CompensationPolicyResponse)
async def create_policy(
    policy: CompensationPolicyCreate,
    company_id: str | None = Query(None),
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_demo),
gated_company_id: str = Depends(require_company_id_strict_match("query.company_id"))):
    """Create a new PRV policy."""
    try:
        effective_company_id = gated_company_id  # canonical client_account_id from JWT gate (auto-resolves company_profile_id) — same fix pattern as company_benefits.py
        validate_company_access(current_user, effective_company_id)
        repo = CompensationPolicyRepository(db)
        created_by = getattr(current_user, "id", None) or getattr(
            current_user, "email", None
        )
        new_policy = await repo.create(
            effective_company_id,
            policy.model_dump(exclude_none=False),
            created_by=str(created_by) if created_by else None,
        )
        await db.commit()
        logger.info(
            f"Created compensation policy: {new_policy.name} "
            f"for company: {effective_company_id}"
        )
        return _to_response(new_policy)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating compensation policy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{policy_id}", response_model=CompensationPolicyResponse)
async def get_policy(
    policy_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get a specific PRV policy by ID."""
    try:
        repo = CompensationPolicyRepository(db)
        policy = await repo.get_by_id(policy_id)
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        validate_company_access(current_user, str(policy.company_id))
        return _to_response(policy)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting compensation policy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{policy_id}", response_model=CompensationPolicyResponse)
async def update_policy(
    policy_id: UUID,
    updates: CompensationPolicyUpdate,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Update a PRV policy (auto-increments version + appends revision_history)."""
    try:
        repo = CompensationPolicyRepository(db)
        policy = await repo.get_by_id(policy_id)
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        validate_company_access(current_user, str(policy.company_id))
        updated_by = getattr(current_user, "id", None) or getattr(
            current_user, "email", None
        )
        policy = await repo.update(
            policy,
            updates.model_dump(exclude_unset=True),
            updated_by=str(updated_by) if updated_by else None,
        )
        await db.commit()
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Updated compensation policy: {policy.name} v{policy.version}")
        return _to_response(policy)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating compensation policy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{policy_id}", response_model=None)
async def delete_policy(
    policy_id: UUID,
    hard_delete: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Deactivate (soft) or permanently delete a PRV policy."""
    try:
        repo = CompensationPolicyRepository(db)
        policy = await repo.get_by_id(policy_id)
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        validate_company_access(current_user, str(policy.company_id))
        updated_by = getattr(current_user, "id", None) or getattr(
            current_user, "email", None
        )
        if hard_delete:
            await repo.hard_delete(policy)
            message = f"Policy '{policy.name}' permanently deleted"
        else:
            await repo.deactivate(
                policy, updated_by=str(updated_by) if updated_by else None
            )
            message = f"Policy '{policy.name}' deactivated"
        await db.commit()
        logger.info(message)
        return {"success": True, "message": message}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting compensation policy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/seed-defaults", response_model=None)
async def seed_default_policies(
    company_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
gated_company_id: str = Depends(require_company_id_strict_match("query.company_id"))):
    """Seed PLR Anual Padrão + Bônus Comercial templates for a new company."""
    try:
        effective_company_id = gated_company_id  # canonical client_account_id from JWT gate (auto-resolves company_profile_id) — same fix pattern as company_benefits.py
        validate_company_access(current_user, effective_company_id)
        repo = CompensationPolicyRepository(db)
        existing = await repo.count_for_company(effective_company_id)
        if existing > 0:
            return {
                "success": True,
                "message": f"Policies already exist ({existing} policies)",
                "created": 0,
                "total": existing,
            }
        created_by = getattr(current_user, "id", None) or getattr(
            current_user, "email", None
        )
        created_count = await repo.seed_defaults(
            effective_company_id,
            created_by=str(created_by) if created_by else None,
        )
        await db.commit()
        logger.info(
            f"Seeded {created_count} default policies for company: {effective_company_id}"
        )
        return {
            "success": True,
            "message": f"Seeded {created_count} default PRV policies",
            "created": created_count,
            "total": created_count,
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error seeding default policies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/policy-types/list", response_model=None)
async def list_policy_types(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List available PRV policy types."""
    return [
        {
            "id": "hierarchical_bands",
            "name": "Bandas Salariais Hierárquicas",
            "description": "Bandas Min/Mid/Max por nível de senioridade",
        },
        {
            "id": "variable_only",
            "name": "Remuneração Variável Pura",
            "description": "PLR, PPR, Bônus, Comissão — sem bandas fixas",
        },
        {
            "id": "mixed",
            "name": "Misto (Bandas + Variável)",
            "description": "Bandas salariais + verbas variáveis",
        },
    ]
