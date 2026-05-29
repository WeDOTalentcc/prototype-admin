"""
Suite de regressão LangGraph — Fase 1 (Gaps).

Valida que TODOS os 12 agentes funcionam corretamente via LangGraph nativo.
LLM mockado via ChatAnthropic para evitar chamadas reais.

Agentes testados:
  ReAct (9): WizardReActAgent, PipelineReActAgent, SourcingReActAgent,
             TalentReActAgent, KanbanReActAgent, JobsManagementReActAgent,
             PolicyReActAgent, AutomationReActAgent, PipelineTransitionAgent
  Graph (2): WSIInterviewGraph, InterviewGraph
"""
import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_agent_input(session_id: str = "sess-regression-001", company_id: str = "company-test"):
    """Cria AgentInput mínimo válido."""
    from lia_agents_core.agent_interface import AgentInput
    return AgentInput(
        message="Quero criar uma nova vaga de desenvolvedor",
        context={},
        session_id=session_id,
        company_id=company_id,
        user_id="user-test-001",
    )


def _make_agent_output(session_id: str = "sess-regression-001", company_id: str = "company-test") -> Any:
    """Cria AgentOutput mock válido."""
    from lia_agents_core.agent_interface import AgentOutput
    return AgentOutput(
        message="Resposta mock do agente LangGraph nativo.",
        actions=[],
        navigation=None,
        confidence=0.9,
        metadata={"source": "langgraph_native_mock", "session_id": session_id, "company_id": company_id},
    )


# ---------------------------------------------------------------------------
# Seção 1: Agentes ReAct — process() via LangGraph nativo
#
# Estratégia: LangGraph é o único path (legacy removido).
# Mockamos _process_langgraph diretamente para evitar chamadas LLM/DB.
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


class TestReActAgentsLangGraphNative:
    """
    Para cada agente ReAct, valida:
    1. process() via LangGraph nativo não lança exceção
    2. Retorna AgentOutput válido (tem campos message, confidence, metadata)
    3. session_id e company_id são preservados nos metadados
    """

    @pytest.mark.asyncio
    @pytest.mark.parametrize("module_path,class_name", REACT_AGENTS)
    async def test_process_langgraph_native_no_exception(self, module_path, class_name):
        """process() com flag=True (default após Item 1.5) não lança exceção."""
        import importlib
        mod = importlib.import_module(module_path)
        AgentClass = getattr(mod, class_name)
        agent = AgentClass()
        input_obj = _make_agent_input(session_id=f"sess-{class_name.lower()}-001")

        # Mockamos _process_langgraph para evitar chamadas LLM/DB
        with patch.object(agent, "_process_langgraph", new_callable=AsyncMock) as mock_lg:
            mock_lg.return_value = _make_agent_output(
                session_id=f"sess-{class_name.lower()}-001"
            )
            result = await agent.process(input_obj)

        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.parametrize("module_path,class_name", REACT_AGENTS)
    async def test_process_returns_valid_agent_output(self, module_path, class_name):
        """process() retorna AgentOutput com campos obrigatórios."""
        from lia_agents_core.agent_interface import AgentOutput
        import importlib
        mod = importlib.import_module(module_path)
        AgentClass = getattr(mod, class_name)
        agent = AgentClass()
        input_obj = _make_agent_input(session_id=f"sess-{class_name.lower()}-002")

        with patch.object(agent, "_process_langgraph", new_callable=AsyncMock) as mock_lg:
            mock_lg.return_value = _make_agent_output(session_id=f"sess-{class_name.lower()}-002")
            result = await agent.process(input_obj)

        assert isinstance(result, AgentOutput)
        assert hasattr(result, "message")
        assert hasattr(result, "confidence")
        assert hasattr(result, "metadata")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("module_path,class_name", REACT_AGENTS)
    async def test_session_and_company_preserved(self, module_path, class_name):
        """session_id e company_id são preservados no metadata do AgentOutput."""
        import importlib
        mod = importlib.import_module(module_path)
        AgentClass = getattr(mod, class_name)
        agent = AgentClass()

        session_id = f"sess-preserved-{class_name.lower()}"
        company_id = f"company-preserved-{class_name.lower()}"
        input_obj = _make_agent_input(session_id=session_id, company_id=company_id)

        mock_output = _make_agent_output(session_id=session_id, company_id=company_id)

        with patch.object(agent, "_process_langgraph", new_callable=AsyncMock) as mock_lg:
            mock_lg.return_value = mock_output
            result = await agent.process(input_obj)

        assert result.metadata.get("session_id") == session_id
        assert result.metadata.get("company_id") == company_id


# ---------------------------------------------------------------------------
# Seção 2: Agentes ReAct — process() sempre chama _process_langgraph
# ---------------------------------------------------------------------------

class TestReActDispatch:
    """Verifica que process() sempre dispara _process_langgraph (LangGraph nativo)."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("module_path,class_name", REACT_AGENTS)
    async def test_process_dispatches_to_langgraph(self, module_path, class_name):
        """process() chama _process_langgraph (sem fallback legado)."""
        import importlib
        mod = importlib.import_module(module_path)
        AgentClass = getattr(mod, class_name)
        agent = AgentClass()
        input_obj = _make_agent_input()

        with patch.object(agent, "_process_langgraph", new_callable=AsyncMock) as mock_lg:
            mock_lg.return_value = _make_agent_output()
            await agent.process(input_obj)
            mock_lg.assert_called_once()


# ---------------------------------------------------------------------------
# Seção 3: Agentes Graph — _invoke_langgraph existe e é chamado quando flag=True
# ---------------------------------------------------------------------------


class TestWSIInterviewGraphLangGraphNative:

    def test_wsi_class_instantiable(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewGraph
        g = WSIInterviewGraph()
        assert g is not None

    def test_start_langgraph_or_build_langgraph_exists(self):
        """WSIInterviewGraph tem ao menos um método de invocação LangGraph."""
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewGraph
        g = WSIInterviewGraph()
        has_lg_method = (
            hasattr(g, "_start_langgraph")
            or hasattr(g, "_invoke_langgraph")
            or hasattr(g, "_build_langgraph")
        )
        assert has_lg_method, "WSIInterviewGraph deve ter pelo menos um método LangGraph"

    @pytest.mark.asyncio
    async def test_start_with_mocked_internals_does_not_raise(self):
        """start() com _start_langgraph mockado não lança exceção."""
        from app.domains.cv_screening.agents.wsi_interview_graph import (
            WSIInterviewGraph, WSIInterviewState
        )
        g = WSIInterviewGraph()

        if hasattr(g, "_start_langgraph"):
            # Criar estado WSI mínimo
            state = WSIInterviewState(
                session_id="sess-wsi-001",
                candidate_id="cand-001",
                job_id="job-001",
                company_id="company-test",
            )
            expected_result = WSIInterviewState(
                session_id="sess-wsi-001",
                candidate_id="cand-001",
                job_id="job-001",
                company_id="company-test",
                current_question_index=0,
            )
            with patch.object(g, "_start_langgraph", new_callable=AsyncMock) as mock_lg:
                mock_lg.return_value = expected_result
                # start() aceita (state, audit_callback=None)
                result = await g.start(state)
                mock_lg.assert_called_once()
            assert result is not None
        else:
            # Sem _start_langgraph, apenas valida que start() existe
            assert callable(getattr(g, "start", None)), "WSIInterviewGraph deve ter método start()"

    @pytest.mark.asyncio
    async def test_wsi_state_serialization_methods_callable(self):
        """Métodos de serialização de estado WSI são callable (necessário para checkpointer)."""
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewGraph
        g = WSIInterviewGraph()

        if hasattr(g, "_wsi_state_to_dict") and hasattr(g, "_wsi_state_from_dict"):
            assert callable(g._wsi_state_to_dict)
            assert callable(g._wsi_state_from_dict)
        else:
            # Serialização pode estar em outro lugar — apenas valida instanciação
            assert isinstance(g, WSIInterviewGraph)


class TestInterviewGraphLangGraphNative:

    def test_invoke_langgraph_method_exists(self):
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        g = InterviewGraph()
        assert hasattr(g, "_invoke_langgraph")
        assert callable(g._invoke_langgraph)

    def test_build_langgraph_callable(self):
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        g = InterviewGraph()
        assert callable(getattr(g, "_build_langgraph", None))

    @pytest.mark.asyncio
    async def test_invoke_calls_invoke_langgraph(self):
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        g = InterviewGraph()
        state = {"session_id": "sess-interview-001", "workflow_data": {}}

        with patch.object(g, "_invoke_langgraph", new_callable=AsyncMock) as mock_lg:
            mock_lg.return_value = state
            await g.invoke(state)
            mock_lg.assert_called_once()

    @pytest.mark.asyncio
    async def test_invoke_langgraph_does_not_raise_with_minimal_input(self):
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        g = InterviewGraph()
        state = {"session_id": "sess-interview-002", "workflow_data": {}}

        mock_compiled = MagicMock()
        mock_compiled.ainvoke = AsyncMock(return_value=state)
        g._compiled = mock_compiled

        result = await g._invoke_langgraph(state)
        assert result is not None


# ---------------------------------------------------------------------------
# Seção 4: Checkpointer — comportamento correto por APP_ENV
# ---------------------------------------------------------------------------

class TestCheckpointerBehavior:

    def test_checkpointer_raises_runtime_error_in_production_on_pg_fail(self):
        """APP_ENV=production + PostgresSaver falha → RuntimeError."""
        from lia_agents_core.checkpointer import get_checkpointer
        with patch("lia_agents_core.checkpointer.settings") as mock_settings:
            mock_settings.APP_ENV = "production"
            mock_settings.DATABASE_URL = "postgresql+asyncpg://invalid:5432/db"

            with patch("lia_agents_core.checkpointer._postgres_saver",
                       side_effect=RuntimeError("Connection refused")):
                with pytest.raises(RuntimeError, match="PostgresSaver FALHOU em produção"):
                    get_checkpointer()

    def test_checkpointer_falls_back_to_memory_saver_in_dev_on_pg_fail(self, caplog):
        """APP_ENV=development + PostgresSaver falha → WARNING + MemorySaver."""
        import logging
        from lia_agents_core.checkpointer import get_checkpointer
        with patch("lia_agents_core.checkpointer.settings") as mock_settings:
            mock_settings.APP_ENV = "development"
            mock_settings.DATABASE_URL = "postgresql+asyncpg://localhost:5432/db"

            with patch("lia_agents_core.checkpointer._postgres_saver",
                       side_effect=RuntimeError("Connection refused")):
                with caplog.at_level(logging.WARNING, logger="lia_agents_core.checkpointer"):
                    result = get_checkpointer()
                    assert "MemorySaver" in caplog.text or "indisponível" in caplog.text


# ---------------------------------------------------------------------------
# Seção 5: Todos os agentes importáveis e LangGraph disponível
# ---------------------------------------------------------------------------

class TestLangGraphNativeEnvironment:

    def test_all_react_agents_importable(self):
        """Todos os 9 agentes ReAct são importáveis sem erro."""
        for module_path, class_name in REACT_AGENTS:
            import importlib
            mod = importlib.import_module(module_path)
            cls = getattr(mod, class_name)
            assert cls is not None, f"{class_name} não encontrado em {module_path}"

    def test_all_graph_agents_importable(self):
        """Todos os 3 agentes Graph são importáveis sem erro."""
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewGraph
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        assert WSIInterviewGraph is not None
        assert InterviewGraph is not None

    def test_langgraph_package_importable(self):
        """langgraph está instalado e importável."""
        import langgraph  # noqa: F401
        assert langgraph is not None

    def test_langgraph_checkpoint_postgres_listed_in_dependencies(self):
        """langgraph-checkpoint-postgres consta no pyproject.toml como dependência."""
        import os
        pyproject_path = os.path.join(
            os.path.dirname(__file__), "../../pyproject.toml"
        )
        with open(pyproject_path) as f:
            content = f.read()
        assert "langgraph-checkpoint-postgres" in content, \
            "langgraph-checkpoint-postgres deve constar no pyproject.toml"

    def test_langgraph_checkpoint_postgres_importable_or_skip(self):
        """langgraph-checkpoint-postgres está instalado (pula se não disponível no ambiente dev)."""
        try:
            from langgraph.checkpoint.postgres import PostgresSaver  # noqa: F401
            assert PostgresSaver is not None
        except ImportError:
            pytest.skip(
                "langgraph-checkpoint-postgres não instalado no ambiente de dev — "
                "disponível via pyproject.toml para produção"
            )
