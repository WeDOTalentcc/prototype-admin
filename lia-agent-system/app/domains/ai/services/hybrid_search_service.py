"""
HybridSearchService — busca híbrida tsvector + pgvector (André R9/P7).

Combina:
  - PostgreSQL Full-Text Search (tsvector/tsquery) — precisão léxica, BM25-like
  - pgvector cosine similarity — semântica

Score final: alpha * vector_score + (1-alpha) * text_score
alpha padrão: 0.5 (configurável)

Benchmark vs hash MD5 (VectorSemanticCache atual):
  - tsvector: sem embedding, mais rápido, bom para queries exatas
  - pgvector: embedding necessário, melhor para variações semânticas
  - híbrido: melhor recall geral

Tabelas suportadas:
  - job_vacancies (title, description, requirements)
  - candidates (name, summary, skills)
"""
import logging
import time
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


def _normalize_scores(results: list[dict[str, Any]], score_key: str) -> list[dict[str, Any]]:
    """Normaliza scores para o intervalo [0, 1]."""
    if not results:
        return results
    scores = [r.get(score_key, 0.0) or 0.0 for r in results]
    min_s = min(scores)
    max_s = max(scores)
    rng = max_s - min_s
    for r in results:
        raw = r.get(score_key, 0.0) or 0.0
        r[score_key] = (raw - min_s) / rng if rng > 0 else 1.0
    return results


def _merge_results(
    text_results: list[dict[str, Any]],
    vector_results: list[dict[str, Any]],
    alpha: float,
    id_key: str = "id",
    name_key: str = "title",
) -> list[dict[str, Any]]:
    """
    Merge e normaliza resultados text + vector.
    Aplica score híbrido: alpha * vector_score + (1-alpha) * text_score.
    """
    merged: dict[str, dict[str, Any]] = {}

    # Normalizar scores individualmente
    text_results = _normalize_scores([dict(r) for r in text_results], "text_score")
    vector_results = _normalize_scores([dict(r) for r in vector_results], "vector_score")

    for r in text_results:
        rid = str(r[id_key])
        merged[rid] = {
            "id": rid,
            name_key: r.get(name_key, ""),
            "text_score": r.get("text_score", 0.0),
            "vector_score": 0.0,
            "source": "text",
        }

    for r in vector_results:
        rid = str(r[id_key])
        if rid in merged:
            merged[rid]["vector_score"] = r.get("vector_score", 0.0)
            merged[rid]["source"] = "hybrid"
        else:
            merged[rid] = {
                "id": rid,
                name_key: r.get(name_key, ""),
                "text_score": 0.0,
                "vector_score": r.get("vector_score", 0.0),
                "source": "vector",
            }

    # Calcular hybrid_score
    for rid, item in merged.items():
        item["hybrid_score"] = (
            alpha * item["vector_score"] + (1 - alpha) * item["text_score"]
        )

    return sorted(merged.values(), key=lambda x: x["hybrid_score"], reverse=True)


class HybridSearchService:
    """
    Busca híbrida combinando tsvector (FTS) e pgvector (semântica).

    Parâmetros
    ----------
    alpha : float
        Peso do score vetorial vs textual. 0 = apenas texto, 1 = apenas vetor.
    """

    def __init__(self, alpha: float = 0.5):
        self.alpha = alpha  # peso do vetor vs texto

    # ------------------------------------------------------------------
    # Busca de vagas
    # ------------------------------------------------------------------

    async def search_jobs(
        self,
        query: str,
        company_id: str,
        db: AsyncSession,
        limit: int = 10,
        embedding: list[float] | None = None,
    ) -> list[dict]:
        """
        Busca vagas combinando tsvector (título+descrição) e pgvector (embedding).
        Se embedding=None, usa apenas tsvector.
        """
        text_results = await self._text_search_jobs(query, company_id, db, limit)
        if embedding is None:
            for r in text_results:
                r["vector_score"] = 0.0
                r["hybrid_score"] = r.get("text_score", 0.0)
                r["source"] = "text"
            return text_results

        vector_results = await self._vector_search_jobs(company_id, db, limit, embedding)
        return _merge_results(text_results, vector_results, self.alpha, name_key="title")

    async def _text_search_jobs(
        self,
        query: str,
        company_id: str,
        db: AsyncSession,
        limit: int,
    ) -> list[dict[str, Any]]:
        try:
            sql = text("""
                SELECT id, title,
                       ts_rank(
                           to_tsvector('portuguese', coalesce(title,'') || ' ' || coalesce(description,'')),
                           plainto_tsquery('portuguese', :query)
                       ) AS text_score
                FROM job_vacancies
                WHERE company_id = :company_id
                  AND to_tsvector('portuguese', coalesce(title,'') || ' ' || coalesce(description,''))
                      @@ plainto_tsquery('portuguese', :query)
                ORDER BY text_score DESC
                LIMIT :limit
            """)
            result = await db.execute(sql, {"query": query, "company_id": company_id, "limit": limit})
            rows = result.fetchall()
            return [{"id": str(r[0]), "title": r[1], "text_score": float(r[2])} for r in rows]
        except Exception as exc:
            logger.warning("[HybridSearch] text_search_jobs falhou: %s", exc)
            return []

    async def _vector_search_jobs(
        self,
        company_id: str,
        db: AsyncSession,
        limit: int,
        embedding: list[float],
    ) -> list[dict[str, Any]]:
        try:
            embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"
            sql = text("""
                SELECT id, title,
                       1 - (embedding <=> :embedding::vector) AS vector_score
                FROM job_vacancies
                WHERE company_id = :company_id
                  AND embedding IS NOT NULL
                ORDER BY vector_score DESC
                LIMIT :limit
            """)
            result = await db.execute(sql, {
                "embedding": embedding_str,
                "company_id": company_id,
                "limit": limit,
            })
            rows = result.fetchall()
            return [{"id": str(r[0]), "title": r[1], "vector_score": float(r[2])} for r in rows]
        except Exception as exc:
            logger.warning("[HybridSearch] vector_search_jobs falhou: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Busca de candidatos
    # ------------------------------------------------------------------

    async def search_candidates(
        self,
        query: str,
        company_id: str,
        db: AsyncSession,
        limit: int = 10,
        embedding: list[float] | None = None,
    ) -> list[dict]:
        """
        Busca candidatos combinando tsvector (nome+resumo) e pgvector.
        """
        text_results = await self._text_search_candidates(query, company_id, db, limit)
        if embedding is None:
            for r in text_results:
                r["vector_score"] = 0.0
                r["hybrid_score"] = r.get("text_score", 0.0)
                r["source"] = "text"
            return text_results

        vector_results = await self._vector_search_candidates(company_id, db, limit, embedding)
        return _merge_results(text_results, vector_results, self.alpha, name_key="name")

    async def _text_search_candidates(
        self,
        query: str,
        company_id: str,
        db: AsyncSession,
        limit: int,
    ) -> list[dict[str, Any]]:
        try:
            sql = text("""
                SELECT id, name,
                       ts_rank(
                           to_tsvector('portuguese', coalesce(name,'') || ' ' || coalesce(summary,'')),
                           plainto_tsquery('portuguese', :query)
                       ) AS text_score
                FROM candidates
                WHERE company_id = :company_id
                  AND to_tsvector('portuguese', coalesce(name,'') || ' ' || coalesce(summary,''))
                      @@ plainto_tsquery('portuguese', :query)
                ORDER BY text_score DESC
                LIMIT :limit
            """)
            result = await db.execute(sql, {"query": query, "company_id": company_id, "limit": limit})
            rows = result.fetchall()
            return [{"id": str(r[0]), "name": r[1], "text_score": float(r[2])} for r in rows]
        except Exception as exc:
            logger.warning("[HybridSearch] text_search_candidates falhou: %s", exc)
            return []

    async def _vector_search_candidates(
        self,
        company_id: str,
        db: AsyncSession,
        limit: int,
        embedding: list[float],
    ) -> list[dict[str, Any]]:
        try:
            embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"
            sql = text("""
                SELECT id, name,
                       1 - (embedding <=> :embedding::vector) AS vector_score
                FROM candidates
                WHERE company_id = :company_id
                  AND embedding IS NOT NULL
                ORDER BY vector_score DESC
                LIMIT :limit
            """)
            result = await db.execute(sql, {
                "embedding": embedding_str,
                "company_id": company_id,
                "limit": limit,
            })
            rows = result.fetchall()
            return [{"id": str(r[0]), "name": r[1], "vector_score": float(r[2])} for r in rows]
        except Exception as exc:
            logger.warning("[HybridSearch] vector_search_candidates falhou: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Benchmark
    # ------------------------------------------------------------------

    async def benchmark(
        self,
        query: str,
        company_id: str,
        db: AsyncSession,
        embedding: list[float] | None = None,
    ) -> dict:
        """
        Executa e compara os 3 modos: text_only, vector_only, hybrid.
        Retorna métricas de latência e contagem de resultados.
        """
        results: dict[str, Any] = {}

        # --- text_only ---
        t0 = time.perf_counter()
        text_res = await self._text_search_jobs(query, company_id, db, 10)
        text_latency = (time.perf_counter() - t0) * 1000

        results["text_only"] = {
            "count": len(text_res),
            "latency_ms": round(text_latency, 2),
            "results": text_res,
        }

        # --- vector_only ---
        vector_latency = 0.0
        vector_res: list[dict[str, Any]] = []
        if embedding is not None:
            t0 = time.perf_counter()
            vector_res = await self._vector_search_jobs(company_id, db, 10, embedding)
            vector_latency = (time.perf_counter() - t0) * 1000

        results["vector_only"] = {
            "count": len(vector_res),
            "latency_ms": round(vector_latency, 2),
            "results": vector_res,
        }

        # --- hybrid ---
        t0 = time.perf_counter()
        hybrid_res = _merge_results(text_res, vector_res, self.alpha, name_key="title")
        hybrid_latency = (time.perf_counter() - t0) * 1000

        results["hybrid"] = {
            "count": len(hybrid_res),
            "latency_ms": round(hybrid_latency + text_latency + vector_latency, 2),
            "results": hybrid_res,
        }

        results["alpha"] = self.alpha
        results["query"] = query

        return results


# Singleton global
hybrid_search_service = HybridSearchService()
