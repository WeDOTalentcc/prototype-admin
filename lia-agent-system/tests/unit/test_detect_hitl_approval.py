"""_detect_hitl_approval (AUD-4 1b-b/c, 2026-06-07).

Server-authoritative: so libera (True) se existe pending VALIDO desta sessao com
o id recebido. Fail-CLOSED em todo o resto. receive_approval (audit) so e
chamado no match. NUNCA confia na LLM.
"""
from __future__ import annotations

import asyncio

from app.api.v1.agent_chat_sse import _detect_hitl_approval


class _FakeHsvc:
    def __init__(self, pending=None):
        self._pending = pending
        self.received = []

    async def get_pending(self, thread_id):
        return self._pending

    async def receive_approval(self, **kw):
        self.received.append(kw)
        return {"approved": kw.get("approved")}


def _run(**kw):
    return asyncio.run(_detect_hitl_approval(**kw))


def test_no_pending_id_false():
    assert _run(approve_pending_id=None, session_id="s", company_id="c", user_id="u") is False


def test_match_approves(monkeypatch):
    fake = _FakeHsvc(pending={"pending_id": "p1", "domain": "job_management", "action": "close_job"})
    monkeypatch.setattr("app.services.hitl_service.hitl_service", fake, raising=False)
    r = _run(approve_pending_id="p1", session_id="s", company_id="c", user_id="u")
    assert r is True
    assert fake.received and fake.received[0]["pending_id"] == "p1"
    assert fake.received[0]["approved"] is True
    assert fake.received[0]["thread_id"] == "s"


def test_mismatch_no_approve(monkeypatch):
    fake = _FakeHsvc(pending={"pending_id": "OTHER"})
    monkeypatch.setattr("app.services.hitl_service.hitl_service", fake, raising=False)
    r = _run(approve_pending_id="p1", session_id="s", company_id="c", user_id="u")
    assert r is False
    assert fake.received == []  # NAO registra aprovacao em mismatch


def test_no_pending_false(monkeypatch):
    fake = _FakeHsvc(pending=None)
    monkeypatch.setattr("app.services.hitl_service.hitl_service", fake, raising=False)
    assert _run(approve_pending_id="p1", session_id="s", company_id="c", user_id="u") is False
    assert fake.received == []


def test_exception_fail_closed(monkeypatch):
    class _Boom:
        async def get_pending(self, thread_id):
            raise RuntimeError("redis down")
    monkeypatch.setattr("app.services.hitl_service.hitl_service", _Boom(), raising=False)
    # fail-CLOSED: erro -> nao aprova
    assert _run(approve_pending_id="p1", session_id="s", company_id="c", user_id="u") is False
