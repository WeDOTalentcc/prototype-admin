"""
Task #570 hardening — guards against the audit #569 regressions.

These tests do NOT require a live Postgres. They exercise the FastAPI
endpoint functions directly with mocked dependencies so they stay fast
and runnable in any CI shell.

What they cover (the two P0/P1 invariants the architect review called out):

1. ``/lia/feedback/thumbs`` with a free-text comment must persist that text
   into ``InteractionFeedback.correction`` (NOT ``feedback_text``) so it
   feeds the ``_update_patterns_from_feedback`` qualitative-signal branch.
2. ``/lia/feedback/regenerate`` must enforce multi-tenant isolation: an
   assistant message owned by another company surfaces as 404 (never as
   "regenerated") — this is the IDOR guard for the regeneration loop.
"""
from __future__ import annotations

import asyncio
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.api.v1 import lia_feedback


# ─── Helpers ──────────────────────────────────────────────────────────────


def _user(company_id: str | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        company_id=company_id or str(uuid.uuid4()),
    )


class _FakeFeedbackRow:
    """Minimal stand-in for InteractionFeedback used by the endpoint."""

    def __init__(self):
        self.id = uuid.uuid4()
        self.feedback_text: str | None = None
        self.feedback_category: str | None = None
        self.correction: str | None = None


# ─── Tests ────────────────────────────────────────────────────────────────


def test_thumbs_with_text_persists_to_correction_field(monkeypatch):
    """
    Audit fix: thumbs-down free text MUST land in ``correction``, not
    ``feedback_text``. ``_update_patterns_from_feedback`` only looks at
    ``correction`` when deciding whether to mine a learning pattern from
    the row (feedback_service.py line 152), so writing to the wrong
    field would silently break the learning loop.
    """
    fake_row = _FakeFeedbackRow()

    fake_service = MagicMock()
    fake_service.record_feedback = AsyncMock(return_value=fake_row)
    fake_service._update_patterns_from_feedback = AsyncMock()
    monkeypatch.setattr(lia_feedback, "_feedback_service", fake_service)

    fake_db = MagicMock()
    fake_db.commit = AsyncMock()
    fake_db.refresh = AsyncMock()

    user = _user()
    body = lia_feedback.ThumbsRequest(
        session_id="sess-1",
        message_id="msg-1",
        thumbs="down",
        feedback_text="resposta imprecisa",
        category="inaccurate",
    )

    ack = asyncio.run(
        lia_feedback.submit_thumbs(
            body,
            current_user=user,
            company_id=user.company_id,
            db=fake_db,
        )
    )

    assert ack.status == "recorded"
    # Critical assertion — text went to `correction`, not `feedback_text`.
    assert fake_row.correction == "resposta imprecisa"
    assert fake_row.feedback_text is None
    assert fake_row.feedback_category == "inaccurate"
    # Pattern update was re-triggered after we attached the qualitative signal.
    fake_service._update_patterns_from_feedback.assert_awaited_once()


def test_regenerate_rejects_cross_company_message(monkeypatch):
    """
    Multi-tenant guard: requesting regeneration of a message that does
    not belong to the caller's company must 404. This is what stops a
    tenant from poking another tenant's conversation history through
    the regenerate handshake.

    Recovery 2026-05-23 update: assinatura agora separa ``company_id``
    como parâmetro próprio (canonical ``Depends(require_company_id)``
    do ``app.shared.security``). Passamos explícito aqui já que estamos
    chamando a função direto, fora do FastAPI dependency injection.
    """
    user = _user()
    body = lia_feedback.RegenerateRequest(
        session_id="sess-x",
        message_id=str(uuid.uuid4()),
    )

    # Simulate "row not found for this company" — the SELECT returns None.
    scalar_one_or_none = MagicMock(return_value=None)
    execute_result = MagicMock(scalar_one_or_none=scalar_one_or_none)
    fake_db = MagicMock()
    fake_db.execute = AsyncMock(return_value=execute_result)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            lia_feedback.regenerate_response(
                body,
                current_user=user,
                company_id=user.company_id,
                db=fake_db,
            )
        )
    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail.lower()


def test_regenerate_rejects_invalid_company_id():
    """
    Recovery 2026-05-23 — substitui o test legacy
    ``test_regenerate_requires_company_context``. Antes o helper local
    ``_require_company_id`` retornava 400 quando user.company_id == None.

    Com o canonical ``require_company_id`` do ``app.shared.security``, esse
    cenário é interceptado upstream (no FastAPI dependency, com Prometheus
    counter ``lia_endpoint_require_company_id_total{outcome=invalid}``).
    Tests do helper canonical já cobrem esse caminho.

    O que ainda faz sentido testar aqui: o endpoint ``regenerate_response``
    rejeita company_id sintaticamente inválido (NÃO-UUID) com 400. Esse é
    o guard do `_UUID(company_id)` parse, que protege contra payload
    manualmente forjado mesmo se o canonical gate passar.
    """
    user = _user()
    body = lia_feedback.RegenerateRequest(
        session_id="sess-x",
        message_id=str(uuid.uuid4()),
    )
    fake_db = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            lia_feedback.regenerate_response(
                body,
                current_user=user,
                company_id="not-a-uuid",  # forçar ValueError no _UUID parse
                db=fake_db,
            )
        )
    assert exc_info.value.status_code == 400
    assert "invalid" in exc_info.value.detail.lower()
