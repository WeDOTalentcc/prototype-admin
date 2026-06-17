"""
Unit tests for GAP-09-002: SSE idempotency key — turn_id emission.

Structural tests that verify agent_chat_sse.py emits stream_start with turn_id:
  1. In the normal event_generator path (new turn)
  2. In the _reconnect_generator path (reconnect detected)

These tests parse source code — no live server needed.
"""
import re
from pathlib import Path

SSE_PATH = Path(__file__).parent.parent.parent / "app" / "api" / "v1" / "agent_chat_sse.py"


def read_sse() -> str:
    return SSE_PATH.read_text(encoding="utf-8")


class TestSseStreamStartEvent:
    """Verify stream_start event is emitted with turn_id in both paths."""

    def test_event_generator_emits_stream_start_with_turn_id(self):
        """The main event_generator must emit stream_start + turn_id before any other event."""
        src = read_sse()
        # Find event_generator function body
        gen_block = src.split("async def event_generator():")[1]
        assert "stream_start" in gen_block, (
            "event_generator must emit a stream_start event (GAP-09-002)"
        )
        assert "turn_id" in gen_block.split("stream_start")[0] or "turn_id" in gen_block, (
            "stream_start event must include turn_id field (GAP-09-002)"
        )

    def test_event_generator_stream_start_before_thinking(self):
        """stream_start must appear before serialize_thinking() in event_generator."""
        src = read_sse()
        gen_block = src.split("async def event_generator():")[1]
        stream_start_pos = gen_block.find("stream_start")
        thinking_pos = gen_block.find("serialize_thinking()")
        assert stream_start_pos != -1, "stream_start not found in event_generator"
        assert thinking_pos != -1, "serialize_thinking not found in event_generator"
        assert stream_start_pos < thinking_pos, (
            "stream_start must be emitted BEFORE serialize_thinking() — "
            "FE needs turn_id to guard before any UI rendering begins"
        )

    def test_reconnect_generator_emits_stream_start_with_turn_id(self):
        """_reconnect_generator must include stream_start with turn_id so FE can detect."""
        src = read_sse()
        reconn_block = src.split("async def _reconnect_generator():")[1]
        assert "stream_start" in reconn_block, (
            "_reconnect_generator must emit stream_start (GAP-09-002)"
        )
        assert "turn_id" in reconn_block, (
            "_reconnect_generator stream_start must include turn_id (GAP-09-002)"
        )

    def test_turn_hash_referenced_in_stream_start(self):
        """The turn_id value must be the _turn_hash (stable per session+content+user)."""
        src = read_sse()
        # Both stream_start events should reference _turn_hash
        matches = [m.start() for m in re.finditer(r'"stream_start"', src)]
        assert len(matches) >= 2, (
            f"Expected at least 2 stream_start events (normal + reconnect), found {len(matches)}"
        )
        for idx in matches:
            context = src[idx:idx + 200]
            assert "_turn_hash" in context, (
                f"stream_start event at pos {idx} must reference _turn_hash: {context[:100]}"
            )

    def test_turn_hash_computed_from_session_content_user(self):
        """_turn_hash must be computed from session_id:content:user_id (deterministic)."""
        src = read_sse()
        assert re.search(
            r'_turn_hash\s*=\s*hashlib\.sha256\([^)]*session_id[^)]*content[^)]*user_id',
            src,
        ) or re.search(
            r'_turn_hash\s*=\s*hashlib\.sha256\(f".*session_id.*content.*user_id',
            src,
        ), (
            "_turn_hash must be computed from session_id:content:user_id for stability on reconnect"
        )
