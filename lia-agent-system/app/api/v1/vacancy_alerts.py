"""Endpoints de configuração de alertas por vaga.

Permite que um recrutador sobrescreva a frequência global de alertas
para uma vaga específica. Pattern canônico:
- company_id vem do JWT via require_company_id
- user_id passado como query param (mesmo padrão de alerts.py)
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
    """Retorna preferências de alerta do recrutador para esta vaga."""
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
    """Salva preferências de alerta do recrutador para esta vaga (upsert).

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
