"""
api-funil — Rotas de funil de recrutamento.

Rotas mínimas que podem ser testadas de forma isolada (sem DB real).
Integração com DB será adicionada na fase seguinte.
"""
from fastapi import APIRouter, Query
from typing import List

router = APIRouter(tags=["funil"])


@router.get("/health")
async def health():
    """Health check do serviço api-funil."""
    return {"status": "ok", "service": "api-funil"}


@router.get("/api/v1/funil/stages")
async def list_stages(company_id: str = Query(..., description="ID da empresa (multi-tenant)")):
    """Lista estágios do funil de recrutamento para a empresa."""
    # Dados representativos — integração com DB na fase seguinte
    return {
        "company_id": company_id,
        "stages": ["triagem", "entrevista", "oferta"],
    }


@router.get("/api/v1/funil/metrics")
async def funil_metrics(company_id: str = Query(..., description="ID da empresa (multi-tenant)")):
    """Métricas do funil: candidatos por estágio."""
    # Dados representativos — integração com DB na fase seguinte
    return {
        "company_id": company_id,
        "metrics": {},
    }
