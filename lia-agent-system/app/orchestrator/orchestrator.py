"""
LIA-D06: DEPRECATED — This Orchestrator class is the v1 entry point.

All NEW code must use MainOrchestrator from main_orchestrator.py via
get_main_orchestrator(). This class is still used by app/api/orchestrator_routes.py
(legacy route). Kept for backwards compat and will be removed in a future release.

DO NOT use this class in new code.
"""
import warnings as _lia_warnings

import logging
import os
from typing import Any

from app.orchestrator._observability import V1_SPANS
from app.shared.observability.tracing import trace_span


from app.core.config import settings
from app.domains.base import DomainContext, DomainResponse
from app.domains.registry import DomainRegistry
from app.domains.workflow import DomainWorkflow
from app.shared.execution import PlanDetector, PlanExecutor
from app.shared.robustness import CancellationHandler, sanitize_text

from .cascaded_router import CascadedRouter
from .policy_engine import PolicyEngine
from .state_manager import StateManager
from .task_planner import TaskPlanner

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
from app.tools.scope_config import (
    PromptScope,
    filter_tools_by_scope,
    get_scope_system_prompt_addition,
    is_tool_allowed_in_scope,
)

logger = logging.getLogger(__name__)

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
        _lia_warnings.warn(
            "[LIA-D06] Orchestrator is deprecated. Use MainOrchestrator instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.llm_service = llm_service
        self.db_service = db_service
        self.task_planner = TaskPlanner(llm_service)
        self.policy_engine = PolicyEngine(db_service)
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
        # Sprint II.2 + III audit: init no __init__ evita race condition em concurrent calls
        # (lazy init via hasattr criava 2 instâncias quando 2 requests chegavam simultaneamente)
        from app.orchestrator.services.fallback_react_service import FallbackReActService
        self._fallback_react_service = FallbackReActService(llm_service=llm_service)
        # Sprint IV: rubric dispatch para BARS CV match (extraído de _handle_cv_screening_with_rubric)
        from app.domains.cv_screening.services.rubric_dispatch import RubricDispatchService
        self._rubric_dispatch_service = RubricDispatchService(llm_service=llm_service)
        # Extraction follow-up: analytics dispatch (extraído de process_analytics_request)
        from app.domains.analytics.services.analytics_dispatch import AnalyticsDispatchService
        self._analytics_dispatch_service = AnalyticsDispatchService(
            analytics_service=job_analytics_prompt_service,
            command_templates=COMMAND_TEMPLATES,
        )
        logger.info("Orchestrator initialized with CascadedRouter + DomainWorkflow")

    def _init_cascaded_router(self):
        self._cascaded_router = CascadedRouter(
            domain_registry=self._domain_registry,
        )

    def _initialize_tools(self) -> None:
        try:
            initialize_tools()
            logger.info(f"Initialized {len(tool_registry.list_tools())} tools")
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

    @trace_span(V1_SPANS.PROCESS_REQUEST)
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

            # PR-A: hint override do Rail A (FE-H03 do audit enterprise 2026-04-26).
            # Precedência: rail_a_hint > context_type > CascadedRouter.
            from app.orchestrator.services.rail_a_hint_override import try_hint_route
            from app.orchestrator.services.context_type_override import try_override_route
            route = try_hint_route(ctx)
            if route is not None:
                logger.info(
                    "[Orchestrator] rail_a_hint override: card=%s → domain=%s intent=%s",
                    (ctx.get("metadata") or {}).get("card_id", "?"),
                    route.domain_id,
                    (route.intent_details or {}).get("raw_intent", "?"),
                )
            else:
                route = try_override_route(ctx)
                if route is not None:
                    logger.info(
                        "[Orchestrator] context_type override: %s → domain=%s",
                        ctx.get("context_type", ""),
                        route.domain_id,
                    )
                else:
                    route = await self._cascaded_router.route(sanitized, ctx, session_id=conversation_id)
            domain_id, confidence = route.domain_id, route.confidence
            intent = (route.intent_details or {}).get("raw_intent") or route.domain_id
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
            policy = await self.policy_engine.validate_request(intent, user_id, context=ctx)
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
                _auto_response = (route.intent_details or {}).get("response", "")
                _auto_meta = (route.intent_details or {}).get("metadata", {})
                _tool_calls = (route.intent_details or {}).get("tool_calls", 0)
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
                # LIA-LCF-01 (Task #620): Surface ReAct tool calls so eval/judge
                # and downstream consumers can observe which tools the agent used.
                _tool_results = (dr.metadata or {}).get("tool_results") or []
                _actions: list[dict[str, Any]] = []
                for _tr in _tool_results:
                    if not isinstance(_tr, dict):
                        continue
                    _name = _tr.get("tool_name") or _tr.get("name")
                    if not _name:
                        continue
                    _actions.append({
                        "name": _name,
                        "args": _tr.get("arguments") or _tr.get("args") or _tr.get("params") or {},
                        "success": bool(_tr.get("success", True)),
                        "error": _tr.get("error"),
                    })
                result = {"success": dr.success, "conversation_id": conversation_id,
                          "intent": dr.action_id or domain_id, "agent": domain_id,
                          "agent_type": domain_id, "confidence": dr.confidence or confidence,
                          "message": resp_msg, "requires_user_input": dr.needs_clarification or dr.needs_confirmation,
                          "suggested_prompts": dr.suggestions or [], "next_actions": [],
                          "actions": _actions,
                          "result": {"message": resp_msg, "data": dr.data, "suggestions": dr.suggestions,
                                     "tool_calls": _actions},
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
                except Exception:
                    pass
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
                                          context: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            if conversation_id:
                conv = await self.conversation_memory.get_conversation(db=db, conversation_id=conversation_id, include_messages=True)
                if not conv:
                    conv = await self.conversation_memory.get_or_create_conversation(db=db, user_id=user_id, context_type=context_type, context_id=context_id)
                    conversation_id = str(conv.id)
            else:
                conv = await self.conversation_memory.get_or_create_conversation(db=db, user_id=user_id, context_type=context_type, context_id=context_id)
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
                        # Audit task #545 — billing por empresa para
                        # sumarização de conversas do recruiter.
                        _company_id = (context or {}).get("company_id") if context else None
                        await self.conversation_memory.update_summary(
                            db=db, conversation_id=conversation_id,
                            tracking_context={
                                "company_id": _company_id,
                                "user_id": user_id,
                            } if _company_id else None,
                        )
                    except Exception:
                        pass
            await db.commit()
            result.update({"conversation_id": conversation_id, "context_type": context_type, "context_id": context_id})
            return result
        except Exception as e:
            logger.error(f"Process with memory failed: {e}", exc_info=True)
            await db.rollback()
            return {"success": False, "error": str(e), "conversation_id": conversation_id,
                    "message": SystemPromptBuilder.build_error_response()}

    def _is_technical_response(self, message: str) -> bool:
        """Delegação canônica para heuristics module (Sprint II.3, ADR-019).

        Mantido como método para preservar API interna do V1. Comportamento
        é idêntico ao implementado no módulo canônico — verificado via
        `tests/unit/orchestrator/heuristics/test_heuristics.py::TestEquivalenceWithV1`.
        """
        from app.orchestrator.heuristics import is_technical_response
        return is_technical_response(message)

    def _is_cv_matching_request(self, message: str) -> bool:
        """Delegação canônica para heuristics module (Sprint II.3, ADR-019).

        Check if message requests CV/candidate analysis regardless of classified intent.
        Comportamento idêntico ao módulo canônico (validado em characterization tests).
        """
        from app.orchestrator.heuristics import is_cv_matching_request
        return is_cv_matching_request(message)

    async def _handle_directly(
        self,
        intent: str,
        message: str,
        entities: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Sprint II.2 — delegação canônica ao FallbackReActService (LIA-A04).

        Pre-flight CV screening rubric mantém-se aqui (domain-specific),
        mas a lógica core do fallback ReAct foi extraída ao service.

        Estrutura:
        1. Tenta CV rubric primeiro (se intent ou heurística sinaliza CV match)
        2. Delega ao FallbackReActService.handle_directly para LLM + tools
        """
        # 1. Pre-flight CV rubric — domain-specific, fica em V1 por enquanto.
        #    Sprint III: caller (V2) decide se quer essa pre-flight via cv_screening domain.
        if intent == "cv_screening" or self._is_cv_matching_request(message):
            rubric_result = await self._handle_cv_screening_with_rubric(message, context or {})
            if rubric_result.get("success"):
                return rubric_result

        # 2. Delegação canônica para o service (Sprint II.2 + III audit fix, ADR-019)
        # Service criado no __init__ — sem race condition em concurrent.
        return await self._fallback_react_service.handle_directly(
            intent=intent,
            message=message,
            entities=entities,
            context=context,
        )

    async def _handle_cv_screening_with_rubric(
        self,
        message: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Sprint IV — delegação canônica ao RubricDispatchService.

        Service em app/domains/cv_screening/services/rubric_dispatch.py
        substitui implementação inline do V1 com:
        - Mesmo fluxo: entity extraction (LLM) + BARS rubric tool dispatch
        - Mesmo shape de retorno (V1-compatible)
        - Multi-tenant isolation preservada (company_id em ToolExecutionContext)
        - Graceful degradation: any exception -> {"success": False}

        Comportamento idêntico ao V1 inline — verificado via 18 unit tests
        em tests/unit/domains/cv_screening/test_rubric_dispatch.py.

        Reference: ADR-019 — Sprint IV
        """
        return await self._rubric_dispatch_service.dispatch(message, context)

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
                "policy_config": self.policy_engine.policies,
                "routing_stats": self._cascaded_router.get_stats(),
                "cache_stats": self._response_cache.get_stats(),
                "smart_extractor_stats": self._domain_workflow.smart_extractor.get_stats(),
                "plan_detector_stats": self._plan_detector.get_stats()}

    async def process_analytics_request(self, user_id: str, command: str,
                                        context: dict[str, Any],
                                        conversation_id: str | None = None) -> dict[str, Any]:
        """Delegação canônica ao AnalyticsDispatchService (extraction follow-up).

        State manager update fica em V1 (V1-specific session lifecycle).
        Service handle the dispatch + response shaping.

        Reference: ADR-019 — process_analytics_request extraction
        """
        result = await self._analytics_dispatch_service.dispatch(command, context)

        # State manager update (V1-specific — não passou para service)
        if result.get("success") and conversation_id:
            self.state_manager.update_state(conversation_id, {
                "last_analytics_command": command,
                "last_analytics_result": result.get("command"),
            })

        return result
