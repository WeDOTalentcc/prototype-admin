"""Funções compartilhadas entre agent_chat_ws.py e agent_chat_sse.py.

Extraído de agent_chat_ws.py para quebrar a dependência oculta
agent_chat_sse.py → agent_chat_ws.py (P0).

Não importar fastapi/websocket aqui — este módulo é agnóstico de transporte.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


def _build_agent_input(
    content: str,
    context: dict[str, Any],
    session_id: str,
    company_id: str,
    user_id: str,
    conversation_history: list,
):
    """Constrói AgentInput a partir dos dados da mensagem WS/SSE."""
    from lia_agents_core.agent_interface import AgentInput
    return AgentInput(
        message=content,
        context=context,
        session_id=session_id,
        company_id=company_id,
        user_id=user_id,
        conversation_history=conversation_history,
    )


def _subagent_for_kanban(message: str) -> str:
    """Z1-01: classifica mensagem kanban → subagente especializado.

    Retorna um de: kanban_action | kanban_insight | kanban_search
    Fail-safe: retorna "kanban" (agente original) se não conseguir classificar.
    """
    msg = message.lower()
    # Action: mutations, batch ops, communications
    _action_kw = (
        "mover", "aprovar", "reprovar", "rejeitar", "lote", "batch",
        "em massa", "triagem em lote", "relatório de pipeline", "prata da casa",
        "silver medalist", "backlog", "benchmark do recrutador", "fairness",
        "check_rejection", "comunicação em massa",
    )
    # Insight: analytics, predictions, bottlenecks
    _insight_kw = (
        "gargalo", "bottleneck", "previsão", "risco", "aging",
        "tempo na etapa", "analisar etapa", "comparar etapa",
        "sugerir movimentação", "journey metric", "predição",
        "identify_bottleneck", "at_risk", "pipeline_prediction",
    )
    if any(kw in msg for kw in _action_kw):
        return "kanban_action"
    if any(kw in msg for kw in _insight_kw):
        return "kanban_insight"
    # Default for kanban: read-only search (safer)
    return "kanban_search"


def _subagent_for_sourcing(message: str) -> str:
    """Z2-02: classifica mensagem sourcing → subagente especializado.

    Retorna um de: sourcing_engagement | sourcing_enrich | sourcing_search | sourcing_planner
    Fail-safe: retorna "sourcing" (agente original) se não conseguir classificar.
    """
    msg = message.lower()
    # Engagement: outreach, mensagem, rastreamento de resposta
    _engagement_kw = (
        "abordagem", "outreach", "enviar mensagem", "mensagem de contato",
        "contatar candidato", "rastrear resposta", "gerar mensagem",
    )
    # Enrich: análise, scoring, shortlist, comparação
    _enrich_kw = (
        "analisar perfil", "score", "shortlist", "comparar candidatos",
        "ranking", "avaliar perfil", "adicionar shortlist", "remover shortlist",
    )
    # Search: busca, filtrar, ver candidato
    _search_kw = (
        "busca de talentos", "talent search", "talent pool", "filtrar candidatos",
        "listar candidatos encontrados", "ver perfil do candidato",
        "boolean search", "busca booleana",
    )
    # Planner: critérios, parâmetros, skills
    _planner_kw = (
        "critérios de busca", "parâmetros de busca", "definir critérios",
        "configurar busca", "sugerir skills", "sugestão de skills",
    )
    if any(kw in msg for kw in _engagement_kw):
        return "sourcing_engagement"
    if any(kw in msg for kw in _enrich_kw):
        return "sourcing_enrich"
    if any(kw in msg for kw in _search_kw):
        return "sourcing_search"
    if any(kw in msg for kw in _planner_kw):
        return "sourcing_planner"
    # Default: search (leitura — mais seguro)
    return "sourcing_search"


def _subagent_for_pipeline(message: str) -> str:
    """Z1-02: classifica mensagem pipeline → subagente especializado.

    Retorna um de: pipeline_action | pipeline_decision | pipeline_context
    Fail-safe: retorna "pipeline_transition" (agente original) se falhar.
    """
    msg = message.lower()
    # Action: field updates, interview management, fairness
    _action_kw = (
        "atualizar candidato", "personalizar comunicação", "cancelar entrevista",
        "reagendar entrevista", "update_candidate", "personalize_communication",
        "fairness", "check_rejection",
    )
    # Decision: transitions, preferences, sub-status
    _decision_kw = (
        "validar transição", "sub-status", "preferências do recrutador",
        "coletar dados", "agendar tarefa secundária", "validate_transition",
        "suggest_sub_status", "recruiter_preference",
    )
    if any(kw in msg for kw in _action_kw):
        return "pipeline_action"
    if any(kw in msg for kw in _decision_kw):
        return "pipeline_decision"
    # Default for pipeline: read-only context (safer)
    return "pipeline_context"


def _get_agent(domain: str) -> Any | None:
    """Retorna instancia do agente para o dominio solicitado.

    Fase 3a (Wave 2): Delegates to AgentRegistry. The 21-branch if/elif
    was replaced — each agent class is decorated with @register_agent(id).
    Fallback to "talent" preserved for unknown domain.
    """
    try:
        # Trigger agent module imports (one-time, idempotent) so decorators run.
        # Each import registers the class in AgentRegistry.
        _ensure_agents_loaded()

        from app.shared.agents.agent_registry import AgentRegistry
        return AgentRegistry().get_or_fallback(domain, fallback_id="talent")
    except Exception as exc:
        logger.error("[ChatShared] Falha ao carregar agente domain=%s: %s", domain, exc)
        return None


_AGENTS_LOADED = False


def _ensure_agents_loaded() -> None:
    """Import all agent modules once to trigger @register_agent decorators.

    Idempotent. Safe to call repeatedly.
    """
    global _AGENTS_LOADED
    if _AGENTS_LOADED:
        return

    try:
        # Top-level ReAct agents
        from app.domains.job_management.agents.wizard_react_agent import WizardReActAgent  # noqa: F401
        from app.domains.cv_screening.agents.pipeline_react_agent import PipelineReActAgent  # noqa: F401
        from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent  # noqa: F401
        from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent  # noqa: F401  # backward-compat shim
        from app.domains.recruiter_assistant.agents.talent_funnel_react_agent import TalentFunnelReActAgent  # noqa: F401
        from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent  # noqa: F401
        from app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent import JobsManagementReActAgent  # noqa: F401
        from app.domains.recruiter_assistant.agents.recruiter_copilot_react_agent import RecruiterCopilotReActAgent  # noqa: F401  # chat global federado
        from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent  # noqa: F401
        from app.domains.pipeline.agents.pipeline_transition_agent import PipelineTransitionAgent  # noqa: F401
        from app.domains.analytics.agents.analytics_react_agent import AnalyticsReActAgent  # noqa: F401
        from app.domains.communication.agents.communication_react_agent import CommunicationReActAgent  # noqa: F401
        from app.domains.ats_integration.agents.ats_integration_react_agent import ATSIntegrationReActAgent  # noqa: F401

        # Sourcing sub-agents (W1-001 cleanup 2026-05-22 — granular)
        from app.domains.sourcing.agents.github_sourcing_agent import GithubSourcingAgent  # noqa: F401
        from app.domains.sourcing.agents.stackoverflow_sourcing_agent import StackOverflowSourcingAgent  # noqa: F401
        from app.domains.sourcing.agents.diversity_sourcing_agent import DiversitySourcingAgent  # noqa: F401
        from app.domains.sourcing.agents.passive_pipeline_agent import PassivePipelineAgent  # noqa: F401
        from app.domains.sourcing.agents.referral_agent import ReferralAgent  # noqa: F401
        from app.domains.sourcing.agents.nurture_sequence_agent import NurtureSequenceAgent  # noqa: F401
        # Sourcing sub-agents
        from app.domains.sourcing.agents.sourcing_planner_agent import SourcingPlannerAgent  # noqa: F401
        from app.domains.sourcing.agents.sourcing_search_agent import SourcingSearchAgent  # noqa: F401
        from app.domains.sourcing.agents.sourcing_enrich_agent import SourcingEnrichAgent  # noqa: F401
        from app.domains.sourcing.agents.sourcing_engagement_agent import SourcingEngagementAgent  # noqa: F401

        # Kanban sub-agents
        from app.domains.recruiter_assistant.agents.kanban_search_agent import KanbanSearchAgent  # noqa: F401
        from app.domains.recruiter_assistant.agents.kanban_insight_agent import KanbanInsightAgent  # noqa: F401
        from app.domains.recruiter_assistant.agents.kanban_action_agent import KanbanActionAgent  # noqa: F401

        # Pipeline sub-agents
        from app.domains.pipeline.agents.pipeline_context_agent import PipelineContextAgent  # noqa: F401
        from app.domains.pipeline.agents.pipeline_decision_agent import PipelineDecisionAgent  # noqa: F401
        from app.domains.pipeline.agents.pipeline_action_agent import PipelineActionAgent  # noqa: F401

        # Standalone domain agents (added 2026-05-20 by Sprint A.1 — Task #28)
        from app.domains.talent_pool.agents.talent_pool_agent import TalentPoolReActAgent  # noqa: F401
        from app.domains.company_settings.agents.company_react_agent import CompanySettingsReActAgent  # noqa: F401
        from app.domains.candidate_self_service.agents.candidate_react_agent import CandidateSelfServiceAgent  # noqa: F401

        _AGENTS_LOADED = True
    except Exception as exc:
        logger.error("[ChatShared] Falha ao carregar modulos de agentes: %s", exc)
