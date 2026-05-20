"""WSI admin endpoints — observabilidade e operação (audit rev. 23).

G23-05: expõe `get_layer2_cache_stats()` via REST para dashboard ops.
G23-07: expõe `purge_layer2_cache_*` para atender DSR (LGPD Art. 18).

Acesso restrito a usuários com role admin (verificado via dependência
canônica `require_admin_user`).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.domains.cv_screening.services.wsi_service.layer2_extractor import (
    get_layer2_cache_stats,
    purge_layer2_cache_all,
    purge_layer2_cache_entry,
)
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

try:
    from app.auth.dependencies import require_admin as require_admin_user  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover — fallback se dependency não existir
    def require_admin_user():  # type: ignore[misc]
        return None

router = APIRouter(prefix="/admin", tags=["WSI Admin"])


class Layer2CacheStats(BaseModel):
    """Telemetria do cache LRU in-process da Camada 2 LLM."""
    hits: int = Field(..., description="Número de cache hits desde o boot")
    misses: int = Field(..., description="Número de cache misses (chamou LLM) desde o boot")
    purges: int = Field(..., description="Número de entradas removidas via DSR/admin")
    size: int = Field(..., description="Entradas atualmente no cache")
    max: int = Field(..., description="Capacidade máxima do cache (LRU eviction acima disso)")
    hit_rate: float = Field(..., description="hits / (hits + misses), 0.0 se nunca chamado")


class PurgeEntryRequest(WeDoBaseModel):
    question_id: str = Field(..., description="ID da pergunta WSI")
    response_text: str = Field(..., description="Texto exato da resposta a remover do cache")


class PurgeResult(BaseModel):
    removed: int = Field(..., description="Número de entradas removidas")
    detail: str


@router.get("/layer2/cache/stats", response_model=Layer2CacheStats)
async def layer2_cache_stats(_: None = Depends(require_admin_user), company_id: str = Depends(require_company_id)) -> Layer2CacheStats:
    # multi-tenancy: admin/platform-level (/admin) — role-based access required
    """Retorna estatísticas do cache LRU da Camada 2 LLM.

    Use para monitorar hit-rate em produção. Hit-rate alto (>30%) indica
    que retries/reprocessamentos estão sendo bem amortizados pelo cache;
    hit-rate baixo é normal em cargas com respostas únicas por candidato.
    """
    stats = get_layer2_cache_stats()
    total = stats["hits"] + stats["misses"]
    hit_rate = (stats["hits"] / total) if total > 0 else 0.0
    return Layer2CacheStats(
        hits=stats["hits"],
        misses=stats["misses"],
        purges=stats.get("purges", 0),
        size=stats["size"],
        max=stats["max"],
        hit_rate=round(hit_rate, 4),
    )


@router.post("/layer2/cache/purge", response_model=PurgeResult)
async def layer2_cache_purge_entry(
    payload: PurgeEntryRequest,
    _: None = Depends(require_admin_user),
company_id: str = Depends(require_company_id)) -> PurgeResult:
    # multi-tenancy: admin/platform-level (/admin) — role-based access required
    """Remove uma entrada específica do cache (DSR — LGPD Art. 18).

    Use quando um candidato exerce direito ao esquecimento e o cache em
    memória ainda contém sinais derivados das respostas dele. Idempotente:
    se a entrada não existe, retorna `removed=0` sem erro.
    """
    if not payload.question_id or not payload.response_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="question_id e response_text são obrigatórios",
        )
    existed = purge_layer2_cache_entry(payload.question_id, payload.response_text)
    return PurgeResult(
        removed=1 if existed else 0,
        detail="Entrada removida do cache" if existed else "Entrada não estava em cache",
    )


@router.post("/layer2/cache/purge-all", response_model=PurgeResult)
async def layer2_cache_purge_all(_: None = Depends(require_admin_user), company_id: str = Depends(require_company_id)) -> PurgeResult:
    # multi-tenancy: admin/platform-level (/admin) — role-based access required
    """Limpa o cache LRU inteiro. Use para DSR amplo, deploys ou
    troubleshooting. Não afeta dados persistidos no banco."""
    n = purge_layer2_cache_all()
    return PurgeResult(removed=n, detail=f"{n} entrada(s) removida(s) do cache")
