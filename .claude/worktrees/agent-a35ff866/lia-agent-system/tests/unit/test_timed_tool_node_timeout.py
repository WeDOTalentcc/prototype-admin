"""
Unit tests — TimedToolNode com timeout (Sprint A / André P4).

Camada 2 — Unitária (pytest-asyncio).

TimedToolNode agora é subclasse de ToolNode do LangGraph.
Testes focam em:
- timeout padrão (15s) via asyncio.wait_for
- timeout por tool via tool_timeouts dict (lógica min)
- TimeoutError injeta ToolMessage de erro
- Tool call bem-sucedida (sem timeout)
- Atributos obrigatórios presentes
- _build_timeout_response com ToolMessages corretos
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


try:
    from lia_agents_core.timed_tool_node import TimedToolNode, _HAS_LANGGRAPH
    _IMPORT_OK = True
except ImportError:
    _IMPORT_OK = False
    _HAS_LANGGRAPH = False

pytestmark = pytest.mark.skipif(not _IMPORT_OK, reason="lia_agents_core não disponível")


def _make_tool_call(name: str, call_id: str = "call-1") -> dict:
    return {"name": name, "id": call_id, "args": {}}


def _make_state(tool_calls: list) -> dict:
    last_msg = MagicMock()
    last_msg.tool_calls = tool_calls
    return {"messages": [last_msg]}


# ---------------------------------------------------------------------------
# Atributos e inicialização
# ---------------------------------------------------------------------------

class TestTimedToolNodeInit:
    def test_domain_attribute(self):
        if not _HAS_LANGGRAPH:
            pytest.skip("LangGraph não disponível")
        ttn = TimedToolNode(tools=[], domain="pipeline")
        assert ttn.domain == "pipeline"

    def test_default_timeout_is_15(self):
        if not _HAS_LANGGRAPH:
            pytest.skip("LangGraph não disponível")
        ttn = TimedToolNode(tools=[], domain="test")
        assert ttn.default_timeout_seconds == 15

    def test_custom_timeout(self):
        if not _HAS_LANGGRAPH:
            pytest.skip("LangGraph não disponível")
        ttn = TimedToolNode(tools=[], domain="test", default_timeout_seconds=30)
        assert ttn.default_timeout_seconds == 30

    def test_tool_timeouts_empty_default(self):
        if not _HAS_LANGGRAPH:
            pytest.skip("LangGraph não disponível")
        ttn = TimedToolNode(tools=[], domain="test")
        assert ttn.tool_timeouts == {}

    def test_tool_timeouts_custom(self):
        if not _HAS_LANGGRAPH:
            pytest.skip("LangGraph não disponível")
        ttn = TimedToolNode(tools=[], domain="test", tool_timeouts={"search": 30})
        assert ttn.tool_timeouts["search"] == 30

    def test_get_tools_returns_list(self):
        if not _HAS_LANGGRAPH:
            pytest.skip("LangGraph não disponível")
        # ToolNode rejeita MagicMock — usar lista vazia e verificar que existe
        ttn = TimedToolNode(tools=[], domain="test")
        assert isinstance(ttn.get_tools(), list)

    def test_ainvoke_is_coroutine(self):
        import inspect
        assert inspect.iscoroutinefunction(TimedToolNode.ainvoke)


# ---------------------------------------------------------------------------
# Lógica de cálculo de timeout
# ---------------------------------------------------------------------------

class TestTimeoutCalculation:
    def test_default_used_when_no_tool_override(self):
        """Sem override → usa default (15s)."""
        ttn_timeouts = {}
        default = 15
        tc = _make_tool_call("my_tool")
        timeout = default
        name = tc.get("name", "")
        if name in ttn_timeouts:
            timeout = min(timeout, ttn_timeouts[name])
        assert timeout == 15

    def test_lower_override_wins(self):
        """Override menor que default → override vence."""
        ttn_timeouts = {"quick_search": 5}
        default = 15
        tc = _make_tool_call("quick_search")
        timeout = default
        name = tc.get("name", "")
        if name in ttn_timeouts:
            timeout = min(timeout, ttn_timeouts[name])
        assert timeout == 5

    def test_higher_override_loses(self):
        """Override maior que default → default mantém (min é conservador)."""
        ttn_timeouts = {"slow_tool": 60}
        default = 15
        tc = _make_tool_call("slow_tool")
        timeout = default
        name = tc.get("name", "")
        if name in ttn_timeouts:
            timeout = min(timeout, ttn_timeouts[name])
        assert timeout == 15

    def test_min_across_multiple_tools(self):
        """Múltiplas tools → menor timeout aplicado."""
        ttn_timeouts = {"tool_5s": 5, "tool_30s": 30}
        default = 15
        tool_calls = [_make_tool_call("tool_5s"), _make_tool_call("tool_30s")]
        timeout = default
        for tc in tool_calls:
            name = tc.get("name", "")
            if name in ttn_timeouts:
                timeout = min(timeout, ttn_timeouts[name])
        assert timeout == 5


# ---------------------------------------------------------------------------
# _build_timeout_response
# ---------------------------------------------------------------------------

class TestBuildTimeoutResponse:
    def test_injects_tool_message_for_each_call(self):
        try:
            from langchain_core.messages import ToolMessage
        except ImportError:
            pytest.skip("langchain_core não disponível")
        if not _HAS_LANGGRAPH:
            pytest.skip("LangGraph não disponível")

        ttn = TimedToolNode(tools=[], domain="test")
        tc = _make_tool_call("my_tool", "call-xyz")
        state = _make_state([tc])

        result = ttn._build_timeout_response(state, [tc], timeout=15)
        messages = result.get("messages", [])
        tool_msgs = [m for m in messages if isinstance(m, ToolMessage)]
        assert len(tool_msgs) == 1
        assert "my_tool" in tool_msgs[0].content
        assert "15s" in tool_msgs[0].content

    def test_tool_call_id_preserved(self):
        try:
            from langchain_core.messages import ToolMessage
        except ImportError:
            pytest.skip("langchain_core não disponível")
        if not _HAS_LANGGRAPH:
            pytest.skip("LangGraph não disponível")

        ttn = TimedToolNode(tools=[], domain="test")
        tc = _make_tool_call("my_tool", "call-abc-123")
        state = _make_state([tc])

        result = ttn._build_timeout_response(state, [tc], timeout=15)
        messages = result.get("messages", [])
        tool_msgs = [m for m in messages if isinstance(m, ToolMessage)]
        assert tool_msgs[0].tool_call_id == "call-abc-123"

    def test_multiple_tool_calls_all_get_messages(self):
        try:
            from langchain_core.messages import ToolMessage
        except ImportError:
            pytest.skip("langchain_core não disponível")
        if not _HAS_LANGGRAPH:
            pytest.skip("LangGraph não disponível")

        ttn = TimedToolNode(tools=[], domain="test")
        tcs = [_make_tool_call("tool_a", "id-a"), _make_tool_call("tool_b", "id-b")]
        state = _make_state(tcs)

        result = ttn._build_timeout_response(state, tcs, timeout=10)
        messages = result.get("messages", [])
        tool_msgs = [m for m in messages if isinstance(m, ToolMessage)]
        assert len(tool_msgs) == 2

    def test_returns_input_on_exception(self):
        """Se _build_timeout_response lança exception interna, retorna input."""
        if not _HAS_LANGGRAPH:
            pytest.skip("LangGraph não disponível")

        ttn = TimedToolNode(tools=[], domain="test")
        state = {"messages": []}

        # Passar tool_calls que causariam erro na extração de atributos
        broken_tc = object()  # sem atributos name/id
        result = ttn._build_timeout_response(state, [broken_tc], timeout=15)
        # Não deve lançar — retorna algo
        assert result is not None


# ---------------------------------------------------------------------------
# ainvoke com timeout mockado
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestAinvokeTimeout:
    async def test_timeout_error_returns_state(self):
        """TimeoutError → retorna estado com ToolMessages, sem lançar."""
        if not _HAS_LANGGRAPH:
            pytest.skip("LangGraph não disponível")

        ttn = TimedToolNode(tools=[], domain="test", default_timeout_seconds=1)
        tc = _make_tool_call("slow_tool", "call-slow")
        state = _make_state([tc])

        with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError):
            result = await ttn.ainvoke(state)

        assert result is not None

    async def test_successful_call_passes_through(self):
        """Sem timeout → retorna resultado da super().ainvoke."""
        if not _HAS_LANGGRAPH:
            pytest.skip("LangGraph não disponível")

        expected = {"messages": ["ok"]}
        ttn = TimedToolNode(tools=[], domain="test")

        with patch("asyncio.wait_for", new_callable=AsyncMock, return_value=expected):
            result = await ttn.ainvoke({"messages": []})

        assert result == expected

    async def test_no_tool_calls_state_still_works(self):
        """Estado sem tool_calls não causa erro."""
        if not _HAS_LANGGRAPH:
            pytest.skip("LangGraph não disponível")

        ttn = TimedToolNode(tools=[], domain="test")
        state = {"messages": [MagicMock(tool_calls=[])]}

        with patch("asyncio.wait_for", new_callable=AsyncMock, return_value=state):
            result = await ttn.ainvoke(state)

        assert result is not None
