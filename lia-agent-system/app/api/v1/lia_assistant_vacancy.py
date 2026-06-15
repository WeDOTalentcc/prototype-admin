"""
LIA Assistant — Vacancy search/reuse endpoints (Fast Track support).

Extracted from lia_assistant.py (Phase 5 decomposition).
All routes share prefix="/lia" to preserve existing /api/v1/lia/vacancy-* URLs.
"""
import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.core.database import get_db
from app.domains.job_management.services.vacancy_search_service import vacancy_search_service
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lia", tags=["lia-vacancy"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class VacancySearchRequest(WeDoBaseModel):
    search_criteria: dict[str, Any] = {}
    limit: int = 10


class VacancySearchResponse(BaseModel):
    vacancies: list[dict[str, Any]]
    total: int
    criteria_used: dict[str, Any] = {}
    message: str | None = None


class VacancyCriteriaExtractionRequest(WeDoBaseModel):
    message: str


class VacancyCriteriaExtractionResponse(BaseModel):
    criteria: dict[str, Any]
    has_minimum_criteria: bool
    message: str


class VacancyAdjustmentsRequest(WeDoBaseModel):
    vacancy_id: UUID
    message: str


class VacancyAdjustmentsResponse(BaseModel):
    adjustments: dict[str, Any]
    adjusted_vacancy: dict[str, Any] | None = None
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/vacancy-search", response_model=VacancySearchResponse)
async def search_previous_vacancies(
    request: VacancySearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)) -> VacancySearchResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        company_id = current_user.company_id

        vacancies = await vacancy_search_service.search_vacancies(
            criteria=request.search_criteria,
            company_id=company_id,
            db=db,
            limit=request.limit
        )

        vacancies_dict = [v.model_dump(mode='json') for v in vacancies]
        message = (
            f"Encontrei {len(vacancies)} vaga(s) que correspondem aos seus critérios."
            if vacancies
            else "Não encontrei vagas anteriores com esses critérios. Tente ajustar a busca ou criar uma vaga do zero."
        )

        return VacancySearchResponse(
            vacancies=vacancies_dict,
            total=len(vacancies),
            criteria_used=request.search_criteria,
            message=message
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in Fast Track vacancy search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/vacancy-full/{vacancy_id}", response_model=None)
async def get_vacancy_full_details(
    vacancy_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)) -> dict[str, Any]:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        company_id = current_user.company_id
        vacancy_details = await vacancy_search_service.get_vacancy_full_details(
            vacancy_id=vacancy_id,
            db=db,
            company_id=company_id
        )
        if not vacancy_details:
            raise HTTPException(status_code=404, detail="Vaga não encontrada")
        return vacancy_details.model_dump(mode='json')
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vacancy full details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/vacancy-criteria-extract", response_model=VacancyCriteriaExtractionResponse)
async def extract_vacancy_criteria(
    request: VacancyCriteriaExtractionRequest,
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)) -> VacancyCriteriaExtractionResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        criteria = await vacancy_search_service.extract_search_criteria(request.message)
        has_minimum = vacancy_search_service.validate_minimum_criteria(criteria)

        if has_minimum:
            criteria_list = [f"{k}: {v}" for k, v in criteria.items() if v]
            message = f"Encontrei os seguintes critérios: {', '.join(criteria_list)}. Vou buscar vagas anteriores."
        elif criteria:
            message = "Encontrei alguns critérios, mas preciso de pelo menos 2 para fazer uma busca precisa. Pode me dar mais detalhes sobre a vaga que procura?"
        else:
            message = "Não consegui identificar critérios de busca. Por favor, me diga qual cargo, área, gestor ou ano da vaga que deseja reaproveitar."

        return VacancyCriteriaExtractionResponse(
            criteria=criteria,
            has_minimum_criteria=has_minimum,
            message=message
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting vacancy criteria: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/vacancy-adjustments", response_model=VacancyAdjustmentsResponse)
async def extract_and_apply_adjustments(
    request: VacancyAdjustmentsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)) -> VacancyAdjustmentsResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        adjustments = await vacancy_search_service.extract_adjustments(request.message)

        vacancy_details = await vacancy_search_service.get_vacancy_full_details(
            vacancy_id=request.vacancy_id,
            db=db,
            company_id=current_user.company_id
        )
        if not vacancy_details:
            raise HTTPException(status_code=404, detail="Vaga não encontrada")

        adjusted_vacancy = None
        if adjustments:
            adjusted_vacancy = vacancy_search_service.apply_adjustments(
                vacancy=vacancy_details,
                adjustments=adjustments
            )
            adjustment_parts = []
            if adjustments.get("salary_min") or adjustments.get("salary_max"):
                adjustment_parts.append("faixa salarial")
            if adjustments.get("work_model"):
                adjustment_parts.append(f"modelo de trabalho para {adjustments['work_model']}")
            if adjustments.get("location"):
                adjustment_parts.append(f"localização para {adjustments['location']}")
            if adjustments.get("manager"):
                adjustment_parts.append(f"gestor para {adjustments['manager']}")
            message = f"Apliquei os ajustes: {', '.join(adjustment_parts)}. A vaga está pronta para publicar?"
        else:
            message = "Não identifiquei ajustes específicos. A vaga permanece como estava. Deseja fazer alguma alteração?"

        return VacancyAdjustmentsResponse(
            adjustments=adjustments,
            adjusted_vacancy=adjusted_vacancy.model_dump(mode='json') if adjusted_vacancy else None,
            message=message
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying vacancy adjustments: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
