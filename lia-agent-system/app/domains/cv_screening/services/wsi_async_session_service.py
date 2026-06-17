"""
WSIAsyncSessionService — gerencia sessões WSI assíncronas (candidato responde offline).
O candidato acessa o chat web e responde no seu próprio ritmo (sem pressão de tempo real).
Timeout padrão: 48h. Re-engajamento automático via followup_service.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from enum import Enum, StrEnum
from typing import Any

logger = logging.getLogger(__name__)

WSI_SESSION_TIMEOUT_HOURS = 48
WSI_SESSION_TTL_SECONDS = WSI_SESSION_TIMEOUT_HOURS * 3600


class WSIAsyncSessionStatus(StrEnum):
    PENDING = "pending"        # Convite enviado, aguardando início
    IN_PROGRESS = "in_progress"  # Candidato iniciou
    COMPLETED = "completed"    # Candidato finalizou
    EXPIRED = "expired"        # Timeout 48h
    ABANDONED = "abandoned"    # Sem atividade > 96h


class WSIAsyncSessionService:
    """
    Gerencia o ciclo de vida de sessões WSI assíncronas.
    Usa Redis para estado da sessão + PostgreSQL para persistência.
    """

    async def create_session(
        self,
        candidate_id: str,
        job_id: str,
        company_id: str,
        db: Any,
    ) -> str:
        """Cria nova sessão assíncrona. Retorna session_id."""
        session_id = f"system:{uuid.uuid4()}"
        expires_at = datetime.utcnow() + timedelta(hours=WSI_SESSION_TIMEOUT_HOURS)

        session_data = {
            "session_id": session_id,
            "candidate_id": candidate_id,
            "job_id": job_id,
            "company_id": company_id,
            "status": WSIAsyncSessionStatus.PENDING.value,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at.isoformat(),
            "current_block": 1,
            "responses": [],
            "reminder_count": 0,
        }

        # Persistir no Redis com TTL
        try:
            import json

            import redis
            from lia_config.config import settings
            _r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=5, socket_timeout=5)
            _r.setex(
                f"wsi_async:{session_id}",
                WSI_SESSION_TTL_SECONDS,
                json.dumps(session_data),
            )
        except Exception as exc:
            logger.debug("[WSIAsync] Redis store failed: %s", exc)

        # Persistir no banco (via wsi_sessions model se existir)
        try:
            from sqlalchemy import insert

            from app.models.wsi_session import WSISession
            await db.execute(
                insert(WSISession).values(
                    id=session_id,
                    candidate_id=candidate_id,
                    job_id=job_id,
                    company_id=company_id,
                    status=WSIAsyncSessionStatus.PENDING.value,
                    expires_at=expires_at,
                    metadata={"async_mode": True},
                )
            )
            await db.commit()
        except Exception as exc:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.debug("[WSIAsync] DB store failed: %s", exc)

        logger.info(
            "[WSIAsync] Sessão criada: session_id=%s candidate=%s job=%s expires=%s",
            session_id, candidate_id, job_id, expires_at.isoformat(),
        )
        return session_id

    async def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Busca sessão no Redis. Retorna None se expirada ou não encontrada."""
        try:
            import json

            import redis
            from lia_config.config import settings
            _r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=5, socket_timeout=5)
            data = _r.get(f"wsi_async:{session_id}")
            if data:
                return json.loads(data)
        except Exception as exc:
            logger.debug("[WSIAsync] Redis get failed: %s", exc)
        return None

    async def submit_response(
        self,
        session_id: str,
        block: int,
        question_id: str,
        response_text: str,
    ) -> bool:
        """Registra resposta do candidato para um bloco WSI."""
        session = await self.get_session(session_id)
        if not session:
            return False

        session["responses"].append({
            "block": block,
            "question_id": question_id,
            "response": response_text,
            "answered_at": datetime.utcnow().isoformat(),
        })
        session["status"] = WSIAsyncSessionStatus.IN_PROGRESS.value
        session["current_block"] = block + 1

        try:
            import json

            import redis
            from lia_config.config import settings
            _r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=5, socket_timeout=5)
            remaining_ttl = _r.ttl(f"wsi_async:{session_id}")
            _r.setex(
                f"wsi_async:{session_id}",
                max(remaining_ttl, 3600),
                json.dumps(session),
            )
            return True
        except Exception as exc:
            logger.debug("[WSIAsync] Response submit failed: %s", exc)
            return False

    async def check_expired_sessions(self, db: Any) -> int:
        """Verifica e marca sessões expiradas. Retorna count de sessões processadas."""
        try:
            from sqlalchemy import and_, update

            from app.models.wsi_session import WSISession

            expired_at = datetime.utcnow() - timedelta(hours=WSI_SESSION_TIMEOUT_HOURS)
            result = await db.execute(
                update(WSISession)
                .where(
                    and_(
                        WSISession.status == WSIAsyncSessionStatus.IN_PROGRESS.value,
                        WSISession.updated_at < expired_at,
                    )
                )
                .values(status=WSIAsyncSessionStatus.EXPIRED.value)
            )
            await db.commit()
            count = result.rowcount
            if count > 0:
                logger.info("[WSIAsync] %d sessões marcadas como expiradas", count)
            return count
        except Exception as exc:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.debug("[WSIAsync] check_expired failed: %s", exc)
            return 0


wsi_async_session_service = WSIAsyncSessionService()


def get_wsi_async_session_service() -> "WSIAsyncSessionService":
    return wsi_async_session_service
