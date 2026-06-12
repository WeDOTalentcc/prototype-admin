"""API: /notifications/digest-schedule — per-user + company-default digest frequency.

Fatia 2 (2026-06-12) — Decisão 3: ambos os níveis (empresa + por-usuário).

Endpoints:
  GET  /notifications/digest-schedule          — preferência efetiva do usuário autenticado
  PUT  /notifications/digest-schedule          — define override pessoal
  DELETE /notifications/digest-schedule        — remove override pessoal (volta ao default empresa)
  GET  /notifications/digest-schedule/company  — padrão da empresa (qualquer papel)
  PUT  /notifications/digest-schedule/company  — atualiza padrão da empresa (admin only)

Multi-tenancy: company_id SEMPRE do JWT via Depends(require_company_id). NUNCA do payload.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User, UserRole
from app.core.database import get_db
from app.domains.communication.repositories.digest_schedule_repository import (
    DigestScheduleRepository,
)
from app.schemas.digest_schedule import DigestScheduleRequest, DigestScheduleResponse
from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications/digest-schedule", tags=["notifications"])

_CANONICAL_FREQUENCIES = frozenset({"daily", "twice_daily", "weekly", "monthly"})
_POLICY_FALLBACK_FREQUENCY = "weekly"


def _pref_to_response(pref, source: str, user_id: str | None = None) -> DigestScheduleResponse:
    return DigestScheduleResponse(
        frequency=pref.frequency,
        preferred_time_morning=pref.preferred_time_morning,
        preferred_time_afternoon=pref.preferred_time_afternoon,
        quiet_hours_start=pref.quiet_hours_start,
        quiet_hours_end=pref.quiet_hours_end,
        source=source,
        user_id=user_id,
    )


async def _resolve_policy_fallback(db: AsyncSession, company_id: str) -> str:
    """Lê HiringPolicy.communication_rules.briefing_frequency como último fallback."""
    try:
        from app.domains.recruitment.repositories.hiring_policy_repository import (
            HiringPolicyRepository,
        )

        repo = HiringPolicyRepository()
        policy = await repo.get_by_company(company_id)
        if policy:
            comm = policy.communication_rules or {}
            freq = comm.get("briefing_frequency") if isinstance(comm, dict) else None
            if freq and freq in _CANONICAL_FREQUENCIES:
                return freq
    except Exception:
        pass
    return _POLICY_FALLBACK_FREQUENCY


# ---------------------------------------------------------------------------
# GET /notifications/digest-schedule — effective preference for current user
# ---------------------------------------------------------------------------

@router.get("", response_model=DigestScheduleResponse)
async def get_digest_schedule(
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
):
    """Retorna a frequência efetiva do usuário autenticado.

    Precedência: user override > company default > HiringPolicy fallback.
    """
    repo = DigestScheduleRepository()
    user_id = str(current_user.id)

    pref, source = await repo.get_effective(db, company_id=company_id, user_id=user_id)
    if pref:
        return _pref_to_response(pref, source=source, user_id=pref.user_id)

    # Último fallback: HiringPolicy
    fallback_freq = await _resolve_policy_fallback(db, company_id)
    return DigestScheduleResponse(
        frequency=fallback_freq,
        source="policy_fallback",
        user_id=None,
    )


# ---------------------------------------------------------------------------
# PUT /notifications/digest-schedule — set per-user override
# ---------------------------------------------------------------------------

@router.put("", response_model=DigestScheduleResponse, status_code=status.HTTP_200_OK)
async def update_digest_schedule(
    body: DigestScheduleRequest,
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
):
    """Define a frequência pessoal do usuário autenticado (override do padrão empresa)."""
    repo = DigestScheduleRepository()
    user_id = str(current_user.id)

    pref = await repo.upsert_user_preference(
        db,
        company_id=company_id,
        user_id=user_id,
        frequency=body.frequency,
        preferred_time_morning=body.preferred_time_morning,
        preferred_time_afternoon=body.preferred_time_afternoon,
        quiet_hours_start=body.quiet_hours_start,
        quiet_hours_end=body.quiet_hours_end,
    )
    await db.commit()

    logger.info(
        "[digest_schedule] user_pref updated user=%s company=%s freq=%s",
        user_id, company_id, body.frequency,
    )
    return _pref_to_response(pref, source="user", user_id=user_id)


# ---------------------------------------------------------------------------
# DELETE /notifications/digest-schedule — remove per-user override
# ---------------------------------------------------------------------------

@router.delete("", status_code=status.HTTP_200_OK)
async def delete_digest_schedule(
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
):
    """Remove override pessoal; usuário volta ao padrão da empresa."""
    repo = DigestScheduleRepository()
    user_id = str(current_user.id)
    deleted = await repo.delete_user_preference(db, company_id=company_id, user_id=user_id)
    await db.commit()
    return {"deleted": deleted, "message": "Override pessoal removido — usando padrão da empresa"}


# ---------------------------------------------------------------------------
# GET /notifications/digest-schedule/company — company default (any role)
# ---------------------------------------------------------------------------

@router.get("/company", response_model=DigestScheduleResponse)
async def get_company_digest_schedule(
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
):
    """Retorna o padrão de frequência da empresa (ou fallback da política)."""
    repo = DigestScheduleRepository()
    pref = await repo.get_company_default(db, company_id=company_id)
    if pref:
        return _pref_to_response(pref, source="company_default")

    fallback_freq = await _resolve_policy_fallback(db, company_id)
    return DigestScheduleResponse(
        frequency=fallback_freq,
        source="policy_fallback",
        user_id=None,
    )


# ---------------------------------------------------------------------------
# PUT /notifications/digest-schedule/company — set company default (admin only)
# ---------------------------------------------------------------------------

@router.put("/company", response_model=DigestScheduleResponse)
async def update_company_digest_schedule(
    body: DigestScheduleRequest,
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
):
    """Atualiza o padrão de frequência da empresa (apenas admin)."""
    if current_user.role not in (UserRole.admin, UserRole.wedotalent_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem alterar o padrão de frequência da empresa.",
        )

    repo = DigestScheduleRepository()
    pref = await repo.upsert_company_default(
        db,
        company_id=company_id,
        frequency=body.frequency,
        preferred_time_morning=body.preferred_time_morning,
        preferred_time_afternoon=body.preferred_time_afternoon,
        quiet_hours_start=body.quiet_hours_start,
        quiet_hours_end=body.quiet_hours_end,
    )
    await db.commit()

    logger.info(
        "[digest_schedule] company_default updated company=%s freq=%s by user=%s",
        company_id, body.frequency, str(current_user.id),
    )
    return _pref_to_response(pref, source="company_default")
