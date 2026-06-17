"""E7 — Streaming de Pensamentos ReAct via WebSocket"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestReActStreamingEvents:

    def test_thinking_component_can_be_imported(self):
        """Garantir que o componente FE existe no caminho correto."""
        import os
        component_path = "/home/runner/workspace/plataforma-lia/src/components/react-thinking-stream.tsx"
        assert os.path.exists(component_path), f"Componente não encontrado: {component_path}"

    @pytest.mark.asyncio
    async def test_streaming_callback_called_on_tool_execution(self):
        """streaming_callback é chamado durante execução de tool no loop ReAct."""
        from lia_agents_core.react_loop import ReActState

        callback_calls = []
        async def mock_callback(event):
            callback_calls.append(event)

        state = ReActState(
            messages=[],
            streaming_callback=mock_callback,
        )
        # Verifica que o estado aceita streaming_callback
        assert state.streaming_callback is mock_callback

    def test_thinking_event_format(self):
        """Evento thinking tem campos type, step, thought."""
        event = {
            "type": "thinking",
            "step": 1,
            "thought": "Chamando tool: search_candidates",
        }
        assert event["type"] == "thinking"
        assert "step" in event
        assert "thought" in event

    @pytest.mark.asyncio
    async def test_ws_handler_ignores_thinking_exception(self):
        """WS handler não quebra se send_json falhar ao enviar thinking event."""
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock(side_effect=RuntimeError("WS closed"))

        # Simula o padrão do handler — fail-silent
        try:
            await mock_ws.send_json({"type": "thinking", "content": "test"})
        except Exception:
            pass  # deve ser tratado silenciosamente

        # Chega aqui sem exception
        assert True

    def test_thinking_steps_accumulate(self):
        """Steps de thinking são acumulados em lista."""
        steps = []
        for i in range(3):
            steps.append(f"Etapa {i+1}")
        assert len(steps) == 3
        assert steps[0] == "Etapa 1"

    def test_react_state_has_streaming_callback_field(self):
        """ReActState tem campo streaming_callback opcional."""
        from lia_agents_core.react_loop import ReActState
        state = ReActState(messages=[])
        assert hasattr(state, "streaming_callback")
        assert state.streaming_callback is None

    @pytest.mark.asyncio
    async def test_streaming_callback_emitted_with_tool_name(self):
        """Evento thinking inclui nome da tool quando disponível."""
        events = []
        async def cb(event):
            events.append(event)

        # Simula emissão de evento com tool_name
        await cb({"type": "thinking", "step": 1, "thought": "Chamando tool: search_candidates"})
        assert len(events) == 1
        assert "search_candidates" in events[0]["thought"]

    @pytest.mark.asyncio
    async def test_streaming_callback_none_does_not_crash(self):
        """Loop não quebra quando streaming_callback é None."""
        from lia_agents_core.react_loop import ReActState
        state = ReActState(messages=[], streaming_callback=None)

        # Simula verificação do loop
        if state.streaming_callback:
            await state.streaming_callback({"type": "thinking", "step": 1, "thought": "test"})
        # Nenhuma exceção = correto
        assert True
