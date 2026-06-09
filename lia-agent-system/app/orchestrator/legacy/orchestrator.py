"""
LIA-D06: DEPRECATED — This Orchestrator class is the v1 entry point.

All NEW code must use MainOrchestrator from main_orchestrator.py via
get_main_orchestrator(). This class is still used by app/api/orchestrator_routes.py
(legacy route). Kept for backwards compat and will be removed in a future release.

DO NOT use this class in new code.
"""
import warnings as _lia_warnings

# UC-P1-23: Module-level deprecation — fires on import, not just on instantiation.
_lia_warnings.warn(
    "app.orchestrator.orchestrator (Orchestrator v1) is deprecated. "
    "Use app.orchestrator.main_orchestrator.MainOrchestrator via "
    "get_main_orchestrator() instead. Will be removed Q3 2026. [LIA-D06]",
    DeprecationWarning,
    stacklevel=2,
)

import logging
import os
from typing import Any


from app.core.config import settings
from app.domains.base import DomainContext, DomainResponse
from app.domains.registry import DomainRegistry
from app.domains.workflow import DomainWorkflow
from app.shared.execution import PlanDetector, PlanExecutor
from app.shared.robustness import CancellationHandler, sanitize_text

from app.orchestrator.routing.cascaded_router import CascadedRouter
# WT-2022 P3.1 (2026-05-21): V1 PolicyEngine retirado de runtime path.
# Orchestrator V1 (deprecated, removed Q3 2026) agora usa PolicyGateService
# wrappando PolicyEngineService V2. validate() retorna PolicyResult com
# .to_legacy_dict() para zero-break-contract no call site abaixo.
from app.domains.policy.services.policy_engine_service import PolicyEngineService
from app.orchestrator.services.policy_gate_service import PolicyGateService
from app.orchestrator.execution.state_manager import StateManager
from app.orchestrator.execution.task_planner import TaskPlanner

try:
    from app.api.v1.ws_manager import ws_manager as _ws_manager
except Exception:
    _ws_manager = None  # WS not available in test context
from app.domains.recruiter_assistant.services.conversation_memory import conversation_memory
from app.services import COMMAND_TEMPLATES, job_analytics_prompt_service
from app.shared.services.response_cache_service import response_cache_service
from app.shared.memory.conversation_state import ConversationState
from app.tools import get_all_tool_schemas, initialize_tools, tool_registry
from app.enums.orchestrator import CacheableIntent, OrchestratorScope
from app.shared.constants.prompt_constants import SALARY_BENCHMARK_ADDENDUM
from app.tools.scope_config import (
    PromptScope,
    filter_tools_by_scope,
    get_scope_system_prompt_addition,
    is_tool_allowed_in_scope,
)

logger = logging.getLogger(__name__)

# _LIA_SYSTEM_PROMPT: module-level constant for orchestrator anti-sycophancy guard.
# Tests import this directly. Uses ORCHESTRATOR variant (compact, <200 chars).
try:
    from app.shared.prompts.anti_sycophancy_block import ANTI_SYCOPHANCY_ORCHESTRATOR as _LIA_SYSTEM_PROMPT
except ImportError:
    _LIA_SYSTEM_PROMPT = (
        "Anti-sycophancy rule: NUNCA concorde apenas para evitar conflito. "
        "Apresente dados antes de concordar com afirmações do recrutador."
    )

SCOPE_MAPPING = {
    OrchestratorScope.TALENT_FUNNEL: PromptScope.TALENT_FUNNEL,
    OrchestratorScope.JOB_TABLE: PromptScope.JOB_TABLE,
    OrchestratorScope.IN_JOB: PromptScope.IN_JOB,
    OrchestratorScope.GLOBAL: PromptScope.GLOBAL,
    OrchestratorScope.PIPELINE: PromptScope.IN_JOB,
    OrchestratorScope.CANDIDATES: PromptScope.TALENT_FUNNEL,
    OrchestratorScope.JOBS: PromptScope.JOB_TABLE,
    OrchestratorScope.VACANCIES: PromptScope.JOB_TABLE,
}

from app.shared.prompts.system_prompt_builder import SystemPromptBuilder


class Orchestrator:
    def __init__(self, llm_service, db_service=None):
        # W3-024 (2026-05-23): canary log · legacy Orchestrator instanciado.
        # Pre-deletion telemetry · Q3 2026 deletion target requires zero callers.
        import os as _os_w3024
        _env_w3024 = _os_w3024.environ.get("APP_ENV", "development")
        if _env_w3024 in ("production", "prod", "staging"):
            logger.info(
                "[W3-024 CANARY] Legacy Orchestrator instantiated in %s · "
                "track caller migration progress.",
                _env_w3024,
            )
        _lia_warnings.warn(
            "[LIA-D06] Orchestrator is deprecated. Use MainOrchestrator instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.llm_service = llm_service
        self.db_service = db_service
        self.task_planner = TaskPlanner(llm_service)
        # WT-2022 P3.1: PolicyGateService wraps V2 PolicyEngineService.
        # self.policy_engine kept as legacy alias for compat with .policies access at L633.
        self.policy_gate = PolicyGateService(policy_engine=PolicyEngineService())
        self.policy_engine = self.policy_gate  # legacy alias (deprecated)
        self.state_manager = StateManager(db_service)
        self.conversation_memory = conversation_memory
        self.cancellation_handler = CancellationHandler()
        self._response_cache = response_cache_service
        self._domain_registry = DomainRegistry()
        self._domain_workflow = DomainWorkflow()
        self._plan_detector = PlanDetector()
        self._plan_executor = PlanExecutor(
            domain_registry=self._domain_registry,
            domain_workflow=self._domain_workflow,
        )
        self._init_cascaded_router()
        self._cacheable_intents = {intent.value for intent in CacheableIntent}
        self._initialize_tools()
        logger.info("Orchestrator initialized with CascadedRouter + DomainWorkflow")

    def _init_cascaded_router(self):
        self._cascaded_router = CascadedRouter(
            domain_registry=self._domain_registry,
        )

    def _initialize_tools(self) -> None:
        try:
            initialize_tools()
            # T-1170 (Bug 4): initialize_tools() já loga "Initialized N tools" no
            # caller canônico (app.tools.__init__). Legacy duplicava a linha → 2x
            # no startup. Mantemos como debug para diagnóstico sem poluir INFO.
            logger.debug(f"Tool registry size after init: {len(tool_registry.list_tools())}")
        except Exception as e:
            logger.warning(f"Tool initialization warning: {e}")

    def get_cache_stats(self) -> dict[str, Any]:
        return self._response_cache.get_stats()

    async def invalidate_cache_for_entity(self, entity_type: str, entity_id: str) -> int:
        if entity_type == "job":
            return await self._response_cache.invalidate_for_job(entity_id)
        elif entity_type == "candidate":
            return await self._response_cache.invalidate_for_candidate(entity_id)
        elif entity_type == "company":
            return await self._response_cache.invalidate_for_company(entity_id)
        return await self._response_cache.invalidate_by_pattern(f"*{entity_type}*{entity_id}*")

    async def process_request(self, user_id: str, message: str,
                              conversation_id: str | None = None,
                              context: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            sanitized = sanitize_text(message)
            if CancellationHandler.is_cancellation_request(sanitized):
                return {"success": True, "message": "Ok, operação cancelada. Como posso ajudar?", "cancelled": True}
            if CancellationHandler.is_restart_request(sanitized):
                if conversation_id:
                    self.state_manager.clear_state(conversation_id)
                return {"success": True, "message": "Vamos recomeçar! O que você gostaria de fazer?", "restarted": True}
            ctx = context or {}
            if conversation_id:
                state = self.state_manager.get_state(conversation_id)
                if state:
                    ctx.update({k: state.get(k) for k in ("last_agent", "current_job", "current_candidate")})
            route = await self._cascaded_router.route(sanitized, ctx, session_id=conversation_id)
            domain_id, confidence = route.domain_id, route.confidence
            # Normalize: intent_details may be OrchestratorIntentResult (dataclass) or legacy dict
            _idet = route.intent_details
            _idet_d: dict = (_idet.to_dict() if hasattr(_idet, "to_dict") else (_idet or {})) or {}
            intent = _idet_d.get("raw_intent") or route.domain_id
            if intent in self._cacheable_intents and self._response_cache.is_enabled():
                ck = self._response_cache.generate_cache_key(
                    intent=intent, context=ctx, user_message=sanitized,
                    company_id=ctx.get("company_id"))
                cached = await self._response_cache.get_cached_response(ck)
                if cached:
                    cached.update({"_from_cache": True, "cache_key": ck})
                    return {"success": True, "conversation_id": conversation_id, "intent": intent,
                            "agent": domain_id, "agent_type": domain_id, "confidence": confidence,
                            "from_cache": True, **cached}
            # WT-2022 P3.1: PolicyGateService.validate retorna PolicyResult; .to_legacy_dict() preserva contrato dict legacy
            policy_result = await self.policy_gate.validate(intent, user_id, context=ctx)
            policy = policy_result.to_legacy_dict()
            if not policy["allowed"]:
                return {"success": False, "message": f"Não foi possível processar: {policy['reason']}",
                        "requires_approval": policy.get("constraints", {}).get("requires_approval", False)}
            if not conversation_id:
                conversation_id = self.state_manager.create_conversation(user_id, message)
            else:
                self.state_manager.add_message(conversation_id, "user", message)
            conv_state = None
            if conversation_id:
                raw_state = self.state_manager.get_state(conversation_id)
                if raw_state and "conversation_state" in raw_state:
                    conv_state = ConversationState.from_dict(raw_state["conversation_state"])
                else:
                    conv_state = ConversationState()
            try:
                detected_plan = self._plan_detector.detect(sanitized)
                if detected_plan:
                    logger.info(f"Multi-step plan detected: {detected_plan.detected_pattern}")
                    plan_context = dict(ctx)
                    plan_context["conversation_state"] = conv_state

                    # Build real-time progress callback (WebSocket)
                    _session_id_for_ws = conversation_id or ""
                    async def _plan_progress_callback(event_type: str, data: dict) -> None:
                        if _ws_manager and _session_id_for_ws:
                            await _ws_manager.send_to_session(_session_id_for_ws, {
                                "type": "plan_progress",
                                "event": event_type,
                                **data,
                            })

                    executed_plan = await self._plan_executor.execute(
                        plan=detected_plan,
                        user_id=user_id,
                        session_id=conversation_id or "",
                        tenant_id=ctx.get("company_id"),
                        base_context=plan_context,
                        progress_callback=_plan_progress_callback,
                    )
                    consolidated = self._plan_executor.build_consolidated_response(executed_plan)
                    resp_msg = consolidated.message or "Plano executado."
                    self.state_manager.add_message(conversation_id, "assistant", resp_msg,
                        metadata={"agent": "plan_executor", "plan_id": executed_plan.plan_id,
                                  "pattern": executed_plan.detected_pattern})
                    if conv_state and conversation_id:
                        state_updates = {"last_agent": "plan_executor", "last_intent": f"plan:{executed_plan.detected_pattern}"}
                        state_updates["conversation_state"] = conv_state.to_dict()
                        self.state_manager.update_state(conversation_id, state_updates)
                    return {
                        "success": consolidated.success,
                        "conversation_id": conversation_id,
                        "intent": f"plan:{executed_plan.detected_pattern}",
                        "agent": "plan_executor",
                        "agent_type": "execution_plan",
                        "confidence": confidence,
                        "message": resp_msg,
                        "result": {"message": resp_msg, "data": consolidated.data},
                        "execution_plan": executed_plan.get_summary(),
                        "requires_user_input": False,
                        "suggested_prompts": consolidated.suggestions or [],
                        "next_actions": [],
                        "policy_constraints": policy.get("constraints", {}),
                    }
            except Exception as plan_err:
                logger.warning(f"Plan detection/execution failed (non-blocking): {plan_err}")
            # ── Tier 6: AutonomousReActAgent — intercept before DomainRegistry ──
            if domain_id == "autonomous":
                _auto_response = _idet_d.get("response", "") or _idet_d.get("routing_metadata", {}).get("response", "")
                _auto_meta = _idet_d.get("metadata", {})
                _tool_calls = _idet_d.get("tool_calls", 0)
                if _auto_response:
                    self.state_manager.add_message(conversation_id, "assistant", _auto_response,
                        metadata={"agent": "autonomous_react_agent", "intent": "cross_domain",
                                  "confidence": confidence, "tool_calls": _tool_calls})
                    state_updates = {"last_agent": "autonomous_react_agent", "last_intent": "cross_domain"}
                    if conv_state and conversation_id:
                        state_updates["conversation_state"] = conv_state.to_dict()
                    self.state_manager.update_state(conversation_id, state_updates)
                    return {
                        "success": True,
                        "conversation_id": conversation_id,
                        "intent": "cross_domain",
                        "agent": "autonomous_react_agent",
                        "agent_type": "autonomous",
                        "confidence": confidence,
                        "message": _auto_response,
                        "requires_user_input": _auto_meta.get("needs_clarification", False),
                        "suggested_prompts": [],
                        "next_actions": [],
                        "result": {"message": _auto_response, "data": {"tool_calls": _tool_calls}},
                        "policy_constraints": policy.get("constraints", {}),
                        "tier": 6,
                    }
                # If no pre-resolved response (should not happen), fall through to _handle_directly
                logger.warning("[Orchestrator] Tier 6 routed to autonomous but no response in intent_details")
            domain = self._domain_registry.get_instance(domain_id)
            if domain:
                dc = DomainContext(domain_id=domain_id, user_id=user_id,
                    session_id=conversation_id or "", tenant_id=ctx.get("company_id"),
                    current_data=ctx, conversation_state=conv_state,
                    metadata={"conversation_id": conversation_id,
                              "constraints": policy.get("constraints", {})})
                dr = await self._domain_workflow.process(domain=domain, context=dc, query=sanitized)
                resp_msg = dr.message or "Processado com sucesso."
                executor = (dr.metadata or {}).get("executor", "domain_heuristic")
                if executor != "react_agent" and self._is_technical_response(resp_msg):
                    logger.info(
                        f"[Orchestrator] Technical response detected from domain '{domain_id}' "
                        f"(executor={executor}), falling back to LLM"
                    )
                    fb = await self._handle_directly(intent, sanitized, dr.data or {}, context=ctx)
                    resp_msg = fb.get("message") or resp_msg
                self.state_manager.add_message(conversation_id, "assistant", resp_msg,
                    metadata={"agent": domain_id, "intent": domain_id, "confidence": confidence})
                state_updates = {"last_agent": domain_id, "last_intent": domain_id}
                if conv_state and conversation_id:
                    state_updates["conversation_state"] = conv_state.to_dict()
                self.state_manager.update_state(conversation_id, state_updates)
                result = {"success": dr.success, "conversation_id": conversation_id,
                          "intent": dr.action_id or domain_id, "agent": domain_id,
                          "agent_type": domain_id, "confidence": dr.confidence or confidence,
                          "message": resp_msg, "requires_user_input": dr.needs_clarification or dr.needs_confirmation,
                          "suggested_prompts": dr.suggestions or [], "next_actions": [],
                          "result": {"message": resp_msg, "data": dr.data, "suggestions": dr.suggestions},
                          # FIX-RRP-SUP (AUD-4 §4.2, 2026-06-07): carrega response_blocks
                          # do sub-agente (vivem em dr.metadata, via rrp_block_sink) que o
                          # legacy dropava -> from_orchestrator_result le ->
                          # _orchestrator_result_to_frames emite no frame message. Fecha o
                          # moat RRP na trilha supervisor (paridade com o federado).
                          "response_blocks": (dr.metadata or {}).get("response_blocks"),
                          "hitl_pending": (dr.metadata or {}).get("hitl_pending"),
                          # Fase 2 (2026-06-09): diretiva ui_action do sub-agente
                          # (open_ui/apply_table_state via ui_action_sink -> metadata)
                          # que o legacy dropava -> from_orchestrator_result le ->
                          # ChatResponse.ui_action. Simetria do supervisor Phase 2.
                          "ui_action": (dr.metadata or {}).get("ui_action"),
                          "ui_action_params": (dr.metadata or {}).get("ui_action_params"),
                          "policy_constraints": policy.get("constraints", {})}
            else:
                fb = await self._handle_directly(intent, sanitized, {}, context=ctx)
                result = {"success": True, "conversation_id": conversation_id, "intent": intent,
                          "agent": domain_id, "agent_type": domain_id, "confidence": confidence,
                          "message": fb.get("message", ""), "result": fb,
                          "requires_user_input": fb.get("requires_user_input", False),
                          "suggested_prompts": fb.get("suggested_prompts", []),
                          "next_actions": fb.get("next_actions", []),
                          "policy_constraints": policy.get("constraints", {})}
            if intent in self._cacheable_intents and self._response_cache.is_enabled():
                try:
                    ck = self._response_cache.generate_cache_key(
                        intent=intent, context=ctx, user_message=sanitized,
                        company_id=ctx.get("company_id"))
                    await self._response_cache.cache_response(ck, result, intent=intent)
                except Exception as cache_exc:
                    logger.warning(
                        "[orchestrator] response_cache write failed intent=%s - next request pays full LLM cost: %s",
                        intent, cache_exc, exc_info=True,
                    )
            return result
        except Exception as e:
            logger.error(f"Orchestration failed: {e}", exc_info=True)
            _user_name = ctx.get("user_name", "") if isinstance(ctx, dict) else ""
            return {"success": False, "error": str(e),
                    "message": SystemPromptBuilder.build_error_response(user_name=_user_name)}

    async def process_request_with_memory(self, db, user_id: str, message: str,
                                          conversation_id: str | None = None,
                                          context_type: str = "general",
                                          context_id: str | None = None,
                                          context: dict[str, Any] | None = None,
                                          company_id: str = "") -> dict[str, Any]:
        # Multi-tenancy: legacy orchestrator path (replaced by main_orchestrator).
        # If revived, callers MUST pass company_id from the request scope —
        # default "" triggers fail-closed raise in conversation_memory.
        try:
            if conversation_id:
                conv = await self.conversation_memory.get_conversation(db=db, conversation_id=conversation_id, include_messages=True)
                if not conv:
                    conv = await self.conversation_memory.get_or_create_conversation(db=db, user_id=user_id, company_id=company_id, context_type=context_type, context_id=context_id)
                    conversation_id = str(conv.id)
            else:
                conv = await self.conversation_memory.get_or_create_conversation(db=db, user_id=user_id, company_id=company_id, context_type=context_type, context_id=context_id)
                conversation_id = str(conv.id)
            await self.conversation_memory.add_message(db=db, conversation_id=conversation_id, role="user", content=message)
            llm_ctx = await self.conversation_memory.get_context_for_llm(db=db, conversation_id=conversation_id, max_messages=20)
            enhanced = context or {}
            enhanced.update({"conversation_history": llm_ctx.get("messages", []),
                             "conversation_summary": llm_ctx.get("summary"),
                             "context_type": context_type, "context_id": context_id})
            result = await self.process_request(user_id=user_id, message=message,
                                                conversation_id=conversation_id, context=enhanced)
            if result.get("success"):
                await self.conversation_memory.add_message(db=db, conversation_id=conversation_id,
                    role="assistant", content=result.get("message", ""), intent=result.get("intent"))
                if conv.message_count and conv.message_count % settings.ROUTER_SUMMARY_EVERY_N_MESSAGES == 0:
                    try:
                        await self.conversation_memory.update_summary(db=db, conversation_id=conversation_id, llm_service=self.llm_service)
                    except Exception as exc:
                        logger.warning(
                            "[orchestrator] update_summary failed (memory lost) conv_id=%s: %s",
                            conversation_id, exc, exc_info=True,
                        )
            await db.commit()
            result.update({"conversation_id": conversation_id, "context_type": context_type, "context_id": context_id})
            return result
        except Exception as e:
            logger.error(f"Process with memory failed: {e}", exc_info=True)
            await db.rollback()
            return {"success": False, "error": str(e), "conversation_id": conversation_id,
                    "message": SystemPromptBuilder.build_error_response()}

    _TECHNICAL_PATTERNS = (
        "Keyword heuristic matched",
        "Ferramenta '",
        "Ação '",
        "encaminhada para o agente",
        "executada para ação",
    )

    def _is_technical_response(self, message: str) -> bool:
        if message == "Processado com sucesso.":
            return True
        return any(p in message for p in self._TECHNICAL_PATTERNS)

    # CV matching keywords — used to trigger rubric tool regardless of classified intent
    _CV_MATCHING_PATTERNS = (
        "analise o cv", "analisa o cv", "analisar o cv", "análise do cv",
        "compatibilidade do candidato", "compatibilidade de candidato",
        "match do candidato", "match de cv", "match score",
        "triagem de cv", "triagem do candidato",
        "score do candidato", "avaliar cv", "avalie o cv",
        "analise a compatibilidade", "análise de compatibilidade",
        "quanto o candidato", "como o candidato se encaixa",
        "candidato para a vaga", "candidato está alinhado",
    )

    def _is_cv_matching_request(self, message: str) -> bool:
        """Check if message requests CV/candidate analysis regardless of classified intent."""
        msg_lower = message.lower()
        return any(p in msg_lower for p in self._CV_MATCHING_PATTERNS)

    # Structured-output additions injected per intent (fix C-05 / C-06)
    _STRUCTURED_INTENT_ADDENDA = {
        "cv_screening": (
            "\n\nRegra de saída estruturada (C-05): sempre que responder a uma análise de "
            "compatibilidade ou match de CV, inclua ao final da resposta um bloco JSON no formato:\n"
            "```json\n"
            "{\"match_score\": <0-100>, \"matched_skills\": [\"skill1\", \"skill2\"], "
            "\"missing_skills\": [\"skill3\"], \"recommendation\": \"APROVADO|EM_ANALISE|REPROVADO\"}\n"
            "```\n"
            "O match_score deve ser um número inteiro de 0 a 100."
        ),
        "salary_benchmark": SALARY_BENCHMARK_ADDENDUM,  # R-039
    }

    async def _handle_directly(
        self,
        intent: str,
        message: str,
        entities: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if intent == "cv_screening" or self._is_cv_matching_request(message):
            rubric_result = await self._handle_cv_screening_with_rubric(message, context or {})
            if rubric_result.get("success"):
                return rubric_result

        ctx = context or {}
        try:
            from langchain_core.prompts import ChatPromptTemplate
            extra = self._STRUCTURED_INTENT_ADDENDA.get(intent, "")
            # R3 (Task T-F): canonical tenant snippet resolver — emite
            # telemetria + fail-closed em strict-mode (mesmo contrato do
            # TenantAwareAgentMixin). Fecha o ponto cego do Orchestrator V1
            # (legacy /api/orchestrator route ainda em uso) que destruiu T-D/T-E.
            from app.shared.agents.tenant_aware_agent import (
                resolve_tenant_snippet_for_non_react,
            )
            _tenant_snippet = resolve_tenant_snippet_for_non_react(
                ctx,
                agent_name="orchestrator_v1",
                company_id_raw=ctx.get("company_id"),
            )
            _persona_cid = ctx.get("company_id")
            if _persona_cid:
                from app.shared.prompts.persona_aware_prompt import (
                    build_system_prompt_with_persona,
                )
                from lia_config.database import AsyncSessionLocal
                async with AsyncSessionLocal() as _persona_db:
                    system_prompt = await build_system_prompt_with_persona(
                        company_id=str(_persona_cid),
                        db=_persona_db,
                        agent_type="orchestrator",
                        tenant_context_snippet=_tenant_snippet,
                        user_name=ctx.get("user_name", ""),
                        user_role=ctx.get("user_role", ""),
                        conversation_summary=ctx.get("conversation_summary", ""),
                        conversation_history=ctx.get("conversation_history"),
                        context_page=ctx.get("context_page", "general"),
                        entity_type=ctx.get("entity_type"),
                        intent=intent,
                        entities=entities,
                        extra_instructions=extra,
                    )
            else:
                system_prompt = SystemPromptBuilder.build(
                    ai_persona=None,
                    agent_type="orchestrator",
                    tenant_context_snippet=_tenant_snippet,
                    user_name=ctx.get("user_name", ""),
                    user_role=ctx.get("user_role", ""),
                    conversation_summary=ctx.get("conversation_summary", ""),
                    conversation_history=ctx.get("conversation_history"),
                    context_page=ctx.get("context_page", "general"),
                    entity_type=ctx.get("entity_type"),
                    intent=intent,
                    entities=entities,
                    extra_instructions=extra,
                )
            # LIA-M03: Include conversation history as real message turns
            messages = [("system", system_prompt)]

            # Add conversation history as actual turns (last 10 messages max)
            conversation_history = ctx.get("conversation_history", [])
            if conversation_history and isinstance(conversation_history, list):
                recent_history = conversation_history[-10:]
                for msg in recent_history:
                    role = msg.get("role", "")
                    content = msg.get("content", "")
                    if role == "user":
                        messages.append(("human", content))
                    elif role == "assistant":
                        messages.append(("ai", content))

            messages.append(("human", "{message}"))
            prompt = ChatPromptTemplate.from_messages(messages)

            # LIA-A04 (Fase 4): bind tools in fallback path so LIA can act, not just talk.
            # ReAct agents already have tools via create_react_agent; this gives the
            # _handle_directly fallback path the same agentic capability.
            llm = self.llm_service.get_audited_model()
            _bind_tools_enabled = os.environ.get("LIA_FALLBACK_BIND_TOOLS", "true").lower() in ("1", "true", "yes")  # R-044: verified-active — mirrors FallbackReActService.TOOL_BIND_ENV_VAR
            if _bind_tools_enabled:
                try:
                    from app.tools import get_all_tool_schemas
                    tool_schemas = get_all_tool_schemas(agent_type="orchestrator", format="claude")
                    if tool_schemas:
                        llm = llm.bind_tools(tool_schemas)
                        logger.debug("[LIA-A04] _handle_directly bound %d tools", len(tool_schemas))
                except Exception as _bind_exc:
                    logger.warning("[LIA-A04] bind_tools failed (continuing without): %s", _bind_exc)

            chain = prompt | llm
            response = await chain.ainvoke({"message": message})

            # Extract content (string) from response (which may have tool_calls)
            response_content = response.content if hasattr(response, "content") else str(response)
            response_tools_used = []
            if hasattr(response, "tool_calls") and response.tool_calls:
                response_tools_used = [tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", "") for tc in response.tool_calls]
                logger.info("[LIA-A04] _handle_directly LLM requested %d tool(s): %s", len(response_tools_used), response_tools_used)

            return {"message": response_content, "success": True, "data": {"tool_calls_requested": response_tools_used},
                    "requires_user_input": True, "suggested_prompts": [], "next_actions": [],
                    "agent_used": "LIA Orchestrator", "agent_type": "orchestrator"}
        except Exception:
            user_name = ctx.get("user_name", "")
            error_msg = SystemPromptBuilder.build_error_response(user_name=user_name)
            return {"message": error_msg,
                    "success": True, "requires_user_input": True,
                    "suggested_prompts": [],
                    "agent_used": "LIA Orchestrator", "agent_type": "orchestrator"}

    async def _handle_cv_screening_with_rubric(
        self,
        message: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Opção B: Extract candidate/vacancy from message and invoke the BARS rubric tool.

        Uses the LLM for entity extraction only, then delegates scoring to
        CVScoringService (deterministic BARS methodology — not LLM free-text).
        Falls back gracefully so _handle_directly can use the LLM addendum instead.
        """
        try:
            import json
            import re

            from app.tools.executor import ToolExecutionContext, tool_executor

            # ── Entity extraction ─────────────────────────────────────────────
            extraction_prompt = (
                "Extraia do texto abaixo as informações de candidato e vaga para análise de CV. "
                "Retorne SOMENTE um JSON válido (sem markdown) com as chaves: "
                'candidate_id, candidate_name, vacancy_id, vacancy_title. '
                "Use null quando não encontrar. Não invente IDs — somente use se mencionados "
                "explicitamente como UUID.\n\n"
                f"Texto: {message}"
            )

            raw = await self.llm_service.generate(extraction_prompt, provider="gemini")

            # Strip potential markdown fences
            raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`")
            match = re.search(r"\{.*?\}", raw, re.DOTALL)
            if not match:
                logger.debug("[cv_screening rubric] No JSON in extraction response")
                return {"success": False}

            params = json.loads(match.group())
            # Remove null / empty values
            params = {k: v for k, v in params.items() if v not in (None, "", "null")}

            if not params.get("candidate_id") and not params.get("candidate_name"):
                logger.debug("[cv_screening rubric] No candidate found in message")
                return {"success": False}

            # ── Build execution context ───────────────────────────────────────
            exec_context = ToolExecutionContext(
                user_id=context.get("user_id", "system"),
                company_id=context.get("company_id"),
                session_id=context.get("session_id"),
            )

            # ── Execute tool ─────────────────────────────────────────────────
            tool_result = await tool_executor.execute(
                tool_name="analyze_cv_match",
                parameters=params,
                agent_type="orchestrator",
                context=exec_context,
            )

            if tool_result.success and tool_result.result:
                data = tool_result.result
                return {
                    "success": True,
                    "message": data.get("message", "Análise de CV concluída."),
                    "data": data,
                    "requires_user_input": False,
                    "suggested_prompts": [
                        "Mover candidato para próxima etapa",
                        "Ver outros candidatos para esta vaga",
                        "Enviar feedback ao candidato",
                    ],
                    "next_actions": [],
                    "agent_used": "CV Match Tool (BARS Rubric)",
                    "agent_type": "tool",
                    # C-05 structured fields surfaced at top level
                    "match_score": data.get("match_score"),
                    "matched_skills": data.get("matched_skills", []),
                    "missing_skills": data.get("missing_skills", []),
                    "recommendation": data.get("recommendation"),
                }

            logger.warning("[cv_screening rubric] Tool returned failure: %s", tool_result.error)
            return {"success": False}

        except Exception as exc:
            logger.warning("[cv_screening rubric] Tool invocation failed (%s), falling back to LLM", exc)
            return {"success": False}

    def get_available_tools(self, agent_type: str | None = None) -> list[dict[str, Any]]:
        return get_all_tool_schemas(agent_type=agent_type, format="claude")


    def get_scope_system_prompt(self, prompt_context: str) -> str:
        return get_scope_system_prompt_addition(SCOPE_MAPPING.get(prompt_context.lower(), PromptScope.GLOBAL))

    def is_tool_allowed(self, tool_name: str, prompt_context: str) -> bool:
        return is_tool_allowed_in_scope(tool_name, SCOPE_MAPPING.get(prompt_context.lower(), PromptScope.GLOBAL))

    async def execute_plan(self, conversation_id: str, plan: dict[str, Any]) -> dict[str, Any]:
        from app.shared.execution import AgentTask, ExecutionPlan
        exec_plan = ExecutionPlan()
        for i, step in enumerate(plan.get("plan", [])):
            task = AgentTask(
                task_id=f"task_{i}",
                domain_id=step.get("domain_id", step.get("agent_type", "recruiter_assistant")),
                action_id=step.get("action_id", step.get("description", "process")),
                depends_on=[f"task_{i-1}"] if i > 0 else [],
            )
            exec_plan.add_task(task)
        executed = await self._plan_executor.execute(
            plan=exec_plan, user_id="plan_executor",
            session_id=conversation_id, tenant_id=None,
        )
        results = []
        for task in executed.tasks:
            result_data = {}
            if task.result and isinstance(task.result, DomainResponse):
                result_data = {"message": task.result.message}
            results.append({
                "step": int(task.task_id.split("_")[1]) + 1,
                "agent": task.domain_id,
                "success": task.status.value == "completed",
                "result": result_data,
            })
        return {"success": executed.all_succeeded,
                "steps_executed": sum(1 for r in results if r["success"]),
                "steps_total": len(results), "results": results,
                "plan_summary": executed.get_summary()}

    def get_conversation_state(self, conversation_id: str) -> dict[str, Any] | None:
        return self.state_manager.get_state(conversation_id)

    def get_metrics(self) -> dict[str, Any]:
        return {"registered_domains": self._domain_registry.list_domains(),
                "domain_classes": self._domain_registry.list_registered_classes(),
                "active_conversations": len(self.state_manager.state_store),
                "policy_config": {"engine_version": self.policy_gate.engine_version},  # WT-2022 P3.1
                "routing_stats": self._cascaded_router.get_stats(),
                "cache_stats": self._response_cache.get_stats(),
                "smart_extractor_stats": self._domain_workflow.smart_extractor.get_stats(),
                "plan_detector_stats": self._plan_detector.get_stats()}

    async def process_analytics_request(self, user_id: str, command: str,
                                        context: dict[str, Any],
                                        conversation_id: str | None = None) -> dict[str, Any]:
        try:
            if command in COMMAND_TEMPLATES:
                result = await job_analytics_prompt_service.execute_command(command, context)
            else:
                result = await job_analytics_prompt_service.analyze_natural_query(command, context)
            if conversation_id:
                self.state_manager.update_state(conversation_id, {
                    "last_analytics_command": command, "last_analytics_result": result.command})
            return {"success": True, "command": result.command, "agent_used": result.agent_used,
                    "response": result.response, "data": result.data, "charts": result.charts,
                    "suggestions": result.suggestions, "metadata": result.metadata}
        except Exception as e:
            logger.error(f"Analytics request failed: {e}")
            return {"success": False, "error": str(e)}
