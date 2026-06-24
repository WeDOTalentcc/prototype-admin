"""Sprint 3.2 — ProactiveContextStore canonical (Redis-backed, TTL 30min).

Persiste notes "[contexto] Recrutador editou via UI" dispatched pelo
frontend hub Configurações (settings-notify.ts) para que LIA backend
veja e possa reagir proativamente no próximo turn.

Architecture:
  Frontend dispatch `lia:settings-updated` (debounced 1500ms per-key)
  → settings-notify.ts POST /api/v1/lia/proactive-context (Sprint 3.3)
  → endpoint persiste em Redis via this store (Sprint 3.2)
  → MainOrchestrator.process build_system_prompt busca via list()
    e inclui em context_block (Sprint 3.4)
  → LLM próximo turn vê e pode validar/sugerir/quietar (Anti-pattern #1
    do lia_persona.yaml respeitado pelo backend).

Key shape: `lia:proactive_ctx:{company_id}:{user_id}:{action_id}:{section}:{field}`
  - Cardinality bounded: cada (action_id, section, field) tem apenas 1
    value vivo por user — novo dispatch SOBRESCREVE anterior (canonical
    pra "valor atual configurado", não histórico)
  - TTL nativo Redis 1800s (30min) — context efêmero, não acumula

Value: JSON com {actionId, section, field, value, ts}.

Fail-open em todas as ops: Redis down → operations no-op + log warn,
não bloqueiam chat. Caller usa fallback (vazio = sem proactive context).
"""
from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


PROACTIVE_CTX_KEY_PREFIX = "lia:proactive_ctx"
PROACTIVE_CTX_TTL_S = 1800  # 30 minutos

# ── PR-12 / F-4.15 (Onda 4) — canonical env var for inject limit ──────────
# Default 8 preserves the historical hardcoded value. Operations can tune
# via env without code change. Read at module load (cheap; not hot-path).
import os as _os
PROACTIVE_CTX_MAX_NOTES = int(_os.getenv("LIA_PROACTIVE_CONTEXT_MAX_NOTES", "8"))


# ── PR-12 / F-4.14 (Onda 4) — Prometheus counter for inject sites ────────
# Two call sites today: wizard_session_service + main_orchestrator. Counter
# is canonical here so both register against the same metric. Pattern
# mirrors `app/services/voice/wsi_pipeline.py:35-55` (try/except fail-open,
# REGISTRY lookup to survive double-init under pytest).
try:
    from prometheus_client import REGISTRY as _PROM_REGISTRY
    from prometheus_client import Counter as _PromCounter

    _PROACTIVE_INJECT_METRIC = "lia_proactive_context_inject_total"
    _existing_inject = getattr(_PROM_REGISTRY, "_names_to_collectors", {}).get(
        _PROACTIVE_INJECT_METRIC
    )
    if _existing_inject is not None:
        proactive_context_inject_counter = _existing_inject
    else:
        proactive_context_inject_counter = _PromCounter(
            _PROACTIVE_INJECT_METRIC,
            "Proactive settings-context injection into LIA system prompt "
            "(PR-12 / F-4.14 Onda 4).",
            labelnames=("path", "status"),  # path: wizard|orchestrator; status: hit|miss|fail_open
        )
except (ImportError, ValueError):  # pragma: no cover
    proactive_context_inject_counter = None



async def _get_redis():
    """Async Redis client. None se indisponível (fail-open)."""
    try:
        import redis.asyncio as aioredis

        from app.core.config import settings
        return await aioredis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=5, socket_timeout=5)
    except Exception:
        try:
            import aioredis  # type: ignore[union-attr]

            from app.core.config import settings
            return await aioredis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=5, socket_timeout=5)
        except Exception:
            return None


def _key(company_id: str, user_id: str, action_id: str,
         section: str, field: str | None) -> str:
    """Compose canonical key.

    Cardinality bounded: ~50 (action_ids) × 20 (sections) × 30 (fields)
    × users per company = ~30k keys peak per company. Aceitável em Redis.
    """
    _field = field or "_"
    return f"{PROACTIVE_CTX_KEY_PREFIX}:{company_id}:{user_id}:{action_id}:{section}:{_field}"


def _index_key(company_id: str, user_id: str) -> str:
    """Per-user index sorted set — facilita list() em ordem temporal."""
    return f"{PROACTIVE_CTX_KEY_PREFIX}:{company_id}:{user_id}:_index"


class ProactiveContextStore:
    """Redis-backed store de proactive context notes (Settings → Chat).

    All operations fail-open: Redis indisponível NÃO quebra chat — caller
    vê empty list e segue sem proactive injection.
    """

    @staticmethod
    async def put(
        *,
        company_id: str,
        user_id: str,
        action_id: str,
        section: str,
        field: str | None,
        value: Any | None,
        ts_ms: int | None = None,
    ) -> bool:
        """Persiste note. Retorna True se gravado, False se Redis down."""
        if not company_id or not user_id or not action_id or not section:
            return False
        redis = await _get_redis()
        if redis is None:
            logger.debug("[ProactiveContextStore] Redis indisponível — put noop")
            return False
        try:
            k = _key(company_id, user_id, action_id, section, field)
            payload = {
                "action_id": action_id,
                "section": section,
                "field": field,
                "value": value,
                "ts_ms": ts_ms or 0,
            }
            await redis.set(k, json.dumps(payload), ex=PROACTIVE_CTX_TTL_S)
            # Mantém index sorted set por timestamp
            idx = _index_key(company_id, user_id)
            await redis.zadd(idx, {k: ts_ms or 0})
            await redis.expire(idx, PROACTIVE_CTX_TTL_S)
            return True
        except Exception as exc:
            logger.debug("[ProactiveContextStore] put failed: %s", exc)
            return False
        finally:
            try:
                await redis.aclose()
            except Exception:
                pass

    @staticmethod
    async def list_recent(
        *,
        company_id: str,
        user_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Lista até N notes mais recentes não-expiradas. Fail-open: [].

        LLM use case: include in system_prompt context_block para próximo
        turn ter awareness de configurações mudadas recentemente.
        """
        if not company_id or not user_id:
            return []
        redis = await _get_redis()
        if redis is None:
            return []
        try:
            idx = _index_key(company_id, user_id)
            # ZREVRANGE: chaves ordenadas por ts decrescente
            keys = await redis.zrevrange(idx, 0, limit - 1)
            if not keys:
                return []
            values = await redis.mget(*keys)
            notes: list[dict[str, Any]] = []
            for raw in values:
                if not raw:
                    continue  # key expirou entre zrevrange e mget
                try:
                    notes.append(json.loads(raw))
                except (json.JSONDecodeError, TypeError):
                    continue
            return notes
        except Exception as exc:
            logger.debug("[ProactiveContextStore] list_recent failed: %s", exc)
            return []
        finally:
            try:
                await redis.aclose()
            except Exception:
                pass

    @staticmethod
    async def clear_consumed(
        *,
        company_id: str,
        user_id: str,
    ) -> int:
        """Limpa todos notes do user (chamado após LIA reagir).

        Returns: número de keys deletadas. Fail-open: 0.
        """
        redis = await _get_redis()
        if redis is None:
            return 0
        try:
            idx = _index_key(company_id, user_id)
            keys = await redis.zrange(idx, 0, -1)
            if not keys:
                return 0
            deleted = await redis.delete(*keys, idx)
            return int(deleted or 0)
        except Exception as exc:
            logger.debug("[ProactiveContextStore] clear_consumed failed: %s", exc)
            return 0
        finally:
            try:
                await redis.aclose()
            except Exception:
                pass
