"""
Tests for LangGraphBase._run_graph() e LangGraphReActBase._process_langgraph() — streaming.

Garante que:
- _run_graph() inclui AuditCallback no config["callbacks"] quando fornecido
- _run_graph() inclui StreamingCallback no config["callbacks"] quando fornecido
- _run_graph() combina ambos os callbacks
- _run_graph() omite callbacks None do config
- StreamingCallback é criado com session_id, company_id, user_id corretos
- tokens enviados via on_llm_new_token chegam ao ws_manager.send_to_session
"""
import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch, call

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


# ---------------------------------------------------------------------------
# Section 1: _run_graph callbacks injection
# ---------------------------------------------------------------------------

class TestRunGraphCallbacks:

    def _make_concrete_base(self):
        """Cria instância concreta de LangGraphBase para testes."""
        from lia_agents_core.langgraph_base import LangGraphBase
        from lia_agents_core.agent_interface import AgentInput, AgentOutput

        class ConcreteBase(LangGraphBase):
            @property
            def domain_name(self):
                return "test"

            @property
            def available_tools(self):
                return []

            def _build_graph(self):
                return MagicMock()

            async def process(self, input: AgentInput) -> AgentOutput:
                return AgentOutput(message="ok")

        with patch("lia_agents_core.langgraph_base.get_checkpointer", return_value=None):
            return ConcreteBase()

    @pytest.mark.asyncio
    async def test_run_graph_with_audit_callback_only(self):
        base = self._make_concrete_base()
        audit = MagicMock()

        mock_compiled = MagicMock()
        mock_compiled.ainvoke = AsyncMock(return_value={"messages": []})
        base._compiled = mock_compiled

        await base._run_graph(
            initial_state={"messages": []},
            session_id="sess-001",
            audit_callback=audit,
        )

        call_kwargs = mock_compiled.ainvoke.call_args
        config = call_kwargs[1].get("config") or call_kwargs[0][1]
        assert audit in config["callbacks"]

    @pytest.mark.asyncio
    async def test_run_graph_with_streaming_callback_only(self):
        base = self._make_concrete_base()
        streaming = MagicMock()

        mock_compiled = MagicMock()
        mock_compiled.ainvoke = AsyncMock(return_value={"messages": []})
        base._compiled = mock_compiled

        await base._run_graph(
            initial_state={"messages": []},
            session_id="sess-001",
            streaming_callback=streaming,
        )

        call_kwargs = mock_compiled.ainvoke.call_args
        config = call_kwargs[1].get("config") or call_kwargs[0][1]
        assert streaming in config["callbacks"]

    @pytest.mark.asyncio
    async def test_run_graph_with_both_callbacks(self):
        base = self._make_concrete_base()
        audit = MagicMock()
        streaming = MagicMock()

        mock_compiled = MagicMock()
        mock_compiled.ainvoke = AsyncMock(return_value={"messages": []})
        base._compiled = mock_compiled

        await base._run_graph(
            initial_state={"messages": []},
            session_id="sess-001",
            audit_callback=audit,
            streaming_callback=streaming,
        )

        call_kwargs = mock_compiled.ainvoke.call_args
        config = call_kwargs[1].get("config") or call_kwargs[0][1]
        assert audit in config["callbacks"]
        assert streaming in config["callbacks"]
        assert len(config["callbacks"]) == 2

    @pytest.mark.asyncio
    async def test_run_graph_no_callbacks_omits_key(self):
        base = self._make_concrete_base()

        mock_compiled = MagicMock()
        mock_compiled.ainvoke = AsyncMock(return_value={"messages": []})
        base._compiled = mock_compiled

        await base._run_graph(
            initial_state={"messages": []},
            session_id="sess-001",
        )

        call_kwargs = mock_compiled.ainvoke.call_args
        config = call_kwargs[1].get("config") or call_kwargs[0][1]
        assert "callbacks" not in config

    @pytest.mark.asyncio
    async def test_run_graph_sets_thread_id(self):
        base = self._make_concrete_base()

        mock_compiled = MagicMock()
        mock_compiled.ainvoke = AsyncMock(return_value={"messages": []})
        base._compiled = mock_compiled

        await base._run_graph(
            initial_state={"messages": []},
            session_id="my-session-abc",
        )

        call_kwargs = mock_compiled.ainvoke.call_args
        config = call_kwargs[1].get("config") or call_kwargs[0][1]
        # Canonical thread_id format (commit a7d756097, P0 chat hang fix):
        # "session::domain" — each (session, domain) pair gets its own
        # checkpointer namespace. ConcreteBase.domain_name == "test".
        assert config["configurable"]["thread_id"] == "my-session-abc::test"


# ---------------------------------------------------------------------------
# Section 2: StreamingCallback criação correta
# ---------------------------------------------------------------------------

class TestStreamingCallbackCreation:

    def test_streaming_callback_instantiates(self):
        from lia_agents_core.streaming_callback import StreamingCallback
        cb = StreamingCallback(
            session_id="sess-cb-001",
            company_id="comp-001",
            user_id="user-001",
        )
        assert cb.session_id == "sess-cb-001"
        assert cb.company_id == "comp-001"
        assert cb.user_id == "user-001"

    def test_streaming_callback_inherits_base_callback_handler(self):
        from lia_agents_core.streaming_callback import StreamingCallback
        try:
            from langchain_core.callbacks.base import BaseCallbackHandler
        except ImportError:
            from langchain.callbacks.base import BaseCallbackHandler
        cb = StreamingCallback(session_id="test", company_id="", user_id="")
        assert isinstance(cb, BaseCallbackHandler)

    def test_streaming_callback_has_on_llm_new_token(self):
        from lia_agents_core.streaming_callback import StreamingCallback
        cb = StreamingCallback(session_id="test", company_id="", user_id="")
        assert callable(cb.on_llm_new_token)

    def test_streaming_callback_has_on_llm_end(self):
        from lia_agents_core.streaming_callback import StreamingCallback
        cb = StreamingCallback(session_id="test", company_id="", user_id="")
        assert callable(cb.on_llm_end)

    def test_streaming_callback_has_on_llm_error(self):
        from lia_agents_core.streaming_callback import StreamingCallback
        cb = StreamingCallback(session_id="test", company_id="", user_id="")
        assert callable(cb.on_llm_error)


# ---------------------------------------------------------------------------
# Section 3: on_llm_new_token scheduling
# ---------------------------------------------------------------------------

class TestStreamingCallbackTokenScheduling:

    def test_on_llm_new_token_schedules_send(self):
        from lia_agents_core.streaming_callback import StreamingCallback
        cb = StreamingCallback(session_id="sess-token", company_id="c1", user_id="u1")

        with patch.object(cb, "_schedule_send") as mock_schedule:
            cb.on_llm_new_token("hello")
            mock_schedule.assert_called_once()
            args = mock_schedule.call_args[0][0]
            assert args["type"] == "token"
            assert "hello" in args["content"]

    def test_on_llm_new_token_ignores_empty_token(self):
        from lia_agents_core.streaming_callback import StreamingCallback
        cb = StreamingCallback(session_id="sess-token", company_id="c1", user_id="u1")

        with patch.object(cb, "_schedule_send") as mock_schedule:
            cb.on_llm_new_token("")
            mock_schedule.assert_not_called()

    def test_on_llm_end_sends_token_done(self):
        from lia_agents_core.streaming_callback import StreamingCallback
        cb = StreamingCallback(session_id="sess-token", company_id="c1", user_id="u1")

        sent = []
        with patch.object(cb, "_schedule_send", side_effect=sent.append):
            cb.on_llm_end(MagicMock())

        assert any(m.get("type") == "token_done" for m in sent)

    def test_on_llm_error_sends_error_type(self):
        from lia_agents_core.streaming_callback import StreamingCallback
        cb = StreamingCallback(session_id="sess-token", company_id="c1", user_id="u1")

        with patch.object(cb, "_schedule_send") as mock_schedule:
            cb.on_llm_error(RuntimeError("LLM died"))
            mock_schedule.assert_called_once()
            args = mock_schedule.call_args[0][0]
            assert args["type"] == "error"

    def test_on_llm_end_flushes_buffer(self):
        """Tokens pendentes no buffer devem ser enviados antes de token_done."""
        from lia_agents_core.streaming_callback import StreamingCallback
        cb = StreamingCallback(
            session_id="sess-buffer",
            company_id="c1",
            user_id="u1",
            buffer_chunks=5,  # buffer de 5 tokens
        )

        sent = []
        with patch.object(cb, "_schedule_send", side_effect=sent.append):
            # Adiciona 3 tokens (abaixo do buffer de 5)
            cb.on_llm_new_token("a")
            cb.on_llm_new_token("b")
            cb.on_llm_new_token("c")
            # end deve flush
            cb.on_llm_end(MagicMock())

        token_msgs = [m for m in sent if m.get("type") == "token"]
        done_msgs = [m for m in sent if m.get("type") == "token_done"]
        assert len(token_msgs) >= 1  # buffer flushed
        assert len(done_msgs) == 1


# ---------------------------------------------------------------------------
# Section 4: _process_langgraph cria StreamingCallback
# ---------------------------------------------------------------------------

class TestProcessLangGraphCreatesStreaming:

    def _make_react_agent(self):
        from lia_agents_core.langgraph_react_base import LangGraphReActBase
        from lia_agents_core.agent_interface import AgentInput, AgentOutput

        class ConcreteReAct(LangGraphReActBase):
            @property
            def domain_name(self):
                return "test"

            @property
            def available_tools(self):
                return []

            def _build_graph(self):
                return MagicMock()

            async def process(self, input: AgentInput) -> AgentOutput:
                return AgentOutput(message="ok")

        with patch("lia_agents_core.langgraph_base.get_checkpointer", return_value=None):
            return ConcreteReAct()

    def _make_agent_input(self):
        from lia_agents_core.agent_interface import AgentInput
        return AgentInput(
            message="Olá LIA",
            session_id="sess-react-001",
            company_id="comp-001",
            user_id="user-001",
        )

    @pytest.mark.asyncio
    async def test_process_langgraph_creates_streaming_callback(self):
        agent = self._make_react_agent()
        input_data = self._make_agent_input()

        mock_compiled = MagicMock()
        mock_compiled.ainvoke = AsyncMock(return_value={"messages": [
            MagicMock(content="Resposta da LIA")
        ]})

        # StreamingCallback é importado inline — patchear no módulo de origem
        with patch.object(agent, "_get_compiled_graph", return_value=mock_compiled):
            with patch("lia_agents_core.streaming_callback.StreamingCallback") as MockSC:
                mock_sc_instance = MagicMock()
                MockSC.return_value = mock_sc_instance

                with patch("app.shared.compliance.audit_callback.AuditCallback"):
                    await agent._process_langgraph(input_data)

                # Verifica que StreamingCallback foi criado com args corretos
                MockSC.assert_called_once_with(
                    session_id="sess-react-001",
                    company_id="comp-001",
                    user_id="user-001",
                )

    @pytest.mark.asyncio
    async def test_process_langgraph_passes_streaming_to_run_graph(self):
        agent = self._make_react_agent()
        input_data = self._make_agent_input()

        mock_sc = MagicMock()

        with patch("lia_agents_core.streaming_callback.StreamingCallback", return_value=mock_sc):
            with patch("app.shared.compliance.audit_callback.AuditCallback"):
                with patch.object(agent, "_run_graph", new_callable=AsyncMock) as mock_run:
                    mock_run.return_value = {"messages": [MagicMock(content="ok")]}
                    await agent._process_langgraph(input_data)

                    call_kwargs = mock_run.call_args[1]
                    assert call_kwargs.get("streaming_callback") == mock_sc

    @pytest.mark.asyncio
    async def test_process_langgraph_continues_if_streaming_callback_fails(self):
        """Se StreamingCallback lançar exceção na criação, processo continua."""
        agent = self._make_react_agent()
        input_data = self._make_agent_input()

        mock_compiled = MagicMock()
        mock_compiled.ainvoke = AsyncMock(return_value={"messages": [
            MagicMock(content="Resposta ok")
        ]})

        with patch.object(agent, "_get_compiled_graph", return_value=mock_compiled):
            with patch("lia_agents_core.streaming_callback.StreamingCallback",
                       side_effect=ImportError("ws_manager not available")):
                with patch("app.shared.compliance.audit_callback.AuditCallback"):
                    # Não deve lançar — streaming_cb ficará None e processo continua
                    output = await agent._process_langgraph(input_data)
                    assert output is not None
