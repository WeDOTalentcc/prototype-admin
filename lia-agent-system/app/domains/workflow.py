"""
Domain Workflow - 3-node processing pipeline for domain operations.

Pipeline: analyze_intent → execute → format

Each step is an async function that processes and updates the workflow state.
This replaces per-agent processing logic with a unified domain-driven flow.

Compatible with the JobWizardGraph pattern but generalized for any domain.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, StrEnum
from typing import Any

from app.domains.base import (
    DomainContext,
    DomainPrompt,
    DomainResponse,
    IntentResult,
)


# LIA-C02: Import lazy para evitar circular imports
def _get_compliance_class():
    """Lazy import de ComplianceDomainPrompt para evitar importação circular."""
    try:
        from app.domains.compliance_base import ComplianceDomainPrompt
        return ComplianceDomainPrompt
    except ImportError:
        return None

logger = logging.getLogger(__name__)


class WorkflowStep(StrEnum):
    PRE_CHECK = "pre_check"
    RESOLVE_REFERENCES = "resolve_references"
    SMART_EXTRACT = "smart_extract"
    ANALYZE_INTENT = "analyze_intent"
    EXECUTE = "execute"
    FORMAT = "format"
    POST_CHECK = "post_check"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class WorkflowState:
    query: str
    domain: DomainPrompt
    context: DomainContext
    current_step: WorkflowStep = WorkflowStep.ANALYZE_INTENT
    intent_result: IntentResult | None = None
    raw_response: DomainResponse | None = None
    formatted_response: DomainResponse | None = None
    error: str | None = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    execution_log: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def log_step(self, step: str, details: dict[str, Any]) -> None:
        self.execution_log.append({
            "step": step,
            "timestamp": datetime.utcnow().isoformat(),
            **details,
        })


CONFIDENCE_THRESHOLD = 0.5


class DomainWorkflow:
    """
    Unified workflow for processing domain requests.

    Pipeline:
    1. analyze_intent: Domain classifies user intent, extracts params
    2. execute: If confidence >= threshold, domain executes the action
    3. format: Build final response with suggestions and metadata

    Usage:
        workflow = DomainWorkflow()
        response = await workflow.process(domain, context, "buscar candidatos python")
    """

    def __init__(
        self,
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
        enable_fairness_guard: bool = True,
        enable_fact_checker: bool = True,
        enable_learning_loop: bool = True,
    ):
        self.confidence_threshold = confidence_threshold
        self.enable_fairness_guard = enable_fairness_guard
        self.enable_fact_checker = enable_fact_checker
        self.enable_learning_loop = enable_learning_loop
        self._smart_extractor = None

    @property
    def smart_extractor(self):
        if self._smart_extractor is None:
            from app.shared.intelligence.smart_extractor import SmartExtractor
            self._smart_extractor = SmartExtractor()
        return self._smart_extractor

    async def process(
        self,
        domain: DomainPrompt,
        context: DomainContext,
        query: str,
    ) -> DomainResponse:
        state = WorkflowState(query=query, domain=domain, context=context)

        try:
            # LIA-C02: Type check — domínios devem herdar ComplianceDomainPrompt
            _ComplianceDomainPrompt = _get_compliance_class()
            if _ComplianceDomainPrompt is not None and not isinstance(domain, _ComplianceDomainPrompt):
                logger.warning(
                    "[LIA-C02] Domain '%s' herda DomainPrompt diretamente — "
                    "migre para ComplianceDomainPrompt para compliance automático. "
                    "(classe=%s)",
                    domain.domain_id,
                    domain.__class__.__name__,
                )

            if self.enable_fairness_guard:
                blocked_response = await self._pre_check(state)
                if blocked_response is not None:
                    return blocked_response

            # LIA-C02: Pre-process compliance (FairnessGuard L3 + PII + InjectionGuard)
            # Executado APÓS _pre_check para não duplicar check L1 do FairnessGuard
            if _ComplianceDomainPrompt is not None and isinstance(domain, _ComplianceDomainPrompt):
                pre_response = await domain.pre_process(query, context)
                if pre_response is not None:
                    logger.info(
                        "[LIA-C02] pre_process bloqueou query no domínio '%s'",
                        domain.domain_id,
                    )
                    return pre_response

            await self._resolve_references(state)

            state = await self._analyze_intent(state)

            if state.current_step == WorkflowStep.ERROR:
                return self._build_error_response(state)

            state = await self._execute(state)

            if state.current_step == WorkflowStep.ERROR:
                return self._build_error_response(state)

            state = await self._format(state)

            # LIA-A02: LLM interpretation for domain execution results
            # If the formatted response looks like a raw template, interpret it
            if state.formatted_response and state.formatted_response.message:
                try:
                    _interpreted_msg = await self._interpret_if_technical(
                        state.formatted_response.message,
                        query,
                        {},
                    )
                    if _interpreted_msg != state.formatted_response.message:
                        state.formatted_response.message = _interpreted_msg
                        state.log_step("agentic_interpret", {"status": "rewritten"})
                except Exception as _interp_exc:
                    logger.debug("[LIA-A02] Interpretation skipped (fail-open): %s", _interp_exc)

            # LIA-C02: Post-process compliance (FactCheck via ComplianceDomainPrompt)
            _ComplianceDomainPrompt2 = _get_compliance_class()
            if (
                _ComplianceDomainPrompt2 is not None
                and isinstance(domain, _ComplianceDomainPrompt2)
                and state.formatted_response is not None
            ):
                state.formatted_response = await domain.post_process(
                    state.formatted_response, context
                )
                state.log_step("post_process_compliance", {"status": "completed"})

            # Skip _post_check if ComplianceDomainPrompt.post_process already ran FactChecker
            # to avoid double fact-checking the same response (performance + accuracy)
            _already_fact_checked = (
                _ComplianceDomainPrompt2 is not None
                and isinstance(domain, _ComplianceDomainPrompt2)
            )
            if self.enable_fact_checker and not _already_fact_checked:
                state = await self._post_check(state)

            state.current_step = WorkflowStep.COMPLETE
            state.completed_at = datetime.utcnow()

            if self.enable_learning_loop:
                try:
                    from app.shared.learning.learning_loop_service import learning_loop_service
                    await learning_loop_service.record_interaction(
                        domain_id=domain.domain_id,
                        action_id=state.intent_result.action_id if state.intent_result else "unknown",
                        query=query,
                        success=state.formatted_response.success if state.formatted_response else False,
                        confidence=state.intent_result.confidence if state.intent_result else 0.0,
                        response_metadata=state.formatted_response.metadata if state.formatted_response else {},
                    )
                except Exception as e:
                    logger.warning(f"LearningLoop recording failed: {e}")

            return state.formatted_response or DomainResponse.error_response(
                "Workflow completed without producing a response"
            )

        except Exception as e:
            logger.error(f"DomainWorkflow error for domain '{domain.domain_id}': {e}", exc_info=True)
            state.error = str(e)
            state.current_step = WorkflowStep.ERROR
            state.completed_at = datetime.utcnow()
            return DomainResponse.error_response(
                error=f"Workflow processing failed: {e}",
                message="Desculpe, ocorreu um erro ao processar sua solicitação.",
                metadata={"execution_log": state.execution_log},
            )

    async def _resolve_references(self, state: WorkflowState) -> None:
        state.current_step = WorkflowStep.RESOLVE_REFERENCES

        if not state.context.conversation_state:
            state.log_step("resolve_references", {"status": "skipped", "reason": "no_conversation_state"})
            return

        try:
            from app.shared.memory.reference_resolver import ReferenceResolver

            resolver = ReferenceResolver()
            ref = resolver.resolve(state.query, state.context.conversation_state)

            if not ref.resolved:
                state.log_step("resolve_references", {
                    "status": "no_match",
                    "reference_type": ref.reference_type,
                })
                return

            if ref.reference_type in ("pronoun", "position", "previous", "name"):
                if ref.resolved_id is not None:
                    state.context.current_data["resolved_candidate_id"] = ref.resolved_id
                    state.context.selected_ids.append(str(ref.resolved_id))

            elif ref.reference_type == "shortlist":
                if ref.action == "add_shortlist" and ref.resolved_id is not None:
                    state.context.conversation_state.add_to_shortlist(ref.resolved_id)
                    state.context.current_data["shortlist_action"] = "added"
                    state.context.current_data["shortlist_candidate_id"] = ref.resolved_id
                elif ref.action == "show_shortlist":
                    state.context.current_data["shortlist_ids"] = ref.resolved_ids
                    state.context.current_data["shortlist_action"] = "show"
                elif ref.action == "remove_shortlist" and ref.resolved_id is not None:
                    state.context.conversation_state.remove_from_shortlist(ref.resolved_id)
                    state.context.current_data["shortlist_action"] = "removed"
                    state.context.current_data["shortlist_candidate_id"] = ref.resolved_id

            elif ref.reference_type == "continuation":
                if state.context.conversation_state.active_filters:
                    state.context.filters_applied = dict(state.context.conversation_state.active_filters)
                if ref.resolved_ids:
                    state.context.current_data["continuation_ids"] = ref.resolved_ids

            state.log_step("resolve_references", {
                "status": "resolved",
                "reference_type": ref.reference_type,
                "resolved_id": ref.resolved_id,
                "resolved_ids": ref.resolved_ids,
                "confidence": ref.confidence,
                "action": ref.action,
                "original_text": ref.original_text,
            })

            logger.debug(
                f"Reference resolved: type={ref.reference_type} "
                f"id={ref.resolved_id} confidence={ref.confidence:.2f}"
            )

        except Exception as e:
            logger.warning(f"Reference resolution failed (non-blocking): {e}", exc_info=True)
            state.log_step("resolve_references", {"status": "error", "error": str(e)})

    async def _pre_check(self, state: WorkflowState) -> DomainResponse | None:
        state.current_step = WorkflowStep.PRE_CHECK

        from app.shared.compliance.fairness_guard import FairnessGuard

        guard = FairnessGuard()
        result = guard.check(state.query)

        if result.is_blocked:
            state.log_step("pre_check", {
                "status": "blocked",
                "category": result.category,
                "blocked_terms": result.blocked_terms,
                "confidence": result.confidence,
            })

            return DomainResponse(
                success=False,
                message=result.educational_message or "",
                metadata={
                    "blocked_by": "fairness_guard",
                    "block_category": result.category,
                    "blocked_terms": result.blocked_terms,
                    "confidence": result.confidence,
                    "original_query": result.original_query,
                    "execution_log": state.execution_log,
                },
            )

        state.log_step("pre_check", {"status": "passed"})
        return None

    async def _analyze_intent(self, state: WorkflowState) -> WorkflowState:
        state.current_step = WorkflowStep.ANALYZE_INTENT

        try:
            if not state.domain.validate_context(state.context):
                state.error = f"Invalid context for domain '{state.domain.domain_id}'"
                state.current_step = WorkflowStep.ERROR
                state.log_step("analyze_intent", {"status": "failed", "reason": "invalid_context"})
                return state

            try:
                extraction = self.smart_extractor.extract(
                    query=state.query,
                    domain_id=state.domain.domain_id,
                )
                if extraction.has_params:
                    state.context.current_data["pre_extracted_params"] = extraction.params
                    state.context.current_data["extraction_source"] = extraction.source
                    state.context.current_data["extraction_confidence"] = extraction.confidence
                    state.log_step("smart_extract", {
                        "status": "success",
                        "params_count": len(extraction.params),
                        "source": extraction.source,
                        "confidence": extraction.confidence,
                        "cached": extraction.cached,
                        "time_ms": extraction.extraction_time_ms,
                    })
            except Exception as e:
                logger.warning(f"SmartExtractor failed (non-blocking): {e}")
                state.log_step("smart_extract", {"status": "error", "error": str(e)})

            # LIA-I02: Info/Action disambiguation
            # If the user asks "como funciona X?", tag it so domains can route to explanation
            try:
                from app.shared.services.keyword_intent_matcher import KeywordIntentMatcher
                _info_matcher = KeywordIntentMatcher()
                if _info_matcher.is_info_query(state.query):
                    logger.info("[LIA-I02] Info query detected: %s", state.query[:80])
                    state.metadata["is_info_query"] = True
                    if hasattr(state.context, "current_data"):
                        state.context.current_data["is_info_query"] = True
            except Exception as _info_exc:
                logger.debug("[LIA-I02] Info detection skipped: %s", _info_exc)

            intent_result = await state.domain.process_intent(state.query, state.context)
            state.intent_result = intent_result

            state.log_step("analyze_intent", {
                "status": "success",
                "intent_id": intent_result.intent_id,
                "action_id": intent_result.action_id,
                "confidence": intent_result.confidence,
                "confidence_level": intent_result.confidence_level.value,
            })

            logger.debug(
                f"Intent analyzed: {intent_result.intent_id} → {intent_result.action_id} "
                f"(confidence={intent_result.confidence:.2f})"
            )

        except Exception as e:
            logger.error(f"Intent analysis failed: {e}", exc_info=True)
            state.error = f"Intent analysis failed: {e}"
            state.current_step = WorkflowStep.ERROR
            state.log_step("analyze_intent", {"status": "error", "error": str(e)})

        return state

    async def _execute(self, state: WorkflowState) -> WorkflowState:
        state.current_step = WorkflowStep.EXECUTE

        if not state.intent_result:
            state.error = "No intent result available for execution"
            state.current_step = WorkflowStep.ERROR
            return state

        if state.intent_result.confidence < self.confidence_threshold:
            suggestions = state.domain.get_suggestions(state.context)
            state.raw_response = DomainResponse.clarification_response(
                question="Não tenho certeza do que você precisa. Pode reformular?",
                options=suggestions,
                metadata={
                    "confidence": state.intent_result.confidence,
                    "alternatives": state.intent_result.alternative_intents,
                },
            )
            state.log_step("execute", {
                "status": "skipped",
                "reason": "low_confidence",
                "confidence": state.intent_result.confidence,
                "threshold": self.confidence_threshold,
            })
            return state

        action = state.domain.get_action_by_id(state.intent_result.action_id)

        if action and action.requires_confirmation:
            state.raw_response = DomainResponse.confirmation_response(
                message=f"Confirma a execução de: {action.name}?",
                data=state.intent_result.extracted_params,
                metadata={"action": state.intent_result.action_id},
            )
            state.log_step("execute", {
                "status": "awaiting_confirmation",
                "action_id": state.intent_result.action_id,
            })
            return state

        try:
            # LIA-C06: Compliance pre-check before agent delegation
            if hasattr(state.domain, "pre_process"):
                try:
                    _compliance_result = await state.domain.pre_process(state.query, state.context)
                    if _compliance_result and getattr(_compliance_result, "is_blocked", False):
                        state.raw_response = _compliance_result
                        state.log_step("execute", {
                            "status": "blocked_by_compliance",
                            "action_id": state.intent_result.action_id if state.intent_result else "",
                            "executor": "compliance_pre_check",
                        })
                        return state
                except Exception as e:
                    logger.debug("[LIA-C06] Compliance pre-check skipped (fail-open): %s", e)

            # Tenta delegar para o ReAct agent do domínio (com raciocínio autônomo)
            # Fallback para execute_action (heurística) se o agente não estiver disponível
            react_response = await self._try_react_agent(state)
            if react_response is not None:
                state.raw_response = react_response
                state.log_step("execute", {
                    "status": "success",
                    "action_id": state.intent_result.action_id,
                    "executor": "react_agent",
                    "response_success": react_response.success,
                })
                return state

            response = await state.domain.execute_action(
                action_id=state.intent_result.action_id,
                params=state.intent_result.extracted_params,
                context=state.context,
            )
            state.raw_response = response

            if response.success and state.context.conversation_state and state.intent_result:
                try:
                    response_data = response.data if isinstance(response.data, dict) else {}
                    state.context.conversation_state.update_after_action(
                        action_id=state.intent_result.action_id,
                        domain_id=state.domain.domain_id,
                        response_data=response_data,
                    )
                except Exception as update_err:
                    logger.warning(f"Failed to update conversation state after action: {update_err}")

            if not response.metadata:
                response.metadata = {}
            response.metadata["executor"] = "domain_heuristic"

            state.log_step("execute", {
                "status": "success" if response.success else "failed",
                "action_id": state.intent_result.action_id,
                "executor": "domain_heuristic",
                "response_success": response.success,
            })

        except Exception as e:
            logger.error(f"Action execution failed: {e}", exc_info=True)
            state.error = f"Action execution failed: {e}"
            state.current_step = WorkflowStep.ERROR
            state.log_step("execute", {"status": "error", "error": str(e)})

        return state

    async def _format(self, state: WorkflowState) -> WorkflowState:
        state.current_step = WorkflowStep.FORMAT

        if not state.raw_response:
            state.error = "No response to format"
            state.current_step = WorkflowStep.ERROR
            return state

        response = state.raw_response

        response.domain_id = state.domain.domain_id
        if state.intent_result:
            response.action_id = state.intent_result.action_id
            response.confidence = state.intent_result.confidence

        if not response.suggestions:
            response.suggestions = state.domain.get_suggestions(state.context)

        response.metadata["workflow"] = {
            "execution_log": state.execution_log,
            "duration_ms": (
                int((datetime.utcnow() - state.started_at).total_seconds() * 1000)
            ),
        }

        state.formatted_response = response
        state.log_step("format", {"status": "success"})

        return state

    async def _post_check(self, state: WorkflowState) -> WorkflowState:
        state.current_step = WorkflowStep.POST_CHECK

        if not state.formatted_response:
            state.log_step("post_check", {"status": "skipped", "reason": "no_response"})
            return state

        from app.shared.compliance.fact_checker import FactChecker

        checker = FactChecker()
        context_data = state.context.current_data if state.context else {}
        result = checker.check_response(state.formatted_response.message, context_data)

        fact_check_metadata = result.to_metadata()
        state.formatted_response.metadata.update(fact_check_metadata)

        if result.inaccurate_claims > 0:
            state.formatted_response.metadata["fact_check_warning"] = (
                f"{result.inaccurate_claims} claim(s) could not be verified as accurate"
            )

        state.log_step("post_check", {
            "status": "completed",
            "total_claims": result.total_claims,
            "verified_claims": result.verified_claims,
            "accurate_claims": result.accurate_claims,
            "inaccurate_claims": result.inaccurate_claims,
            "overall_accuracy": result.overall_accuracy,
        })

        return state

    # ------------------------------------------------------------------
    # LIA-A02 — LLM interpretation for domain execution results
    # ------------------------------------------------------------------

    async def _interpret_if_technical(self, response_text: str, question: str, context: dict) -> str:
        """LIA-A02: Interpret technical/template responses into natural language."""
        # Skip if response is already natural (> 200 chars, has multiple sentences)
        # FIX-5: Skip only if response is clearly natural language (long + conversational)
        if len(response_text) > 500 and response_text.count('.') > 5:
            return response_text

        # Skip known natural patterns
        # FIX-6: Expanded technical patterns for better detection
        _technical_patterns = [
            "encaminhada", "executada", "realizada", "cancelada",
            "Acao ", "Operacao ", "Lista ", "Resultado:",
            "Candidato movido", "Email enviado", "Etapa atualizada",
            "Registro criado", "Registro atualizado", "Registro removido",
            "Vaga criada", "Vaga atualizada", "Agente criado",
            "Processo seletivo", "Pipeline atualizado",
            "total:", "items:", "count:",
            "ID:", "id:", "uuid:",
        ]
        is_technical = any(p in response_text for p in _technical_patterns)
        if not is_technical:
            return response_text

        import os as _os
        if _os.getenv("LIA_AGENTIC_INTERPRET", "true").lower() not in ("true", "1"):
            return response_text

        try:
            from app.domains.ai.services.llm import LLMService
            llm_svc = LLMService()

            prompt = (
                f"O usuario perguntou: {question}\n"
                f"O sistema respondeu: {response_text}\n\n"
                f"Reescreva essa resposta de forma natural, amigavel e informativa. "
                f"Mantenha o conteudo. Seja conciso."
            )

            import asyncio as _asyncio
            # FIX-7: Timeout to prevent slow LLM calls from blocking
            result = await _asyncio.wait_for(
                llm_svc.generate(prompt=prompt, provider="gemini", max_tokens=300),
                timeout=8.0,
            )
            return result.strip() if result else response_text
        except Exception:
            return response_text

    def _build_error_response(self, state: WorkflowState) -> DomainResponse:
        return DomainResponse.error_response(
            error=state.error or "Unknown workflow error",
            message="Desculpe, ocorreu um erro ao processar sua solicitação.",
            metadata={
                "domain_id": state.domain.domain_id,
                "step": state.current_step.value,
                "execution_log": state.execution_log,
            },
        )

    _DOMAIN_TO_AGENT: dict[str, list[str]] = {
        "job_management": ["wizard", "jobs_management"],
        "cv_screening": ["pipeline"],
        "hiring_policy": ["policy"],
        # CR (2026-06-03): chat global federado (vagas+candidatos+pipeline)
        # -- fix "chat cego" (recruiter_copilot tem list_jobs+list_candidates).
        "recruiter_assistant": ["recruiter_copilot"],
        "sourcing": ["sourcing"],
        "communication": ["communication"],
        "analytics": ["analytics"],
        "automation": ["automation"],
        "ats_integration": ["ats_integration"],
        "interview_scheduling": [],
    }

    def _resolve_agent_domain(self, domain_id: str, action_id: str) -> str | None:
        candidates = self._DOMAIN_TO_AGENT.get(domain_id)
        if candidates is None:
            return domain_id

        if not candidates:
            return None

        if len(candidates) == 1:
            return candidates[0]

        if domain_id == "job_management":
            wizard_actions = {
                "create_job", "enrich_job", "salary_analysis", "wsi_questions",
                "publish_job", "draft_jd", "suggest_skills", "wizard_step",
            }
            if action_id in wizard_actions:
                return "wizard"
            return "jobs_management"

        if domain_id == "recruiter_assistant":
            kanban_actions = {
                "kanban_analysis", "pipeline_health", "stale_candidates",
                "move_candidate", "stage_recommendation",
            }
            if action_id in kanban_actions:
                return "kanban"
            return "talent"

        return candidates[0]

    async def _try_react_agent(self, state: WorkflowState) -> DomainResponse | None:
        """Tenta delegar a execução para o ReAct agent do domínio.

        W1-001-B (2026-05-23): Migrado de ReactAgentRegistry legacy para
        AgentRegistry canonical. Padrão alinhado com agent_chat_ws._get_agent
        (Phase A wired). session_id/company_id/user_id agora vão via AgentInput
        (per-call) ao invés do constructor — singleton-ish pattern canonical.

        Resolve o mapeamento entre domain_id (DomainRegistry) e agent_domain
        (AgentRegistry), pois os nomes diferem em vários domínios.

        Retorna DomainResponse se o agente foi acionado com sucesso,
        ou None se o domínio não tem agente registrado (fallback para execute_action).
        """
        try:
            from lia_agents_core.agent_interface import AgentInput

            from app.api.v1.agent_chat_ws import _ensure_agents_loaded
            from app.shared.agents.agent_registry import AgentRegistry

            # Idempotent: garante que @register_agent decorators rodaram
            _ensure_agents_loaded()
            registry = AgentRegistry()

            domain_id = state.domain.domain_id
            action_id = state.intent_result.action_id if state.intent_result else ""

            agent_domain = self._resolve_agent_domain(domain_id, action_id)
            if not agent_domain or not registry.is_registered(agent_domain):
                logger.debug(
                    f"[DomainWorkflow] No ReAct agent for domain_id='{domain_id}' "
                    f"(resolved='{agent_domain}')"
                )
                return None

            agent = registry.get_instance(agent_domain)
            if agent is None:
                logger.debug(
                    f"[DomainWorkflow] AgentRegistry returned None for '{agent_domain}'"
                )
                return None

            agent_input = AgentInput(
                message=state.query,
                context={
                    **state.context.current_data,
                    "domain_id": domain_id,
                    "agent_domain": agent_domain,
                    "action_id": action_id,
                    "extracted_params": state.intent_result.extracted_params if state.intent_result else {},
                },
                session_id=state.context.session_id or "",
                company_id=state.context.tenant_id,
                user_id=state.context.user_id or "",
            )

            output = await agent.process(agent_input)

            return DomainResponse(
                success=not bool(output.error),
                message=output.message,
                data=output.state_updates,
                metadata={
                    "executor": "react_agent",
                    "domain": domain_id,
                    "agent_domain": agent_domain,
                    "confidence": output.confidence,
                    "reasoning_steps": output.reasoning_steps,
                    "tool_results": output.tool_results,
                    **output.metadata,
                },
            )

        except Exception as exc:
            logger.warning(
                f"[DomainWorkflow] ReAct agent delegation failed for domain "
                f"'{state.domain.domain_id}' (falling back to execute_action): {exc}"
            )
            return None

    def __repr__(self) -> str:
        return f"<DomainWorkflow confidence_threshold={self.confidence_threshold}>"
