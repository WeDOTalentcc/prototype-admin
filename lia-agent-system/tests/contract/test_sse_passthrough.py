"""Fase B sensor: o _streaming_callback do SSE repassa tool_started/finished/
reasoning_step preservando shape (via serializers), em vez de achatar em thinking.
Sensor de source (o callback é closure aninhada, não isolável)."""
from pathlib import Path

_SSE = (
    Path(__file__).resolve().parents[2] / "app" / "api" / "v1" / "agent_chat_sse.py"
)


def test_sse_callback_passes_through_tool_events():
    src = _SSE.read_text(encoding="utf-8")
    for et, ser in [
        ("tool_started", "serialize_tool_started"),
        ("tool_finished", "serialize_tool_finished"),
        ("reasoning_step", "serialize_reasoning_step"),
    ]:
        assert f'event_type == "{et}"' in src, (
            f"_streaming_callback do SSE não trata '{et}' explicitamente → será "
            f"achatado em thinking (perde shape). Fix: adicionar elif "
            f'event_type == "{et}" → {ser}(...) antes do else.'
        )
        assert f"{ser}(" in src, f"'{ser}' não é usado em agent_chat_sse.py"
        assert ser in src.split("def ")[0] or f"    {ser}," in src, (
            f"'{ser}' não importado no topo de agent_chat_sse.py"
        )
