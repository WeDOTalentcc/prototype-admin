"""
GET /job-vacancies/options — vocabulários canônicos dos dropdowns do formulário
de vaga (status, prioridade, urgência, modelo de trabalho, tipo de contrato,
senioridade).

FastAPI é a fonte única da verdade (Rails fora do fluxo). Esta rota estática de
coleção DEVE ser registrada ANTES do catch-all de item /{job_vacancy_id}
(ver invariante de ordenação em job_vacancies/__init__.py).
"""
from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_active_user
from ._shared import (
    VALID_JOB_STATUSES,
    VALID_PRIORITIES,
    URGENCY_LEVELS,
    WORK_MODEL_OPTIONS,
    EMPLOYMENT_TYPE_OPTIONS,
    SENIORITY_OPTIONS,
)

router = APIRouter()


def _opts(values):
    """Map a list of canonical string values to RemoteOption {id, name}."""
    return [{"id": v, "name": v} for v in values]


@router.get("/job-vacancies/options")
async def get_job_vacancy_options(
    current_user=Depends(get_current_active_user),
):
    """Todos os vocabulários de dropdown da vaga num único payload.

    Estático/global (não tenant-specific), mas exige autenticação para manter
    o contrato do proxy (auth:true) e não vazar nada a anônimos.
    """
    return {
        "statuses": _opts(VALID_JOB_STATUSES),
        "priorities": _opts(VALID_PRIORITIES),
        "urgency_levels": URGENCY_LEVELS,
        "work_models": _opts(WORK_MODEL_OPTIONS),
        "employment_types": _opts(EMPLOYMENT_TYPE_OPTIONS),
        "seniority_levels": _opts(SENIORITY_OPTIONS),
    }
