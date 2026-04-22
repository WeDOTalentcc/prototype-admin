"""Onda 5.3.c — History compaction in agentic_loop.

Canonical-fix consumer: agentic_loop consumes conversation_history and
conversation_summary (both existing producers). Compaction logic trims
older turns while preserving recent full turns + summary context.

Design:
  - If N turns > COMPACT_THRESHOLD (default 5), compact older turns
  - Keep last KEEP_RECENT_TURNS (default 6 messages) full
  - If conversation_summary available in ctx.extra, prepend it as
    "system" message so LLM has context of older turns
  - If no summary → fall back to current last-10 slice (no regression)

Feature flag LIA_HISTORY_COMPACTION_ENABLED (default true) for rollback.
Emits [LIA-HISTORY] marker.
"""
from __future__ import annotations

import os
from unittest.mock import MagicMock, AsyncMock, patch

import pytest


# ---------------------------------------------------------------------------
# 1. Structural: agentic_loop has history compaction logic
# ---------------------------------------------------------------------------

def test_agentic_loop_has_history_compaction_wire() -> None:
    """Structural: agentic_loop.py must reference compaction logic."""
    from pathlib import Path
    p = Path(__file__).resolve()
    src = ""
    for parent in p.parents:
        cand = parent / "app/orchestrator/agentic_loop.py"
        if cand.exists():
            src = cand.read_text(encoding="utf-8")
            break
    assert "Onda 5.3.c" in src, "Onda 5.3.c marker must be present"
    assert "LIA-HISTORY" in src, "[LIA-HISTORY] marker must be present"
    assert "conversation_summary" in src, "must reference conversation_summary"


def test_agentic_loop_run_accepts_conversation_summary() -> None:
    """Structural: run() must accept conversation_summary kwarg."""
    import inspect
    from app.orchestrator.agentic_loop import AgenticLoop
    sig = inspect.signature(AgenticLoop.run)
    assert "conversation_summary" in sig.parameters


# ---------------------------------------------------------------------------
# 2. Behavioral: short conversation → no compaction (fallback)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_short_history_no_compaction(monkeypatch) -> None:
    """Conversation with <=5 turns: keep all (no compaction)."""
    monkeypatch.setenv("LIA_HISTORY_COMPACTION_ENABLED", "true")
    from app.orchestrator.agentic_loop import AgenticLoop
    loop = AgenticLoop()
    # Use a small history of 3 messages
    history = [
        {"role": "user", "content": "q1"},
        {"role": "assistant", "content": "a1"},
        {"role": "user", "content": "q2"},
    ]
    messages = loop._compact_history(history, conversation_summary=None)
    assert len(messages) == 3
    assert all(m.get("role") in {"user", "assistant"} for m in messages)


# ---------------------------------------------------------------------------
# 3. Behavioral: long conversation + summary → compacted
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_long_history_with_summary_compacts(monkeypatch) -> None:
    """When >5 turns AND summary exists: prepend summary + keep last 6."""
    monkeypatch.setenv("LIA_HISTORY_COMPACTION_ENABLED", "true")
    monkeypatch.setenv("LIA_HISTORY_COMPACT_THRESHOLD", "5")
    monkeypatch.setenv("LIA_HISTORY_KEEP_RECENT", "6")
    from app.orchestrator.agentic_loop import AgenticLoop
    loop = AgenticLoop()
    history = [{"role": "user" if i % 2 == 0 else "assistant", "content": f"msg{i}"} for i in range(20)]
    summary = "Previous conversation: user asked about 30 jobs, LIA explained."
    result = loop._compact_history(history, conversation_summary=summary)
    # Expect: 1 system-like message with summary + last 6 of history
    assert len(result) == 7  # 1 summary + 6 kept
    # Summary should be first
    first_content = result[0].get("content", "")
    assert "Previous conversation" in first_content or summary in first_content


# ---------------------------------------------------------------------------
# 4. Behavioral: long conversation WITHOUT summary → fallback to last-10
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_long_history_without_summary_fallback(monkeypatch) -> None:
    """When >5 turns but no summary: fall back to last-10 slice (no regression)."""
    monkeypatch.setenv("LIA_HISTORY_COMPACTION_ENABLED", "true")
    from app.orchestrator.agentic_loop import AgenticLoop
    loop = AgenticLoop()
    history = [{"role": "user" if i % 2 == 0 else "assistant", "content": f"msg{i}"} for i in range(15)]
    result = loop._compact_history(history, conversation_summary=None)
    # Fallback: last-10 slice (same as before 5.3.c)
    assert len(result) == 10


# ---------------------------------------------------------------------------
# 5. Behavioral: feature flag disabled → no compaction
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_feature_flag_disabled_no_compaction(monkeypatch) -> None:
    """LIA_HISTORY_COMPACTION_ENABLED=false → always last-10 slice."""
    monkeypatch.setenv("LIA_HISTORY_COMPACTION_ENABLED", "false")
    from app.orchestrator.agentic_loop import AgenticLoop
    loop = AgenticLoop()
    history = [{"role": "user", "content": f"m{i}"} for i in range(20)]
    result = loop._compact_history(history, conversation_summary="some summary")
    # Flag off → ignore summary, last-10
    assert len(result) == 10


# ---------------------------------------------------------------------------
# 6. Behavioral: empty history
# ---------------------------------------------------------------------------

def test_empty_history_returns_empty() -> None:
    from app.orchestrator.agentic_loop import AgenticLoop
    loop = AgenticLoop()
    assert loop._compact_history([], conversation_summary=None) == []
    assert loop._compact_history(None, conversation_summary=None) == []


# ---------------------------------------------------------------------------
# 7. Behavioral: summary with short history still prepends summary
# ---------------------------------------------------------------------------

def test_short_history_with_summary_includes_summary(monkeypatch) -> None:
    """Summary always included when present (even with short history) —
    user preferences, episodic memory should always surface."""
    monkeypatch.setenv("LIA_HISTORY_COMPACTION_ENABLED", "true")
    from app.orchestrator.agentic_loop import AgenticLoop
    loop = AgenticLoop()
    history = [{"role": "user", "content": "q1"}, {"role": "assistant", "content": "a1"}]
    result = loop._compact_history(history, conversation_summary="recruiter prefers top-3 picks")
    # Summary prepended + 2 kept = 3
    assert len(result) == 3
    assert "top-3" in result[0].get("content", "")
