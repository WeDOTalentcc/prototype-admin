"""
Salary Benchmark API — D7

GET /api/v1/salary-benchmark?job_title=&seniority=&location=&company_id=
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.shared.services.salary_benchmark_service import salary_benchmark_service
from app.shared.tenant_guard import get_verified_company_id
from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/salary-benchmark", tags=["salary-benchmark"])


@router.get("", response_model=None)
async def get_salary_benchmark(
    job_title: str = Query(..., description="Título do cargo"),
    seniority: str = Query("pleno", description="Nível: junior, pleno, senior, especialista, gerente"),
    location: str = Query("Brasil", description="Cidade ou 'Brasil' para nacional"),
    company_id: str = Depends(get_verified_company_id),
_company_gate: str = Depends(require_company_id)) -> dict:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Retorna benchmark salarial real para o cargo/nível/localização.
    Fonte: Apify (Glassdoor/LinkedIn) com cache 7 dias. Fallback: dados setoriais.
    """
    try:
        benchmark = await salary_benchmark_service.get_benchmark(
            job_title=job_title,
            seniority=seniority,
            location=location,
            company_id=company_id,
        )
        return benchmark.to_dict()
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[salary-benchmark] Erro: %s", exc)
        raise HTTPException(status_code=500, detail="Erro ao buscar benchmark salarial")
