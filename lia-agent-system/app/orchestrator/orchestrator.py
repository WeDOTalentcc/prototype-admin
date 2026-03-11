import logging
from typing import Dict, Any, Optional, List
from app.core.config import settings
from .task_planner import TaskPlanner
from .policy_engine import PolicyEngine
from .state_manager import StateManager
from .cascaded_router import CascadedRouter
from app.shared.robustness import sanitize_text, CancellationHandler, create_user_friendly_error, AgentErrorCode
from app.domains.registry import DomainRegistry
from app.domains.workflow import DomainWorkflow
from app.domains.base import DomainContext, DomainResponse
from app.shared.execution import PlanDetector, PlanExecutor
from app.shared.memory.conversation_state import ConversationState
from app.services import job_analytics_prompt_service, COMMAND_TEMPLATES
from app.services.conversation_memory import conversation_memory
from app.services.response_cache_service import response_cache_service
from app.tools import (
    tool_registry, initialize_tools, get_all_tool_schemas
)
from app.tools.scope_config import (
    PromptScope, filter_tools_by_scope, get_scope_system_prompt_addition, is_tool_allowed_in_scope
)

logger = logging.getLogger(__name__)

SCOPE_MAPPING = {
    "talent_funnel": PromptScope.TALENT_FUNNEL,
    "job_table": PromptScope.JOB_TABLE,
    "in_job": PromptScope.IN_JOB,
    "global": PromptScope.GLOBAL,
    "pipeline": PromptScope.IN_JOB,
    "candidates": PromptScope.TALENT_FUNNEL,
    "jobs": PromptScope.JOB_TABLE,
    "vacancies": PromptScope.JOB_TABLE,
}

_LIA_SYSTEM_PROMPT = (
    "Você é LIA, a assistente inteligente de recrutamento da WeDOTalent. "
    "Profissional de RH experiente, amigável e eficiente. "
    "Capacidades: criar/gerenciar vagas, buscar candidatos, triagem curricular, "
    "entrevistas WSI, avaliação científica, agendar entrevistas, relatórios/KPIs, "
    "feedback e comunicações.\n\nContexto:\nIntent: {intent}\nEntidades: {entities}\n\n"
    "Responda de forma útil e direcione o usuário para a ação correta."
)


class Orchestrator:
    def __init__(self, llm_service, db_service=None):
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
        self._cacheable_intents = {
            "pipeline_stats", "job_status", "candidate_count", "stage_distribution",
            "funnel_analysis", "job_insights", "market_data", "salary_benchmark",
            "analytics", "recommendations", "skills_analysis", "candidate_search"
        }
        self._initialize_tools()
        logger.info("Orchestrator initialized with CascadedRouter + DomainWorkflow")

    def _init_cascaded_router(self):
        try:
            from .intent_router import IntentRouter
            llm_fallback = IntentRouter(self.llm_service)
        except Exception:
            llm_fallback = None
        self._cascaded_router = CascadedRouter(
            intent_router=llm_fallback, domain_registry=self._domain_registry,
        )

    def _initialize_tools(self) -> None:
        try:
            initialize_tools()
            logger.info(f"Initialized {len(tool_registry.list_tools())} tools")
        except Exception as e:
            logger.warning(f"Tool initialization warning: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
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
                              conversation_id: Optional[str] = None,
                              context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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
                    executed_plan = await self._plan_executor.execute(
                        plan=detected_plan,
                        user_id=user_id,
                        session_id=conversation_id or "",
                        tenant_id=ctx.get("company_id", "default"),
                        base_context=plan_context,
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
            domain = self._domain_registry.get_instance(domain_id)
            if domain:
                dc = DomainContext(domain_id=domain_id, user_id=user_id,
                    session_id=conversation_id or "", tenant_id=ctx.get("company_id", "default"),
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
                    fb = await self._handle_directly(intent, sanitized, dr.data or {})
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
                          "policy_constraints": policy.get("constraints", {})}
            else:
                fb = await self._handle_directly(intent, sanitized, {})
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
            return {"success": False, "error": str(e),
                    "message": "Desculpe, ocorreu um erro ao processar sua requisição. Por favor, tente novamente."}

    async def process_request_with_memory(self, db, user_id: str, message: str,
                                          conversation_id: Optional[str] = None,
                                          context_type: str = "general",
                                          context_id: Optional[str] = None,
                                          context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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
                        await self.conversation_memory.update_summary(db=db, conversation_id=conversation_id, llm_service=self.llm_service)
                    except Exception:
                        pass
            await db.commit()
            result.update({"conversation_id": conversation_id, "context_type": context_type, "context_id": context_id})
            return result
        except Exception as e:
            logger.error(f"Process with memory failed: {e}", exc_info=True)
            await db.rollback()
            return {"success": False, "error": str(e), "conversation_id": conversation_id,
                    "message": "Desculpe, ocorreu um erro ao processar sua requisição."}

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

    async def _handle_directly(self, intent: str, message: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from langchain_core.prompts import ChatPromptTemplate
            prompt = ChatPromptTemplate.from_messages([("system", _LIA_SYSTEM_PROMPT), ("human", "{message}")])
            chain = prompt | self.llm_service.claude
            response = await chain.ainvoke({"intent": intent, "entities": str(entities), "message": message})
            return {"message": response.content, "success": True, "data": {},
                    "requires_user_input": True, "suggested_prompts": [], "next_actions": [],
                    "agent_used": "LIA Orchestrator", "agent_type": "orchestrator"}
        except Exception:
            return {"message": f"Olá! Sou a LIA, sua assistente de recrutamento. "
                               f"Recebi sua mensagem sobre '{message[:50]}...' Como posso ajudar você hoje?",
                    "success": True, "requires_user_input": True,
                    "suggested_prompts": ["Criar uma nova vaga", "Buscar candidatos", "Ver minhas tarefas pendentes"],
                    "agent_used": "LIA Orchestrator", "agent_type": "orchestrator"}

    def get_available_tools(self, agent_type: Optional[str] = None) -> List[Dict[str, Any]]:
        return get_all_tool_schemas(agent_type=agent_type, format="claude")

    def get_tools_for_context(self, prompt_context: str) -> List[Dict[str, Any]]:
        scope = SCOPE_MAPPING.get(prompt_context.lower(), PromptScope.GLOBAL)
        return filter_tools_by_scope(get_all_tool_schemas(format="claude"), scope)

    def get_scope_system_prompt(self, prompt_context: str) -> str:
        return get_scope_system_prompt_addition(SCOPE_MAPPING.get(prompt_context.lower(), PromptScope.GLOBAL))

    def is_tool_allowed(self, tool_name: str, prompt_context: str) -> bool:
        return is_tool_allowed_in_scope(tool_name, SCOPE_MAPPING.get(prompt_context.lower(), PromptScope.GLOBAL))

    async def execute_plan(self, conversation_id: str, plan: Dict[str, Any]) -> Dict[str, Any]:
        from app.shared.execution import ExecutionPlan, AgentTask
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
            session_id=conversation_id, tenant_id="default",
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

    def get_conversation_state(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        return self.state_manager.get_state(conversation_id)

    def get_metrics(self) -> Dict[str, Any]:
        return {"registered_domains": self._domain_registry.list_domains(),
                "domain_classes": self._domain_registry.list_registered_classes(),
                "active_conversations": len(self.state_manager.state_store),
                "policy_config": self.policy_engine.policies,
                "routing_stats": self._cascaded_router.get_stats(),
                "cache_stats": self._response_cache.get_stats(),
                "smart_extractor_stats": self._domain_workflow.smart_extractor.get_stats(),
                "plan_detector_stats": self._plan_detector.get_stats()}

    async def process_analytics_request(self, user_id: str, command: str,
                                        context: Dict[str, Any],
                                        conversation_id: Optional[str] = None) -> Dict[str, Any]:
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
