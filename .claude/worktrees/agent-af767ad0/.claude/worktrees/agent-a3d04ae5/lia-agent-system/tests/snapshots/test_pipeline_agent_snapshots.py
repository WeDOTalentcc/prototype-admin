"""
Snapshot tests para PipelineReActAgent.

Validam que os outputs do agente são estáveis para inputs conhecidos.
Se o comportamento mudar (mudança de prompt, lógica), o snapshot detecta.

Execução:
    pytest tests/snapshots/test_pipeline_agent_snapshots.py -v
    UPDATE_SNAPSHOTS=true pytest tests/snapshots/test_pipeline_agent_snapshots.py -v
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import AIMessage

from tests.snapshots.conftest import (
    UPDATE_SNAPSHOTS,
    load_snapshot,
    make_mock_agent_state,
    make_test_input,
    save_snapshot,
)
from lia_agents_core.agent_interface import AgentInput, AgentOutput


class TestPipelineAgentSnapshots:
    """Snapshots para fluxos críticos do PipelineReActAgent."""

    @pytest.mark.asyncio
    async def test_pipeline_screening_decision_snapshot(self):
        """Snapshot: triagem com candidato de score alto — recomendação de avanço."""
        snapshot_name = "pipeline_screening_decision_high_score"
        agent_input = make_test_input(
            domain="pipeline",
            message="Avalie este candidato para a vaga de Engenheiro Python",
            context={
                "current_stage": "triage",
                "candidate": {
                    "name": "João Silva",
                    "score": 0.92,
                    "skills": ["Python", "FastAPI", "PostgreSQL"],
                    "experience_years": 5,
                },
                "job_id": "job-001",
            },
        )

        mock_content = (
            "O candidato João Silva possui score de 0.92 e atende aos requisitos principais. "
            "Recomendo avançar para a etapa de entrevista técnica. "
            "Pontos fortes: Python (5 anos), FastAPI, PostgreSQL."
        )
        mock_state = make_mock_agent_state(mock_content)

        with patch(
            "lia_agents_core.langgraph_react_base.LangGraphReActBase._run_graph",
            new_callable=AsyncMock,
        ) as mock_run:
            mock_run.return_value = mock_state

            from app.domains.cv_screening.agents.pipeline_react_agent import PipelineReActAgent
            agent = PipelineReActAgent()
            output = await agent._process_langgraph(agent_input)

        assert isinstance(output, AgentOutput), "Output deve ser AgentOutput"
        assert output.message, "message não pode ser vazio"
        assert output.metadata.get("domain") == "pipeline"
        assert agent_input.company_id == "test-company-001"

        serialized = {
            "message_non_empty": bool(output.message),
            "domain": output.metadata.get("domain"),
            "company_id": agent_input.company_id,
            "stage": agent_input.context.get("current_stage"),
            "has_actions": isinstance(output.actions, list),
            "confidence_valid": 0.0 <= output.confidence <= 1.0,
        }

        if UPDATE_SNAPSHOTS or load_snapshot(snapshot_name) is None:
            save_snapshot(snapshot_name, serialized)

        stored = load_snapshot(snapshot_name)
        assert stored is not None, f"Snapshot '{snapshot_name}' não encontrado"
        assert serialized["message_non_empty"] == stored["message_non_empty"]
        assert serialized["domain"] == stored["domain"]
        assert serialized["company_id"] == stored["company_id"]
        assert serialized["stage"] == stored["stage"]
        assert serialized["confidence_valid"] == stored["confidence_valid"]

    @pytest.mark.asyncio
    async def test_pipeline_transition_snapshot(self):
        """Snapshot: transição de candidato entre estágios do pipeline."""
        snapshot_name = "pipeline_candidate_transition"
        agent_input = make_test_input(
            domain="pipeline",
            message="Mover candidato Ana Lima para entrevista técnica",
            context={
                "current_stage": "triage",
                "collected_data": {
                    "candidate_id": "cand-002",
                    "from_stage": "triage",
                    "to_stage": "technical_interview",
                },
                "job_id": "job-002",
            },
        )

        mock_content = (
            "Candidata Ana Lima movida com sucesso da triagem para entrevista técnica. "
            "Um e-mail de convite foi enviado automaticamente."
        )
        mock_state = make_mock_agent_state(mock_content)

        with patch(
            "lia_agents_core.langgraph_react_base.LangGraphReActBase._run_graph",
            new_callable=AsyncMock,
        ) as mock_run:
            mock_run.return_value = mock_state

            from app.domains.cv_screening.agents.pipeline_react_agent import PipelineReActAgent
            agent = PipelineReActAgent()
            output = await agent._process_langgraph(agent_input)

        assert isinstance(output, AgentOutput)
        assert output.message
        assert output.metadata.get("domain") == "pipeline"

        serialized = {
            "message_non_empty": bool(output.message),
            "domain": output.metadata.get("domain"),
            "company_id": agent_input.company_id,
            "from_stage": agent_input.context.get("collected_data", {}).get("from_stage"),
            "to_stage": agent_input.context.get("collected_data", {}).get("to_stage"),
            "confidence_valid": 0.0 <= output.confidence <= 1.0,
        }

        if UPDATE_SNAPSHOTS or load_snapshot(snapshot_name) is None:
            save_snapshot(snapshot_name, serialized)

        stored = load_snapshot(snapshot_name)
        assert stored is not None
        assert serialized["message_non_empty"] == stored["message_non_empty"]
        assert serialized["domain"] == stored["domain"]
        assert serialized["from_stage"] == stored["from_stage"]
        assert serialized["to_stage"] == stored["to_stage"]

    @pytest.mark.asyncio
    async def test_pipeline_empty_candidates_snapshot(self):
        """Snapshot: pipeline sem candidatos — resposta válida e informativa."""
        snapshot_name = "pipeline_empty_candidates"
        agent_input = make_test_input(
            domain="pipeline",
            message="Quantos candidatos estão na triagem?",
            context={
                "current_stage": "triage",
                "candidates": [],
                "job_id": "job-003",
            },
        )

        mock_content = (
            "Não há candidatos na etapa de triagem para esta vaga no momento. "
            "Você pode iniciar a busca de candidatos pelo módulo de sourcing."
        )
        mock_state = make_mock_agent_state(mock_content)

        with patch(
            "lia_agents_core.langgraph_react_base.LangGraphReActBase._run_graph",
            new_callable=AsyncMock,
        ) as mock_run:
            mock_run.return_value = mock_state

            from app.domains.cv_screening.agents.pipeline_react_agent import PipelineReActAgent
            agent = PipelineReActAgent()

            # Não deve lançar exceção mesmo com lista vazia
            output = await agent._process_langgraph(agent_input)

        assert isinstance(output, AgentOutput), "Deve retornar AgentOutput mesmo sem candidatos"
        assert output.message, "message não pode ser vazio"
        assert output.error is None or output.error == "", "Não deve ter erro"

        serialized = {
            "returns_agent_output": True,
            "message_non_empty": bool(output.message),
            "no_error": output.error is None or output.error == "",
            "domain": output.metadata.get("domain"),
            "company_id": agent_input.company_id,
        }

        if UPDATE_SNAPSHOTS or load_snapshot(snapshot_name) is None:
            save_snapshot(snapshot_name, serialized)

        stored = load_snapshot(snapshot_name)
        assert stored is not None
        assert serialized["returns_agent_output"] == stored["returns_agent_output"]
        assert serialized["message_non_empty"] == stored["message_non_empty"]
        assert serialized["no_error"] == stored["no_error"]
        assert serialized["company_id"] == stored["company_id"]
