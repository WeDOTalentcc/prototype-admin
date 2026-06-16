"""
Learning Snapshot Service — Z2-01.

Captura o estado atual dos LearningPattern de uma empresa no Redis
antes de qualquer batch de aprendizado ser aplicado.

Permite rollback para o estado anterior caso um batch apresente viés
detectado posteriormente ou seja revertido manualmente.

Chaves Redis:
  learning_snapshot:{company_id}:index   → lista JSON dos últimos N snapshot keys
  learning_snapshot:{company_id}:{ts}    → payload JSON com os padrões

TTL: 30 dias (SNAPSHOT_TTL_SECONDS)
Max snapshots mantidos por empresa: MAX_SNAPSHOTS (LRU implícito via index)
"""
from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

SNAPSHOT_TTL_SECONDS = 30 * 24 * 3600  # 30 dias
MAX_SNAPSHOTS = 5
_KEY_PREFIX = "learning_snapshot"


def _snapshot_key(company_id: str, ts: str) -> str:
    return f"{_KEY_PREFIX}:{company_id}:{ts}"


def _index_key(company_id: str) -> str:
    return f"{_KEY_PREFIX}:{company_id}:index"


async def _get_redis():
    """Retorna cliente Redis async. Retorna None se indisponível."""
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


class LearningSnapshotService:
    """
    Persiste snapshots dos LearningPattern no Redis antes de cada batch.

    Uso:
        # Antes de aplicar padrões (em learning_loop_service.py)
        await snapshot_svc.save_snapshot(company_id, db)

        # Para reverter (chamado manualmente ou por endpoint admin)
        success = await snapshot_svc.rollback_to_latest(company_id, db)
    """

    async def save_snapshot(
        self,
        company_id: str,
        db: Any,  # AsyncSession — tipagem fraca para evitar import circular
    ) -> str | None:
        """
        Captura os LearningPattern atuais da empresa e persiste no Redis.

        Returns:
            Chave do snapshot criado, ou None se falhar (fail-safe).
        """
        try:
            payload = await self._load_patterns(company_id, db)

            ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
            key = _snapshot_key(company_id, ts)

            redis = await _get_redis()
            if redis is None:
                logger.debug("[LearningSnapshot] Redis indisponível, snapshot ignorado")
                return None

            async with redis:
                await redis.setex(key, SNAPSHOT_TTL_SECONDS, json.dumps(payload))
                await self._update_index(redis, company_id, key)

            logger.info(
                "[LearningSnapshot] company=%s snapshot=%s patterns=%d",
                company_id,
                key,
                len(payload),
            )
            return key

        except Exception as exc:
            logger.debug("[LearningSnapshot] save_snapshot falhou (fail-safe): %s", exc)
            return None

    async def _load_patterns(
        self, company_id: str, db: Any
    ) -> list[dict[str, Any]]:
        """Carrega LearningPattern do DB e serializa para lista de dicts. Mockável em testes."""
        from sqlalchemy import select

        from app.models.intelligent_cache import LearningPattern

        result = await db.execute(
            select(LearningPattern).where(LearningPattern.company_id == company_id)
        )
        patterns = result.scalars().all()
        return [
            {
                "pattern_key": p.pattern_key,
                "pattern_type": p.pattern_type,
                "pattern_value": p.pattern_value,
                "sample_size": p.sample_size,
                "acceptance_rate": float(p.acceptance_rate)
                if p.acceptance_rate is not None
                else None,
                "confidence": p.confidence,
                "confidence_score": float(p.confidence_score)
                if p.confidence_score is not None
                else None,
                "filters": p.filters if hasattr(p, "filters") else {},
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat()
                if hasattr(p, "updated_at") and p.updated_at
                else None,
            }
            for p in patterns
        ]

    async def get_latest_key(self, company_id: str) -> str | None:
        """Retorna a chave do snapshot mais recente, ou None."""
        try:
            redis = await _get_redis()
            if redis is None:
                return None
            async with redis:
                raw = await redis.get(_index_key(company_id))
                if not raw:
                    return None
                index: list[str] = json.loads(raw)
                return index[-1] if index else None
        except Exception as exc:
            logger.debug("[LearningSnapshot] get_latest_key falhou: %s", exc)
            return None

    async def list_snapshots(self, company_id: str) -> list[str]:
        """Retorna lista de chaves de snapshots disponíveis (mais antigo → mais recente)."""
        try:
            redis = await _get_redis()
            if redis is None:
                return []
            async with redis:
                raw = await redis.get(_index_key(company_id))
                if not raw:
                    return []
                return json.loads(raw)
        except Exception as exc:
            logger.debug("[LearningSnapshot] list_snapshots falhou: %s", exc)
            return []

    async def rollback_to_latest(
        self,
        company_id: str,
        db: Any,  # AsyncSession
    ) -> bool:
        """
        Restaura os LearningPattern para o estado do snapshot mais recente.

        Sobrescreve os registros existentes com os valores do snapshot.
        Padrões que não existiam no snapshot são removidos.

        Returns:
            True se o rollback foi aplicado, False caso contrário (fail-safe).
        """
        try:
            key = await self.get_latest_key(company_id)
            if key is None:
                logger.warning(
                    "[LearningSnapshot] rollback solicitado mas nenhum snapshot encontrado "
                    "para company=%s",
                    company_id,
                )
                return False

            redis = await _get_redis()
            if redis is None:
                return False

            async with redis:
                raw = await redis.get(key)

            if not raw:
                logger.warning(
                    "[LearningSnapshot] snapshot key=%s expirado ou não encontrado", key
                )
                return False

            payload: list[dict[str, Any]] = json.loads(raw)

            await self._restore_patterns(company_id, payload, db)
            await db.commit()

            logger.info(
                "[LearningSnapshot] rollback concluído company=%s snapshot=%s patterns=%d",
                company_id,
                key,
                len(payload),
            )
            return True

        except Exception as exc:
            logger.error(
                "[LearningSnapshot] rollback falhou company=%s: %s", company_id, exc
            )
            try:
                await db.rollback()
            except Exception:
                pass
            return False

    async def _restore_patterns(
        self, company_id: str, payload: list[dict[str, Any]], db: Any
    ) -> None:
        """Remove padrões atuais e restaura a partir do payload. Mockável em testes."""
        from sqlalchemy import delete

        from app.models.intelligent_cache import LearningPattern

        await db.execute(
            delete(LearningPattern).where(LearningPattern.company_id == company_id)
        )
        for item in payload:
            pattern = LearningPattern(
                company_id=company_id,
                pattern_key=item["pattern_key"],
                pattern_type=item["pattern_type"],
                pattern_value=item["pattern_value"],
                sample_size=item.get("sample_size", 0),
                acceptance_rate=item.get("acceptance_rate"),
                confidence=item.get("confidence"),
                confidence_score=item.get("confidence_score"),
                filters=item.get("filters") or {},
            )
            db.add(pattern)

    # ── internals ──────────────────────────────────────────────────────────────

    @staticmethod
    async def _update_index(redis: Any, company_id: str, new_key: str) -> None:
        """Mantém índice de até MAX_SNAPSHOTS chaves por empresa."""
        idx_key = _index_key(company_id)
        raw = await redis.get(idx_key)
        index: list[str] = json.loads(raw) if raw else []
        index.append(new_key)
        if len(index) > MAX_SNAPSHOTS:
            index = index[-MAX_SNAPSHOTS:]
        await redis.setex(idx_key, SNAPSHOT_TTL_SECONDS, json.dumps(index))


# Singleton compartilhado
learning_snapshot_service = LearningSnapshotService()
