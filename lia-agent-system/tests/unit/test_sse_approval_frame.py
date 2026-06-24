"""_build_approval_frame (AUD-4 1b surfacing, 2026-06-07).

Frame SSE approval_required montado do hitl_pending (drenado do metadata do
agente). Mesmo shape do ramo supervisor (chat.py:947): type/pending_id/
description/action. Fallbacks seguros.
"""
from __future__ import annotations

from app.api.v1.agent_chat_sse import _build_approval_frame


def test_frame_shape_full():
    f = _build_approval_frame(
        "pid-123",
        {"tool": "close_job", "domain": "job_management", "message": "Confirme?"},
    )
    assert f["type"] == "approval_required"
    assert f["pending_id"] == "pid-123"
    assert f["description"] == "Confirme?"
    assert f["action"] == "close_job"


def test_frame_fallbacks_empty():
    f = _build_approval_frame("", {})
    assert f["type"] == "approval_required"
    assert f["pending_id"] == ""
    assert f["description"] == ""
    assert f["action"] == ""


def test_frame_none_hitl():
    f = _build_approval_frame("pid", None)
    assert f["type"] == "approval_required"
    assert f["pending_id"] == "pid"
    assert f["description"] == ""
    assert f["action"] == ""
