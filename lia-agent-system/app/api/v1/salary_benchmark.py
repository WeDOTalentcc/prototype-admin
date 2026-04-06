"""
Salary Benchmark API — D7

GET /api/v1/salary-benchmark?job_title=&seniority=&location=&company_id=
"""
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from app.services.salary_benchmark_service import salary_benchmark_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/salary-benchmark", tags=["salary-benchmark"])


def _require_company_id(
    x_company_id: str | None = Header(None, alias="X-Company-ID"),
) -> str:
    if not x_company_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="X-Company-ID obrigatório")
    return x_company_id


@router.get("")
async def get_salary_benchmark(
    job_title: str = Query(..., description="Título do cargo"),
    seniority: str = Query("pleno", description="Nível: junior, pleno, senior, especialista, gerente"),
    location: str = Query("Brasil", description="Cidade ou 'Brasil' para nacional"),
    company_id: str = Depends(_require_company_id),
) -> dict:
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
    except Exception as exc:
        logger.error("[salary-benchmark] Erro: %s", exc)
        raise HTTPException(status_code=500, detail="Erro ao buscar benchmark salarial")
