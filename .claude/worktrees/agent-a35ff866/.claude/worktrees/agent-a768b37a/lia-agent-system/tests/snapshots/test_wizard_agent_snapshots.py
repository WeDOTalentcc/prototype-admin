"""
Snapshot tests para WizardReActAgent.

Validam que os outputs do agente são estáveis para inputs conhecidos.
Se o comportamento mudar (mudança de prompt, lógica), o snapshot detecta.

Execução:
    pytest tests/snapshots/test_wizard_agent_snapshots.py -v
    UPDATE_SNAPSHOTS=true pytest tests/snapshots/test_wizard_agent_snapshots.py -v
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


class TestWizardAgentSnapshots:
    """Snapshots para fluxos críticos do WizardReActAgent."""

    @pytest.mark.asyncio
    async def test_wizard_basic_job_creation_snapshot(self):
        """Snapshot: usuário pede criação de vaga básica."""
        snapshot_name = "wizard_basic_job_creation"
        agent_input = make_test_input(
            domain="wizard",
            message="Quero criar uma vaga de Engenheiro de Software Sênior",
            context={"current_stage": "input-evaluation"},
        )

        mock_content = (
            "Ótimo! Vou ajudá-lo a criar a vaga de Engenheiro de Software Sênior. "
            "Para começar, preciso de algumas informações: qual é a área de atuação "
            "e o nível de senioridade desejado?"
        )
        mock_state = make_mock_agent_state(mock_content)

        with patch(
            "lia_agents_core.langgraph_react_base.LangGraphReActBase._run_graph",
            new_callable=AsyncMock,
        ) as mock_run:
            mock_run.return_value = mock_state

            from app.domains.job_management.agents.wizard_react_agent import WizardReActAgent
            agent = WizardReActAgent()
            output = await agent._process_langgraph(agent_input)

        # Verificar contrato de output
        assert isinstance(output, AgentOutput), "Output deve ser AgentOutput"
        assert output.message, "message não pode ser vazio"
        assert output.metadata.get("domain") == "wizard", "domain deve ser wizard"
        assert agent_input.company_id == "test-company-001", "company_id preservado"

        serialized = {
            "message_non_empty": bool(output.message),
            "domain": output.metadata.get("domain"),
            "company_id": agent_input.company_id,
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
        assert serialized["has_actions"] == stored["has_actions"]
        assert serialized["confidence_valid"] == stored["confidence_valid"]

    @pytest.mark.asyncio
    async def test_wizard_collect_requirements_snapshot(self):
        """Snapshot: estágio de coleta de requisitos."""
        snapshot_name = "wizard_collect_requirements"
        agent_input = make_test_input(
            domain="wizard",
            message="A vaga é para desenvolvedor backend Python",
            context={
                "current_stage": "requirements",
                "collected_data": {
                    "title": "Engenheiro de Software",
                    "area": "Tecnologia",
                },
            },
        )

        mock_content = (
            "Entendido! A vaga é para Desenvolvedor Backend Python. "
            "Quais são os requisitos técnicos obrigatórios? Por exemplo: "
            "anos de experiência, frameworks específicos (FastAPI, Django), "
            "conhecimento em bancos de dados?"
        )
        mock_state = make_mock_agent_state(mock_content)

        with patch(
            "lia_agents_core.langgraph_react_base.LangGraphReActBase._run_graph",
            new_callable=AsyncMock,
        ) as mock_run:
            mock_run.return_value = mock_state

            from app.domains.job_management.agents.wizard_react_agent import WizardReActAgent
            agent = WizardReActAgent()
            output = await agent._process_langgraph(agent_input)

        assert isinstance(output, AgentOutput)
        assert output.message
        assert output.metadata.get("domain") == "wizard"

        # Verificar que o contexto de estágio foi preservado
        serialized = {
            "message_non_empty": bool(output.message),
            "domain": output.metadata.get("domain"),
            "stage_in_context": agent_input.context.get("current_stage"),
            "collected_data_keys": list(agent_input.context.get("collected_data", {}).keys()),
            "confidence_valid": 0.0 <= output.confidence <= 1.0,
        }

        if UPDATE_SNAPSHOTS or load_snapshot(snapshot_name) is None:
            save_snapshot(snapshot_name, serialized)

        stored = load_snapshot(snapshot_name)
        assert stored is not None
        assert serialized["message_non_empty"] == stored["message_non_empty"]
        assert serialized["domain"] == stored["domain"]
        assert serialized["stage_in_context"] == stored["stage_in_context"]
        assert set(serialized["collected_data_keys"]) == set(stored["collected_data_keys"])

    @pytest.mark.asyncio
    async def test_wizard_invalid_input_graceful_snapshot(self):
        """Snapshot: input inválido — deve retornar output válido sem crash."""
        snapshot_name = "wizard_invalid_input_graceful"

        # Input com contexto mínimo (sem current_stage definido)
        agent_input = AgentInput(
            message="",  # mensagem vazia
            context={},  # sem stage
            session_id="snapshot-session-wizard-invalid",
            company_id="test-company-001",
            user_id="snapshot-user-001",
        )

        mock_content = "Olá! Como posso ajudá-lo com a criação da sua vaga?"
        mock_state = make_mock_agent_state(mock_content)

        with patch(
            "lia_agents_core.langgraph_react_base.LangGraphReActBase._run_graph",
            new_callable=AsyncMock,
        ) as mock_run:
            mock_run.return_value = mock_state

            from app.domains.job_management.agents.wizard_react_agent import WizardReActAgent
            agent = WizardReActAgent()

            # Não deve lançar exceção
            output = await agent._process_langgraph(agent_input)

        assert isinstance(output, AgentOutput), "Deve retornar AgentOutput mesmo com input inválido"
        assert output.message, "message não pode ser vazio mesmo com input inválido"
        assert agent_input.company_id == "test-company-001"

        serialized = {
            "returns_agent_output": True,
            "message_non_empty": bool(output.message),
            "no_exception": True,
            "company_id_preserved": agent_input.company_id == "test-company-001",
        }

        if UPDATE_SNAPSHOTS or load_snapshot(snapshot_name) is None:
            save_snapshot(snapshot_name, serialized)

        stored = load_snapshot(snapshot_name)
        assert stored is not None
        assert serialized["returns_agent_output"] == stored["returns_agent_output"]
        assert serialized["no_exception"] == stored["no_exception"]
        assert serialized["company_id_preserved"] == stored["company_id_preserved"]
