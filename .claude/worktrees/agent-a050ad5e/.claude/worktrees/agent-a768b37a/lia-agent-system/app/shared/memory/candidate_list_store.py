"""
CandidateListStore — Redis-backed store para listas completas de candidatos.

Armazena os dados completos (id, name, score, skills, stage, etc.) da última
lista retornada por uma sessão, com TTL de 30 minutos.

Separação de responsabilidades:
  ConversationState.last_candidates_shown  → apenas IDs (PostgreSQL / in-memory)
  CandidateListStore                       → dados completos (Redis TTL 30min)

Isso evita inflar o ConversationState com payloads grandes e garante que dados
sensíveis de candidatos expirem automaticamente no cache.

Fallback: in-memory dict quando Redis indisponível (dev local / testes).
"""
import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

LIST_TTL_SECONDS = 1800  # 30 minutos
KEY_PREFIX = "candidate_list:"

try:
    import redis.asyncio as aioredis
    _AIOREDIS_AVAILABLE = True
except ImportError:
    aioredis = None  # type: ignore
    _AIOREDIS_AVAILABLE = False


class CandidateListStore:
    """
    Store Redis + in-memory fallback para listas completas de candidatos.

    Uso:
        store = CandidateListStore()
        await store.set(conv_id, candidates)       # salva lista completa
        candidates = await store.get(conv_id)      # recupera (ou None se expirado)
        candidate = await store.get_by_position(conv_id, position=2)  # 0-based
        await store.delete(conv_id)
    """

    def __init__(self) -> None:
        self._memory: Dict[str, List[Dict[str, Any]]] = {}
        self._redis: Optional[Any] = None
        self._redis_available = False

    async def _get_redis(self) -> Optional[Any]:
        if not _AIOREDIS_AVAILABLE:
            return None
        if self._redis is not None:
            return self._redis
        try:
            from app.core.config import settings
            self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            await self._redis.ping()
            self._redis_available = True
            logger.info("[CandidateListStore] Connected to Redis")
        except Exception as exc:
            logger.warning(
                "[CandidateListStore] Redis unavailable (%s), using in-memory fallback", exc
            )
            self._redis = None
            self._redis_available = False
        return self._redis

    async def set(self, conv_id: str, candidates: List[Dict[str, Any]]) -> None:
        """Salva a lista completa de candidatos para a conversa com TTL 30min."""
        if not candidates:
            return
        key = KEY_PREFIX + conv_id
        redis = await self._get_redis()
        if redis and self._redis_available:
            try:
                await redis.setex(key, LIST_TTL_SECONDS, json.dumps(candidates))
                logger.debug(
                    "[CandidateListStore] Stored %d candidates for conv=%s", len(candidates), conv_id
                )
                return
            except Exception as exc:
                logger.warning("[CandidateListStore] Redis set failed (%s), falling back", exc)
        # Fallback: guarda no dict in-memory (sem TTL, expira com o processo)
        self._memory[conv_id] = candidates

    async def get(self, conv_id: str) -> Optional[List[Dict[str, Any]]]:
        """Recupera a lista completa de candidatos. Retorna None se não encontrada/expirada."""
        key = KEY_PREFIX + conv_id
        redis = await self._get_redis()
        if redis and self._redis_available:
            try:
                raw = await redis.get(key)
                if raw is not None:
                    return json.loads(raw)
                return None
            except Exception as exc:
                logger.warning("[CandidateListStore] Redis get failed (%s), falling back", exc)
        return self._memory.get(conv_id)

    async def get_by_position(
        self, conv_id: str, position: int
    ) -> Optional[Dict[str, Any]]:
        """
        Retorna o candidato na posição `position` (0-based) da última lista.
        Retorna None se a lista não existir ou a posição estiver fora do range.
        """
        candidates = await self.get(conv_id)
        if not candidates:
            return None
        if position < 0 or position >= len(candidates):
            logger.debug(
                "[CandidateListStore] Position %d out of range (list size=%d)",
                position, len(candidates),
            )
            return None
        return candidates[position]

    async def delete(self, conv_id: str) -> None:
        """Remove a lista da conversa (ex: quando uma nova busca é iniciada)."""
        key = KEY_PREFIX + conv_id
        redis = await self._get_redis()
        if redis and self._redis_available:
            try:
                await redis.delete(key)
                return
            except Exception as exc:
                logger.warning("[CandidateListStore] Redis delete failed (%s)", exc)
        self._memory.pop(conv_id, None)

    async def get_ttl(self, conv_id: str) -> Optional[int]:
        """Retorna o TTL restante em segundos (-1 se não existe, -2 se sem TTL)."""
        redis = await self._get_redis()
        if redis and self._redis_available:
            try:
                return await redis.ttl(KEY_PREFIX + conv_id)
            except Exception:
                pass
        return None


# Singleton — compartilhado entre todos os workers do mesmo processo
candidate_list_store = CandidateListStore()
