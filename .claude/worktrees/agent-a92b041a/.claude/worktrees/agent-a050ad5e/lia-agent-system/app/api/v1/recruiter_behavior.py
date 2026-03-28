"""
Recruiter Behavior Profile API — Z7-01.

Endpoints:
  GET  /api/v1/recruiters/{recruiter_id}/behavior-profile   → perfil comportamental
  POST /api/v1/recruiters/{recruiter_id}/behavior-signal    → registra sinal de comportamento
  POST /api/v1/recruiters/{recruiter_id}/behavior-invalidate → força re-computação
"""
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo, get_user_company_id
from app.auth.models import User
from app.core.database import get_db
from app.services.recruiter_behavior_service import recruiter_behavior_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recruiters", tags=["recruiter-behavior"])


# ── schemas ───────────────────────────────────────────────────────────────────

class BehaviorProfileResponse(BaseModel):
    recruiter_id: str
    company_id: str
    computed_at: str
    active_hours_distribution: Dict[str, int] = {}
    preferred_sourcing_channels: Dict[str, int] = {}
    avg_response_time_hours: Optional[float] = None
    avg_hiring_velocity_days: Optional[float] = None
    stage_conversion_rates: Dict[str, float] = {}
    communication_style: str = "balanced"
    typical_batch_size: Optional[int] = None
    rejection_reasons_top: List[str] = []
    bias_risk_score: Optional[float] = None
    experience_level: str = "intermediate"


class BehaviorSignalRequest(BaseModel):
    action_type: str
    metadata: Optional[Dict[str, Any]] = None


# ── endpoints ─────────────────────────────────────────────────────────────────

@router.get("/{recruiter_id}/behavior-profile", response_model=BehaviorProfileResponse)
async def get_behavior_profile(
    recruiter_id: str = Path(..., description="ID do recrutador"),
    force_refresh: bool = False,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna o perfil comportamental de um recrutador.

    Inclui padrões de horário, canais de sourcing preferidos,
    taxas de conversão por estágio e estilo de comunicação.
    Cache Redis de 24h (use force_refresh=true para re-computar).
    """
    company_id = get_user_company_id(current_user)
    # Recrutador só pode ver seu próprio perfil (ou admin pode ver qualquer um)
    if str(current_user.id) != recruiter_id and not getattr(current_user, "is_admin", False):
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para ver o perfil deste recrutador.",
        )

    profile = await recruiter_behavior_service.get_or_compute(
        recruiter_id=recruiter_id,
        company_id=company_id,
        db=db,
        force_refresh=force_refresh,
    )
    return BehaviorProfileResponse(**profile.to_dict())


@router.post("/{recruiter_id}/behavior-signal", status_code=202)
async def record_behavior_signal(
    body: BehaviorSignalRequest,
    recruiter_id: str = Path(..., description="ID do recrutador"),
    current_user: User = Depends(get_current_user_or_demo),
):
    """
    Registra um sinal comportamental do recrutador (fire-and-forget).

    action_type exemplos:
      - "sourcing_channel_used"  → metadata: {"channel": "linkedin"}
      - "candidate_responded"    → metadata: {"response_time_hours": 2.5}
      - "stage_approved"         → metadata: {"stage": "gate1"}
      - "batch_review"           → metadata: {"batch_size": 15}
    """
    company_id = get_user_company_id(current_user)
    await recruiter_behavior_service.record_action(
        recruiter_id=recruiter_id,
        company_id=company_id,
        action_type=body.action_type,
        metadata=body.metadata,
    )
    return {"accepted": True}


@router.post("/{recruiter_id}/behavior-invalidate", status_code=200)
async def invalidate_behavior_cache(
    recruiter_id: str = Path(..., description="ID do recrutador"),
    current_user: User = Depends(get_current_user_or_demo),
):
    """Força re-computação do perfil comportamental (remove cache Redis)."""
    company_id = get_user_company_id(current_user)
    if str(current_user.id) != recruiter_id and not getattr(current_user, "is_admin", False):
        raise HTTPException(status_code=403, detail="Permissão negada.")
    await recruiter_behavior_service.invalidate(recruiter_id, company_id)
    return {"invalidated": True, "recruiter_id": recruiter_id}
