"""
Sourcing ReAct Agent - Autonomous agent for candidate search and screening.

Usa LangGraph nativo (create_react_agent) com PostgresSaver para persistência.
Migração completa concluída — path legado ReActLoop removido.
"""
import logging

from lia_agents_core.agent_interface import (
    AgentAction,
    AgentInput,
    AgentOutput,
    NavigationCommand,
)
from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
from lia_agents_core.langgraph_react_base import LangGraphReActBase
from lia_agents_core.working_memory import WorkingMemoryService

from app.domains.sourcing.agents.sourcing_stage_context import (
    STAGE_DEFINITIONS,
    SOURCING_SUBAGENT_STAGE_MAP,
    get_stage_context,
)
from app.domains.sourcing.agents.sourcing_system_prompt import get_sourcing_system_prompt, SOURCING_DOMAIN_SPECIFIC, SOURCING_FEW_SHOT_EXAMPLES, SOURCING_REASONING_PROMPT
from app.domains.sourcing.agents.sourcing_tool_registry import (
    get_sourcing_tools,
)

logger = logging.getLogger(__name__)

_CONFIRMATION_WORDS = {
    "sim", "pode", "vamos", "avanca", "ok", "beleza", "perfeito",
    "vamos la", "proximo", "seguir", "continuar", "ta bom", "pode ser",
    "manda ver", "bora", "certo", "isso", "confirmo", "positivo",
    "buscar", "enviar",
}


def _aggregate_all_tool_names() -> list[str]:
    """
    Agrega nomes de tools de todos os domínios e sub-agentes de sourcing.

    Usado para popular `available_tools` com o conjunto completo de ferramentas,
    garantindo que introspection/observability reflita o que _get_tools() expõe.
    Importa lazy para evitar circular deps no boot.
    """
    try:
        from app.domains.sourcing.tools import get_sourcing_tools
        from app.domains.sourcing.agents.github_tool_registry import get_github_tools
        from app.domains.sourcing.agents.stackoverflow_tool_registry import get_stackoverflow_tools
        from app.domains.sourcing.agents.diversity_tool_registry import get_diversity_tools
        from app.domains.sourcing.agents.passive_pipeline_tool_registry import get_passive_pipeline_tools
        from app.domains.sourcing.agents.referral_tool_registry import get_referral_tools
        from app.domains.sourcing.agents.nurture_sequence_tool_registry import get_nurture_sequence_tools

        all_defs = (
            get_sourcing_tools()
            + get_github_tools()
            + get_stackoverflow_tools()
            + get_diversity_tools()
            + get_passive_pipeline_tools()
            + get_referral_tools()
            + get_nurture_sequence_tools()
        )
        seen: set[str] = set()
        names: list[str] = []
        for td in all_defs:
            if td.name not in seen:
                seen.add(td.name)
                names.append(td.name)
        return names
    except Exception as exc:
        logger.warning("[SourcingReActAgent] _aggregate_all_tool_names fallback: %s", exc)
        try:
            from app.domains.sourcing.tools import get_sourcing_tools
            return [t.name for t in get_sourcing_tools()]
        except Exception:
            return []


from app.shared.agents.agent_registry import register_agent
from app.shared.agents.tenant_aware_agent import TenantAwareAgentMixin
from app.shared.prompts.prompt_composer import PromptComposer

@register_agent("sourcing")
class SourcingReActAgent(TenantAwareAgentMixin, LangGraphReActBase, EnhancedAgentMixin):
    DOMAIN_INSTRUCTIONS = PromptComposer.for_domain(
        agent_type="sourcing",
        domain_specific=SOURCING_DOMAIN_SPECIFIC,
        few_shot_examples=SOURCING_FEW_SHOT_EXAMPLES,
        reasoning_pattern=SOURCING_REASONING_PROMPT.format(memory_summary="", stage_context=""),
    ).text

    def _get_runtime_domain_instructions(self, input: AgentInput) -> str:
        """Sprint 2 Phase 4: substitute {memory_summary} + {stage_context}
        from input.context at runtime (vs empty class-attr default).

        Falls back to legacy DOMAIN_INSTRUCTIONS if PromptComposer fails.
        """
        try:
            ctx = input.context or {}
            return self._compose_runtime_prompt(
                input,
                agent_type="sourcing",
                domain_specific=SOURCING_DOMAIN_SPECIFIC,
            few_shot_examples=SOURCING_FEW_SHOT_EXAMPLES,
                reasoning_template=SOURCING_REASONING_PROMPT,
                memory_summary=ctx.get("memory_summary", ""),
                stage_context=ctx.get("stage_context", ""),
            ).text
        except Exception as exc:
            logger.warning(
                "[sourcing] runtime prompt composition failed: %s — "
                "falling back to static DOMAIN_INSTRUCTIONS",
                exc,
            )
            return self.DOMAIN_INSTRUCTIONS

    """Autonomous agent for talent sourcing and candidate screening via LangGraph nativo."""

    def __init__(self) -> None:
        super().__init__()
        self._memory_service = WorkingMemoryService()
        # Inclui tools de todos os 6 sub-agentes para introspection/observability precisas
        self._all_tool_names = _aggregate_all_tool_names()
        self._setup_enhanced(domain="sourcing")
        logger.info("[SourcingReActAgent] Initialized with %d tools", len(self._all_tool_names))

    @property
    def domain_name(self) -> str:
        return "sourcing"

    @property
    def available_tools(self) -> list[str]:
        return list(self._all_tool_names)


    def _get_tool_contracts(self) -> list:
        """Ativa GovernanceToolNode para este agente."""
        try:
            from app.domains.sourcing.agents.sourcing_tool_registry import get_sourcing_tools
            return get_sourcing_tools()
        except ImportError:
            return []

    def _get_tools(self) -> list:
        """
        Todos os tools do domínio Sourcing + tools dos sub-agentes especializados.

        O SourcingReActAgent é o orquestrador de sourcing. Ele inclui as tools de todos
        os 6 sub-agentes especializados (GitHub, StackOverflow, Diversity,
        PassivePipeline, Referral, NurtureSequence) para que o LangGraph possa
        delegar para a ferramenta correta com base na intenção do usuário.

        As tools de cada sub-agente são expostas diretamente no grafo LangGraph principal,
        permitindo que o LLM selecione a ferramenta correta por intenção sem precisar
        invocar sub-agentes separadamente. SOURCING_SUBAGENT_STAGE_MAP documenta
        a associação domain→stage para referência de stage context (não é roteamento ativo).
        """
        from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool
        from app.domains.sourcing.agents.github_tool_registry import get_github_tools
        from app.domains.sourcing.agents.stackoverflow_tool_registry import get_stackoverflow_tools
        from app.domains.sourcing.agents.diversity_tool_registry import get_diversity_tools
        from app.domains.sourcing.agents.passive_pipeline_tool_registry import get_passive_pipeline_tools
        from app.domains.sourcing.agents.referral_tool_registry import get_referral_tools
        from app.domains.sourcing.agents.nurture_sequence_tool_registry import get_nurture_sequence_tools

        # Ferramentas base do sourcing + enhanced mixin
        from app.domains.recruiter_assistant.agents.ui_tool_registry import get_open_ui_tools
        # Grant UI: open_ui (modais/nav). apply_table_state NAO (surface sem ponte FE ainda).
        tool_defs = get_sourcing_tools() + get_open_ui_tools() + self._get_all_enhanced_tools()

        # Ferramentas dos sub-agentes especializados — expostas diretamente no grafo LangGraph.
        # SOURCING_SUBAGENT_STAGE_MAP documenta a associação domain→stage para referência
        # de stage context, mas o roteamento real é por intenção via tools expostas aqui.
        tool_defs += get_github_tools()           # sourcing_github   → talent-search
        tool_defs += get_stackoverflow_tools()    # sourcing_stackoverflow → talent-search
        tool_defs += get_diversity_tools()        # sourcing_diversity → talent-search
        tool_defs += get_passive_pipeline_tools() # sourcing_passive_pipeline → talent-search
        tool_defs += get_referral_tools()         # sourcing_referral → shortlist-creation
        tool_defs += get_nurture_sequence_tools() # sourcing_nurture_sequence → outreach

        # Deduplicar por nome (base tools têm precedência)
        seen: set[str] = set()
        deduped = []
        for td in tool_defs:
            if td.name not in seen:
                seen.add(td.name)
                deduped.append(td)

        return [tool_definition_to_langchain_tool(td) for td in deduped]

    def _state_to_output(self, state: dict, input: AgentInput) -> AgentOutput:
        messages = state.get("messages", [])
        response = ""
        for m in reversed(messages):
            content = getattr(m, "content", None) or (m.get("content", "") if isinstance(m, dict) else "")
            if content and not getattr(m, "tool_call_id", None) and not (isinstance(m, dict) and m.get("tool_call_id")):
                response = self._extract_text_content(content)
                break
        if not response:
            response = "Desculpe, não consegui processar sua solicitação."

        actions = []
        for m in messages:
            for tc in (getattr(m, "tool_calls", None) or []):
                name = tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", "")
                actions.append(AgentAction(action_type="call_tool", params={"tool": name}))

        current_stage = input.context.get("current_stage", "search-criteria")
        collected_fields = input.context.get("collected_data", {})
        navigation = None
        try:
            stage_def = STAGE_DEFINITIONS.get(current_stage, {})
            next_stage = stage_def.get("next_stage", "")
            if next_stage:
                required = stage_def.get("required_fields", [])
                missing = [f for f in required if collected_fields.get(f) in (None, "", [])]
                if not missing:
                    user_msgs = [
                        (m.content if hasattr(m, "content") else m.get("content", "")).lower()
                        for m in messages
                        if (getattr(m, "type", "") == "human" or (isinstance(m, dict) and m.get("role") == "user"))
                    ]
                    last_user = user_msgs[-1] if user_msgs else ""
                    if any(w in last_user for w in _CONFIRMATION_WORDS):
                        transition_criteria = stage_def.get("transition_criteria", {})
                        reason = transition_criteria.get("description", "Criterios atendidos") if isinstance(transition_criteria, dict) else str(transition_criteria)
                        navigation = NavigationCommand(
                            target_stage=next_stage,
                            reason=reason,
                            auto_navigate=False,
                        )
        except Exception:
            pass

        return AgentOutput(
            message=response,
            actions=actions,
            navigation=navigation,
            confidence=0.85,
            metadata={"source": "langgraph_native", "domain": self.domain_name},
        )

    async def _invoke_langgraph(self, input: AgentInput) -> dict:
        """Invokes the LangGraph compiled graph. Returns raw state dict. Overridable for testing."""
        # Delegate to parent if it has its own _invoke_langgraph, else return empty state
        if hasattr(super(), '_invoke_langgraph'):
            return await super()._invoke_langgraph(input)  # type: ignore[misc]
        return {}

    async def _build_output_from_langgraph(self, state: dict, input: AgentInput) -> AgentOutput:
        """Builds AgentOutput from LangGraph execution state. Overridable for testing."""
        # Default: run full base class processing (which handles state internally)
        return await super()._process_langgraph(input)

    async def _process_langgraph(self, input: AgentInput) -> AgentOutput:
        """Override: adiciona audit SEG-5 após execução LangGraph nativa."""
        state = await self._invoke_langgraph(input)
        output = await self._build_output_from_langgraph(state, input)

        # SEG-5: AuditService
        try:
            from app.shared.compliance.audit_service import PROTECTED_CRITERIA, audit_service
            current_stage = input.context.get("current_stage", "search-criteria")
            await audit_service.log_decision(
                company_id=str(input.company_id or ""),
                agent_name="sourcing_react_agent",
                decision_type="score_candidate",
                action=f"sourcing_langgraph:{current_stage}",
                decision="completed",
                reasoning=[f"Sourcing via LangGraph native no stage {current_stage}"],
                criteria_used=[current_stage],
                criteria_ignored=list(PROTECTED_CRITERIA),
                confidence=output.confidence,
            )
        except Exception as _audit_exc:
            logger.debug("[SourcingReActAgent][SEG-5/LG] AuditService skipped: %s", _audit_exc)

        return output

    async def process(self, input: AgentInput) -> AgentOutput:
        # SEG-2 / FAR-4: FairnessGuard com Layer 3 ativo em sourcing
        _soft_warnings: list = []
        try:
            from app.shared.compliance.fairness_guard import FairnessGuard
            _fg = FairnessGuard()
            try:
                _fg_result = await _fg.check_with_layer3(input.message, action_type="sourcing_search")
            except TypeError:
                _fg_result = _fg.check(input.message)
            if _fg_result.is_blocked:
                logger.warning(
                    "[SourcingReActAgent][SEG-2] FairnessGuard bloqueou mensagem "
                    "session=%s category=%s terms=%s",
                    input.session_id, _fg_result.category, _fg_result.blocked_terms,
                )
                await _fg.log_check(
                    result=_fg_result,
                    context="sourcing",
                    company_id=str(input.company_id or ""),
                )
                return AgentOutput(
                    message=_fg_result.educational_message or (
                        "Esta solicitação não pode ser processada pois contém critérios "
                        "que podem ser discriminatórios. Por favor, reformule com base em "
                        "competências e requisitos técnicos da vaga."
                    ),
                    confidence=1.0,
                    metadata={
                        "fairness_blocked": True,
                        "fairness_category": _fg_result.category,
                        "domain": self.domain_name,
                    },
                )
            _soft_warnings = _fg_result.soft_warnings or []
            if _soft_warnings:
                logger.info(
                    "[SourcingReActAgent][FAR-3] FairnessGuard soft warnings session=%s count=%d",
                    input.session_id, len(_soft_warnings),
                )
                await _fg.log_check(
                    result=_fg_result,
                    context="sourcing",
                    company_id=str(input.company_id or ""),
                )
        except Exception as _fg_exc:
            logger.debug("[SourcingReActAgent] FairnessGuard check skipped: %s", _fg_exc)
            _soft_warnings = []

        # AUD-4: HITL — abordagem (outreach) exige aprovação humana antes de enviar
        _current_stage = input.context.get("current_stage", "")
        _hitl_approved = input.context.get("hitl_approved", False)
        if _current_stage == "outreach" and not _hitl_approved:
            _msg_lower = input.message.strip().lower()
            if any(w in _msg_lower for w in _CONFIRMATION_WORDS):
                try:
                    import app.services.hitl_service as _hitl_svc_mod
                    from app.shared.compliance.audit_service import PROTECTED_CRITERIA, audit_service
                    hitl_service = _hitl_svc_mod.hitl_service
                    thread_id = str(input.session_id)
                    candidate_ids = input.context.get("selected_candidates", [])
                    candidate_count = len(candidate_ids) if candidate_ids else 1
                    pending_id = await hitl_service.request_approval(
                        thread_id=thread_id,
                        action="send_outreach",
                        description=f"Enviar mensagem de abordagem para {candidate_count} candidato(s)",
                        data={
                            "stage": _current_stage,
                            "candidate_count": candidate_count,
                            "candidate_ids": candidate_ids,
                            "job_id": input.context.get("job_id", ""),
                        },
                        ws_session_id=thread_id,
                        domain="sourcing",
                        company_id=str(input.company_id or ""),
                    )
                    await hitl_service.store_resume_info(
                        thread_id=thread_id,
                        domain="sourcing",
                        session_id=thread_id,
                        agent_input_dict={
                            "message": input.message,
                            "context": {**input.context, "hitl_approved": True, "hitl_pending_id": pending_id},
                            "session_id": str(input.session_id),
                            "company_id": str(input.company_id or ""),
                            "user_id": str(input.user_id or ""),
                            "conversation_history": input.conversation_history or [],
                        },
                        hitl_context="sourcing_outreach",
                    )
                    try:
                        await audit_service.log_decision(
                            company_id=str(input.company_id or ""),
                            agent_name="sourcing_react_agent",
                            decision_type="send_outreach",
                            action="hitl_requested:send_outreach",
                            decision="pending_review",
                            reasoning=["Envio de abordagem requer aprovação HITL (LGPD)"],
                            criteria_used=["outreach_confirmation"],
                            human_review_required=True,
                            criteria_ignored=list(PROTECTED_CRITERIA),
                        )
                    except Exception as _ae:
                        logger.debug("[SourcingReActAgent][AUD-4] AuditService skipped: %s", _ae)
                    logger.info("[SourcingReActAgent][AUD-4] HITL solicitado session=%s", input.session_id)
                    return AgentOutput(
                        message=(
                            "Aguardando aprovação para enviar mensagens de abordagem. "
                            "Um recrutador precisa confirmar antes do envio."
                        ),
                        confidence=1.0,
                        metadata={
                            "hitl_pending": True,
                            "hitl_pending_id": pending_id,
                            "thread_id": thread_id,
                            "domain": self.domain_name,
                        },
                    )
                except Exception as _hitl_exc:
                    logger.warning("[SourcingReActAgent][AUD-4] HITL check failed (fail-open): %s", _hitl_exc)

        _output = await self._process_langgraph(input)

        # FAR-3: propagar soft_warnings ao output
        if _soft_warnings:
            if _output.metadata is None:
                _output.metadata = {}
            _output.metadata.setdefault("fairness_warnings", _soft_warnings)

        return _output

    async def get_status(self) -> dict:
        return {
            "domain": self.domain_name,
            "available_tools": self.available_tools,
            "status": "ready",
            "stages": list(STAGE_DEFINITIONS.keys()),
            "max_iterations": 5,
            "model_provider": "claude",
        }
