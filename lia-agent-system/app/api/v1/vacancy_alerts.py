"""Endpoints de configuracao de alertas por vaga.

Permite que um recrutador sobrescreva a frequencia global de alertas
para uma vaga especifica. Pattern canonico:
- company_id vem do JWT via require_company_id
- user_id passado como query param (mesmo padrao de alerts.py)
"""
from fastapi import APIRouter, Depends, Query
from pydantic import ConfigDict
from typing import Literal, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

router = APIRouter(prefix="/alerts/vacancy", tags=["alerts"])

FrequencyType = Literal["daily", "twice_daily", "weekly", "monthly", "off"]


class VacancyAlertPreferenceItem(WeDoBaseModel):
    alert_type: str
    frequency: FrequencyType


class VacancyAlertPreferencesRequest(WeDoBaseModel):
    preferences: List[VacancyAlertPreferenceItem]


@router.get("/{vacancy_id}/preferences")
async def get_vacancy_alert_preferences(
    vacancy_id: str,
    user_id: str = Query(..., description="ID do recrutador"),
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
):
    """Retorna preferencias de alerta do recrutador para esta vaga."""
    from libs.models.lia_models.vacancy_alert_config import VacancyAlertConfig
    stmt = select(VacancyAlertConfig).where(
        and_(
            VacancyAlertConfig.company_id == company_id,
            VacancyAlertConfig.vacancy_id == vacancy_id,
            VacancyAlertConfig.recruiter_id == user_id,
        )
    )
    result = await db.execute(stmt)
    configs = result.scalars().all()
    return {
        "vacancy_id": vacancy_id,
        "user_id": user_id,
        "preferences": [{"alert_type": c.alert_type, "frequency": c.frequency} for c in configs],
    }


@router.put("/{vacancy_id}/preferences")
async def update_vacancy_alert_preferences(
    vacancy_id: str,
    payload: VacancyAlertPreferencesRequest,
    user_id: str = Query(..., description="ID do recrutador"),
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
):
    """Salva preferencias de alerta do recrutador para esta vaga (upsert).

    multi-tenancy: company_id do JWT, nunca do payload.
    """
    from libs.models.lia_models.vacancy_alert_config import VacancyAlertConfig
    for pref in payload.preferences:
        stmt = select(VacancyAlertConfig).where(
            and_(
                VacancyAlertConfig.company_id == company_id,
                VacancyAlertConfig.vacancy_id == vacancy_id,
                VacancyAlertConfig.recruiter_id == user_id,
                VacancyAlertConfig.alert_type == pref.alert_type,
            )
        )
        result = await db.execute(stmt)
        config = result.scalar_one_or_none()
        if config:
            config.frequency = pref.frequency
        else:
            db.add(VacancyAlertConfig(
                company_id=company_id,
                vacancy_id=vacancy_id,
                recruiter_id=user_id,
                alert_type=pref.alert_type,
                frequency=pref.frequency,
            ))
    await db.commit()
    return {"status": "ok", "vacancy_id": vacancy_id, "updated": len(payload.preferences)}


@router.get("/preview")
async def preview_alert(
    alert_type: str,
    vacancy_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
):
    """Retorna preview do alerta: count de candidatos no estado alvo nas ultimas 24h.

    Usado pelo badge live no FE para mostrar contagem near-realtime.
    """
    from sqlalchemy import text

    if alert_type == "new_candidate":
        stmt = text(
            "SELECT COUNT(*) FROM vacancy_candidates"
            " WHERE company_id = :company_id"
            " AND (:vacancy_id IS NULL OR vacancy_id = CAST(:vacancy_id AS UUID))"
            " AND created_at >= NOW() - INTERVAL '24 hours'"
        )
        result = await db.execute(stmt, {"company_id": company_id, "vacancy_id": vacancy_id})
        count = result.scalar() or 0
        return {
            "alert_type": alert_type,
            "preview_count": count,
            "description": f"{count} novo(s) candidato(s) nas ultimas 24h",
        }

    elif alert_type == "screening_complete":
        stmt = text(
            "SELECT COUNT(*) FROM vacancy_candidates"
            " WHERE company_id = :company_id"
            " AND (:vacancy_id IS NULL OR vacancy_id = CAST(:vacancy_id AS UUID))"
            " AND screening_completed_at >= NOW() - INTERVAL '24 hours'"
        )
        result = await db.execute(stmt, {"company_id": company_id, "vacancy_id": vacancy_id})
        count = result.scalar() or 0
        return {
            "alert_type": alert_type,
            "preview_count": count,
            "description": f"{count} triagem(ns) concluida(s) nas ultimas 24h",
        }

    elif alert_type == "stage_change":
        stmt = text(
            "SELECT COUNT(*) FROM vacancy_candidates"
            " WHERE company_id = :company_id"
            " AND (:vacancy_id IS NULL OR vacancy_id = CAST(:vacancy_id AS UUID))"
            " AND stage_entered_at >= NOW() - INTERVAL '24 hours'"
        )
        result = await db.execute(stmt, {"company_id": company_id, "vacancy_id": vacancy_id})
        count = result.scalar() or 0
        return {
            "alert_type": alert_type,
            "preview_count": count,
            "description": f"{count} mudanca(s) de etapa nas ultimas 24h",
        }

    return {
        "alert_type": alert_type,
        "preview_count": 0,
        "description": "Preview nao disponivel para este tipo de alerta",
    }
