"""
Onda 2B: GET /cities — autocomplete de cidades (dataset global IBGE).
"""
from fastapi import APIRouter, Depends, Query

from app.domains.job_management.services.cities_service import search_cities
from app.shared.security.require_company_id import require_company_id

router = APIRouter(prefix="/cities", tags=["cities"])


@router.get("")
async def list_cities(
    search: str = Query("", description="Busca por nome da cidade"),
    limit: int = Query(50, ge=1, le=100),
    company_id: str = Depends(require_company_id),
):
    """Lista cidades (RemoteOption {id,name}) filtradas por `search`. Dataset global IBGE."""
    return search_cities(search, limit)
