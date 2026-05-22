"""
Embedding Cache Service for LIA Agent System.

Armazena embeddings em Redis (backend primário, multi-instância safe) com
fallback automático para dict in-memory quando Redis está indisponível.

Padrão de uso:
    vector = await embedding_cache.get_embedding(text, model)
    if vector is None:
        vector = await generate_embedding(text, model)   # chamada ao LLM
        await embedding_cache.cache_embedding(text, vector, model)

O warm-up registra os títulos das vagas ativas no cache para que a primeira
chamada de matching não precise ir ao LLM para vagas conhecidas.
TTL padrão: SEMANTIC_CACHE_TTL (86400s = 24h).
"""
import hashlib
import json
import logging
import sys
import time


logger = logging.getLogger(__name__)

_REDIS_PREFIX = "emb:"
_REDIS_TTL_DEFAULT = 86400  # 24h — alinhado com SEMANTIC_CACHE_TTL

# Injectable monotonic clock for testability (monkeypatch this in tests).
_now = time.monotonic

# Max entries in local in-memory fallback (injectable for tests).
_LOCAL_MAX_ENTRIES: int = 500


class EmbeddingCacheService:
    """
    Cache de embeddings com Redis como backend primário.

    Fallback automático para dict in-memory quando Redis indisponível
    (ex: dev local sem Redis). Multi-instância safe quando Redis disponível.
    """

    def __init__(self):
        # Fallback in-memory: {key: (embedding, expiry_monotonic)}
        self._local: dict[str, tuple[list[float], float]] = {}
        self._redis = None
        self._redis_ok: bool = False
        self._warmed_up = False
        self._warm_up_job_count = 0

    # ------------------------------------------------------------------
    # Redis — lazy init
    # ------------------------------------------------------------------

    async def _get_redis(self):
        if self._redis is not None:
            return self._redis
        try:
            import redis.asyncio as aioredis

            from app.core.config import settings
            client = aioredis.from_url(
                settings.REDIS_URL, encoding="utf-8", decode_responses=True
            )
            await client.ping()
            self._redis = client
            self._redis_ok = True
            logger.info("[EmbeddingCache] Redis conectado: %s", settings.REDIS_URL)
        except Exception as exc:
            logger.warning("[EmbeddingCache] Redis indisponível, usando cache in-memory: %s", exc)
            self._redis_ok = False
        return self._redis

    # ------------------------------------------------------------------
    # Operações públicas
    # ------------------------------------------------------------------

    async def get_embedding(self, text: str, model: str = "text-embedding-3-small") -> list[float] | None:
        """Retorna embedding cacheado ou None se não encontrado/expirado."""
        key = self._make_key(text, model)
        redis = await self._get_redis()
        if redis and self._redis_ok:
            try:
                raw = await redis.get(key)
                if raw:
                    return json.loads(raw)
            except Exception as exc:
                logger.debug("[EmbeddingCache] Redis get falhou: %s", exc)
        # In-memory fallback: check TTL
        entry = self._local.get(key)
        if entry is None:
            return None
        embedding, expiry = entry
        if _now() > expiry:
            del self._local[key]
            return None
        return embedding

    async def cache_embedding(
        self,
        text: str,
        embedding: list[float],
        model: str = "text-embedding-3-small",
        ttl: int = _REDIS_TTL_DEFAULT,
    ) -> None:
        """Persiste embedding no Redis (e in-memory como write-through)."""
        key = self._make_key(text, model)
        serialized = json.dumps(embedding)
        redis = await self._get_redis()
        if redis and self._redis_ok:
            try:
                await redis.setex(key, ttl, serialized)
            except Exception as exc:
                logger.debug("[EmbeddingCache] Redis set falhou: %s", exc)
        # Write-through para local (acesso instantâneo sem rede) com TTL
        self._local[key] = (embedding, _now() + ttl)
        # Enforce size cap: evict oldest entries when over limit
        if len(self._local) > _LOCAL_MAX_ENTRIES:
            # Remove entries up to the cap (no ordering guarantee needed — just drop some)
            excess = len(self._local) - _LOCAL_MAX_ENTRIES
            for k in list(self._local.keys())[:excess]:
                del self._local[k]

    async def warm_up(self, db_session) -> None:
        """
        Warm-up: registra metadados de vagas ativas no cache.

        Não gera embeddings (evita custo de LLM no boot) — apenas marca os
        títulos como conhecidos. O embedding real é gerado na primeira chamada
        de matching e então cacheado automaticamente pelo caller.
        """
        if self._warmed_up:
            return
        try:
            # ADR-001-EXEMPT: warm-up scan across all active job vacancies (system-wide,
            # not tenant-scoped) for embedding pre-warming. Cross-domain JobVacancy reads
            # in job_management; introducing a foreign repo for a single warm-up site is
            # disproportionate. Bounded by limit(100).
            from sqlalchemy import select

            from lia_models.job_vacancy import JobVacancy

            # TENANT-EXEMPT: system-wide warm-up scan (ADR-001-EXEMPT context above),
            # bounded by limit(100); pre-warms embedding cache across all active vacancies
            stmt = (
                select(JobVacancy)
                .where(JobVacancy.status.in_(["active", "Ativa", "published"]))
                .limit(100)
            )
            result = await db_session.execute(stmt)
            active_jobs = result.scalars().all()
            self._warm_up_job_count = len(active_jobs)
            self._warmed_up = True
            logger.info(
                "[EmbeddingCache] Warm-up concluído: %d vagas ativas indexadas (embeddings gerados on-demand)",
                self._warm_up_job_count,
            )
        except Exception as exc:
            logger.warning("[EmbeddingCache] Warm-up falhou: %s", exc)
            self._warmed_up = True

    # ------------------------------------------------------------------
    # Utilitários
    # ------------------------------------------------------------------

    def _make_key(self, text: str, model: str) -> str:
        digest = hashlib.sha256(f"{model}:{text}".encode()).hexdigest()[:32]
        return f"{_REDIS_PREFIX}{digest}"

    def get_stats(self) -> dict:
        """Estatísticas para observabilidade."""
        local_bytes = sys.getsizeof(self._local)
        for k, v in self._local.items():
            local_bytes += sys.getsizeof(k) + sys.getsizeof(v)
        return {
            "backend": "redis" if self._redis_ok else "in-memory",
            "local_entries": len(self._local),
            "warmed_up": self._warmed_up,
            "warm_up_job_count": self._warm_up_job_count,
            "local_memory_mb": round(local_bytes / 1024 / 1024, 4),
        }

    def clear(self) -> None:
        """Limpa cache local (Redis não é afetado — TTL natural)."""
        self._local.clear()
        self._warmed_up = False
        self._warm_up_job_count = 0
        logger.info("[EmbeddingCache] Cache local limpo")


embedding_cache = EmbeddingCacheService()
