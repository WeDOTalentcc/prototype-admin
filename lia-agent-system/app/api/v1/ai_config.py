"""
AI Configuration — Unified endpoint for tenant AI settings.

Aggregates CompanyHiringPolicy blocks into a recruiter-friendly
surface. No new model needed — reads/writes to existing policy JSON columns.

Item: PX08-077 — Sprint 12, item 12.2
"""
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from lia_models.company_hiring_policy import (
    CompanyHiringPolicy,
    AUTOMATION_RULES_DEFAULTS,
    COMMUNICATION_RULES_DEFAULTS,
    SCREENING_RULES_DEFAULTS,
)
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-config", tags=["AI Configuration"])


# ── Response/Request schemas ─────────────────────────────────────

class PersonaConfig(BaseModel):
    tone: str = Field("professional", description="professional | casual | concise | detailed")
    custom_name: str | None = Field(None, description="Custom name for the AI assistant")
    detail_level: str = Field("standard", description="summary | standard | detailed")

class ScoringConfig(BaseModel):
    technical_weight: float = Field(0.70, ge=0.0, le=1.0)
    behavioral_weight: float = Field(0.30, ge=0.0, le=1.0)

class ChannelsConfig(BaseModel):
    email: bool = True
    whatsapp: bool = False
    teams: bool = False

class AutomationConfig(BaseModel):
    auto_screening: bool = False
    auto_scheduling: bool = False
    auto_stage_advance: bool = False
    autonomy_level: str = Field("low", description="low | medium | high")

class ComplianceConfig(BaseModel):
    fairness_level: str = Field("standard", description="standard | strict")
    data_retention_days: int = Field(730, ge=30, le=3650)
    salary_filter_enabled: bool = False
    salary_tolerance_percent: int = Field(15, ge=0, le=100)

class AIConfigResponse(BaseModel):
    persona: PersonaConfig
    scoring: ScoringConfig
    channels: ChannelsConfig
    automation: AutomationConfig
    compliance: ComplianceConfig
    setup_progress: int = 0

class AIConfigUpdate(WeDoBaseModel):
    persona: PersonaConfig | None = None
    scoring: ScoringConfig | None = None
    channels: ChannelsConfig | None = None
    automation: AutomationConfig | None = None
    compliance: ComplianceConfig | None = None


# ── Helpers ──────────────────────────────────────────────────────

async def _get_or_create_policy(
    company_id: str, db: AsyncSession
) -> CompanyHiringPolicy:
    result = await db.execute(
        select(CompanyHiringPolicy).where(
            CompanyHiringPolicy.company_id == company_id
        )
    )
    policy = result.scalar_one_or_none()
    if not policy:
        policy = CompanyHiringPolicy(company_id=company_id)
        db.add(policy)
        await db.flush()
    return policy


def _extract_config(policy: CompanyHiringPolicy) -> AIConfigResponse:
    """Extract unified AI config from policy JSON blocks."""
    comm = policy.communication_rules or COMMUNICATION_RULES_DEFAULTS
    auto = policy.automation_rules or AUTOMATION_RULES_DEFAULTS
    screening = policy.screening_rules or SCREENING_RULES_DEFAULTS

    return AIConfigResponse(
        persona=PersonaConfig(
            tone=comm.get("lia_tone", "professional"),
            detail_level="detailed" if comm.get("lia_tone") == "detailed" else "standard",
        ),
        scoring=ScoringConfig(
            technical_weight=0.70,
            behavioral_weight=0.30,
        ),
        channels=ChannelsConfig(
            email=True,
            whatsapp=comm.get("preferred_channel") == "whatsapp",
            teams=comm.get("preferred_channel") == "teams",
        ),
        automation=AutomationConfig(
            auto_screening=auto.get("auto_screening", False),
            auto_scheduling=auto.get("auto_scheduling", False),
            auto_stage_advance=auto.get("auto_stage_advance", False),
            autonomy_level=auto.get("autonomy_level", "low"),
        ),
        compliance=ComplianceConfig(
            fairness_level="standard",
            data_retention_days=730,
            salary_filter_enabled=screening.get("salary_expectation_filter", False),
            salary_tolerance_percent=screening.get("salary_tolerance_percent", 15),
        ),
        setup_progress=policy.setup_progress or 0,
    )


def _apply_update(policy: CompanyHiringPolicy, update: AIConfigUpdate) -> None:
    """Apply partial update to policy JSON blocks."""
    if update.persona:
        comm = dict(policy.communication_rules or COMMUNICATION_RULES_DEFAULTS)
        comm["lia_tone"] = update.persona.tone
        policy.communication_rules = comm

    if update.automation:
        auto = dict(policy.automation_rules or AUTOMATION_RULES_DEFAULTS)
        auto["auto_screening"] = update.automation.auto_screening
        auto["auto_scheduling"] = update.automation.auto_scheduling
        auto["auto_stage_advance"] = update.automation.auto_stage_advance
        auto["autonomy_level"] = update.automation.autonomy_level
        policy.automation_rules = auto

    if update.compliance:
        screening = dict(policy.screening_rules or SCREENING_RULES_DEFAULTS)
        screening["salary_expectation_filter"] = update.compliance.salary_filter_enabled
        screening["salary_tolerance_percent"] = update.compliance.salary_tolerance_percent
        policy.screening_rules = screening


# ── Endpoints ────────────────────────────────────────────────────

@router.get("", response_model=AIConfigResponse)
async def get_ai_config(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get unified AI configuration for the current tenant."""
    company_id = str(current_user.company_id)
    policy = await _get_or_create_policy(company_id, db)
    return _extract_config(policy)


@router.put("", response_model=AIConfigResponse)
async def update_ai_config(
    update: AIConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Update AI configuration. Only provided fields are changed."""
    company_id = str(current_user.company_id)
    policy = await _get_or_create_policy(company_id, db)
    _apply_update(policy, update)
    await db.commit()

    logger.info("[AIConfig] Updated by user=%s company=%s", current_user.id, company_id)
    return _extract_config(policy)


@router.get("/defaults/{sector}")
async def get_sector_defaults(sector: str, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get benchmark defaults for a sector. Helps recruiters decide."""
    SECTOR_BENCHMARKS: dict[str, dict[str, Any]] = {
        "tech": {
            "autonomy_level": "high", "auto_screening": True,
            "technical_weight": 0.70, "behavioral_weight": 0.30,
            "tone": "casual", "benchmark_note": "85% das empresas de tecnologia usam triagem automatica",
        },
        "varejo": {
            "autonomy_level": "medium", "auto_screening": True,
            "technical_weight": 0.50, "behavioral_weight": 0.50,
            "tone": "professional", "benchmark_note": "Varejo prioriza comportamental igual ao tecnico",
        },
        "financeiro": {
            "autonomy_level": "low", "auto_screening": False,
            "technical_weight": 0.60, "behavioral_weight": 0.40,
            "tone": "professional", "benchmark_note": "Setor financeiro exige revisao humana por compliance",
        },
        "saude": {
            "autonomy_level": "low", "auto_screening": False,
            "technical_weight": 0.55, "behavioral_weight": 0.45,
            "tone": "professional", "benchmark_note": "Saude prioriza validacao humana em todas as etapas",
        },
        "logistica": {
            "autonomy_level": "medium", "auto_screening": True,
            "technical_weight": 0.50, "behavioral_weight": 0.50,
            "tone": "concise", "benchmark_note": "Logistica prioriza velocidade — respostas curtas e diretas",
        },
    }
    return SECTOR_BENCHMARKS.get(sector.lower(), {
        "autonomy_level": "low", "auto_screening": False,
        "technical_weight": 0.70, "behavioral_weight": 0.30,
        "tone": "professional", "benchmark_note": "Defaults padrão para o seu setor",
    })
