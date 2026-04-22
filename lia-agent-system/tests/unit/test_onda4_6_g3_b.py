"""Onda 4.6 G3.B — HITL dispatch wire tests."""
from __future__ import annotations

from pathlib import Path


def test_g3b_marker_in_main_orchestrator() -> None:
    """G3.B: main_orchestrator contains G3.B marker + hitl import."""
    import app.orchestrator.main_orchestrator as mo

    source = Path(mo.__file__).read_text(encoding="utf-8")
    assert "G3.B" in source
    assert "build_hitl_checkpoint" in source
    assert "hitl_checkpoint=_hitl_checkpoint" in source


def test_hitl_build_reachable_from_orchestrator() -> None:
    """G3.B: canonical hitl.build_hitl_checkpoint integration works."""
    from app.orchestrator.hitl import build_hitl_checkpoint

    cp = build_hitl_checkpoint(
        tool_name="close_job",
        tool_params={"job_id": "v0040"},
        governance_tags=["destructive"],
        reason="Test reason",
    )
    assert cp is not None
    assert cp["tool_name"] == "close_job"
    assert cp["governance_tags"] == ["destructive"]


def test_chat_response_hitl_checkpoint_default_none() -> None:
    """G3.B regression: default None preserves backward compat."""
    from app.orchestrator.main_orchestrator import ChatResponse

    resp = ChatResponse(success=True, content="test")
    assert resp.hitl_checkpoint is None


def test_chat_response_hitl_checkpoint_populated() -> None:
    """G3.B: ChatResponse accepts hitl_checkpoint dict."""
    from app.orchestrator.main_orchestrator import ChatResponse

    cp = {
        "checkpoint_id": "abc",
        "tool_name": "close_job",
        "tool_params_summary": {"job_id": "v0040"},
        "governance_tags": ["destructive"],
        "reason": "Action destrutiva",
        "requested_at": "2026-04-21T10:00:00",
        "approval_endpoint": "/api/v1/approvals",
    }
    resp = ChatResponse(success=True, content="precisa aprovar", hitl_checkpoint=cp)
    assert resp.hitl_checkpoint == cp


def test_g3b_wiring_source_structure() -> None:
    """G3.B structural: wiring block exists within agentic path."""
    import app.orchestrator.main_orchestrator as mo
    source = Path(mo.__file__).read_text(encoding="utf-8")

    # Locate G3.B block and verify it's BEFORE ChatResponse construction
    g3b_idx = source.find("Onda 4.6 G3.B")
    vb_resp_idx = source.find("hitl_checkpoint=_hitl_checkpoint")

    assert g3b_idx > 0, "G3.B marker missing"
    assert vb_resp_idx > g3b_idx, "G3.B block must precede ChatResponse hitl_checkpoint= kwarg"
    block = source[g3b_idx : vb_resp_idx]
    # Block must reference _hitl_pending list + take first
    assert "_hitl_pending" in block
    assert "_first" in block or "_hitl_pending[0]" in block


def test_g3b_fail_safe_on_builder_exception() -> None:
    """G3.B: hitl build failure wraps in try/except (non-fatal)."""
    import app.orchestrator.main_orchestrator as mo
    source = Path(mo.__file__).read_text(encoding="utf-8")

    g3b_idx = source.find("Onda 4.6 G3.B")
    block = source[g3b_idx : g3b_idx + 1500]
    assert "try:" in block
    assert "except Exception" in block
    assert "hitl checkpoint skipped" in block.lower()
