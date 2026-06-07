"""hitl_preflight helper (AUD-4 1c, 2026-06-07).

Pre-flight DRY pro produtor: None quando gate OFF ou ja aprovado; dict
needs_confirmation quando gate ON + nao aprovado. Usado pelas tools sensiveis
que NAO passam por @tool_handler.
"""
from __future__ import annotations

from app.shared.hitl.hitl_approval_context import (
    hitl_preflight,
    set_hitl_approved,
    reset_hitl_approved,
)


def test_dormant_when_gate_off(monkeypatch):
    monkeypatch.delenv("LIA_HITL_GATE", raising=False)
    assert hitl_preflight(tool="send_email", domain="communication") is None


def test_blocks_when_gate_on_unapproved(monkeypatch):
    monkeypatch.setenv("LIA_HITL_GATE", "1")
    r = hitl_preflight(
        tool="send_email", domain="communication", data={"to": "x@y.com"}
    )
    assert r is not None
    assert r["needs_confirmation"] is True
    assert r["success"] is False
    assert r["hitl"] == {"tool": "send_email", "domain": "communication"}
    assert r["data"] == {"to": "x@y.com"}


def test_passes_when_approved(monkeypatch):
    monkeypatch.setenv("LIA_HITL_GATE", "1")
    tok = set_hitl_approved(True)
    try:
        assert hitl_preflight(tool="send_email", domain="communication") is None
    finally:
        reset_hitl_approved(tok)


def test_extra_merged(monkeypatch):
    monkeypatch.setenv("LIA_HITL_GATE", "1")
    r = hitl_preflight(
        tool="close_job",
        domain="job_management",
        extra={"action_taken": "close_job", "confirmation_message": "Tem certeza?"},
    )
    assert r["action_taken"] == "close_job"
    assert r["confirmation_message"] == "Tem certeza?"
