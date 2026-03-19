"""
MainOrchestrator — entry point único para todas as mensagens da LIA.

Consolida a lógica que hoje está espalhada em:
- orchestrated_talent_chat.py (500 linhas, 7 fases)
- orchestrated_job_chat.py
- pipeline_orchestrator.py
- agent_chat_ws.py

Fluxo unificado:
  UniversalContext
    → Phase 0: PendingAction (multi-turn / confirmação)
    → Phase 1: ActionExecutor (ações fechadas detectadas por intent)
    → Phase 2: Orchestrator.process_request_with_memory()
               → CascadedRouter (6 tiers)
               → DomainWorkflow (PRE_CHECK → ... → POST_CHECK + FairnessGuard)
               → ReAct Agent (execute step)
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field

from app.orchestrator.context_adapter import UniversalContext
from app.orchestrator.action_executor import (
    ActionResult,
    ACTIONABLE_INTENTS,
    action_executor,
    is_confirmation,
    is_rejection,
    resolve_candidate_from_context,
)
from app.orchestrator.pending_action import PendingActionState, pending_action_store
from app.shared.memory.candidate_list_store import candidate_list_store

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Response schema unificado
# ---------------------------------------------------------------------------

class ChatResponse(BaseModel):
    success: bool
    content: str
    agent_used: str = "main_orchestrator"
    agents_consulted: List[str] = Field(default_factory=list)
    intent_detected: str = "general"
    confidence: float = 1.0
    structured_data: Optional[Dict[str, Any]] = None
    suggested_prompts: List[str] = Field(default_factory=list)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    conversation_id: Optional[str] = None
    ui_action: Optional[str] = None
    ui_action_params: Optional[Dict[str, Any]] = None
    action_executed: bool = False
    action_result: Optional[Dict[str, Any]] = None
    action_type: Optional[str] = None
    needs_confirmation: bool = False
    needs_params: bool = False
    pending_action_id: Optional[str] = None

    @classmethod
    def from_orchestrator_result(cls, result: Dict[str, Any], conv_id: str) -> "ChatResponse":
        """Converte o dict retornado por Orchestrator.process_request_with_memory()."""
        return cls(
            success=result.get("success", True),
            content=result.get("response", result.get("content", "")),
            agent_used=result.get("agent_used", result.get("domain_id", "orchestrator")),
            agents_consulted=result.get("agents_consulted", []),
            intent_detected=result.get("intent_detected", result.get("intent", "general")),
            confidence=result.get("confidence", 1.0),
            structured_data=result.get("structured_data", result.get("data")),
            suggested_prompts=result.get("suggested_prompts", result.get("suggestions", [])),
            actions=result.get("actions", []),
            conversation_id=conv_id,
            ui_action=result.get("ui_action"),
            ui_action_params=result.get("ui_action_params"),
        )

    @classmethod
    def from_action_result(
        cls,
        action_result: ActionResult,
        intent: str,
        conv_id: str,
        suggested_prompts: Optional[List[str]] = None,
    ) -> "ChatResponse":
        return cls(
            success=True,
            content=action_result.message,
            agent_used="ActionExecutor",
            agents_consulted=["ActionExecutor"],
            intent_detected=intent,
            confidence=1.0,
            structured_data=action_result.data,
            suggested_prompts=suggested_prompts or [],
            conversation_id=conv_id,
            action_executed=action_result.status == "executed",
            action_result=action_result.data,
            action_type=action_result.action_type,
            needs_confirmation=action_result.status == "needs_confirmation",
            needs_params=action_result.status == "needs_params",
            pending_action_id=action_result.pending_action_id,
        )


# ---------------------------------------------------------------------------
# MainOrchestrator
# ---------------------------------------------------------------------------

class MainOrchestrator:
    """
    Entry point único para todas as mensagens da LIA.
    Recebe UniversalContext (normalizado pelo ContextAdapter) e processa
    através das fases consolidadas.
    """

    def __init__(self, orchestrator: Any) -> None:
        self._orchestrator = orchestrator

    async def process(
        self,
        ctx: UniversalContext,
        db: Any,
        streaming_callback: Optional[Callable] = None,
    ) -> ChatResponse:
        """
        Processa uma mensagem através do pipeline unificado.

        Phase 0: PendingAction — se há ação pendente aguardando confirmação/params
        Phase 1: ActionExecutor — ações fechadas detectáveis por padrão
        Phase 2: Orchestrator completo — CascadedRouter → DomainWorkflow → ReAct Agent
        """
        conv_id = ctx.conversation_id or str(uuid.uuid4())

        try:
            # ── Phase 0: PendingAction ──────────────────────────────────────
            pending_response = await self._handle_pending_action(ctx, conv_id)
            if pending_response is not None:
                return pending_response

            # ── Phase 1: ActionExecutor ────────────────────────────────────
            action_response = await self._try_action_executor(ctx, conv_id)
            if action_response is not None:
                return action_response

            # ── Phase 2: Orchestrator completo ─────────────────────────────
            return await self._process_via_orchestrator(ctx, conv_id, db, streaming_callback)

        except Exception as exc:
            logger.error(
                f"[MainOrchestrator] Unhandled error for user={ctx.user_id} "
                f"company={ctx.company_id} channel={ctx.channel}: {exc}",
                exc_info=True,
            )
            return ChatResponse(
                success=False,
                content="Ocorreu um erro ao processar sua solicitação. Tente novamente.",
                intent_detected="error",
                conversation_id=conv_id,
            )

    # ------------------------------------------------------------------
    # Phase 0 — PendingAction
    # ------------------------------------------------------------------

    async def _handle_pending_action(
        self, ctx: UniversalContext, conv_id: str
    ) -> Optional[ChatResponse]:
        pending = pending_action_store.get(conv_id)
        if not pending:
            return None

        candidates = ctx.candidates or []
        candidates_count = len(candidates)

        # ── Aguardando confirmação ──
        if pending.awaiting_confirmation:
            if is_confirmation(ctx.message):
                config = ACTIONABLE_INTENTS.get(pending.intent, {})
                exec_result = await action_executor._execute_action(
                    pending.intent,
                    config,
                    pending.collected_params,
                    {"conversation_id": conv_id, "user_id": ctx.user_id},
                )
                pending_action_store.remove(conv_id)
                return ChatResponse.from_action_result(
                    exec_result,
                    intent=pending.intent,
                    conv_id=conv_id,
                    suggested_prompts=_get_suggested_prompts(pending.intent, candidates_count, 0),
                )

            if is_rejection(ctx.message):
                pending_action_store.remove(conv_id)
                return ChatResponse(
                    success=True,
                    content="Ok, ação cancelada. Como posso te ajudar?",
                    agent_used="ActionExecutor",
                    intent_detected="cancelamento",
                    suggested_prompts=["Quem são os melhores candidatos?", "Busque perfis similares"],
                    conversation_id=conv_id,
                )

            # Mensagem não é confirmação nem rejeição — cancela e continua
            pending_action_store.remove(conv_id)
            return None

        # ── Coletando parâmetros faltantes ──
        if pending.missing_params:
            next_param = pending.next_missing_param()
            if next_param:
                extracted = await _extract_param_value(ctx.message, next_param, candidates)
                if extracted:
                    pending.add_param(next_param, extracted)

                    # Resolve contexto de candidato se necessário
                    if next_param == "candidate_id":
                        resolved = resolve_candidate_from_context(None, extracted, candidates)
                        if resolved:
                            pending.collected_params["candidate_name"] = resolved.get("name", "")
                            pending.collected_params["candidate_email"] = resolved.get("email", "")
                            if resolved.get("stage"):
                                pending.collected_params["from_stage"] = resolved["stage"]

                    if pending.is_complete:
                        config = ACTIONABLE_INTENTS.get(pending.intent, {})
                        if config.get("requires_confirmation", False):
                            summary = action_executor._build_confirmation_summary(
                                pending.intent, config, pending.collected_params
                            )
                            pending.awaiting_confirmation = True
                            pending.confirmation_summary = summary
                            pending_action_store.save(conv_id, pending)
                            return ChatResponse(
                                success=True,
                                content=summary["message"],
                                agent_used="ActionExecutor",
                                intent_detected=pending.intent,
                                conversation_id=conv_id,
                                needs_confirmation=True,
                                pending_action_id=pending.pending_id,
                            )
                        else:
                            exec_result = await action_executor._execute_action(
                                pending.intent,
                                config,
                                pending.collected_params,
                                {"conversation_id": conv_id, "user_id": ctx.user_id},
                            )
                            pending_action_store.remove(conv_id)
                            return ChatResponse.from_action_result(
                                exec_result,
                                intent=pending.intent,
                                conv_id=conv_id,
                                suggested_prompts=_get_suggested_prompts(pending.intent, candidates_count, 0),
                            )
                    else:
                        # Ainda faltam params
                        pending_action_store.save(conv_id, pending)
                        next_param2 = pending.next_missing_param()
                        config = ACTIONABLE_INTENTS.get(pending.intent, {})
                        prompt_label = config.get("param_labels", {}).get(next_param2, next_param2)
                        return ChatResponse(
                            success=True,
                            content=f"Entendido. Agora preciso de: **{prompt_label}**",
                            agent_used="ActionExecutor",
                            intent_detected=pending.intent,
                            conversation_id=conv_id,
                            needs_params=True,
                            pending_action_id=pending.pending_id,
                        )

        pending_action_store.remove(conv_id)
        return None

    # ------------------------------------------------------------------
    # Phase 1 — ActionExecutor
    # ------------------------------------------------------------------

    async def _try_action_executor(
        self, ctx: UniversalContext, conv_id: str
    ) -> Optional[ChatResponse]:
        candidates = ctx.candidates or []

        try:
            action_result: ActionResult = await action_executor.try_execute(
                message=ctx.message,
                context={
                    "candidates": candidates,
                    "selected_candidate_ids": ctx.selected_candidate_ids,
                    "job_context": ctx.job_context,
                    "conversation_id": conv_id,
                    "user_id": ctx.user_id,
                    "company_id": ctx.company_id,
                },
            )
        except Exception as exc:
            logger.warning(f"[MainOrchestrator] ActionExecutor error: {exc}")
            return None

        if action_result.status == "not_actionable":
            return None

        if action_result.status in ("needs_params", "needs_confirmation"):
            if action_result.pending_action_id:
                pass  # PendingActionStore já foi atualizado pelo ActionExecutor
            return ChatResponse.from_action_result(
                action_result,
                intent=action_result.action_type or "action",
                conv_id=conv_id,
            )

        if action_result.status == "executed":
            return ChatResponse.from_action_result(
                action_result,
                intent=action_result.action_type or "action",
                conv_id=conv_id,
                suggested_prompts=_get_suggested_prompts(
                    action_result.action_type or "", len(candidates), 0
                ),
            )

        return None

    # ------------------------------------------------------------------
    # Phase 2 — Orchestrator completo
    # ------------------------------------------------------------------

    async def _process_via_orchestrator(
        self,
        ctx: UniversalContext,
        conv_id: str,
        db: Any,
        streaming_callback: Optional[Callable],
    ) -> ChatResponse:
        orchestrator_context = ctx.to_orchestrator_context()
        if streaming_callback:
            orchestrator_context["streaming_callback"] = streaming_callback

        result = await self._orchestrator.process_request_with_memory(
            db=db,
            user_id=ctx.user_id,
            message=ctx.message,
            conversation_id=conv_id,
            context_type=ctx.context_type,
            context_id=ctx.entity_id,
            context=orchestrator_context,
        )

        # Persiste lista completa de candidatos no Redis (TTL 30min) para
        # resolução posicional na próxima mensagem ("e o terceiro?")
        candidates_in_result = (
            result.get("candidates")
            or result.get("structured_data", {}).get("candidates") if isinstance(result.get("structured_data"), dict) else None
            or []
        )
        if candidates_in_result:
            try:
                await candidate_list_store.set(conv_id, candidates_in_result)
            except Exception as exc:
                logger.debug("[MainOrchestrator] CandidateListStore set error: %s", exc)

        return ChatResponse.from_orchestrator_result(result, conv_id=conv_id)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_suggested_prompts(intent: str, candidates_count: int, selected_count: int) -> List[str]:
    base_prompts = {
        "mover_candidato": ["Ver pipeline completo", "Quem mais está pronto para avançar?"],
        "reprovar_candidato": ["Ver outros candidatos", "Buscar perfis similares"],
        "enviar_email": ["Agendar entrevista", "Ver histórico de comunicações"],
        "agendar_entrevista": ["Ver agenda disponível", "Enviar confirmação ao candidato"],
        "create_job": ["Ver vagas abertas", "Configurar pipeline de triagem"],
    }
    if candidates_count > 0:
        return base_prompts.get(intent, ["Quem são os melhores candidatos?", "Comparar top 3"])
    return base_prompts.get(intent, ["Como posso te ajudar?"])


async def _extract_param_value(
    message: str, param_name: str, candidates: List[Dict[str, Any]]
) -> Optional[str]:
    """Extração simples de parâmetro da mensagem do usuário."""
    msg = message.strip()
    if not msg:
        return None

    # Candidato por nome na lista disponível
    if param_name == "candidate_id" and candidates:
        msg_lower = msg.lower()
        for c in candidates:
            name = c.get("name", "")
            if name and name.lower() in msg_lower:
                return str(c.get("id", ""))

    # Fallback: retorna a mensagem bruta como valor
    return msg if len(msg) <= 200 else msg[:200]


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_main_orchestrator_instance: Optional[MainOrchestrator] = None


def get_main_orchestrator(orchestrator: Any = None) -> MainOrchestrator:
    global _main_orchestrator_instance
    if _main_orchestrator_instance is None:
        if orchestrator is None:
            from app.api.orchestrator_routes import get_orchestrator
            orchestrator = get_orchestrator()
        _main_orchestrator_instance = MainOrchestrator(orchestrator)
    return _main_orchestrator_instance
