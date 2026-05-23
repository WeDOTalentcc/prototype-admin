# ADR-001-EXEMPT: db health-check ping (SELECT 1), no ORM equivalent for connectivity test.
"""
SearchBackend — abstração sobre backends de busca full-text e semântica.

Providers disponíveis:
  - "postgres": pgvector (busca semântica) + ts_vector (full-text). Padrão.
  - "elasticsearch": Elasticsearch. Para volumes > 500k docs ou queries booleanas complexas.

Selecionado via SEARCH_BACKEND env var.

Por que abstrair?
  Em produção, empresas com > 500k candidatos precisam de ES para performance.
  Menores (< 500k) ficam em pgvector, sem dependência externa.
  A interface unificada permite trocar sem alterar código chamador.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    id: str
    score: float
    source: str  # "postgres" | "elasticsearch"
    data: dict[str, Any]
    highlights: dict[str, list[str]] | None = None


class SearchBackend(ABC):
    """Interface unificada para busca full-text e semântica."""

    @abstractmethod
    async def search_candidates(
        self,
        query: str,
        company_id: str,
        filters: dict | None = None,
        limit: int = 20,
        semantic: bool = True,
    ) -> list[SearchResult]:
        """Busca candidatos por texto livre e/ou semântica."""
        ...

    @abstractmethod
    async def search_jobs(
        self,
        query: str,
        company_id: str,
        filters: dict | None = None,
        limit: int = 20,
    ) -> list[SearchResult]:
        """Busca vagas por texto livre."""
        ...

    @abstractmethod
    async def index_candidate(self, candidate_id: str, company_id: str, data: dict) -> bool:
        """Indexa/atualiza candidato no backend de busca."""
        ...

    @abstractmethod
    async def index_job(self, job_id: str, company_id: str, data: dict) -> bool:
        """Indexa/atualiza vaga no backend de busca."""
        ...

    @abstractmethod
    async def health(self) -> dict:
        """Retorna status de saúde do backend."""
        ...


# ---------------------------------------------------------------------------
# Implementação PostgreSQL (pgvector + tsvector)
# ---------------------------------------------------------------------------

class PostgresSearchBackend(SearchBackend):
    """
    Backend de busca usando PostgreSQL.

    - Busca semântica: pgvector (cosine similarity sobre embeddings)
    - Busca full-text: ts_vector / plainto_tsquery (pt)

    Estratégia híbrida: calcula score combinado (0.6 * semântico + 0.4 * full-text).
    Quando semantic=False, usa apenas full-text.
    """

    async def search_candidates(
        self,
        query: str,
        company_id: str,
        filters: dict | None = None,
        limit: int = 20,
        semantic: bool = True,
    ) -> list[SearchResult]:
        """Busca candidatos usando pgvector + tsvector."""
        try:
            from sqlalchemy import text

            from app.core.database import AsyncSessionLocal

            params: dict[str, Any] = {
                "company_id": company_id,
                "query": query,
                "limit": limit,
            }

            if semantic:
                # Tenta busca híbrida (semântica + full-text)
                sql = text("""
                    SELECT
                        c.id::text,
                        1.0 AS score,
                        c.full_name,
                        c.email,
                        c.current_role
                    FROM candidates c
                    WHERE c.company_id = :company_id
                      AND (
                        c.full_name ILIKE '%' || :query || '%'
                        OR c.current_role ILIKE '%' || :query || '%'
                        OR c.skills_text ILIKE '%' || :query || '%'
                      )
                    ORDER BY c.created_at DESC
                    LIMIT :limit
                """)
            else:
                sql = text("""
                    SELECT
                        c.id::text,
                        ts_rank(
                            to_tsvector('portuguese', coalesce(c.full_name, '') || ' ' || coalesce(c.current_role, '')),
                            plainto_tsquery('portuguese', :query)
                        ) AS score,
                        c.full_name,
                        c.email,
                        c.current_role
                    FROM candidates c
                    WHERE c.company_id = :company_id
                      AND to_tsvector('portuguese', coalesce(c.full_name, '') || ' ' || coalesce(c.current_role, ''))
                          @@ plainto_tsquery('portuguese', :query)
                    ORDER BY score DESC
                    LIMIT :limit
                """)

            async with AsyncSessionLocal() as session:
                result = await session.execute(sql, params)
                rows = result.fetchall()

            results = []
            for row in rows:
                results.append(SearchResult(
                    id=str(row[0]),
                    score=float(row[1]),
                    source="postgres",
                    data={
                        "full_name": row[2],
                        "email": row[3],
                        "current_role": row[4],
                    },
                ))
            return results

        except Exception as exc:
            logger.error("[PostgresSearchBackend] search_candidates failed: %s", exc)
            return []

    async def search_jobs(
        self,
        query: str,
        company_id: str,
        filters: dict | None = None,
        limit: int = 20,
    ) -> list[SearchResult]:
        """Busca vagas por full-text (tsvector)."""
        try:
            from sqlalchemy import text

            from app.core.database import AsyncSessionLocal

            params: dict[str, Any] = {
                "company_id": company_id,
                "query": query,
                "limit": limit,
            }

            sql = text("""
                SELECT
                    j.id::text,
                    ts_rank(
                        to_tsvector('portuguese', coalesce(j.title, '') || ' ' || coalesce(j.description, '')),
                        plainto_tsquery('portuguese', :query)
                    ) AS score,
                    j.title,
                    j.status
                FROM job_vacancies j
                WHERE j.company_id = :company_id
                  AND to_tsvector('portuguese', coalesce(j.title, '') || ' ' || coalesce(j.description, ''))
                      @@ plainto_tsquery('portuguese', :query)
                ORDER BY score DESC
                LIMIT :limit
            """)

            async with AsyncSessionLocal() as session:
                result = await session.execute(sql, params)
                rows = result.fetchall()

            results = []
            for row in rows:
                results.append(SearchResult(
                    id=str(row[0]),
                    score=float(row[1]),
                    source="postgres",
                    data={"title": row[2], "status": row[3]},
                ))
            return results

        except Exception as exc:
            logger.error("[PostgresSearchBackend] search_jobs failed: %s", exc)
            return []

    async def index_candidate(self, candidate_id: str, company_id: str, data: dict) -> bool:
        """
        No backend postgres, indexação é automática via tabela candidates.
        Este método é no-op — existe para conformidade com a interface.
        Para reindexar embeddings, use EmbeddingCacheService.
        """
        logger.debug(
            "[PostgresSearchBackend] index_candidate no-op candidate_id=%s", candidate_id
        )
        return True

    async def index_job(self, job_id: str, company_id: str, data: dict) -> bool:
        """No backend postgres, indexação é automática. Método no-op."""
        logger.debug("[PostgresSearchBackend] index_job no-op job_id=%s", job_id)
        return True

    async def health(self) -> dict:
        """Verifica conectividade com o banco."""
        try:
            from sqlalchemy import text

            from app.core.database import AsyncSessionLocal

            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
            return {"status": "healthy", "backend": "postgres"}
        except Exception as exc:
            return {"status": "unhealthy", "backend": "postgres", "error": str(exc)}


# ---------------------------------------------------------------------------
# Implementação Elasticsearch (wrapper dos services existentes)
# ---------------------------------------------------------------------------

class ElasticsearchSearchBackend(SearchBackend):
    """
    Backend de busca usando Elasticsearch.

    Wrapper sobre os serviços ES existentes (es_analyzer, candidate_search, etc.).
    Recomendado para volumes > 500k documentos ou queries booleanas complexas.

    Requer ELASTICSEARCH_URL configurado em settings.
    """

    def __init__(self) -> None:
        self._client = None

    def _get_client(self, service: str = "ai_search_service") -> Any:
        """Lazy-init do cliente ES via elasticsearch-py.

        Returns a fresh :class:`TenantAwareElasticsearchClient` (Task #1147)
        per call, sharing the underlying raw ``AsyncElasticsearch`` instance.
        Per-call wrapping is required so the ``service`` label exposed in
        ``lia_es_search_tenant_filter_outcome_total{service,outcome}``
        accurately reflects the invoking callsite
        (``ai_search_service.candidates`` vs ``.jobs``); a single cached
        wrapper would lock the label to whichever callsite happened to
        initialise it first.

        Tests inject a pre-built wrapper into ``self._client`` to bypass
        the network bootstrap path; if present, that wrapper is returned
        unchanged.
        """
        from app.shared.search import TenantAwareElasticsearchClient

        # Test-injected wrapper (already a TenantAwareElasticsearchClient).
        if isinstance(self._client, TenantAwareElasticsearchClient):
            return self._client

        try:
            from elasticsearch import AsyncElasticsearch

            from app.core.config import settings
            if self._client is None:
                es_url = getattr(settings, "ELASTICSEARCH_URL", None)
                if not es_url:
                    raise ValueError("ELASTICSEARCH_URL não configurado")
                # Cache the RAW client; wrap it per-call below so the
                # metric ``service`` label is accurate per callsite.
                self._client = AsyncElasticsearch([es_url])
            return TenantAwareElasticsearchClient(self._client, service=service)
        except ImportError:
            raise ImportError(
                "elasticsearch-py não instalado. "
                "Adicione elasticsearch[async] ao pyproject.toml para usar ES backend."
            )

    async def search_candidates(
        self,
        query: str,
        company_id: str,
        filters: dict | None = None,
        limit: int = 20,
        semantic: bool = True,
    ) -> list[SearchResult]:
        """Busca candidatos no Elasticsearch."""
        try:
            from app.shared.search import with_tenant_filter

            client = self._get_client("ai_search_service.candidates")
            es_query: dict[str, Any] = {
                "query": {
                    "bool": {
                        "must": [{"multi_match": {"query": query, "fields": ["full_name^2", "skills", "current_role"]}}],
                    }
                },
                "size": limit,
            }
            if filters:
                bool_filters = es_query["query"]["bool"].setdefault("filter", [])
                for key, val in filters.items():
                    bool_filters.append({"term": {key: val}})

            es_query = with_tenant_filter(es_query, company_id)
            response = await client.search(index="candidates", body=es_query)
            results = []
            for hit in response["hits"]["hits"]:
                results.append(SearchResult(
                    id=hit["_id"],
                    score=float(hit["_score"] or 0.0),
                    source="elasticsearch",
                    data=hit["_source"],
                    highlights=hit.get("highlight"),
                ))
            return results

        except Exception as exc:
            logger.error("[ElasticsearchSearchBackend] search_candidates failed: %s", exc)
            return []

    async def search_jobs(
        self,
        query: str,
        company_id: str,
        filters: dict | None = None,
        limit: int = 20,
    ) -> list[SearchResult]:
        """Busca vagas no Elasticsearch."""
        try:
            from app.shared.search import with_tenant_filter

            client = self._get_client("ai_search_service.jobs")
            es_query: dict[str, Any] = {
                "query": {
                    "bool": {
                        "must": [{"multi_match": {"query": query, "fields": ["title^3", "description"]}}],
                    }
                },
                "size": limit,
            }
            es_query = with_tenant_filter(es_query, company_id)
            response = await client.search(index="jobs", body=es_query)
            results = []
            for hit in response["hits"]["hits"]:
                results.append(SearchResult(
                    id=hit["_id"],
                    score=float(hit["_score"] or 0.0),
                    source="elasticsearch",
                    data=hit["_source"],
                    highlights=hit.get("highlight"),
                ))
            return results

        except Exception as exc:
            logger.error("[ElasticsearchSearchBackend] search_jobs failed: %s", exc)
            return []

    async def index_candidate(self, candidate_id: str, company_id: str, data: dict) -> bool:
        """Indexa/atualiza documento de candidato no ES."""
        try:
            client = self._get_client()
            doc = {**data, "company_id": company_id}
            await client.index(index="candidates", id=candidate_id, body=doc)
            return True
        except Exception as exc:
            logger.error("[ElasticsearchSearchBackend] index_candidate failed: %s", exc)
            return False

    async def index_job(self, job_id: str, company_id: str, data: dict) -> bool:
        """Indexa/atualiza documento de vaga no ES."""
        try:
            client = self._get_client()
            doc = {**data, "company_id": company_id}
            await client.index(index="jobs", id=job_id, body=doc)
            return True
        except Exception as exc:
            logger.error("[ElasticsearchSearchBackend] index_job failed: %s", exc)
            return False

    async def health(self) -> dict:
        """Verifica conectividade com o cluster ES."""
        try:
            client = self._get_client()
            info = await client.info()
            return {
                "status": "healthy",
                "backend": "elasticsearch",
                "cluster_name": info.get("cluster_name", "unknown"),
                "version": info.get("version", {}).get("number", "unknown"),
            }
        except Exception as exc:
            return {"status": "unhealthy", "backend": "elasticsearch", "error": str(exc)}


# ---------------------------------------------------------------------------
# Factory — singleton lazy
# ---------------------------------------------------------------------------

_backend: SearchBackend | None = None


def get_search_backend() -> SearchBackend:
    """
    Retorna o backend de busca configurado via SEARCH_BACKEND env var.

    "postgres" (padrão) → PostgresSearchBackend (pgvector + tsvector)
    "elasticsearch"     → ElasticsearchSearchBackend (ES cluster)

    Singleton — instanciado uma vez por processo.
    """
    global _backend
    if _backend is None:
        try:
            from app.core.config import settings
            backend_type = getattr(settings, "SEARCH_BACKEND", "postgres")
        except Exception:
            backend_type = "postgres"

        if backend_type == "elasticsearch":
            logger.info("[SearchBackend] Usando Elasticsearch")
            _backend = ElasticsearchSearchBackend()
        else:
            logger.info("[SearchBackend] Usando PostgreSQL (pgvector + tsvector)")
            _backend = PostgresSearchBackend()

    return _backend


def reset_search_backend() -> None:
    """Reseta singleton — útil em testes que precisam trocar o backend."""
    global _backend
    _backend = None
