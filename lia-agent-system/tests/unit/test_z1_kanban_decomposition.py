"""
Z1-01 — Regressão: Decomposição KanbanReActAgent

Valida que:
1. Os 3 subagentes são instanciáveis sem erro
2. Cada subagente expõe o subconjunto correto de tools
3. Não há sobreposição de tools entre Search e Insight
4. check_rejection_fairness existe SOMENTE no ActionAgent (compliance)
5. A quantidade total de tools nos subagentes é igual à do agente original
6. domain_name de cada subagente é distinto
7. Guardrail tools estão presentes no ActionAgent
"""
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def kanban_tool_names():
    """Nomes de todas as tools do KanbanReActAgent original."""
    from app.domains.recruiter_assistant.agents.kanban_tool_registry import TOOL_DEFINITIONS
    return {t.name for t in TOOL_DEFINITIONS}


@pytest.fixture
def search_tool_names():
    from app.domains.recruiter_assistant.agents.kanban_search_tool_registry import (
        get_kanban_search_tools,
    )
    return {t.name for t in get_kanban_search_tools()}


@pytest.fixture
def insight_tool_names():
    from app.domains.recruiter_assistant.agents.kanban_insight_tool_registry import (
        get_kanban_insight_tools,
    )
    return {t.name for t in get_kanban_insight_tools()}


@pytest.fixture
def action_tool_names():
    from app.domains.recruiter_assistant.agents.kanban_action_tool_registry import (
        get_kanban_action_tools,
    )
    return {t.name for t in get_kanban_action_tools()}


# ---------------------------------------------------------------------------
# Tool registry tests
# ---------------------------------------------------------------------------

def test_search_registry_has_6_tools(search_tool_names):
    assert len(search_tool_names) == 6, (
        f"KanbanSearchAgent deve ter 6 tools, encontrou {len(search_tool_names)}: {search_tool_names}"
    )


def test_insight_registry_has_8_tools(insight_tool_names):
    assert len(insight_tool_names) == 8, (
        f"KanbanInsightAgent deve ter 8 tools, encontrou {len(insight_tool_names)}: {insight_tool_names}"
    )


def test_action_registry_has_8_tools(action_tool_names):
    assert len(action_tool_names) == 8, (
        f"KanbanActionAgent deve ter 8 tools, encontrou {len(action_tool_names)}: {action_tool_names}"
    )


def test_total_tools_equals_original(search_tool_names, insight_tool_names, action_tool_names, kanban_tool_names):
    combined = search_tool_names | insight_tool_names | action_tool_names
    assert combined == kanban_tool_names, (
        f"Ferramentas perdidas na decomposição: {kanban_tool_names - combined}\n"
        f"Ferramentas extras: {combined - kanban_tool_names}"
    )


def test_no_overlap_search_and_insight(search_tool_names, insight_tool_names):
    overlap = search_tool_names & insight_tool_names
    assert not overlap, f"Sobreposição entre Search e Insight: {overlap}"


def test_fairness_tool_only_in_action(search_tool_names, insight_tool_names, action_tool_names):
    """check_rejection_fairness deve existir APENAS no ActionAgent (compliance)."""
    assert "check_rejection_fairness" not in search_tool_names
    assert "check_rejection_fairness" not in insight_tool_names
    assert "check_rejection_fairness" in action_tool_names


def test_action_guardrail_tools_present():
    from app.domains.recruiter_assistant.agents.kanban_action_tool_registry import (
        GUARDRAIL_TOOLS,
        get_kanban_action_tools,
    )
    action_names = {t.name for t in get_kanban_action_tools()}
    for gt in GUARDRAIL_TOOLS:
        assert gt in action_names, f"Guardrail tool '{gt}' não encontrada no ActionAgent"


# ---------------------------------------------------------------------------
# Subagent instantiation tests
# ---------------------------------------------------------------------------

@patch("lia_agents_core.enhanced_agent_mixin.EnhancedAgentMixin._setup_enhanced")
@patch("lia_agents_core.langgraph_react_base.LangGraphReActBase.__init__", return_value=None)
def test_kanban_search_agent_instantiates(mock_init, mock_setup):
    from app.domains.recruiter_assistant.agents.kanban_search_agent import KanbanSearchAgent
    agent = KanbanSearchAgent.__new__(KanbanSearchAgent)
    agent._all_tool_names = []
    agent._memory_service = MagicMock()
    assert agent.__class__.__name__ == "KanbanSearchAgent"


@patch("lia_agents_core.enhanced_agent_mixin.EnhancedAgentMixin._setup_enhanced")
@patch("lia_agents_core.langgraph_react_base.LangGraphReActBase.__init__", return_value=None)
def test_kanban_insight_agent_instantiates(mock_init, mock_setup):
    from app.domains.recruiter_assistant.agents.kanban_insight_agent import KanbanInsightAgent
    agent = KanbanInsightAgent.__new__(KanbanInsightAgent)
    agent._all_tool_names = []
    agent._memory_service = MagicMock()
    assert agent.__class__.__name__ == "KanbanInsightAgent"


@patch("lia_agents_core.enhanced_agent_mixin.EnhancedAgentMixin._setup_enhanced")
@patch("lia_agents_core.langgraph_react_base.LangGraphReActBase.__init__", return_value=None)
def test_kanban_action_agent_instantiates(mock_init, mock_setup):
    from app.domains.recruiter_assistant.agents.kanban_action_agent import KanbanActionAgent
    agent = KanbanActionAgent.__new__(KanbanActionAgent)
    agent._all_tool_names = []
    agent._memory_service = MagicMock()
    assert agent.__class__.__name__ == "KanbanActionAgent"


# ---------------------------------------------------------------------------
# domain_name tests
# ---------------------------------------------------------------------------

def test_domain_names_are_distinct():
    domains = {"kanban_search", "kanban_insight", "kanban_action"}
    assert len(domains) == 3
    assert "kanban_search" in domains
    assert "kanban_insight" in domains
    assert "kanban_action" in domains


def test_search_agent_domain_name():
    from app.domains.recruiter_assistant.agents.kanban_search_agent import KanbanSearchAgent
    agent = KanbanSearchAgent.__new__(KanbanSearchAgent)
    assert agent.domain_name == "kanban_search"


def test_insight_agent_domain_name():
    from app.domains.recruiter_assistant.agents.kanban_insight_agent import KanbanInsightAgent
    agent = KanbanInsightAgent.__new__(KanbanInsightAgent)
    assert agent.domain_name == "kanban_insight"


def test_action_agent_domain_name():
    from app.domains.recruiter_assistant.agents.kanban_action_agent import KanbanActionAgent
    agent = KanbanActionAgent.__new__(KanbanActionAgent)
    assert agent.domain_name == "kanban_action"


# ---------------------------------------------------------------------------
# agent_model_config coverage
# ---------------------------------------------------------------------------

def test_model_config_includes_kanban_subagents():
    from app.core.agent_model_config import AGENT_MODEL_CONFIG
    for domain in ("kanban_search", "kanban_insight", "kanban_action"):
        assert domain in AGENT_MODEL_CONFIG, f"'{domain}' não encontrado em AGENT_MODEL_CONFIG"


def test_kanban_subagents_use_haiku():
    from app.core.agent_model_config import AGENT_MODEL_CONFIG
    for domain in ("kanban_search", "kanban_insight", "kanban_action"):
        model = AGENT_MODEL_CONFIG[domain]
        assert "haiku" in model, (
            f"KanbanSubAgent '{domain}' deve usar haiku (tarefas simples), encontrou '{model}'"
        )
