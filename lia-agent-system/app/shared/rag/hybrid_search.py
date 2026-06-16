"""BM25 hybrid search for RAG (UC-P3-01).

Complements the DB-backed hybrid in RAGPipelineService (rag_pipeline_service.py)
with an in-memory HybridSearchService that can be used against arbitrary
document lists (not just candidates/ table rows).

RAGPipelineService already does hybrid search against PostgreSQL tsvector + pgvector.
This service targets scenarios where documents are fetched into memory first
(e.g., policy blocks, FAQ chunks, company docs) and a quick in-memory hybrid
pass is needed before calling an LLM.

Combines dense vector search (embeddings) with sparse BM25 keyword search.
Uses Reciprocal Rank Fusion (RRF) to merge results.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class HybridSearchService:
    """Hybrid semantic + BM25 search for in-memory document lists (UC-P3-01).

    Designed for policy blocks, FAQ chunks, or any corpus loaded into memory.
    For candidate search against the DB, RAGPipelineService already provides
    hybrid tsvector + pgvector search.

    Args:
        alpha: Weight for semantic search (1-alpha for BM25).
               0.7 = 70% semantic, 30% BM25 (good default for job search).
    """

    def __init__(self, alpha: float = 0.7) -> None:
        self.alpha = alpha

    async def search(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """Hybrid search combining semantic + BM25.

        Args:
            query: Search query.
            candidates: List of dicts with 'id', 'text', and optional 'embedding'.
            top_k: Number of results to return.

        Returns:
            Ranked list with 'id' and 'hybrid_score'.
        """
        semantic_results = await self._semantic_search(query, candidates, top_k * 2)
        bm25_results = self._bm25_search(query, candidates, top_k * 2)
        return self._rrf_merge(semantic_results, bm25_results, top_k=top_k, alpha=self.alpha)

    # ------------------------------------------------------------------
    # BM25
    # ------------------------------------------------------------------

    def _bm25_search(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        top_k: int,
    ) -> list[tuple[str, float]]:
        """BM25 via rank-bm25 library; falls back to pure-Python term overlap."""
        try:
            from rank_bm25 import BM25Okapi  # type: ignore[import]

            texts = [c.get("text", "") for c in candidates]
            tokenized = [t.lower().split() for t in texts]
            bm25 = BM25Okapi(tokenized)
            scores = bm25.get_scores(query.lower().split())
            ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
            return [
                (candidates[i]["id"], float(score))
                for i, score in ranked[:top_k]
                if score > 0
            ]
        except ImportError:
            logger.debug("[HybridSearch] rank-bm25 not installed; using term-overlap fallback")
            query_terms = set(query.lower().split())
            results: list[tuple[str, float]] = []
            for c in candidates:
                text_terms = set(c.get("text", "").lower().split())
                score = len(query_terms & text_terms) / max(len(query_terms), 1)
                if score > 0:
                    results.append((c["id"], score))
            return sorted(results, key=lambda x: x[1], reverse=True)[:top_k]

    # ------------------------------------------------------------------
    # Semantic
    # ------------------------------------------------------------------

    async def _semantic_search(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        top_k: int,
    ) -> list[tuple[str, float]]:
        """Cosine similarity against pre-computed embeddings in candidate dicts."""
        try:
            import numpy as np  # type: ignore[import]
            from app.shared.providers.embedding_factory import EmbeddingProviderFactory

            provider = EmbeddingProviderFactory.get_default()
            query_embedding = await provider.embed_text(query)
            query_vec = np.array(query_embedding, dtype=float)
            norm_q = float(np.linalg.norm(query_vec)) + 1e-8

            results: list[tuple[str, float]] = []
            for c in candidates:
                if "embedding" in c:
                    emb = np.array(c["embedding"], dtype=float)
                    score = float(np.dot(query_vec, emb) / (norm_q * (np.linalg.norm(emb) + 1e-8)))
                    results.append((c["id"], score))
            return sorted(results, key=lambda x: x[1], reverse=True)[:top_k]
        except Exception as exc:
            logger.debug("[HybridSearch] Semantic search skipped: %s", exc)
            return []

    # ------------------------------------------------------------------
    # RRF merge
    # ------------------------------------------------------------------

    @staticmethod
    def _rrf_merge(
        semantic: list[tuple[str, float]],
        bm25: list[tuple[str, float]],
        top_k: int,
        alpha: float = 0.7,
        k: int = 60,
    ) -> list[dict[str, Any]]:
        """Reciprocal Rank Fusion weighted by alpha/1-alpha."""
        scores: dict[str, float] = {}
        for rank, (doc_id, _) in enumerate(semantic):
            scores[doc_id] = scores.get(doc_id, 0.0) + alpha / (k + rank + 1)
        for rank, (doc_id, _) in enumerate(bm25):
            scores[doc_id] = scores.get(doc_id, 0.0) + (1 - alpha) / (k + rank + 1)
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [{"id": doc_id, "hybrid_score": score} for doc_id, score in ranked]
