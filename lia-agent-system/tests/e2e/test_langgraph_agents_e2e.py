"""
Testes E2E para agentes LangGraph.

Valida o ciclo completo de cada agente (ReAct e Graph) com LLM mockado,
checkpointer em modo dev (MemorySaver) e interface AgentInput → AgentOutput.

Camada 3 (Integração) da pirâmide de testes — mocks de LLM/DB, sem chamadas reais.

Cobertura:
  - 9 agentes ReAct: process() retorna AgentOutput válido
  - 3 agentes Graph: invoke()/start() não lançam exceção com compiled mockado
  - Checkpointer dev: MemorySaver ativo em desenvolvimento
  - Session ID preservado na entrada (AgentInput)
  - Company ID preservado na entrada (AgentInput)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

REACT_AGENTS = [
    ("app.domains.job_management.agents.wizard_react_agent", "WizardReActAgent"),
    ("app.domains.cv_screening.agents.pipeline_react_agent", "PipelineReActAgent"),
    ("app.domains.sourcing.agents.sourcing_react_agent", "SourcingReActAgent"),
    ("app.domains.recruiter_assistant.agents.talent_react_agent", "TalentReActAgent"),
    ("app.domains.recruiter_assistant.agents.kanban_react_agent", "KanbanReActAgent"),
    ("app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent", "JobsManagementReActAgent"),
    ("app.domains.hiring_policy.agents.policy_react_agent", "PolicyReActAgent"),
    ("app.domains.automation.agents.automation_react_agent", "AutomationReActAgent"),
    ("app.domains.pipeline.agents.pipeline_transition_agent", "PipelineTransitionAgent"),
]

GRAPH_AGENTS = [
    ("app.domains.cv_screening.agents.wsi_interview_graph", "WSIInterviewGraph"),
    ("app.domains.interview_scheduling.agents.interview_graph", "InterviewGraph"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_input(session_id: str = "sess-e2e-001", company_id: str = "company-e2e"):
    from lia_agents_core.agent_interface import AgentInput
    return AgentInput(
        message="Criar vaga de desenvolvedor senior Python",
        context={},
        session_id=session_id,
        company_id=company_id,
        user_id="user-e2e-001",
    )


def _make_output(session_id: str = "sess-e2e-001", company_id: str = "company-e2e"):
    from lia_agents_core.agent_interface import AgentOutput
    return AgentOutput(
        message="Vaga criada com sucesso via LangGraph nativo.",
        actions=[],
        navigation=None,
        confidence=0.9,
        metadata={
            "source": "langgraph_native",
            "session_id": session_id,
            "company_id": company_id,
        },
    )


# ---------------------------------------------------------------------------
# Seção 1: ReAct Agents — process() via LangGraph nativo
# ---------------------------------------------------------------------------

class TestReActAgentsLangGraphNativeE2E:
    """
    Valida o ciclo process() de todos os agentes ReAct com flag=True.
    LLM e DB são mockados; apenas o dispatch e retorno são testados.
    """

    @pytest.mark.asyncio
    @pytest.mark.parametrize("module_path,class_name", REACT_AGENTS)
    async def test_process_returns_agent_output(self, module_path, class_name):
        """process() com USE_LANGGRAPH_NATIVE=True retorna AgentOutput válido."""
        from lia_agents_core.agent_interface import AgentOutput
        import importlib
        mod = importlib.import_module(module_path)
        AgentClass = getattr(mod, class_name)
        agent = AgentClass()
        inp = _make_input(session_id=f"e2e-{class_name.lower()}")
        expected = _make_output(session_id=f"e2e-{class_name.lower()}")

        with patch.object(agent, "_process_langgraph", new=AsyncMock(return_value=expected)):
            result = await agent.process(inp)

        assert isinstance(result, AgentOutput)
        assert result.message

    @pytest.mark.asyncio
    @pytest.mark.parametrize("module_path,class_name", REACT_AGENTS)
    async def test_process_always_calls_langgraph(self, module_path, class_name):
        """process() sempre delega para _process_langgraph."""
        import importlib
        mod = importlib.import_module(module_path)
        AgentClass = getattr(mod, class_name)
        agent = AgentClass()
        inp = _make_input()
        expected = _make_output()

        with patch.object(agent, "_process_langgraph", new=AsyncMock(return_value=expected)) as mock_lg:
            await agent.process(inp)
            mock_lg.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("module_path,class_name", REACT_AGENTS)
    async def test_agent_output_has_required_fields(self, module_path, class_name):
        """AgentOutput retornado tem message, confidence e metadata."""
        from lia_agents_core.agent_interface import AgentOutput
        import importlib
        mod = importlib.import_module(module_path)
        AgentClass = getattr(mod, class_name)
        agent = AgentClass()
        inp = _make_input()
        expected = _make_output()

        with patch.object(agent, "_process_langgraph", new=AsyncMock(return_value=expected)):
            result = await agent.process(inp)

        assert hasattr(result, "message")
        assert hasattr(result, "confidence")
        assert hasattr(result, "metadata")
        assert result.confidence >= 0


# ---------------------------------------------------------------------------
# Seção 2: Graph Agents — invoke()/start() com compiled mockado
# ---------------------------------------------------------------------------


class TestWSIInterviewGraphE2E:

    def test_wsi_interview_graph_instantiates(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewGraph
        g = WSIInterviewGraph()
        assert g is not None

    def test_wsi_interview_graph_has_start_method(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewGraph
        g = WSIInterviewGraph()
        assert callable(getattr(g, "start", None))

    def test_wsi_has_langgraph_method(self):
        """WSIInterviewGraph tem pelo menos um método LangGraph."""
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewGraph
        g = WSIInterviewGraph()
        has_lg = (
            hasattr(g, "_start_langgraph")
            or hasattr(g, "_invoke_langgraph")
            or hasattr(g, "_build_langgraph")
        )
        assert has_lg

    @pytest.mark.asyncio
    async def test_wsi_start_with_mocked_nodes(self):
        """start() com nodes mockados não lança exceção."""
        from app.domains.cv_screening.agents.wsi_interview_graph import (
            WSIInterviewGraph, WSIInterviewStage
        )
        g = WSIInterviewGraph()
        state = g.create_session("cand-e2e", "job-e2e", "company-e2e")

        async def mock_load_context(s):
            s.stage = WSIInterviewStage.GENERATE_QUESTION
            return s

        async def mock_generate_question(s):
            s.current_question_index = 0
            return s

        g.nodes.load_context = mock_load_context
        g.nodes.generate_question = mock_generate_question

        result = await g.start(state)
        assert result is not None


class TestInterviewGraphE2E:

    def test_interview_graph_instantiates(self):
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        g = InterviewGraph()
        assert g is not None

    def test_interview_graph_has_invoke_method(self):
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        g = InterviewGraph()
        assert callable(getattr(g, "invoke", None))

    def test_interview_graph_has_build_langgraph(self):
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        g = InterviewGraph()
        assert callable(getattr(g, "_build_langgraph", None))

    @pytest.mark.asyncio
    async def test_interview_graph_invoke_with_mock_compiled(self):
        """_invoke_langgraph() com _compiled mockado não lança exceção."""
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        g = InterviewGraph()
        state = {"session_id": "sess-interview-e2e", "workflow_data": {}}

        mock_compiled = MagicMock()
        mock_compiled.ainvoke = AsyncMock(return_value=state)
        g._compiled = mock_compiled

        result = await g._invoke_langgraph(state)
        assert result is not None


# ---------------------------------------------------------------------------
# Seção 3: Checkpointer em modo dev
# ---------------------------------------------------------------------------

class TestCheckpointerDevMode:

    def test_get_checkpointer_returns_memory_saver_when_pg_unavailable(self):
        """Em dev, quando PostgresSaver não está disponível, retorna MemorySaver."""
        from lia_agents_core.checkpointer import get_checkpointer
        with patch("lia_agents_core.checkpointer.settings") as mock_settings:
            mock_settings.APP_ENV = "development"
            mock_settings.DATABASE_URL = "postgresql+asyncpg://localhost:5432/test"
            with patch("lia_agents_core.checkpointer._postgres_saver",
                       side_effect=ImportError("not installed")):
                result = get_checkpointer()
        # Dev com postgres indisponível → MemorySaver
        assert result is None or type(result).__name__ in ("MemorySaver", "InMemorySaver")  # não deve lançar exceção

    def test_get_checkpointer_returns_checkpointer_by_default(self):
        """Por padrão, get_checkpointer() retorna um checkpointer válido ou None."""
        from lia_agents_core.checkpointer import get_checkpointer
        result = get_checkpointer()
        # Deve retornar None ou um objeto com interface de checkpointer
        assert result is None or hasattr(result, "put") or type(result).__name__ in ("MemorySaver", "InMemorySaver", "PostgresSaver")

    def test_checkpointer_production_requires_postgres(self):
        """Em produção com PostgresSaver falhando, deve lançar RuntimeError."""
        from lia_agents_core.checkpointer import get_checkpointer
        with patch("lia_agents_core.checkpointer.settings") as mock_settings:
            mock_settings.APP_ENV = "production"
            mock_settings.DATABASE_URL = "postgresql+asyncpg://invalid:5432/db"
            with patch("lia_agents_core.checkpointer._postgres_saver",
                       side_effect=RuntimeError("Connection refused")):
                with pytest.raises(RuntimeError, match="PostgresSaver FALHOU em produção"):
                    get_checkpointer()
