"""
VectorSemanticCache — cache semântico baseado em pgvector para roteamento.

Substitui o SemanticCache (hash MD5) para mensagens semanticamente similares:
  - Hash: "criar vaga dev" e "cria uma vaga pra dev" → MISS (strings diferentes)
  - Vector: "criar vaga dev" e "cria uma vaga pra dev" → HIT (cosine_sim ≈ 0.97)

Reduz chamadas LLM em 40-60% após semanas de uso ao capturar variações
semânticas da mesma intenção.

Estratégia de embedding:
  1. Reutiliza EmbeddingCacheService (Redis) para evitar re-gerar embeddings
  2. Provider primário: OpenAI text-embedding-3-small (1536 dims, barato)
  3. Fallback: Gemini text-embedding-004 (768 dims) via EmbeddingService
  4. Falha graciosa: qualquer erro retorna None sem quebrar o router

Tabela: routing_cache_vectors (criada em 028_add_routing_cache_vectors.py)
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Dimensão do modelo OpenAI text-embedding-3-small
_OPENAI_EMBEDDING_DIM = 1536
# Dimensão do fallback Gemini text-embedding-004
_GEMINI_EMBEDDING_DIM = 768

# Prefixo no EmbeddingCacheService para diferenciar do cache de vagas
_EMBED_MODEL_OPENAI = "text-embedding-3-small"
_EMBED_MODEL_GEMINI = "text-embedding-004"


class VectorSemanticCache:
    """
    Cache semântico baseado em pgvector para roteamento de intenções.

    Diferença do SemanticCache (hash MD5):
    - Hash: "criar vaga dev" e "cria uma vaga pra dev" → MISS (strings diferentes)
    - Vector: "criar vaga dev" e "cria uma vaga pra dev" → HIT (cosine_sim ≈ 0.97)

    Reduz chamadas LLM em 40-60% após semanas de uso.
    """

    def __init__(
        self,
        similarity_threshold: float | None = None,
        embedding_model: str = _EMBED_MODEL_OPENAI,
    ):
        if similarity_threshold is None:
            try:
                from lia_config.config import settings as _s
                similarity_threshold = _s.ROUTER_VECTOR_SIMILARITY_THRESHOLD
            except Exception:
                similarity_threshold = 0.85  # fallback se settings indisponível
        self.threshold = similarity_threshold
        self.embedding_model = embedding_model
        self._db_available: bool | None = None  # None = não testado ainda

    # ------------------------------------------------------------------
    # Operações públicas
    # ------------------------------------------------------------------

    async def get(self, message: str, company_id: str | None = None) -> dict[str, Any] | None:
        """
        Busca por entrada semanticamente similar no pgvector.

        Retorna o dict de roteamento cacheado ou None se:
        - cache vazio
        - similaridade abaixo do threshold
        - qualquer falha de infra (DB, embedding service)
        """
        try:
            embedding = await self._get_embedding(message, company_id=company_id)
            if embedding is None:
                return None

            result = await self._query_similar(embedding)
            return result
        except Exception as exc:
            logger.debug("[VectorSemanticCache] get falhou (gracioso): %s", exc)
            return None

    async def set(self, message: str, result: dict[str, Any], company_id: str | None = None) -> None:
        """
        Armazena resultado de roteamento com embedding da mensagem.

        Falha graciosamente — nunca propaga exceção para o caller.
        """
        try:
            embedding = await self._get_embedding(message, company_id=company_id)
            if embedding is None:
                return

            await self._insert_cache(message, embedding, result)
        except Exception as exc:
            logger.debug("[VectorSemanticCache] set falhou (gracioso): %s", exc)

    # ------------------------------------------------------------------
    # Embedding
    # ------------------------------------------------------------------

    async def _get_embedding(self, text: str, company_id: str | None = None) -> list[float] | None:
        """
        Gera embedding com cache Redis via EmbeddingCacheService.

        Ordem de tentativa:
        1. Cache Redis (evita re-chamar LLM para mensagens já vistas)
        2. OpenAI text-embedding-3-small (1536 dims)
        3. Gemini text-embedding-004 (768 dims) — fallback
        """
        try:
            from app.shared.services.embedding_cache_service import embedding_cache

            cached = await embedding_cache.get_embedding(text, self.embedding_model)
            if cached is not None:
                return cached

            # Gerar novo embedding
            vector = await self._generate_embedding(text, company_id=company_id)
            if vector is not None:
                await embedding_cache.cache_embedding(text, vector, self.embedding_model)
            return vector
        except Exception as exc:
            logger.debug("[VectorSemanticCache] _get_embedding falhou: %s", exc)
            return None

    async def _generate_embedding(self, text: str, company_id: str | None = None) -> list[float] | None:
        """Gera embedding via OpenAI (primário) ou Gemini (fallback)."""
        # Tentativa 1: EmbeddingProviderFactory (OpenAI / fallback)
        try:
            from app.shared.providers.embedding_factory import EmbeddingProviderFactory

            vector, provider_name, _ = await EmbeddingProviderFactory.embed_with_fallback(
                text[:8000], company_id=company_id
            )  # Gap E.1 BYOK: roteia para a chave do tenant quando configurada
            self.embedding_model = _EMBED_MODEL_OPENAI if "openai" in provider_name.lower() else _EMBED_MODEL_GEMINI
            return vector
        except Exception as exc:
            logger.debug("[VectorSemanticCache] EmbeddingProviderFactory falhou: %s", exc)

        # Tentativa 2: Gemini text-embedding-004 (fallback)
        try:
            from app.shared.intelligence.embedding_service import embedding_service

            vector = await embedding_service.generate_embedding(text, provider="gemini")
            self.embedding_model = _EMBED_MODEL_GEMINI
            return vector
        except Exception as exc:
            logger.debug("[VectorSemanticCache] Gemini embedding falhou: %s", exc)

        return None

    # ------------------------------------------------------------------
    # pgvector — queries
    # ------------------------------------------------------------------

    async def _get_db(self):
        """Retorna sessão de DB async (lazy, sem falhar na inicialização)."""
        from app.core.database import AsyncSessionLocal
        return AsyncSessionLocal()

    async def _query_similar(self, embedding: list[float]) -> dict[str, Any] | None:
        """
        Busca entrada com cosine similarity >= threshold no pgvector.
        Incrementa hit_count e last_hit_at ao encontrar.
        """

        # Formata o vetor para a sintaxe pgvector
        vec_str = "[" + ",".join(str(v) for v in embedding) + "]"

        sql = """
            SELECT id, domain_id, confidence, source, hit_count
            FROM routing_cache_vectors
            WHERE 1 - (message_embedding <=> :embedding::vector) >= :threshold
            ORDER BY message_embedding <=> :embedding::vector
            LIMIT 1
        """

        # Z5-03: near-miss query para logging — busca o melhor match abaixo do threshold
        near_miss_sql = """
            SELECT domain_id, 1 - (message_embedding <=> :embedding::vector) AS similarity
            FROM routing_cache_vectors
            ORDER BY message_embedding <=> :embedding::vector
            LIMIT 1
        """

        try:
            db = await self._get_db()
            async with db as session:
                from sqlalchemy import text as sa_text

                row = await session.execute(
                    sa_text(sql),
                    {"embedding": vec_str, "threshold": self.threshold},
                )
                row = row.fetchone()
                if row is None:
                    # Z5-03: logar near-misses para análise de threshold A/B
                    try:
                        _near_margin = 0.05
                        try:
                            from lia_config.config import settings as _s
                            _near_margin = _s.ROUTER_VECTOR_NEAR_MISS_LOG_MARGIN
                        except Exception:
                            # Settings opcional: usa default 0.05 se nao configurado/disponivel
                            pass
                        nm_row = await session.execute(
                            sa_text(near_miss_sql),
                            {"embedding": vec_str},
                        )
                        nm_row = nm_row.fetchone()
                        if nm_row is not None:
                            _nm_domain, _nm_sim = nm_row
                            if _nm_sim >= (self.threshold - _near_margin):
                                logger.debug(
                                    "[VectorSemanticCache][near-miss] melhor_sim=%.4f threshold=%.2f "
                                    "domain=%s — considere reduzir ROUTER_VECTOR_SIMILARITY_THRESHOLD",
                                    _nm_sim, self.threshold, _nm_domain,
                                )
                    except Exception as nm_exc:
                        logger.warning(
                            "[VectorSemanticCache] near-miss query failed - threshold A/B sinal perdido: %s",
                            nm_exc, exc_info=True,
                        )
                    return None

                row_id, domain_id, confidence, source, hit_count = row

                # Atualiza hit_count + last_hit_at
                update_sql = """
                    UPDATE routing_cache_vectors
                    SET hit_count = hit_count + 1, last_hit_at = NOW()
                    WHERE id = :row_id
                """
                await session.execute(sa_text(update_sql), {"row_id": str(row_id)})
                await session.commit()

                return {
                    "domain_id": domain_id,
                    "confidence": confidence,
                    "source": source,
                    "cache_source": "vector_cache",
                }
        except Exception as exc:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.debug("[VectorSemanticCache] _query_similar falhou: %s", exc)
            return None

    async def _insert_cache(
        self,
        message: str,
        embedding: list[float],
        result: dict[str, Any],
    ) -> None:
        """Insere novo registro no routing_cache_vectors."""
        vec_str = "[" + ",".join(str(v) for v in embedding) + "]"

        sql = """
            INSERT INTO routing_cache_vectors
                (message_text, message_embedding, domain_id, confidence, source)
            VALUES
                (:message_text, :embedding::vector, :domain_id, :confidence, :source)
            ON CONFLICT DO NOTHING
        """

        try:
            db = await self._get_db()
            async with db as session:
                from sqlalchemy import text as sa_text

                await session.execute(
                    sa_text(sql),
                    {
                        "message_text": message[:2000],
                        "embedding": vec_str,
                        "domain_id": result.get("domain_id", "recruiter_assistant"),
                        "confidence": float(result.get("confidence", 0.5)),
                        "source": str(result.get("source", "unknown")),
                    },
                )
                await session.commit()
        except Exception as exc:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.debug("[VectorSemanticCache] _insert_cache falhou: %s", exc)


# Singleton compartilhado
vector_semantic_cache = VectorSemanticCache()
