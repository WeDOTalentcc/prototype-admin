"""Response reranking for RAG (UC-P3-02).

Reranks search results by relevance to query using Cohere Rerank API.
Falls back to simple heuristic ordering if Cohere is unavailable.

Primary: Cohere Rerank API (free tier available, env: COHERE_API_KEY)
Fallback: Cross-encoder heuristic (query-document term overlap)
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class RerankerService:
    """Reranks documents by relevance to a query (UC-P3-02).

    Usage::

        reranker = RerankerService()
        docs = [{"id": "1", "text": "..."}, ...]
        reranked = await reranker.rerank("Python engineer", docs, top_n=5)
    """

    def __init__(self, model: str = "rerank-multilingual-v3.0") -> None:
        # multilingual chosen for pt-BR support; override via subclass if needed
        self.model = model
        self._api_key = os.getenv("COHERE_API_KEY")

    async def rerank(
        self,
        query: str,
        documents: list[dict[str, Any]],
        top_n: int | None = None,
        text_field: str = "text",
    ) -> list[dict[str, Any]]:
        """Rerank documents by relevance to query.

        Args:
            query: The search query.
            documents: List of dicts that contain at least `text_field`.
            top_n: Return only top N results; None = all.
            text_field: Dict key that holds the document text.

        Returns:
            Documents reranked by relevance with 'rerank_score' added.
        """
        if self._api_key:
            try:
                return await self._cohere_rerank(query, documents, top_n, text_field)
            except Exception as exc:
                logger.warning("[Reranker] Cohere rerank failed, using fallback: %s", exc)

        return self._heuristic_rerank(query, documents, top_n, text_field)

    # ------------------------------------------------------------------
    # Cohere (primary)
    # ------------------------------------------------------------------

    async def _cohere_rerank(
        self,
        query: str,
        documents: list[dict[str, Any]],
        top_n: int | None,
        text_field: str,
    ) -> list[dict[str, Any]]:
        import cohere  # type: ignore[import]

        co = cohere.AsyncClient(self._api_key)
        texts = [doc.get(text_field, "") for doc in documents]
        response = await co.rerank(
            model=self.model,
            query=query,
            documents=texts,
            top_n=top_n or len(documents),
        )
        reranked: list[dict[str, Any]] = []
        for result in response.results:
            doc = dict(documents[result.index])
            doc["rerank_score"] = float(result.relevance_score)
            reranked.append(doc)
        return reranked

    # ------------------------------------------------------------------
    # Heuristic fallback
    # ------------------------------------------------------------------

    def _heuristic_rerank(
        self,
        query: str,
        documents: list[dict[str, Any]],
        top_n: int | None,
        text_field: str,
    ) -> list[dict[str, Any]]:
        """Term-overlap heuristic — no external dependency required."""
        query_terms = set(query.lower().split())
        scored: list[dict[str, Any]] = []
        for doc in documents:
            text = doc.get(text_field, "").lower()
            term_matches = sum(1 for t in query_terms if t in text)
            score = term_matches / max(len(query_terms), 1)
            d = dict(doc)
            d["rerank_score"] = score
            scored.append(d)
        scored.sort(key=lambda x: x["rerank_score"], reverse=True)
        return scored[:top_n] if top_n else scored
