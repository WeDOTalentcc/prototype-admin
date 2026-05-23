"""
Pipeline Prediction API — Sprint 3A.

Endpoints:
  GET /api/v1/pipeline-prediction?vacancy_id=<uuid>&company_id=<uuid>
      → Previsão individual de uma vaga

  GET /api/v1/pipeline-prediction/company-overview?company_id=<uuid>
      → Ranking de todas as vagas ativas por probabilidade de fechamento
"""
import logging

from fastapi import APIRouter, HTTPException, Query

from app.shared.services.pipeline_prediction_service import pipeline_prediction_service
from fastapi import Depends
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipeline-prediction", tags=["pipeline-prediction"])


@router.get("", response_model=None)
async def get_vacancy_prediction(
    vacancy_id: str = Query(..., description="UUID da vaga"),
    company_id: str = Query(..., description="UUID da empresa"),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Retorna probabilidade de fechamento de uma vaga específica.

    Response:
        closure_probability (0–100)
        estimated_days_to_close
        confidence_level: low | medium | high
        stage_of_best_candidate
        positive_factors: lista de fatores positivos
        risk_factors: lista de fatores de risco
    """
    if not vacancy_id or not company_id:
        raise HTTPException(status_code=422, detail="vacancy_id e company_id são obrigatórios")

    try:
        result = await pipeline_prediction_service.get_vacancy_prediction(
            vacancy_id=vacancy_id,
            company_id=company_id,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[pipeline_prediction] Error for vacancy {vacancy_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao calcular previsão de fechamento")


@router.get("/company-overview", response_model=None)
async def get_company_overview(
    company_id: str = Query(..., description="UUID da empresa"),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Retorna previsões de todas as vagas ativas da empresa,
    ordenadas por closure_probability ascendente (mais em risco primeiro).

    Response:
        vacancies: lista de previsões individuais
        summary: total_active_vacancies, at_risk_count, near_closure_count, avg_closure_probability
    """
    if not company_id:
        raise HTTPException(status_code=422, detail="company_id é obrigatório")

    try:
        result = await pipeline_prediction_service.get_company_overview(
            company_id=company_id,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[pipeline_prediction] Error for company {company_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao calcular visão geral de previsões")
