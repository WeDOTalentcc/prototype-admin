"""
api-funil — Rotas de funil de recrutamento.

Rotas mínimas que podem ser testadas de forma isolada (sem DB real).
Integração com DB será adicionada na fase seguinte.
"""
from fastapi import APIRouter, Depends

from app.shared.auth.auth_provider import AuthContext, get_auth_context_dependency

router = APIRouter(tags=["funil"])

# Dependency singleton (cacheável por sub-app)
_auth_dep = get_auth_context_dependency()


@router.get("/health")
async def health():
    """Health check do serviço api-funil (público — sem auth)."""
    return {"status": "ok", "service": "api-funil"}


@router.get("/api/v1/funil/stages")
async def list_stages(
    auth: AuthContext = Depends(_auth_dep),
):
    """Lista estágios do funil de recrutamento para a empresa.

    Exemplo canônico Sprint G7: company_id extraído do JWT via AuthContext,
    não mais via query param. Multi-tenancy enforçado pelo token.
    """
    # Dados representativos — integração com DB na fase seguinte
    return {
        "company_id": auth.company_id,
        "stages": ["triagem", "entrevista", "oferta"],
    }


@router.get("/api/v1/funil/metrics")
async def funil_metrics(
    auth: AuthContext = Depends(_auth_dep),
):
    """Métricas do funil: candidatos por estágio.

    Exemplo canônico Sprint G7: usa get_auth_context_dependency() em vez de
    get_current_active_user / get_current_user.
    """
    # Dados representativos — integração com DB na fase seguinte
    return {
        "company_id": auth.company_id,
        "metrics": {},
    }
