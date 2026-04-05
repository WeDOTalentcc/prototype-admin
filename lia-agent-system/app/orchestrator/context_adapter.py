"""
ContextAdapter — normaliza contexto de qualquer canal (REST, WS, RabbitMQ)
para UniversalContext, que o MainOrchestrator consome.

Responsabilidade única: transformação de formato + validação de segurança (IDOR).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

logger = logging.getLogger(__name__)

ChannelType = Literal["rest", "ws", "rabbitmq", "cli"]

PAGE_TO_CONTEXT_TYPE: Dict[str, str] = {
    "sourcing": "talent_funnel",
    "talent": "talent_funnel",
    "pipeline": "pipeline",
    "kanban": "pipeline",
    "job": "job_management",
    "jobs": "job_management",
    "vacancies": "job_management",
    "wizard": "job_management",
    "analytics": "analytics",
    "global": "general",
    "general": "general",
}


@dataclass
class UniversalContext:
    """Contexto normalizado — único formato que o MainOrchestrator consome."""

    message: str
    user_id: str
    company_id: str
    channel: ChannelType = "rest"
    conversation_id: Optional[str] = None

    # Contexto de página (de onde o usuário está enviando a mensagem)
    context_page: str = "general"
    context_type: str = "general"  # mapeado de context_page

    # Entidade em foco na página atual
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None  # "sourcing", "job", "candidate"

    # Dados ricos de contexto (repassados para o DomainWorkflow)
    candidates: List[Dict[str, Any]] = field(default_factory=list)
    selected_candidate_ids: Optional[List[str]] = None
    job_context: Optional[Dict[str, Any]] = None
    search_context: Optional[Dict[str, Any]] = None
    target_job: Optional[Dict[str, Any]] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_orchestrator_context(self) -> Dict[str, Any]:
        """Converte para o formato que Orchestrator.process_request_with_memory() espera."""
        ctx: Dict[str, Any] = {
            "context_type": self.context_type,
            "context_id": self.entity_id,
            "candidates": self.candidates,
            "selected_candidate_ids": self.selected_candidate_ids,
            "channel": self.channel,
            "company_id": self.company_id,
        }
        if self.job_context:
            ctx["job_context"] = self.job_context
        if self.search_context:
            ctx["search_context"] = self.search_context
        if self.target_job:
            ctx["target_job"] = self.target_job
        ctx.update(self.extra)
        return ctx


class ContextAdapter:
    """
    Fábrica estática de UniversalContext.
    Cada canal tem seu método from_* que extrai e normaliza os dados.
    """

    # ------------------------------------------------------------------
    # REST genérico (endpoint /api/v1/chat)
    # ------------------------------------------------------------------

    @staticmethod
    def from_rest(
        *,
        message: str,
        user_id: str,
        company_id: str,
        conversation_id: Optional[str] = None,
        context_page: str = "general",
        entity_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        candidates: Optional[List[Dict[str, Any]]] = None,
        selected_candidate_ids: Optional[List[str]] = None,
        job_context: Optional[Dict[str, Any]] = None,
        search_context: Optional[Dict[str, Any]] = None,
        target_job: Optional[Dict[str, Any]] = None,
        **extra: Any,
    ) -> UniversalContext:
        context_type = PAGE_TO_CONTEXT_TYPE.get(context_page, "general")
        return UniversalContext(
            message=message,
            user_id=user_id,
            company_id=company_id,
            channel="rest",
            conversation_id=conversation_id,
            context_page=context_page,
            context_type=context_type,
            entity_id=entity_id,
            entity_type=entity_type,
            candidates=candidates or [],
            selected_candidate_ids=selected_candidate_ids,
            job_context=job_context,
            search_context=search_context,
            target_job=target_job,
            extra=extra,
        )

    # ------------------------------------------------------------------
    # Thin adapters — endpoints específicos existentes
    # ------------------------------------------------------------------

    @staticmethod
    def from_talent_chat(request: Any, *, user_id: str, company_id: str) -> UniversalContext:
        """Adapta OrchestratedTalentChatRequest para UniversalContext."""
        sourcing_id = None
        if request.search_context:
            sourcing_id = request.search_context.get("sourcing_id") or request.search_context.get("id")

        return UniversalContext(
            message=request.message,
            user_id=user_id,
            company_id=company_id or getattr(request, "company_id", ""),
            channel="rest",
            conversation_id=request.conversation_id,
            context_page="sourcing",
            context_type="talent_funnel",
            entity_id=str(sourcing_id) if sourcing_id else None,
            entity_type="sourcing" if sourcing_id else None,
            candidates=request.candidates or [],
            selected_candidate_ids=request.selected_candidate_ids,
            search_context=request.search_context,
            target_job=getattr(request, "target_job", None),
        )

    @staticmethod
    def from_job_chat(request: Any, *, user_id: str, company_id: str) -> UniversalContext:
        """Adapta OrchestratedJobChatRequest para UniversalContext."""
        job_id = None
        if request.job_context:
            job_id = request.job_context.get("id") or request.job_context.get("job_id")

        return UniversalContext(
            message=request.message,
            user_id=user_id,
            company_id=company_id or getattr(request, "company_id", ""),
            channel="rest",
            conversation_id=request.conversation_id,
            context_page="job",
            context_type="job_management",
            entity_id=str(job_id) if job_id else None,
            entity_type="job" if job_id else None,
            candidates=getattr(request, "candidates", []) or [],
            selected_candidate_ids=getattr(request, "selected_candidate_ids", None),
            job_context=request.job_context,
        )

    # ------------------------------------------------------------------
    # WebSocket
    # ------------------------------------------------------------------

    @staticmethod
    def from_ws(
        *,
        session_id: str,
        message_frame: Dict[str, Any],
        jwt_payload: Dict[str, Any],
    ) -> UniversalContext:
        """Adapta frame WS para UniversalContext."""
        user_id = str(jwt_payload.get("sub", ""))
        company_id = str(jwt_payload.get("company_id", ""))
        context = message_frame.get("context", {})
        domain = message_frame.get("domain", "general")

        context_page = domain
        context_type = PAGE_TO_CONTEXT_TYPE.get(domain, "general")
        entity_id = context.get("entity_id") or context.get("sourcing_id") or context.get("job_id")

        return UniversalContext(
            message=message_frame.get("content", ""),
            user_id=user_id,
            company_id=company_id,
            channel="ws",
            conversation_id=session_id,
            context_page=context_page,
            context_type=context_type,
            entity_id=str(entity_id) if entity_id else None,
            candidates=context.get("candidates", []),
            job_context=context.get("job_context"),
            search_context=context.get("search_context"),
            extra={"domain": domain, "ws_session_id": session_id},
        )

    # ------------------------------------------------------------------
    # RabbitMQ (compatível com formato do v5)
    # ------------------------------------------------------------------

    @staticmethod
    def from_rabbitmq(message: Dict[str, Any]) -> UniversalContext:
        """
        Adapta mensagem RabbitMQ para UniversalContext.
        Compatível com o formato do recruiter_agent_v5:
          { question, domain, sourcing_id, user_id, context_data, company_id }
        """
        domain = message.get("domain", "general")
        context_data = message.get("context_data", {})
        entity_id = message.get("sourcing_id") or message.get("job_id") or context_data.get("entity_id")

        return UniversalContext(
            message=message.get("question", ""),
            user_id=str(message.get("user_id", "")),
            company_id=str(message.get("company_id", "")),
            channel="rabbitmq",
            conversation_id=message.get("conversation_id"),
            context_page=domain,
            context_type=PAGE_TO_CONTEXT_TYPE.get(domain, "general"),
            entity_id=str(entity_id) if entity_id else None,
            entity_type="sourcing" if message.get("sourcing_id") else None,
            candidates=context_data.get("candidates", []),
            job_context=context_data.get("job_context"),
            extra={"rabbitmq_payload": message},
        )

    # ------------------------------------------------------------------
    # Segurança: validação de propriedade de entidade (IDOR prevention)
    # ------------------------------------------------------------------

    @staticmethod
    async def validate_entity_ownership(
        entity_id: str,
        entity_type: str,
        company_id: str,
        db: Any,
    ) -> bool:
        """
        Valida que entity_id pertence a company_id.
        Previne IDOR: usuário de empresa A não acessa dados de empresa B.
        Retorna True se válido ou se não há DB disponível (graceful degradation).
        """
        if not entity_id or not company_id or not db:
            return True  # sem dados suficientes para validar — não bloquear

        try:
            from sqlalchemy import text

            table_map = {
                "sourcing": "sourcing_sessions",
                "job": "job_vacancies",
                "candidate": "candidates",
            }
            table = table_map.get(entity_type)
            if not table:
                return True  # tipo desconhecido — não bloquear

            result = await db.execute(
                text(f"SELECT id FROM {table} WHERE id = :eid AND company_id = :cid LIMIT 1"),
                {"eid": entity_id, "cid": company_id},
            )
            return result.fetchone() is not None
        except Exception as exc:
            logger.warning(
                f"[ContextAdapter] IDOR check failed for {entity_type}:{entity_id} "
                f"company:{company_id} — {exc}. Allowing (graceful degradation)."
            )
            return True
