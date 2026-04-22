"""Onda 4.10.b — chat.py send_message must surface citations + hitl_checkpoint in response envelope.

Structural tests — verify source of chat.py contains the wiring that
forwards adapter result fields into message_metadata (_meta) so the
API envelope exposes them to frontend.
"""
from __future__ import annotations

from pathlib import Path


def _chat_source() -> str:
    p = Path(__file__).resolve()
    for parent in p.parents:
        cand = parent / "app/api/v1/chat.py"
        if cand.exists():
            return cand.read_text(encoding="utf-8")
    raise RuntimeError("chat.py not found")


def test_chat_injects_citations_into_meta() -> None:
    """Onda 4.10.b: _meta must include citations from orch_result."""
    src = _chat_source()
    assert 'orch_result.get("citations"' in src or 'orch_result["citations"]' in src, (
        "chat.py must read citations from orch_result"
    )
    # Confirmed forwarded to metadata dict used by MessageResponse
    assert "_meta[\"citations\"]" in src or "_meta['citations']" in src


def test_chat_injects_has_citations_into_meta() -> None:
    """Onda 4.10.b: _meta must include has_citations flag."""
    src = _chat_source()
    assert "has_citations" in src


def test_chat_injects_hitl_checkpoint_into_meta() -> None:
    """Onda 4.10.b: _meta must include hitl_checkpoint when present."""
    src = _chat_source()
    assert "hitl_checkpoint" in src, (
        "chat.py must surface hitl_checkpoint to frontend via _meta"
    )


def test_chat_marker_in_code() -> None:
    """Onda 4.10.b: marker present for traceability."""
    src = _chat_source()
    assert "Onda 4.10" in src
