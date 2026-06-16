"""
Fixtures para snapshot testing de agentes.

Como funciona:
1. Primeira execução: grava resposta real do LLM no arquivo .json
2. Execuções seguintes: compara output atual com snapshot gravado
3. UPDATE_SNAPSHOTS=true: regrava todos os snapshots

Para atualizar snapshots:
    UPDATE_SNAPSHOTS=true pytest tests/snapshots/ -v
"""
import json
import os
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from lia_agents_core.agent_interface import AgentInput, AgentOutput

SNAPSHOT_DIR = Path(__file__).parent / "fixtures"
SNAPSHOT_DIR.mkdir(exist_ok=True)

UPDATE_SNAPSHOTS = os.getenv("UPDATE_SNAPSHOTS", "false").lower() == "true"


def make_test_input(
    domain: str,
    message: str,
    context: dict = None,
    company_id: str = "test-company-001",
) -> AgentInput:
    """Cria AgentInput padronizado para testes de snapshot."""
    return AgentInput(
        message=message,
        context=context or {},
        session_id=f"snapshot-session-{domain}",
        company_id=company_id,
        user_id="snapshot-user-001",
    )


def load_snapshot(name: str) -> dict | None:
    """Carrega snapshot salvo em disco. Retorna None se não existir."""
    path = SNAPSHOT_DIR / f"{name}.json"
    if path.exists():
        return json.loads(path.read_text())
    return None


def save_snapshot(name: str, data: dict) -> None:
    """Grava snapshot em disco."""
    path = SNAPSHOT_DIR / f"{name}.json"
    path.write_text(json.dumps(data, indent=2, default=str))


def make_mock_llm_response(content: str = "Snapshot mock response.") -> MagicMock:
    """Cria mock de resposta LLM para testes de snapshot."""
    from langchain_core.messages import AIMessage

    mock_response = MagicMock(spec=AIMessage)
    mock_response.content = content
    mock_response.tool_calls = []
    mock_response.additional_kwargs = {}
    return mock_response


def make_mock_agent_state(content: str = "Snapshot mock response.") -> dict:
    """Cria mock do estado final do grafo LangGraph para testes de snapshot."""
    from langchain_core.messages import AIMessage

    ai_msg = AIMessage(content=content)
    return {"messages": [ai_msg]}
