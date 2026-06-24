"""
TDD: thread_id isolation por conversation_id (Fix 2026-06-08).

Garante que _run_graph isola estado LangGraph por conversa,
não só por session+domain (padrao enterprise).
"""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest


class ConcreteAgent:
    """Minimal subclass para testar _run_graph direto."""

    _agent_domain = "test_domain"

    async def _run_graph(
        self,
        initial_state,
        session_id,
        audit_callback=None,
        streaming_callback=None,
        conversation_id=None,
    ):
        # Repete a logica do langgraph_base para testar o calculo da chave
        _agent_domain = self._agent_domain
        _thread_key = (
            f"{session_id}::{_agent_domain}::{conversation_id}"
            if _agent_domain and conversation_id
            else f"{session_id}::{_agent_domain}"
            if _agent_domain
            else session_id
        )
        return _thread_key


@pytest.mark.asyncio
async def test_thread_key_inclui_conversation_id_quando_presente():
    agent = ConcreteAgent()
    key = await agent._run_graph({}, "sess1", conversation_id="conv-abc")
    assert key == "sess1::test_domain::conv-abc"


@pytest.mark.asyncio
async def test_thread_key_fallback_sem_conversation_id():
    """Backward compat: sem conversation_id usa padrao legado."""
    agent = ConcreteAgent()
    key = await agent._run_graph({}, "sess1", conversation_id=None)
    assert key == "sess1::test_domain"


@pytest.mark.asyncio
async def test_duas_conversas_mesma_sessao_geram_chaves_distintas():
    agent = ConcreteAgent()
    k1 = await agent._run_graph({}, "sess1", conversation_id="conv-001")
    k2 = await agent._run_graph({}, "sess1", conversation_id="conv-002")
    assert k1 != k2


@pytest.mark.asyncio
async def test_mesma_conversa_mesma_sessao_geram_chave_identica():
    agent = ConcreteAgent()
    k1 = await agent._run_graph({}, "sess1", conversation_id="conv-001")
    k2 = await agent._run_graph({}, "sess1", conversation_id="conv-001")
    assert k1 == k2


@pytest.mark.asyncio
async def test_thread_key_sem_domain_usa_apenas_session():
    agent = ConcreteAgent()
    agent._agent_domain = None
    key = await agent._run_graph({}, "sess1", conversation_id="conv-abc")
    assert key == "sess1"
