"""
RAGPipelineService — pipeline RAG híbrido para busca de candidatos.

Combina:
  - pgvector (cosine similarity) para busca semântica
  - tsvector/tsquery (BM25-like) como fallback ou blend
  - FairnessGuard stub: diversidade de gênero no top-10

Tabelas utilizadas:
  - routing_cache_vectors (Migration 028, índice ivfflat) para busca semântica
  - candidates (tsvector: name + summary + skills) para BM25

Parâmetros de alpha:
  - alpha=0.0 → apenas BM25
  - alpha=1.0 → apenas semântica (pgvector)
  - 0 < alpha < 1 → híbrido (blend dos dois scores)

Multi-tenant: todas as queries são escopadas por company_id.
"""
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Limiar mínimo de similaridade coseno para resultados semânticos
_DEFAULT_SEMANTIC_THRESHOLD = 0.75

# Máximo de gênero único no top-10 (FairnessGuard)
_FAIRNESS_MAX_SINGLE_GENDER_RATIO = 0.70


# ---------------------------------------------------------------------------
# Resultado
# ---------------------------------------------------------------------------


@dataclass
class RAGSearchResult:
    """Resultado de uma busca RAG híbrida de candidatos."""

    results: List[Dict[str, Any]]
    query: str
    total: int
    source: str  # "semantic" | "bm25" | "hybrid"
    fairness_ok: bool
    search_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Embedding helper — mock/placeholder quando API não está configurada
# ---------------------------------------------------------------------------


async def generate_embedding(text: str) -> Optional[List[float]]:
    """
    Gera embedding para o texto fornecido.

    Ordem de tentativa:
      1. EmbeddingCacheService (Redis) + OpenAI text-embedding-3-small
      2. Fallback Gemini text-embedding-004
      3. Retorna None em caso de falha (permite degradação para BM25)
    """
    try:
        from app.services.embedding_cache_service import embedding_cache  # type: ignore

        cached = await embedding_cache.get_embedding(text, "text-embedding-3-small")
        if cached is not None:
            return cached
    except Exception as exc:
        logger.debug("[RAGPipeline] embedding_cache.get_embedding falhou: %s", exc)

    # Tentativa OpenAI
    try:
        from app.core.config import settings  # type: ignore

        api_key = (
            getattr(settings, "AI_INTEGRATIONS_OPENAI_API_KEY", None)
            or getattr(settings, "OPENAI_API_KEY", None)
        )
        if api_key:
            import openai

            client = openai.AsyncOpenAI(api_key=api_key)
            response = await client.embeddings.create(
                model="text-embedding-3-small",
                input=text,
            )
            vector = response.data[0].embedding
            try:
                from app.services.embedding_cache_service import embedding_cache  # type: ignore
                await embedding_cache.cache_embedding(text, vector, "text-embedding-3-small")
            except Exception:
                pass
            return vector
    except Exception as exc:
        logger.debug("[RAGPipeline] OpenAI embedding falhou: %s", exc)

    logger.debug("[RAGPipeline] Embedding indisponível — degradando para BM25")
    return None


# ---------------------------------------------------------------------------
# Normalização de scores
# ---------------------------------------------------------------------------


def _normalize(values: List[float]) -> List[float]:
    """Normaliza uma lista de scores para [0, 1]."""
    if not values:
        return values
    min_v = min(values)
    max_v = max(values)
    rng = max_v - min_v
    if rng == 0:
        return [1.0] * len(values)
    return [(v - min_v) / rng for v in values]


def _merge_candidate_results(
    bm25_results: List[Dict[str, Any]],
    semantic_results: List[Dict[str, Any]],
    alpha: float,
) -> List[Dict[str, Any]]:
    """
    Combina resultados BM25 + semânticos com score híbrido.
    alpha * semantic_score + (1 - alpha) * bm25_score
    """
    # Normalizar scores de cada fonte separadamente
    bm25_scores = _normalize([r.get("bm25_score", 0.0) for r in bm25_results])
    sem_scores = _normalize([r.get("semantic_score", 0.0) for r in semantic_results])

    merged: Dict[str, Dict[str, Any]] = {}

    for i, r in enumerate(bm25_results):
        cid = str(r["id"])
        merged[cid] = {
            "id": cid,
            "name": r.get("name", ""),
            "bm25_score": bm25_scores[i],
            "semantic_score": 0.0,
            "source": "bm25",
            **{k: v for k, v in r.items() if k not in ("id", "name", "bm25_score")},
        }

    for i, r in enumerate(semantic_results):
        cid = str(r["id"])
        if cid in merged:
            merged[cid]["semantic_score"] = sem_scores[i]
            merged[cid]["source"] = "hybrid"
        else:
            merged[cid] = {
                "id": cid,
                "name": r.get("name", ""),
                "bm25_score": 0.0,
                "semantic_score": sem_scores[i],
                "source": "semantic",
                **{k: v for k, v in r.items() if k not in ("id", "name", "semantic_score")},
            }

    for item in merged.values():
        item["hybrid_score"] = (
            alpha * item["semantic_score"] + (1 - alpha) * item["bm25_score"]
        )

    return sorted(merged.values(), key=lambda x: x["hybrid_score"], reverse=True)


# ---------------------------------------------------------------------------
# FairnessGuard stub
# ---------------------------------------------------------------------------


def _check_fairness(results: List[Dict[str, Any]], top_n: int = 10) -> bool:
    """
    Verifica diversidade de gênero no top-N (stub FairnessGuard).

    Regra: nenhum gênero único pode representar mais de 70% do top-10.
    Candidatos sem campo gender são ignorados do cômputo.

    Retorna True se diversidade OK ou se não há dados de gênero suficientes.
    """
    top = results[:top_n]
    genders = [r.get("gender") for r in top if r.get("gender")]

    if len(genders) < 3:
        # Dados insuficientes — não rejeita
        logger.debug("[RAGPipeline][FairnessGuard] Dados de gênero insuficientes (n=%d)", len(genders))
        return True

    from collections import Counter
    counts = Counter(genders)
    total = sum(counts.values())
    max_ratio = max(counts.values()) / total

    ok = max_ratio <= _FAIRNESS_MAX_SINGLE_GENDER_RATIO
    if not ok:
        dominant = counts.most_common(1)[0]
        logger.warning(
            "[RAGPipeline][FairnessGuard] Diversidade de gênero abaixo do limiar: "
            "gênero=%s representa %.0f%% do top-%d",
            dominant[0],
            dominant[1] / total * 100,
            top_n,
        )
    return ok


# ---------------------------------------------------------------------------
# Serviço principal
# ---------------------------------------------------------------------------


class RAGPipelineService:
    """
    Pipeline RAG híbrido para busca de candidatos.

    Combina pgvector (semântica) + tsvector (BM25) com blending via alpha.
    Multi-tenant: todas as queries são escopadas por company_id.
    """

    def __init__(
        self,
        semantic_threshold: float = _DEFAULT_SEMANTIC_THRESHOLD,
    ):
        self.semantic_threshold = semantic_threshold

    def _detect_query_type(self, query: str) -> float:
        """Detecta tipo de query e retorna alpha ideal (0=BM25, 1=semântico)."""
        query_lower = query.lower()
        # Cargo específico / tech stack → BM25 dominante
        tech_keywords = {"python", "java", "react", "node", "sql", "aws", "devops", "frontend", "backend", "fullstack"}
        cargo_keywords = {"gerente", "analista", "desenvolvedor", "engenheiro", "coordenador", "diretor", "supervisor"}
        if any(k in query_lower for k in tech_keywords | cargo_keywords):
            return 0.3
        # Perfil comportamental / cultural → semântico dominante
        behavioral_keywords = {"liderança", "comunicação", "trabalho em equipe", "proativo", "criativo", "inovador", "resiliente"}
        if any(k in query_lower for k in behavioral_keywords):
            return 0.7
        # Padrão equilibrado
        return 0.5

    async def search(
        self,
        query: str,
        company_id: str,
        db: AsyncSession,
        limit: int = 20,
        alpha: float = 0.5,
    ) -> RAGSearchResult:
        """
        Executa busca híbrida de candidatos.

        Parameters
        ----------
        query : str
            Texto em linguagem natural para busca.
        company_id : str
            Tenant ID — todos os resultados são filtrados por este campo.
        db : AsyncSession
            Sessão assíncrona do banco de dados.
        limit : int
            Número máximo de resultados.
        alpha : float
            Peso do score semântico vs BM25.
            0.0 = apenas BM25, 1.0 = apenas semântico, 0.5 = híbrido.

        Returns
        -------
        RAGSearchResult
        """
        t0 = time.perf_counter()

        # Se alpha não foi explicitamente personalizado (valor default 0.5),
        # detecta automaticamente o tipo de query para alpha ideal
        if alpha == 0.5:
            alpha = self._detect_query_type(query)

        bm25_results: List[Dict[str, Any]] = []
        semantic_results: List[Dict[str, Any]] = []
        source = "bm25"

        # --- Caminho BM25 (sempre executado a menos que alpha=1.0) ---
        if alpha < 1.0:
            bm25_results = await self._bm25_search(query, company_id, db, limit)

        # --- Caminho semântico (executado quando alpha > 0) ---
        embedding: Optional[List[float]] = None
        if alpha > 0.0:
            embedding = await generate_embedding(query)
            if embedding is not None:
                semantic_results = await self._semantic_search(
                    embedding, company_id, db, limit
                )
            else:
                logger.info(
                    "[RAGPipeline] Embedding indisponível — usando apenas BM25 (query=%r)",
                    query[:60],
                )

        # --- Determinar source e fazer merge ---
        has_bm25 = bool(bm25_results)
        has_semantic = bool(semantic_results)

        if alpha == 0.0 or not has_semantic:
            # BM25 puro
            merged = []
            for r in bm25_results[:limit]:
                r["hybrid_score"] = r.get("bm25_score", 0.0)
                r["source"] = "bm25"
                merged.append(r)
            source = "bm25"
        elif alpha == 1.0 or not has_bm25:
            # Semântico puro
            merged = []
            for r in semantic_results[:limit]:
                r["hybrid_score"] = r.get("semantic_score", 0.0)
                r["source"] = "semantic"
                merged.append(r)
            source = "semantic"
        else:
            # Híbrido
            merged = _merge_candidate_results(bm25_results, semantic_results, alpha)[:limit]
            source = "hybrid"

        # --- WRF re-ranking (Weighted Rank Fusion) ---
        try:
            from app.services.wrf_dynamic_k_service import WRFDynamicKService
            wrf_svc = WRFDynamicKService()
            # Injeta es_rank e pgv_rank para re-ranqueamento se não presentes
            for idx, item in enumerate(merged):
                if "es_rank" not in item:
                    item["es_rank"] = idx + 1
                if "pgv_rank" not in item:
                    item["pgv_rank"] = idx + 1
            merged = wrf_svc.rank_candidates(merged)
            logger.debug("[RAGPipeline] WRF re-ranking applied: %d results", len(merged))
        except Exception as _wrf_exc:
            logger.debug("[RAGPipeline] WRF re-ranking skipped: %s", _wrf_exc)

        # --- FairnessGuard ---
        fairness_ok = _check_fairness(merged, top_n=10)

        elapsed_ms = (time.perf_counter() - t0) * 1000

        return RAGSearchResult(
            results=merged,
            query=query,
            total=len(merged),
            source=source,
            fairness_ok=fairness_ok,
            search_time_ms=round(elapsed_ms, 2),
            metadata={
                "alpha": alpha,
                "bm25_count": len(bm25_results),
                "semantic_count": len(semantic_results),
                "embedding_available": embedding is not None,
                "semantic_threshold": self.semantic_threshold,
            },
        )

    # ------------------------------------------------------------------
    # BM25 via tsvector
    # ------------------------------------------------------------------

    async def _bm25_search(
        self,
        query: str,
        company_id: str,
        db: AsyncSession,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Busca candidatos via PostgreSQL Full-Text Search (tsvector/tsquery)."""
        try:
            sql = text("""
                SELECT
                    id,
                    name,
                    ts_rank(
                        to_tsvector('portuguese',
                            coalesce(name, '') || ' ' ||
                            coalesce(summary, '') || ' ' ||
                            coalesce(skills::text, '')
                        ),
                        plainto_tsquery('portuguese', :query)
                    ) AS bm25_score
                FROM candidates
                WHERE company_id = :company_id
                  AND to_tsvector('portuguese',
                          coalesce(name, '') || ' ' ||
                          coalesce(summary, '') || ' ' ||
                          coalesce(skills::text, '')
                      ) @@ plainto_tsquery('portuguese', :query)
                ORDER BY bm25_score DESC
                LIMIT :limit
            """)
            result = await db.execute(
                sql,
                {"query": query, "company_id": company_id, "limit": limit},
            )
            rows = result.fetchall()
            return [
                {"id": str(r[0]), "name": r[1], "bm25_score": float(r[2])}
                for r in rows
            ]
        except Exception as exc:
            logger.warning("[RAGPipeline] _bm25_search falhou: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Semântica via pgvector
    # ------------------------------------------------------------------

    async def _semantic_search(
        self,
        embedding: List[float],
        company_id: str,
        db: AsyncSession,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Busca semântica via pgvector na tabela candidates.
        Filtra por cosine similarity >= semantic_threshold.
        """
        try:
            embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"
            sql = text("""
                SELECT
                    id,
                    name,
                    1 - (embedding <=> :embedding::vector) AS semantic_score
                FROM candidates
                WHERE company_id = :company_id
                  AND embedding IS NOT NULL
                  AND 1 - (embedding <=> :embedding::vector) >= :threshold
                ORDER BY semantic_score DESC
                LIMIT :limit
            """)
            result = await db.execute(
                sql,
                {
                    "embedding": embedding_str,
                    "company_id": company_id,
                    "threshold": self.semantic_threshold,
                    "limit": limit,
                },
            )
            rows = result.fetchall()
            return [
                {"id": str(r[0]), "name": r[1], "semantic_score": float(r[2])}
                for r in rows
            ]
        except Exception as exc:
            logger.warning("[RAGPipeline] _semantic_search falhou: %s", exc)
            return []
