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
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.tracing import get_tracer

logger = logging.getLogger(__name__)

# Limiar mínimo de similaridade coseno para resultados semânticos
_DEFAULT_SEMANTIC_THRESHOLD = 0.75

# ---------------------------------------------------------------------------
# Domínios RAG — aliases e normalização
# ---------------------------------------------------------------------------

DOMAIN_ALIASES: dict[str, str] = {
    "candidates": "talent",
    "talent": "talent",
    "job_vacancies": "jobs",
    "jobs": "jobs",
    "policy_blocks": "policy",
    "policy": "policy",
    "hiring_policy": "policy",
    "company_docs": "company",
    "company": "company",
    "general": "general",
}


def normalize_domain(domain: str) -> str:
    """Normaliza um identificador de domínio para o nome canônico.

    Aceita aliases (e.g. "candidates" → "talent", "job_vacancies" → "jobs").
    Retorna "general" para domínios desconhecidos.
    """
    return DOMAIN_ALIASES.get(domain, "general")

# Máximo de gênero único no top-10 (FairnessGuard)
_FAIRNESS_MAX_SINGLE_GENDER_RATIO = 0.70


# ---------------------------------------------------------------------------
# Resultado
# ---------------------------------------------------------------------------


@dataclass
class RAGSearchResult:
    """Resultado de uma busca RAG híbrida de candidatos."""

    results: list[dict[str, Any]]
    query: str
    total: int
    source: str  # "semantic" | "bm25" | "hybrid"
    fairness_ok: bool
    search_time_ms: float
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Embedding helper — mock/placeholder quando API não está configurada
# ---------------------------------------------------------------------------


async def generate_embedding(text: str, company_id: str | None = None) -> list[float] | None:
    """
    Gera embedding para o texto fornecido.

    Ordem de tentativa:
      1. EmbeddingCacheService (Redis) + OpenAI text-embedding-3-small
      2. Fallback Gemini text-embedding-004
      3. Retorna None em caso de falha (permite degradação para BM25)
    """
    try:
        from app.shared.services.embedding_cache_service import embedding_cache  # type: ignore[union-attr]

        cached = await embedding_cache.get_embedding(text, "text-embedding-3-small")
        if cached is not None:
            return cached
    except Exception as exc:
        logger.debug("[RAGPipeline] embedding_cache.get_embedding falhou: %s", exc)

    # Tentativa EmbeddingProviderFactory
    try:
        from app.shared.providers.embedding_factory import EmbeddingProviderFactory

        vector, _, embed_model = await EmbeddingProviderFactory.embed_with_fallback(
        text, company_id=company_id
    )  # Gap E.2 BYOK
        try:
            from app.shared.services.embedding_cache_service import embedding_cache  # type: ignore[union-attr]
            await embedding_cache.cache_embedding(text, vector, embed_model)
        except Exception:
            pass
        return vector
    except Exception as exc:
        logger.debug("[RAGPipeline] EmbeddingProviderFactory falhou: %s", exc)

    logger.debug("[RAGPipeline] Embedding indisponível — degradando para BM25")
    return None


# ---------------------------------------------------------------------------
# Normalização de scores
# ---------------------------------------------------------------------------


def _normalize(values: list[float]) -> list[float]:
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
    bm25_results: list[dict[str, Any]],
    semantic_results: list[dict[str, Any]],
    alpha: float,
) -> list[dict[str, Any]]:
    """
    Combina resultados BM25 + semânticos com score híbrido.
    alpha * semantic_score + (1 - alpha) * bm25_score
    """
    # Normalizar scores de cada fonte separadamente
    bm25_scores = _normalize([r.get("bm25_score", 0.0) for r in bm25_results])
    sem_scores = _normalize([r.get("semantic_score", 0.0) for r in semantic_results])

    merged: dict[str, dict[str, Any]] = {}

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


def _check_fairness(results: list[dict[str, Any]], top_n: int = 10) -> bool:
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
        domain: str | None = None,
        **kwargs,
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
        domain : str, optional
            Domínio RAG para filtragem isolada de embeddings
            (e.g. "talent", "jobs", "policy", "company", "general").
            Se fornecido, é normalizado via normalize_domain() antes de usar.

        Returns
        -------
        RAGSearchResult
        """
        t0 = time.perf_counter()
        _tracer = get_tracer()

        # FAR-2: FairnessGuard — bloquear queries discriminatórias antes do retrieval
        try:
            from app.shared.compliance.fairness_guard import FairnessGuard
            _fg = FairnessGuard()
            _fg_result = _fg.check(query)
            if _fg_result.is_blocked:
                logger.warning(
                    "[RAGPipeline][FAR-2] FairnessGuard bloqueou query: category=%s terms=%s",
                    _fg_result.category, _fg_result.blocked_terms,
                )
                _blocked = RAGSearchResult(
                    results=[],
                    query=query,
                    total=0,
                    source="blocked",
                    fairness_ok=False,
                    search_time_ms=0.0,
                    metadata={
                        "fairness_blocked": True,
                        "fairness_category": _fg_result.category,
                        "educational_message": _fg_result.educational_message,
                    },
                )
                try:
                    await _fg.log_check(result=_fg_result, context="rag_search", company_id=company_id)
                except Exception:
                    pass
                return _blocked
        except Exception as _fg_exc:
            logger.debug("[RAGPipeline] FairnessGuard check skipped: %s", _fg_exc)

        # Normalizar domínio se fornecido
        normalized_domain: str | None = normalize_domain(domain) if domain else None

        # --- Query Analysis ---
        async with _tracer.start_span("rag.query_analysis", attributes={
            "service": "rag_pipeline", "tier_name": "rag_query_analysis",
        }) as _qa_span:
            if alpha == 0.5:
                alpha = self._detect_query_type(query)
            _qa_span.set_attribute("alpha", str(alpha))
            _qa_span.set_attribute("domain", normalized_domain or "all")

        bm25_results: list[dict[str, Any]] = []
        semantic_results: list[dict[str, Any]] = []
        source = "bm25"

        # --- BM25 Search ---
        if alpha < 1.0:
            async with _tracer.start_span("rag.bm25_search", attributes={
                "service": "rag_pipeline", "tier_name": "rag_bm25_search",
            }) as _bm25_span:
                bm25_results = await self._bm25_search(query, company_id, db, limit, domain=normalized_domain)
                _bm25_span.set_attribute("result_count", str(len(bm25_results)))

        # --- Semantic Search ---
        embedding: list[float] | None = None
        if alpha > 0.0:
            async with _tracer.start_span("rag.semantic_search", attributes={
                "service": "rag_pipeline", "tier_name": "rag_semantic_search",
            }) as _sem_span:
                embedding = await generate_embedding(query, company_id=company_id)
                if embedding is not None:
                    semantic_results = await self._semantic_search(
                        embedding, company_id, db, limit, domain=normalized_domain
                    )
                    _sem_span.set_attribute("result_count", str(len(semantic_results)))
                    _sem_span.set_attribute("embedding_available", "true")
                else:
                    _sem_span.set_attribute("embedding_available", "false")
                    logger.info(
                        "[RAGPipeline] Embedding indisponível — usando apenas BM25 (query=%r)",
                        query[:60],
                    )

        # --- Hybrid Blending ---
        has_bm25 = bool(bm25_results)
        has_semantic = bool(semantic_results)

        async with _tracer.start_span("rag.hybrid_blending", attributes={
            "service": "rag_pipeline", "tier_name": "rag_hybrid_blending",
        }) as _blend_span:
            if alpha == 0.0 or not has_semantic:
                merged = []
                for r in bm25_results[:limit]:
                    r["hybrid_score"] = r.get("bm25_score", 0.0)
                    r["source"] = "bm25"
                    merged.append(r)
                source = "bm25"
            elif alpha == 1.0 or not has_bm25:
                merged = []
                for r in semantic_results[:limit]:
                    r["hybrid_score"] = r.get("semantic_score", 0.0)
                    r["source"] = "semantic"
                    merged.append(r)
                source = "semantic"
            else:
                merged = _merge_candidate_results(bm25_results, semantic_results, alpha)[:limit]
                source = "hybrid"
            _blend_span.set_attribute("source", source)
            _blend_span.set_attribute("merged_count", str(len(merged)))

        # --- Reranking (WRF) ---
        async with _tracer.start_span("rag.reranking", attributes={
            "service": "rag_pipeline", "tier_name": "rag_reranking",
        }) as _rerank_span:
            try:
                from app.shared.services.wrf_dynamic_k_service import WRFDynamicKService
                wrf_svc = WRFDynamicKService()
                for idx, item in enumerate(merged):
                    if "es_rank" not in item:
                        item["es_rank"] = idx + 1
                    if "pgv_rank" not in item:
                        item["pgv_rank"] = idx + 1
                es_scores = [float(r.get("bm25_score", 0)) for r in bm25_results] if bm25_results else None
                pgv_scores = [float(r.get("semantic_score", 0)) for r in semantic_results] if semantic_results else None
                merged = wrf_svc.rank_candidates(
                    merged,
                    es_scores=es_scores,
                    pgv_scores=pgv_scores,
                )
                _rerank_span.set_attribute("wrf_applied", "true")
                _rerank_span.set_attribute("reranked_count", str(len(merged)))
                logger.debug("[RAGPipeline] WRF re-ranking applied: %d results", len(merged))

                # WT-2022 P0.C: LGPD Art. 20 + EU AI Act Art. 13 audit trail
                # para reranking automatizado em RAG pipeline (hot path).
                # Apenas loga ranking de CANDIDATOS (domain=talent) — outros domains
                # (jobs/policy/company/general) nao tocam dados de candidatos.
                if normalized_domain == "talent":
                    try:
                        from app.shared.services.automated_decision_logger import (
                            PROTECTED_CRITERIA_PT,
                            log_automated_decision,
                        )
                        top_summary = [
                            {
                                "candidate_id": item.get("id") or item.get("candidate_id"),
                                "rank": item.get("wrf_rank"),
                                "score": item.get("wrf_score"),
                                "hybrid_score": item.get("hybrid_score"),
                            }
                            for item in merged[:10]
                        ]
                        await log_automated_decision(
                            db=db,
                            company_id=company_id,
                            decision_type="candidate_ranking_rag_rerank",
                            ai_model_used="rag_pipeline_hybrid_wrf",
                            explanation_text=(
                                f"RAG pipeline reranking (talent domain): "
                                f"{len(merged)} candidatos reranked com hybrid "
                                f"BM25+semantic+WRF. source={source}, alpha={alpha:.2f}."
                            ),
                            criteria_used=[
                                "bm25_score",
                                "semantic_score",
                                "hybrid_score",
                                "es_rank",
                                "pgv_rank",
                                "wrf_score",
                            ],
                            criteria_ignored=PROTECTED_CRITERIA_PT,
                            review_eligible=True,
                            extra_metadata={
                                "query_excerpt": (query or "")[:200],
                                "alpha": alpha,
                                "source": source,
                                "domain": normalized_domain,
                                "total_reranked": len(merged),
                                "top_10_ranked": top_summary,
                                "caller": "ai.services.rag_pipeline_service",
                            },
                        )
                    except Exception as _audit_exc:  # noqa: BLE001 - fail-safe
                        logger.warning(
                            "WT-2022 P0.C: rag_pipeline reranking audit log failed: %s",
                            _audit_exc, exc_info=True,
                        )
            except Exception as _wrf_exc:
                _rerank_span.set_attribute("wrf_applied", "false")
                logger.debug("[RAGPipeline] WRF re-ranking skipped: %s", _wrf_exc)

        # --- LLM Classification ---
        llm_classification_applied = False
        async with _tracer.start_span("rag.llm_classification", attributes={
            "service": "rag_pipeline", "tier_name": "rag_llm_classification",
        }) as _cls_span:
            try:
                from app.domains.sourcing.services.llm_job_classification_service import llm_job_classification_service
                if len(merged) > 3:
                    job_info = {
                        "title": kwargs.get("job_title", ""),
                        "area": kwargs.get("job_area", ""),
                        "requirements": kwargs.get("job_requirements", query),
                    }
                    if job_info["title"]:
                        classification_result = await llm_job_classification_service.filter_candidates(
                            job_info=job_info,
                            candidates=merged,
                        )
                        merged = classification_result["compatible_candidates"]
                        llm_classification_applied = True
                        _cls_span.set_attribute("applied", "true")
                        _cls_span.set_attribute("compatible", str(classification_result["total_compatible"]))
                        _cls_span.set_attribute("total_input", str(classification_result["total_input"]))
                        logger.debug(
                            "[RAGPipeline] LLM classification: %d/%d compatible",
                            classification_result["total_compatible"],
                            classification_result["total_input"],
                        )
                    else:
                        _cls_span.set_attribute("applied", "false")
                        _cls_span.set_attribute("reason", "no_job_title")
                else:
                    _cls_span.set_attribute("applied", "false")
                    _cls_span.set_attribute("reason", "too_few_results")
            except Exception as _cls_exc:
                _cls_span.set_attribute("applied", "false")
                logger.debug("[RAGPipeline] LLM classification skipped: %s", _cls_exc)

        # --- FairnessGuard (diversidade de gênero no top-10 + sector L3) ---
        fairness_ok = _check_fairness(merged, top_n=10)
        try:
            from app.shared.compliance.fairness_guard import FairnessGuard
            _fg_post = FairnessGuard()
            _sector = kwargs.get("sector")
            if _sector and merged:
                top_texts = [
                    f"{c.get('name', '')} {c.get('title', '')} {c.get('experience', '')}"
                    for c in merged[:10]
                ]
                for _txt in top_texts:
                    if _txt.strip():
                        _sector_result = await _fg_post.check_with_sector(
                            text=_txt,
                            sector=_sector,
                            action_type="ranking_output",
                        )
                        if _sector_result.is_blocked:
                            logger.warning(
                                "[RAGPipeline][FairnessGuard-L3] Sector bias detected: %s",
                                _sector_result.category,
                            )
                            fairness_ok = False
                            break
        except Exception as _fg_s_exc:
            logger.warning("[RAGPipeline] FairnessGuard sector check error: %s", _fg_s_exc)

        # FAR-5: Auditoria de disparate impact em tempo real nos resultados
        ranking_audit: dict[str, Any] = {}
        try:
            from app.shared.services.bias_audit_service import bias_audit_service
            ranking_audit = bias_audit_service.audit_ranking_results(
                results=merged,
                dimension="gender",
                top_n=10,
                company_id=company_id,
            )
            if not ranking_audit.get("fairness_ok", True) and ranking_audit.get("alert"):
                logger.warning("[RAGPipeline][FAR-5] %s", ranking_audit["alert"])
        except Exception as _audit_exc:
            logger.debug("[RAGPipeline] audit_ranking_results skipped: %s", _audit_exc)

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
                "domain": normalized_domain,
                "ranking_audit": ranking_audit,
                "llm_classification_applied": llm_classification_applied,
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
        domain: str | None = None,
    ) -> list[dict[str, Any]]:
        """Busca candidatos via PostgreSQL Full-Text Search (tsvector/tsquery)."""
        try:
            domain_filter = "AND domain = :domain" if domain else ""
            sql = text(f"""
                SELECT
                    id,
                    name,
                    coalesce(summary, '') AS summary,
                    coalesce(skills::text, '') AS skills,
                    coalesce(title, '') AS title,
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
                  {domain_filter}
                  AND to_tsvector('portuguese',
                          coalesce(name, '') || ' ' ||
                          coalesce(summary, '') || ' ' ||
                          coalesce(skills::text, '')
                      ) @@ plainto_tsquery('portuguese', :query)
                ORDER BY bm25_score DESC
                LIMIT :limit
            """)
            params: dict[str, Any] = {"query": query, "company_id": company_id, "limit": limit}
            if domain:
                params["domain"] = domain
            result = await db.execute(sql, params)
            rows = result.fetchall()
            return [
                {
                    "id": str(r[0]),
                    "name": r[1],
                    "experience": r[2],
                    "skills": r[3],
                    "title": r[4],
                    "bm25_score": float(r[5]),
                }
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
        embedding: list[float],
        company_id: str,
        db: AsyncSession,
        limit: int,
        domain: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Busca semântica via pgvector na tabela candidates.
        Filtra por cosine similarity >= semantic_threshold.
        """
        try:
            embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"
            domain_filter = "AND domain = :domain" if domain else ""
            sql = text(f"""
                SELECT
                    id,
                    name,
                    coalesce(summary, '') AS summary,
                    coalesce(skills::text, '') AS skills,
                    coalesce(title, '') AS title,
                    1 - (embedding <=> :embedding::vector) AS semantic_score
                FROM candidates
                WHERE company_id = :company_id
                  AND embedding IS NOT NULL
                  {domain_filter}
                  AND 1 - (embedding <=> :embedding::vector) >= :threshold
                ORDER BY semantic_score DESC
                LIMIT :limit
            """)
            params: dict[str, Any] = {
                "embedding": embedding_str,
                "company_id": company_id,
                "threshold": self.semantic_threshold,
                "limit": limit,
            }
            if domain:
                params["domain"] = domain
            result = await db.execute(sql, params)
            rows = result.fetchall()
            return [
                {
                    "id": str(r[0]),
                    "name": r[1],
                    "experience": r[2],
                    "skills": r[3],
                    "title": r[4],
                    "semantic_score": float(r[5]),
                }
                for r in rows
            ]
        except Exception as exc:
            logger.warning("[RAGPipeline] _semantic_search falhou: %s", exc)
            return []


rag_pipeline_service = RAGPipelineService()


def get_rag_pipeline_service() -> "RAGPipelineService":
    return rag_pipeline_service
