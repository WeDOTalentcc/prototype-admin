"""
MainOrchestrator — entry point único para todas as mensagens da LIA.

Pipeline unificado (eliminando a dupla delegação MainOrchestrator → Orchestrator):

  UniversalContext
    → FairnessGuard (pré-check bloqueio + soft warnings)
    → TenantContext enrichment
    → Phase 0: PendingAction (multi-turn / confirmação)
    → Phase 1: ActionExecutor (ações fechadas detectadas por intent)
    → Phase 2: ConversationMemory + CascadedRouter → DomainWorkflow → ReAct Agent

Consolida a lógica que antes estava espalhada em:
- orchestrated_talent_chat.py (500 linhas, 7 fases)
- orchestrated_job_chat.py
- pipeline_orchestrator.py
- agent_chat_ws.py
- Orchestrator.process_request_with_memory() (intermediário eliminado)
"""
from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field

from app.orchestrator.action_executor import (
    ACTIONABLE_INTENTS,
    ActionResult,
    action_executor,
    is_confirmation,
    is_rejection,
    resolve_candidate_from_context,
)
from app.orchestrator.context_adapter import UniversalContext
from app.orchestrator.pending_action import pending_action_store
from app.shared.services.tenant_context_service import TenantContextService
from app.shared.compliance.fairness_guard import FairnessGuard
from app.shared.robustness.security_patterns import check_input_security, get_block_response
from app.shared.memory.candidate_list_store import candidate_list_store

from app.shared.providers.llm_factory import get_provider_for_tenant
from app.shared.tenant_llm_context import get_current_llm_tenant, get_tenant_llm_config

logger = logging.getLogger(__name__)

_CACHEABLE_DOMAINS: set[str] = {
    "analytics", "kanban_search", "kanban_insight", "recruiter_assistant",
    "pipeline_context",
}
_CACHE_TTL_BY_DOMAIN: dict[str, int] = {
    "analytics": 90,
    "kanban_search": 60,
    "kanban_insight": 120,
    "recruiter_assistant": 300,
    "pipeline_context": 60,
}

_perf_metrics: dict[str, list[float]] = {}


def get_perf_summary() -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for domain, times in _perf_metrics.items():
        recent = times[-100:]
        summary[domain] = {
            "count": len(recent),
            "avg_ms": round(sum(recent) / len(recent), 1) if recent else 0,
            "p95_ms": round(sorted(recent)[int(len(recent) * 0.95)] if recent else 0, 1),
        }
    return summary


# ---------------------------------------------------------------------------
# Response schema unificado
# ---------------------------------------------------------------------------

class ChatResponse(BaseModel):
    success: bool
    content: str
    agent_used: str = "main_orchestrator"
    agents_consulted: list[str] = Field(default_factory=list)
    intent_detected: str = "general"
    confidence: float = 1.0
    structured_data: dict[str, Any] | None = None
    suggested_prompts: list[str] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    conversation_id: str | None = None
    ui_action: str | None = None
    ui_action_params: dict[str, Any] | None = None
    action_executed: bool = False
    action_result: dict[str, Any] | None = None
    action_type: str | None = None
    needs_confirmation: bool = False
    needs_params: bool = False
    pending_action_id: str | None = None
    fairness_warnings: list[str] = Field(default_factory=list)
    from_cache: bool = False

    @classmethod
    def from_orchestrator_result(cls, result: dict[str, Any], conv_id: str) -> ChatResponse:
        """Converte o dict retornado por Orchestrator.process_request()."""
        # Se o resultado tem score_breakdown, incluir em structured_data
        _structured = result.get("structured_data", result.get("data")) or {}
        if result.get("score_breakdown"):
            _structured["score_breakdown"] = result["score_breakdown"]
        return cls(
            success=result.get("success", True),
            content=result.get("response", result.get("message", result.get("content", ""))),
            agent_used=result.get("agent_used", result.get("domain_id", "orchestrator")),
            agents_consulted=result.get("agents_consulted", []),
            intent_detected=result.get("intent_detected", result.get("intent", "general")),
            confidence=result.get("confidence", 1.0),
            structured_data=_structured or None,
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
        suggested_prompts: list[str] | None = None,
    ) -> ChatResponse:
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
    Entry point único consolidado para todas as mensagens da LIA.

    Recebe UniversalContext (normalizado pelo ContextAdapter) e processa através
    do pipeline unificado, sem delegar para Orchestrator.process_request_with_memory
    como camada intermediária. O Orchestrator permanece como motor de roteamento
    e execução de domínio, mas a gestão de memória e o fluxo de fases são
    controlados aqui.
    """

    def __init__(self, orchestrator: Any) -> None:
        self._orchestrator = orchestrator
        self._fairness_guard = FairnessGuard()
        self._tenant_context_service = TenantContextService()

    async def process(
        self,
        ctx: UniversalContext,
        db: Any,
        streaming_callback: Callable | None = None,
    ) -> ChatResponse:
        """
        Processa uma mensagem através do pipeline unificado.

        Phase 0: PendingAction — se há ação pendente aguardando confirmação/params
        Phase 1: ActionExecutor — ações fechadas detectáveis por padrão
        Phase 2: Orchestrator completo — CascadedRouter → DomainWorkflow → ReAct Agent
        """
        conv_id = ctx.conversation_id or str(uuid.uuid4())
        _t0 = time.monotonic()

        try:
            # ── Pré-check SecurityPatterns — antes de qualquer processamento ──
            message_text = ctx.message or ""
            _security_result = check_input_security(message_text)
            if _security_result.is_blocked:
                logger.warning(
                    "[MainOrchestrator] SecurityPatterns blocked input: "
                    "user=%s company=%s risk=%s categories=%s",
                    ctx.user_id, ctx.company_id,
                    _security_result.risk_level, _security_result.threat_categories,
                )
                return ChatResponse(
                    success=False,
                    content=get_block_response(_security_result, language="pt"),
                    agent_used="security_patterns",
                    confidence=_security_result.confidence,
                    intent_detected="blocked_security",
                    conversation_id=conv_id,
                )

            # ── Pré-check FairnessGuard — antes de qualquer fase de processamento ──
            message_text = ctx.message or ""
            _fairness_result = self._fairness_guard.check(message_text)
            if _fairness_result.is_blocked:
                logger.warning(
                    "[MainOrchestrator] FairnessGuard blocked input: "
                    "user=%s company=%s category=%s",
                    ctx.user_id, ctx.company_id, getattr(_fairness_result, "category", "unknown"),
                )
                return ChatResponse(
                    success=False,
                    content=_fairness_result.educational_message or (
                        "Não posso processar essa solicitação pois viola critérios de equidade e compliance."
                    ),
                    agent_used="fairness_guard",
                    confidence=1.0,
                    intent_detected="blocked_bias",
                    conversation_id=conv_id,
                )
            # Camada 2 — soft warnings (advisory, não bloqueia — propagados no response)
            _soft_warnings: list[str] = list(getattr(_fairness_result, "soft_warnings", None) or [])
            try:
                _implicit_warnings = self._fairness_guard.check_implicit_bias(message_text)
                if _implicit_warnings:
                    for _w in _implicit_warnings:
                        if _w not in _soft_warnings:
                            _soft_warnings.append(_w)
                    logger.info(
                        "[MainOrchestrator] FairnessGuard soft warnings: user=%s count=%d",
                        ctx.user_id, len(_soft_warnings),
                    )
            except Exception as _fg_exc:
                logger.debug("[MainOrchestrator] FairnessGuard implicit check skipped: %s", _fg_exc)

            # Enriquecer contexto com informações do tenant
            try:
                _tenant_ctx = await self._tenant_context_service.get_context(
                    company_id=str(ctx.company_id), db=db
                )
                ctx.tenant_context_snippet = _tenant_ctx.to_prompt_snippet()
            except Exception as _tc_exc:
                logger.debug("[MainOrchestrator] TenantContext skipped: %s", _tc_exc)

            # ── Phase 0: PendingAction ──────────────────────────────────────
            pending_response = await self._handle_pending_action(ctx, conv_id)
            if pending_response is not None:
                if _soft_warnings and not pending_response.fairness_warnings:
                    pending_response.fairness_warnings = _soft_warnings
                return pending_response

            # ── Phase 1: ActionExecutor ────────────────────────────────────
            action_response = await self._try_action_executor(ctx, conv_id)
            if action_response is not None:
                if _soft_warnings and not action_response.fairness_warnings:
                    action_response.fairness_warnings = _soft_warnings
                return action_response

            # ── Phase 2: Orchestrator completo ─────────────────────────────
            _phase2_response = await self._process_via_orchestrator(ctx, conv_id, db, streaming_callback)
            if _soft_warnings and not _phase2_response.fairness_warnings:
                _phase2_response.fairness_warnings = _soft_warnings

            _elapsed_ms = (time.monotonic() - _t0) * 1000
            _domain = _phase2_response.agent_used or "unknown"
            _perf_metrics.setdefault(_domain, []).append(_elapsed_ms)
            if len(_perf_metrics[_domain]) > 200:
                _perf_metrics[_domain] = _perf_metrics[_domain][-100:]
            logger.info(
                "[MainOrchestrator] response_time=%.1fms domain=%s intent=%s cache_hit=%s user=%s",
                _elapsed_ms, _domain, _phase2_response.intent_detected,
                getattr(_phase2_response, 'from_cache', False), ctx.user_id,
            )
            return _phase2_response

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
    ) -> ChatResponse | None:
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
    ) -> ChatResponse | None:
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
    # Phase 2 — Pipeline consolidado (sem delegação intermediária)
    # ------------------------------------------------------------------

    async def _process_via_orchestrator(
        self,
        ctx: UniversalContext,
        conv_id: str,
        db: Any,
        streaming_callback: Callable | None,
    ) -> ChatResponse:
        """
        Pipeline consolidado: ConversationMemory → CascadedRouter → DomainWorkflow.

        Elimina a delegação intermediária para Orchestrator.process_request_with_memory,
        inlining a gestão de memória diretamente aqui enquanto usa o Orchestrator
        somente para process_request (roteamento + execução de domínio).
        """
        from app.domains.ai.services.response_cache_service import response_cache_service

        orchestrator_context = ctx.to_orchestrator_context()

        _cache_key = await self._try_cache_lookup(ctx, conv_id, streaming_callback)
        if isinstance(_cache_key, ChatResponse):
            return _cache_key
        if streaming_callback:
            orchestrator_context["streaming_callback"] = streaming_callback

        conv, conv_id = await self._setup_conversation_memory(ctx, conv_id, db, orchestrator_context)

        result = await self._route_with_tenant_llm(ctx, conv_id, db, orchestrator_context)

        await self._persist_response(ctx, conv_id, conv, result, db)

        result.update({"conversation_id": conv_id})

        if isinstance(_cache_key, str) and result.get("success"):
            await self._write_cache(response_cache_service, _cache_key, result)

        await self._persist_candidate_list(conv_id, result)
        await self._audit_output(ctx, conv_id, result)

        result = await self._inject_module_tasting_hints(ctx, result, db)

        return ChatResponse.from_orchestrator_result(result, conv_id=conv_id)

    async def _try_cache_lookup(
        self,
        ctx: UniversalContext,
        conv_id: str,
        streaming_callback: Callable | None,
    ) -> str | ChatResponse | None:
        """Check response cache. Returns cache_key (str), ChatResponse (hit), or None."""
        if streaming_callback:
            return None
        try:
            from app.domains.ai.services.response_cache_service import response_cache_service
            from app.orchestrator.fast_router import FastRouter
            _fast = FastRouter()
            _fast_match = _fast.match(ctx.message or "")
            _detected_domain = _fast_match.domain_id if _fast_match else None
            if not (_detected_domain and _detected_domain in _CACHEABLE_DOMAINS):
                return None
            _cache_context = {
                "company_id": str(ctx.company_id or ""),
                "user_id": str(ctx.user_id or ""),
                "job_id": str(ctx.entity_id or "") if ctx.context_type == "job" else "",
                "candidate_id": str(ctx.entity_id or "") if ctx.context_type == "candidate" else "",
                "conversation_id": str(conv_id or ""),
            }
            _cache_key = response_cache_service.generate_cache_key(
                _detected_domain, _cache_context, ctx.message or "",
                company_id=str(ctx.company_id or ""),
            )
            _cached = await response_cache_service.get_cached_response(_cache_key)
            if _cached:
                logger.info("[MainOrchestrator] Cache HIT domain=%s key=%s", _detected_domain, _cache_key[:40])
                resp = ChatResponse(
                    success=True,
                    content=_cached.get("content", ""),
                    agent_used=_cached.get("agent_used", _detected_domain),
                    intent_detected=_cached.get("intent_detected", _detected_domain),
                    confidence=_cached.get("confidence", 1.0),
                    structured_data=_cached.get("structured_data"),
                    suggested_prompts=_cached.get("suggested_prompts", []),
                    conversation_id=conv_id,
                )
                resp.from_cache = True
                return resp
            return _cache_key
        except Exception as _cache_exc:
            logger.debug("[MainOrchestrator] Cache lookup skipped: %s", _cache_exc)
            return None

    async def _setup_conversation_memory(
        self,
        ctx: UniversalContext,
        conv_id: str,
        db: Any,
        orchestrator_context: dict[str, Any],
    ) -> tuple[Any, str]:
        """Load or create conversation, add user message, enrich context. Returns (conv, conv_id)."""
        from app.domains.recruiter_assistant.services.conversation_memory import conversation_memory
        try:
            if conv_id:
                conv = await conversation_memory.get_conversation(db=db, conversation_id=conv_id, include_messages=True)
                if not conv:
                    conv = await conversation_memory.get_or_create_conversation(
                        db=db, user_id=ctx.user_id, context_type=ctx.context_type, context_id=ctx.entity_id,
                    )
                    conv_id = str(conv.id)
            else:
                conv = await conversation_memory.get_or_create_conversation(
                    db=db, user_id=ctx.user_id, context_type=ctx.context_type, context_id=ctx.entity_id,
                )
                conv_id = str(conv.id)

            await conversation_memory.add_message(db=db, conversation_id=conv_id, role="user", content=ctx.message)
            llm_ctx = await conversation_memory.get_context_for_llm(db=db, conversation_id=conv_id, max_messages=20)
            orchestrator_context.update({
                "conversation_history": llm_ctx.get("messages", []),
                "conversation_summary": llm_ctx.get("summary"),
                "context_type": ctx.context_type,
                "context_id": ctx.entity_id,
            })
            return conv, conv_id
        except Exception as _mem_exc:
            logger.debug("[MainOrchestrator] ConversationMemory setup skipped: %s", _mem_exc)
            return None, conv_id

    async def _route_with_tenant_llm(
        self,
        ctx: UniversalContext,
        conv_id: str,
        db: Any,
        orchestrator_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Inject tenant LLM provider, route via orchestrator, then restore."""
        _llm_svc = getattr(self._orchestrator, "llm_service", None)
        _original_container = getattr(_llm_svc, "_tenant_container", None) if _llm_svc else None
        _original_tenant = getattr(_llm_svc, "_current_tenant", "") if _llm_svc else ""
        _tenant_id = str(ctx.company_id) if ctx.company_id else get_current_llm_tenant()

        if _tenant_id and _llm_svc:
            try:
                _tenant_config = await get_tenant_llm_config(_tenant_id)
                if _tenant_config:
                    _providers_cfg = _tenant_config.get("providers", {})
                    _api_keys = {
                        name: prov.get("api_key")
                        for name, prov in _providers_cfg.items()
                        if prov.get("api_key")
                    }
                    from app.shared.providers.llm_factory import ProviderContainer, TenantProviderRegistry
                    _registry = TenantProviderRegistry.get_instance()
                    _registry.remove_container(_tenant_id)
                    _container = ProviderContainer(
                        tenant_id=_tenant_id,
                        primary_provider=_tenant_config.get("primary_provider"),
                        fallback_order=_tenant_config.get("fallback_order"),
                        provider_api_keys=_api_keys if _api_keys else None,
                    )
                    _registry.register_container(_tenant_id, _container)
                    _llm_svc._tenant_container = _container
                    _llm_svc._current_tenant = _tenant_id
                    logger.info(
                        "[MainOrchestrator] Tenant LLM provider set: tenant=%s primary=%s",
                        _tenant_id, _container.primary_provider,
                    )
                else:
                    logger.debug("[MainOrchestrator] No tenant LLM config for %s — using global", _tenant_id)
            except Exception as _tenant_exc:
                logger.debug("[MainOrchestrator] Tenant LLM resolution failed for %s: %s — using global", _tenant_id, _tenant_exc)

        try:
            result = await self._orchestrator.process_request(
                user_id=ctx.user_id, message=ctx.message,
                conversation_id=conv_id, context=orchestrator_context,
            )
        finally:
            if _llm_svc:
                _llm_svc._tenant_container = _original_container
                _llm_svc._current_tenant = _original_tenant

        return result

    async def _persist_response(
        self, ctx: UniversalContext, conv_id: str, conv: Any, result: dict[str, Any], db: Any
    ) -> None:
        """Persist assistant response to conversation memory and commit."""
        from app.core.config import settings
        from app.domains.recruiter_assistant.services.conversation_memory import conversation_memory
        try:
            if result.get("success") and conv is not None:
                await conversation_memory.add_message(
                    db=db, conversation_id=conv_id, role="assistant",
                    content=result.get("message", result.get("content", "")),
                    intent=result.get("intent"),
                )
                if (
                    getattr(conv, "message_count", None)
                    and conv.message_count % settings.ROUTER_SUMMARY_EVERY_N_MESSAGES == 0
                ):
                    try:
                        await conversation_memory.update_summary(
                            db=db, conversation_id=conv_id, llm_service=self._orchestrator.llm_service,
                        )
                    except Exception:
                        pass
            await db.commit()
        except Exception as _persist_exc:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.debug("[MainOrchestrator] Memory persist skipped: %s", _persist_exc)

    async def _write_cache(self, cache_service: Any, cache_key: str, result: dict[str, Any]) -> None:
        """Write successful result to response cache."""
        try:
            _domain_for_ttl = result.get("agent_used") or result.get("domain_id") or ""
            _ttl = _CACHE_TTL_BY_DOMAIN.get(_domain_for_ttl, 300)
            await cache_service.cache_response(
                cache_key,
                {
                    "content": result.get("response", result.get("message", result.get("content", ""))),
                    "agent_used": result.get("agent_used", ""),
                    "intent_detected": result.get("intent_detected", result.get("intent", "")),
                    "confidence": result.get("confidence", 1.0),
                    "structured_data": result.get("structured_data"),
                    "suggested_prompts": result.get("suggested_prompts", []),
                },
                ttl=_ttl,
            )
        except Exception as _cw_exc:
            logger.debug("[MainOrchestrator] Cache write failed: %s", _cw_exc)

    async def _persist_candidate_list(self, conv_id: str, result: dict[str, Any]) -> None:
        """Persist candidate list to Redis (TTL 30min)."""
        _structured = result.get("structured_data") or {}
        candidates_in_result = (
            result.get("candidates")
            or (_structured.get("candidates") if isinstance(_structured, dict) else None)
            or []
        )
        if candidates_in_result:
            try:
                await candidate_list_store.set(conv_id, candidates_in_result)
            except Exception as exc:
                logger.debug("[MainOrchestrator] CandidateListStore set error: %s", exc)

    async def _audit_output(self, ctx: UniversalContext, conv_id: str, result: dict[str, Any]) -> None:
        """Audit output for high-impact actions (candidate/job mutations)."""
        _should_audit = bool(
            result.get("candidate_id") or result.get("job_id") or result.get("job_vacancy_id")
        )
        if _should_audit:
            try:
                from app.shared.compliance.audit_service import AuditService
                _audit_svc = AuditService()
                await _audit_svc.log_output(
                    company_id=str(ctx.company_id or ""),
                    session_id=conv_id,
                    agent_used=result.get("agent_used", "unknown"),
                    input_text=ctx.message or "",
                    output_text=result.get("content") or result.get("message", ""),
                    action_executed=result.get("action_executed"),
                    candidate_id=result.get("candidate_id"),
                    job_vacancy_id=result.get("job_id") or result.get("job_vacancy_id"),
                    fairness_flags=result.get("fairness_flags", []),
                )
            except Exception as _audit_err:
                logger.warning("Output audit failed (non-blocking): %s", _audit_err)

    _MODULE_TASTING_INTENTS: dict[str, list[str]] = {
        "talent_intelligence_pro": [
            "talent", "skills", "skill_analysis", "gap_analysis",
            "ontology", "market_intelligence", "busca", "sourcing",
        ],
        "internal_mobility": ["internal_mobility", "mobilidade_interna", "talent"],
        "interview_intelligence": ["interview", "entrevista", "screening"],
        "workforce_planning": ["workforce", "planning", "analytics", "previsão"],
        "candidate_nurture": [
            "nurture", "reengagement", "engagement", "crm",
            "candidato_passivo", "communication",
        ],
    }

    _MODULE_TASTING_SUGGESTIONS: dict[str, str] = {
        "talent_intelligence_pro": (
            "💡 **Talent Intelligence Pro** — Analise skills com ontologia de grafos, "
            "identifique gaps e obtenha market intelligence em tempo real."
        ),
        "internal_mobility": (
            "💡 **Internal Mobility** — Descubra talentos internos com matching "
            "por skills adjacentes e readiness scoring."
        ),
        "interview_intelligence": (
            "💡 **Interview Intelligence** — Análise de entrevistas com detecção "
            "de viés, mapeamento de competências e sentimento."
        ),
        "workforce_planning": (
            "💡 **Workforce Planning** — Previsão de contratação baseada em "
            "turnover, pipeline e cenários de crescimento."
        ),
        "candidate_nurture": (
            "💡 **Candidate Nurture** — Sequências automatizadas de engajamento "
            "para candidatos passivos com métricas de conversão."
        ),
    }

    async def _inject_module_tasting_hints(
        self,
        ctx: UniversalContext,
        result: dict[str, Any],
        db: Any,
    ) -> dict[str, Any]:
        if not result.get("success") or not ctx.company_id:
            return result

        detected_intent = result.get("intent_detected", "") or ""
        detected_domain = result.get("agent_used", "") or ""
        context_signals = f"{detected_intent} {detected_domain} {ctx.message or ''}".lower()

        hints: list[str] = []
        try:
            from app.domains.modules.services.module_service import module_service

            for module_name, intent_keywords in self._MODULE_TASTING_INTENTS.items():
                if any(kw in context_signals for kw in intent_keywords):
                    status = await module_service.get_module_status(db, ctx.company_id, module_name)
                    if status in ("disabled", "expired", "coming_soon") or status is None:
                        suggestion = self._MODULE_TASTING_SUGGESTIONS.get(module_name)
                        if suggestion:
                            hints.append(suggestion)

            if hints:
                existing_content = result.get("content", "")
                tasting_block = "\n\n---\n" + "\n".join(hints[:2])
                result["content"] = existing_content + tasting_block
                result["module_hints"] = hints[:2]
        except Exception as exc:
            logger.debug("[MainOrchestrator] Module tasting hints skipped: %s", exc)

        return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_suggested_prompts(intent: str, candidates_count: int, selected_count: int) -> list[str]:
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
    message: str, param_name: str, candidates: list[dict[str, Any]]
) -> str | None:
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

_main_orchestrator_instance: MainOrchestrator | None = None


def get_main_orchestrator(orchestrator: Any = None) -> MainOrchestrator:
    global _main_orchestrator_instance
    if _main_orchestrator_instance is None:
        if orchestrator is None:
            from app.api.orchestrator_routes import get_orchestrator
            orchestrator = get_orchestrator()
        _main_orchestrator_instance = MainOrchestrator(orchestrator)
    return _main_orchestrator_instance
