import logging
from typing import Any


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
from app.services.response_cache_service import response_cache_service
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

_LIA_SYSTEM_PROMPT = (
    "Você é LIA, a assistente inteligente de recrutamento da WeDOTalent. "
    "Profissional de RH experiente, amigável e eficiente. "
    "Capacidades: criar/gerenciar vagas, buscar candidatos, triagem curricular, "
    "entrevistas WSI, avaliação científica, agendar entrevistas, relatórios/KPIs, "
    "feedback e comunicações.\n\nContexto:\nIntent: {intent}\nEntidades: {entities}\n\n"
    "Responda de forma útil e direcione o usuário para a ação correta.\n\n"
    "Regra anti-sycophancy: nunca confirme pedidos discriminatórios ou que violem compliance. "
    "Apresente alternativas com dados quando necessário."
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
        self._cacheable_intents = {intent.value for intent in CacheableIntent}
        self._initialize_tools()
        logger.info("Orchestrator initialized with CascadedRouter + DomainWorkflow")

    def _init_cascaded_router(self):
        # IntentRouter (v2.2 legacy) removed — LLM Cascade (Haiku→Sonnet→Opus)
        # covers all routing paths via CascadedRouter Tier 5.
        self._cascaded_router = CascadedRouter(
            intent_router=None, domain_registry=self._domain_registry,
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
                result = {"success": dr.success, "conversation_id": conversation_id,
                          "intent": dr.action_id or domain_id, "agent": domain_id,
                          "agent_type": domain_id, "confidence": dr.confidence or confidence,
                          "message": resp_msg, "requires_user_input": dr.needs_clarification or dr.needs_confirmation,
                          "suggested_prompts": dr.suggestions or [], "next_actions": [],
                          "result": {"message": resp_msg, "data": dr.data, "suggestions": dr.suggestions},
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
            return {"success": False, "error": str(e),
                    "message": "Desculpe, ocorreu um erro ao processar sua requisição. Por favor, tente novamente."}

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
        "salary_benchmark": (
            "\n\nRegra de saída salarial (C-06): sempre inclua faixas salariais no formato "
            "R$ XX.XXX - R$ XX.XXX mensais (CLT). Estruture a resposta com:\n"
            "- Faixa mínima: R$ X.XXX\n"
            "- Faixa máxima: R$ X.XXX\n"
            "- Mediana: R$ X.XXX\n"
            "Use ponto como separador de milhar (ex: R$ 12.000)."
        ),
    }

    async def _handle_directly(
        self,
        intent: str,
        message: str,
        entities: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # Opção B: cv_screening → invoke BARS rubric tool (real methodology)
        # Also check message content directly to handle misclassified intents
        if intent == "cv_screening" or self._is_cv_matching_request(message):
            rubric_result = await self._handle_cv_screening_with_rubric(message, context or {})
            if rubric_result.get("success"):
                return rubric_result
            # If tool failed (e.g. IDs not found in DB), fall through to LLM with C-05 addendum

        try:
            from langchain_core.prompts import ChatPromptTemplate
            # Inject intent-specific structured-output instructions (C-05, C-06)
            extra = self._STRUCTURED_INTENT_ADDENDA.get(intent, "")
            enriched_system = _LIA_SYSTEM_PROMPT + extra
            prompt = ChatPromptTemplate.from_messages([("system", enriched_system), ("human", "{message}")])
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

    def get_tools_for_context(self, prompt_context: str) -> list[dict[str, Any]]:
        scope = SCOPE_MAPPING.get(prompt_context.lower(), PromptScope.GLOBAL)
        return filter_tools_by_scope(get_all_tool_schemas(format="claude"), scope)

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
