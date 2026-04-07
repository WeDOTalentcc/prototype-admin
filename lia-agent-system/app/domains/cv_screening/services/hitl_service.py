"""
HITL Service — Human-in-the-Loop via LangGraph interrupt (Sprint F1).

Três flows críticos com interrupt_before:
  1. WizardGraph — antes de create_job (criação de vaga definitiva)
  2. PipelineTransitionAgent — antes de mover candidato de stage
  3. WSI Interview — antes de finalizar avaliação com score

Protocolo WS:
  → { type: "approval_required", thread_id, action, description, data }
  ← { type: "approval_response", thread_id, approved: bool, comment? }

Persistência (Sprint F1):
  Redis — fast-path cache, TTL 24h (fallback in-memory se Redis indisponível)
  DB    — source of truth persistente (hitl_pending_actions + hitl_audit_trail)
  DB ops são best-effort: falha não bloqueia o fluxo principal do agente.
"""
import json
import logging
import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

# TTL 24 horas em segundos
_HITL_TTL_SECONDS = 86400


def _get_redis():
    """Retorna cliente Redis ou None se indisponível."""
    try:
        import redis as redis_lib
        redis_url = os.environ.get("REDIS_URL")
        if not redis_url:
            return None
        client = redis_lib.from_url(redis_url, socket_connect_timeout=2)
        client.ping()
        return client
    except Exception as exc:
        logger.warning("[HITL] Redis indisponível: %s", exc)
        return None


async def _db_save_pending(
    pending_id: str,
    thread_id: str,
    domain: str,
    action: str,
    description: str,
    data: dict,
    agent_input: dict,
    ws_session_id: str,
    company_id: str = "",
) -> None:
    """Persiste uma nova solicitação de aprovação no banco (best-effort)."""
    try:
        from app.core.database import AsyncSessionLocal
        from lia_models.hitl import HITLPendingAction
        async with AsyncSessionLocal() as db:
            record = HITLPendingAction(
                pending_id=pending_id,
                thread_id=thread_id,
                company_id=company_id or None,
                domain=domain,
                action=action,
                description=description,
                data=data,
                agent_input=agent_input,
                ws_session_id=ws_session_id,
                status="pending",
                expires_at=datetime.now(UTC) + timedelta(seconds=_HITL_TTL_SECONDS),
            )
            db.add(record)
            await db.commit()
    except Exception as exc:
        try:
            await db.rollback()
        except Exception:
            pass
        logger.warning("[HITL] DB save pending falhou (best-effort): %s", exc)


async def _db_resolve(
    pending_id: str,
    thread_id: str,
    domain: str,
    action: str,
    approved: bool,
    comment: str | None,
    resolved_by: str = "",
    company_id: str = "",
) -> None:
    """Atualiza o registro pendente e insere no audit trail (best-effort)."""
    try:
        from sqlalchemy import select

        from app.core.database import AsyncSessionLocal
        from lia_models.hitl import HITLAuditTrail, HITLPendingAction
        now = datetime.now(UTC)
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(HITLPendingAction).where(HITLPendingAction.pending_id == pending_id)
            )
            record = result.scalar_one_or_none()
            if record:
                record.status = "approved" if approved else "rejected"
                record.approved = approved
                record.comment = comment
                record.resolved_by = resolved_by
                record.resolved_at = now

            trail = HITLAuditTrail(
                company_id=company_id or None,
                thread_id=thread_id,
                pending_id=pending_id,
                domain=domain,
                action=action,
                approved=approved,
                comment=comment,
                resolved_by=resolved_by,
                resolved_at=now,
            )
            db.add(trail)
            await db.commit()
    except Exception as exc:
        try:
            await db.rollback()
        except Exception:
            pass
        logger.warning("[HITL] DB resolve falhou (best-effort): %s", exc)


async def _db_get_pending(thread_id: str) -> dict | None:
    """Busca aprovação pendente no DB como fallback do Redis."""
    try:
        from sqlalchemy import select

        from app.core.database import AsyncSessionLocal
        from lia_models.hitl import HITLPendingAction
        now = datetime.now(UTC)
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(HITLPendingAction)
                .where(
                    HITLPendingAction.thread_id == thread_id,
                    HITLPendingAction.status == "pending",
                    HITLPendingAction.expires_at > now,
                )
                .order_by(HITLPendingAction.created_at.desc())
                .limit(1)
            )
            record = result.scalar_one_or_none()
            if record:
                d = record.to_dict()
                d["requested_at"] = d["created_at"]
                return d
    except Exception as exc:
        logger.warning("[HITL] DB get_pending falhou: %s", exc)
    return None


class HITLService:
    """
    Gerencia aprovações humanas no loop de execução de agentes.

    Fluxo:
      1. Agente chama request_approval() → envia mensagem WS → pausa
      2. Usuário responde via WS (approval_response) ou API (POST /hitl/{thread_id}/approve)
      3. receive_approval() armazena resultado no Redis + DB
      4. Agente chama is_approved() → retoma execução

    Persistência (Sprint F1):
      Redis = cache fast-path (TTL 24h)
      DB    = source of truth (hitl_pending_actions + hitl_audit_trail)
    """

    def __init__(self):
        # fallback in-memory quando Redis indisponível
        self._memory: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Métodos principais
    # ------------------------------------------------------------------

    async def request_approval(
        self,
        thread_id: str,
        action: str,
        description: str,
        data: dict,
        ws_session_id: str,
        domain: str = "",
        company_id: str = "",
        agent_input: dict | None = None,
        user_id: str = "",
    ) -> str:
        """
        Envia mensagem WS de approval_required e retorna um pending_id.
        O agente deve pausar (interrupt) até receive_approval() ser chamado.
        Armazena estado pendente em Redis (TTL 24h) e DB.

        Se o usuário configurou auto_confirm=True para este domain/action,
        aprova automaticamente sem interrupção (log de auditoria registrado).
        """
        # --- Verificação de auto_confirm (Sprint J3) ---
        if user_id:
            auto = await self._check_auto_confirm(
                user_id=user_id, company_id=company_id,
                domain=domain, action_type=action,
            )
            if auto:
                pending_id = str(uuid.uuid4())
                logger.info(
                    "[HITL] Auto-confirmação ativada thread=%s pending=%s action=%s user=%s",
                    thread_id, pending_id, action, user_id,
                )
                # Persiste como já aprovado para que is_approved() retorne True imediatamente
                payload = {
                    "pending_id": pending_id,
                    "thread_id": thread_id,
                    "domain": domain,
                    "action": action,
                    "description": description,
                    "data": data,
                    "ws_session_id": ws_session_id,
                    "requested_at": datetime.now(UTC).isoformat(),
                    "approved": True,
                    "comment": "auto_confirm",
                    "resolved_by": user_id,
                    "resolved_at": datetime.now(UTC).isoformat(),
                }
                key = f"hitl:{thread_id}:{pending_id}"
                self._store(key, payload)
                # Audit trail (best-effort)
                try:
                    await _db_resolve(
                        pending_id=pending_id, thread_id=thread_id,
                        domain=domain, action=action, approved=True,
                        comment="auto_confirm", resolved_by=user_id,
                        company_id=company_id,
                    )
                except Exception:
                    pass
                return pending_id

        pending_id = str(uuid.uuid4())
        payload = {
            "pending_id": pending_id,
            "thread_id": thread_id,
            "domain": domain,
            "company_id": company_id,
            "action": action,
            "description": description,
            "data": data,
            "ws_session_id": ws_session_id,
            "requested_at": datetime.now(UTC).isoformat(),
            "approved": None,  # None = pendente
            "comment": None,
        }

        # Redis (ou in-memory)
        key = f"hitl:{thread_id}:{pending_id}"
        self._store(key, payload)

        # DB — source of truth (best-effort, não bloqueia)
        try:
            await _db_save_pending(
                pending_id=pending_id,
                thread_id=thread_id,
                domain=domain,
                action=action,
                description=description,
                data=data,
                agent_input=agent_input or {},
                ws_session_id=ws_session_id,
                company_id=company_id,
            )
        except Exception as exc:
            logger.warning("[HITL] DB save pending falhou (best-effort): %s", exc)

        # WS notification (best-effort)
        try:
            from app.api.v1.ws_manager import ws_manager
            await ws_manager.send_to_session(ws_session_id, {
                "type": "approval_required",
                "thread_id": thread_id,
                "pending_id": pending_id,
                "action": action,
                "description": description,
                "data": data,
            })
        except Exception as exc:
            logger.warning("[HITL] Falha ao enviar WS approval_required: %s", exc)

        logger.info(
            "[HITL] Aprovação solicitada thread=%s pending=%s action=%s",
            thread_id, pending_id, action,
        )
        return pending_id

    async def receive_approval(
        self,
        thread_id: str,
        pending_id: str,
        approved: bool,
        comment: str | None = None,
        resolved_by: str = "",
        domain: str = "",
        action: str = "",
        company_id: str = "",
    ) -> dict:
        """
        Recebe resposta do usuário.
        Atualiza Redis + insere no audit trail no DB.
        """
        key = f"hitl:{thread_id}:{pending_id}"
        existing = self._load(key)
        if existing is None:
            existing = {
                "pending_id": pending_id,
                "thread_id": thread_id,
                "domain": domain,
                "action": action,
                "description": "",
                "data": {},
                "ws_session_id": "",
                "requested_at": datetime.now(UTC).isoformat(),
            }

        existing["approved"] = approved
        existing["comment"] = comment
        existing["resolved_at"] = datetime.now(UTC).isoformat()
        existing["resolved_by"] = resolved_by

        self._store(key, existing)

        # DB — atualiza pending + insere audit trail (best-effort)
        try:
            await _db_resolve(
                pending_id=pending_id,
                thread_id=thread_id,
                domain=existing.get("domain", domain),
                action=existing.get("action", action),
                approved=approved,
                comment=comment,
                resolved_by=resolved_by,
                company_id=company_id,
            )
        except Exception as exc:
            logger.warning("[HITL] DB resolve falhou (best-effort): %s", exc)

        logger.info(
            "[HITL] Aprovação recebida thread=%s pending=%s approved=%s",
            thread_id, pending_id, approved,
        )
        return existing

    async def get_pending(self, thread_id: str) -> dict | None:
        """
        Busca aprovação pendente. Redis first → fallback DB.
        """
        # Redis
        try:
            redis_client = _get_redis()
            if redis_client is not None:
                pattern = f"hitl:{thread_id}:*"
                keys = redis_client.keys(pattern)
                pending_items = []
                for k in keys:
                    raw = redis_client.get(k)
                    if raw:
                        item = json.loads(raw)
                        if item.get("approved") is None:
                            pending_items.append(item)
                if pending_items:
                    return sorted(
                        pending_items,
                        key=lambda x: x.get("requested_at", ""),
                        reverse=True,
                    )[0]
            else:
                prefix = f"hitl:{thread_id}:"
                candidates = [
                    v for k, v in self._memory.items()
                    if k.startswith(prefix) and v.get("approved") is None
                ]
                if candidates:
                    return sorted(candidates, key=lambda x: x.get("requested_at", ""), reverse=True)[0]
        except Exception as exc:
            logger.warning("[HITL] get_pending Redis falhou: %s", exc)

        # DB fallback
        return await _db_get_pending(thread_id)

    async def store_resume_info(
        self,
        thread_id: str,
        domain: str,
        session_id: str,
        agent_input_dict: dict,
        hitl_context: str = "",
    ) -> None:
        """Armazena informações necessárias para retomar o grafo após aprovação."""
        key = f"hitl:resume:{thread_id}"
        payload = {
            "thread_id": thread_id,
            "domain": domain,
            "session_id": session_id,
            "agent_input": agent_input_dict,
            "hitl_context": hitl_context,
            "stored_at": datetime.now(UTC).isoformat(),
        }
        self._store(key, payload)
        logger.debug("[HITL] Resume info salva thread=%s domain=%s", thread_id, domain)

    async def get_resume_info(self, thread_id: str) -> dict | None:
        """Recupera informações de resume para o thread_id."""
        key = f"hitl:resume:{thread_id}"
        return self._load(key)

    async def is_approved(self, pending_id: str) -> bool | None:
        """
        Verifica se aprovação foi dada.
        Retorna None quando ainda pendente, True/False quando resolvida.
        """
        try:
            redis_client = _get_redis()
            if redis_client is not None:
                pattern = f"hitl:*:{pending_id}"
                keys = redis_client.keys(pattern)
                if not keys:
                    return None
                raw = redis_client.get(keys[0])
                if raw:
                    item = json.loads(raw)
                    return item.get("approved")
                return None
            else:
                suffix = f":{pending_id}"
                for k, v in self._memory.items():
                    if k.endswith(suffix):
                        return v.get("approved")
                return None
        except Exception as exc:
            logger.warning("[HITL] is_approved falhou: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Helpers de auto_confirm (Sprint J3)
    # ------------------------------------------------------------------

    async def _check_auto_confirm(
        self,
        user_id: str,
        company_id: str,
        domain: str,
        action_type: str,
    ) -> bool:
        """Verifica preferência de auto_confirm via UserAgentPreferenceService."""
        try:
            from app.core.database import AsyncSessionLocal
            from app.services.user_agent_preference_service import UserAgentPreferenceService
            async with AsyncSessionLocal() as db:
                return await UserAgentPreferenceService.check_auto_confirm(
                    db, user_id=user_id, company_id=company_id,
                    domain=domain, action_type=action_type,
                )
        except Exception as exc:
            logger.warning("[HITL] _check_auto_confirm falhou (safe=False): %s", exc)
            return False

    # ------------------------------------------------------------------
    # Helpers de armazenamento
    # ------------------------------------------------------------------

    def _store(self, key: str, payload: dict) -> None:
        """Armazena payload no Redis (TTL 24h) ou in-memory como fallback."""
        try:
            redis_client = _get_redis()
            if redis_client is not None:
                redis_client.setex(key, _HITL_TTL_SECONDS, json.dumps(payload))
                return
        except Exception as exc:
            logger.warning("[HITL] _store Redis falhou: %s", exc)
        self._memory[key] = payload

    def _load(self, key: str) -> dict | None:
        """Carrega payload do Redis ou in-memory."""
        try:
            redis_client = _get_redis()
            if redis_client is not None:
                raw = redis_client.get(key)
                if raw:
                    return json.loads(raw)
                return None
        except Exception as exc:
            logger.warning("[HITL] _load Redis falhou: %s", exc)
        return self._memory.get(key)


# Singleton global
hitl_service = HITLService()
