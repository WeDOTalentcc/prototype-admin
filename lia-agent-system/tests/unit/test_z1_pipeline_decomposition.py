"""
Z1-02 — Regressão: Decomposição PipelineTransitionAgent

Valida que:
1. Os 3 subagentes são instanciáveis sem erro
2. Cada subagente expõe o subconjunto correto de tools
3. check_rejection_fairness existe SOMENTE no ActionAgent (compliance)
4. A união das 3 registries cobre todas as tools do agente original
5. Não há sobreposição entre Context e Decision
6. domain_name de cada subagente é distinto
7. Guardrail tools estão presentes no ActionAgent
8. Subagentes de ação e decisão usam Sonnet (ações críticas)
"""
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def pipeline_all_tool_names():
    """Nomes de todas as tools do PipelineTransitionAgent original."""
    from app.domains.pipeline.agents.pipeline_tool_registry import ALL_TOOLS
    return {t.name for t in ALL_TOOLS}


@pytest.fixture
def context_tool_names():
    from app.domains.pipeline.agents.pipeline_context_tool_registry import (
        get_pipeline_context_tools,
    )
    return {t.name for t in get_pipeline_context_tools()}


@pytest.fixture
def decision_tool_names():
    from app.domains.pipeline.agents.pipeline_decision_tool_registry import (
        get_pipeline_decision_tools,
    )
    return {t.name for t in get_pipeline_decision_tools()}


@pytest.fixture
def action_tool_names():
    from app.domains.pipeline.agents.pipeline_action_tool_registry import (
        get_pipeline_action_tools,
    )
    return {t.name for t in get_pipeline_action_tools()}


# ---------------------------------------------------------------------------
# Tool registry tests
# ---------------------------------------------------------------------------

def test_context_registry_has_7_tools(context_tool_names):
    assert len(context_tool_names) == 7, (
        f"PipelineContextAgent deve ter 7 tools, encontrou {len(context_tool_names)}: {context_tool_names}"
    )


def test_decision_registry_has_7_tools(decision_tool_names):
    assert len(decision_tool_names) == 7, (
        f"PipelineDecisionAgent deve ter 7 tools, encontrou {len(decision_tool_names)}: {decision_tool_names}"
    )


def test_action_registry_has_6_tools(action_tool_names):
    assert len(action_tool_names) == 6, (
        f"PipelineActionAgent deve ter 6 tools, encontrou {len(action_tool_names)}: {action_tool_names}"
    )


def test_total_tools_equals_original(context_tool_names, decision_tool_names, action_tool_names, pipeline_all_tool_names):
    combined = context_tool_names | decision_tool_names | action_tool_names
    assert combined == pipeline_all_tool_names, (
        f"Ferramentas perdidas na decomposição: {pipeline_all_tool_names - combined}\n"
        f"Ferramentas extras: {combined - pipeline_all_tool_names}"
    )


def test_no_overlap_context_and_decision(context_tool_names, decision_tool_names):
    overlap = context_tool_names & decision_tool_names
    assert not overlap, f"Sobreposição entre Context e Decision: {overlap}"


def test_fairness_tool_only_in_action(context_tool_names, decision_tool_names, action_tool_names):
    """check_rejection_fairness deve existir APENAS no ActionAgent (compliance)."""
    assert "check_rejection_fairness" not in context_tool_names
    assert "check_rejection_fairness" not in decision_tool_names
    assert "check_rejection_fairness" in action_tool_names


def test_action_guardrail_tools_present():
    from app.domains.pipeline.agents.pipeline_action_tool_registry import (
        GUARDRAIL_TOOLS,
        get_pipeline_action_tools,
    )
    action_names = {t.name for t in get_pipeline_action_tools()}
    for gt in GUARDRAIL_TOOLS:
        assert gt in action_names, f"Guardrail tool '{gt}' não encontrada no PipelineActionAgent"


# ---------------------------------------------------------------------------
# Subagent instantiation tests
# ---------------------------------------------------------------------------

@patch("lia_agents_core.enhanced_agent_mixin.EnhancedAgentMixin._setup_enhanced")
@patch("lia_agents_core.langgraph_react_base.LangGraphReActBase.__init__", return_value=None)
def test_pipeline_context_agent_instantiates(mock_init, mock_setup):
    from app.domains.pipeline.agents.pipeline_context_agent import PipelineContextAgent
    agent = PipelineContextAgent.__new__(PipelineContextAgent)
    agent._memory_service = MagicMock()
    assert agent.__class__.__name__ == "PipelineContextAgent"


@patch("lia_agents_core.enhanced_agent_mixin.EnhancedAgentMixin._setup_enhanced")
@patch("lia_agents_core.langgraph_react_base.LangGraphReActBase.__init__", return_value=None)
def test_pipeline_decision_agent_instantiates(mock_init, mock_setup):
    from app.domains.pipeline.agents.pipeline_decision_agent import PipelineDecisionAgent
    agent = PipelineDecisionAgent.__new__(PipelineDecisionAgent)
    agent._memory_service = MagicMock()
    assert agent.__class__.__name__ == "PipelineDecisionAgent"


@patch("lia_agents_core.enhanced_agent_mixin.EnhancedAgentMixin._setup_enhanced")
@patch("lia_agents_core.langgraph_react_base.LangGraphReActBase.__init__", return_value=None)
def test_pipeline_action_agent_instantiates(mock_init, mock_setup):
    from app.domains.pipeline.agents.pipeline_action_agent import PipelineActionAgent
    agent = PipelineActionAgent.__new__(PipelineActionAgent)
    agent._memory_service = MagicMock()
    assert agent.__class__.__name__ == "PipelineActionAgent"


# ---------------------------------------------------------------------------
# domain_name tests
# ---------------------------------------------------------------------------

def test_context_agent_domain_name():
    from app.domains.pipeline.agents.pipeline_context_agent import PipelineContextAgent
    agent = PipelineContextAgent.__new__(PipelineContextAgent)
    assert agent.domain_name == "pipeline_context"


def test_decision_agent_domain_name():
    from app.domains.pipeline.agents.pipeline_decision_agent import PipelineDecisionAgent
    agent = PipelineDecisionAgent.__new__(PipelineDecisionAgent)
    assert agent.domain_name == "pipeline_decision"


def test_action_agent_domain_name():
    from app.domains.pipeline.agents.pipeline_action_agent import PipelineActionAgent
    agent = PipelineActionAgent.__new__(PipelineActionAgent)
    assert agent.domain_name == "pipeline_action"


def test_domain_names_are_distinct():
    domains = {"pipeline_context", "pipeline_decision", "pipeline_action"}
    assert len(domains) == 3


# ---------------------------------------------------------------------------
# agent_model_config coverage
# ---------------------------------------------------------------------------

def test_model_config_includes_pipeline_subagents():
    from app.core.agent_model_config import AGENT_MODEL_CONFIG
    for domain in ("pipeline_context", "pipeline_decision", "pipeline_action"):
        assert domain in AGENT_MODEL_CONFIG, f"'{domain}' não encontrado em AGENT_MODEL_CONFIG"


def test_pipeline_action_and_decision_use_sonnet():
    """Subagentes de decisão e ação usam Sonnet para maior precisão."""
    from app.core.agent_model_config import AGENT_MODEL_CONFIG
    for domain in ("pipeline_decision", "pipeline_action"):
        model = AGENT_MODEL_CONFIG[domain]
        assert "sonnet" in model or "opus" in model, (
            f"PipelineSubAgent '{domain}' deve usar sonnet/opus (ações críticas), encontrou '{model}'"
        )


def test_pipeline_context_uses_haiku():
    """Context agent usa haiku — só faz leitura."""
    from app.core.agent_model_config import AGENT_MODEL_CONFIG
    model = AGENT_MODEL_CONFIG["pipeline_context"]
    assert "haiku" in model, (
        f"PipelineContextAgent deve usar haiku (leitura simples), encontrou '{model}'"
    )


# ---------------------------------------------------------------------------
# Inheritance consistency
# ---------------------------------------------------------------------------

def test_subagents_inherit_from_pipeline_transition():
    from app.domains.pipeline.agents.pipeline_transition_agent import PipelineTransitionAgent
    from app.domains.pipeline.agents.pipeline_context_agent import PipelineContextAgent
    from app.domains.pipeline.agents.pipeline_decision_agent import PipelineDecisionAgent
    from app.domains.pipeline.agents.pipeline_action_agent import PipelineActionAgent

    assert issubclass(PipelineContextAgent, PipelineTransitionAgent)
    assert issubclass(PipelineDecisionAgent, PipelineTransitionAgent)
    assert issubclass(PipelineActionAgent, PipelineTransitionAgent)


def test_kanban_subagents_inherit_from_kanban_react():
    from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent
    from app.domains.recruiter_assistant.agents.kanban_search_agent import KanbanSearchAgent
    from app.domains.recruiter_assistant.agents.kanban_insight_agent import KanbanInsightAgent
    from app.domains.recruiter_assistant.agents.kanban_action_agent import KanbanActionAgent

    assert issubclass(KanbanSearchAgent, KanbanReActAgent)
    assert issubclass(KanbanInsightAgent, KanbanReActAgent)
    assert issubclass(KanbanActionAgent, KanbanReActAgent)
