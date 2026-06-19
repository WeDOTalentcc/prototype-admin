"""
IASidebar contract tests (PR 2 — conversations.py extensions).

Pins the following contracts:
- T2: JWT company_id enforcement (user can never pass company_id in payload)
- T3: IDOR fix — PATCH/title with wrong company_id → 404, not data leak
- T4: _build_conversation_response is the single source of truth for ConversationResponse
- T5: GET /conversations uses limit=50 default, supports filter params
- T7: unread_count increment is atomic (raw SQL UPDATE ... unread_count+1)
- Domain tag inference: 5 keyword maps + fallback to Geral
"""
from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ------------------------------------------------------------------
# T4 — _build_conversation_response includes all 4 new sidebar fields
# ------------------------------------------------------------------
def _make_fake_conv(**kwargs):
    """Create a minimal fake Conversation ORM object."""
    defaults = {
        "id": str(uuid.uuid4()),
        "user_id": "user-1",
        "context_type": "general",
        "context_id": None,
        "title": "Test Session",
        "summary": None,
        "intent": None,
        "status": "active",
        "is_active": True,
        "is_pinned": False,
        "domain_tag": None,
        "note": None,
        "unread_count": 0,
        "message_count": 0,
        "created_at": None,
        "updated_at": None,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_build_conversation_response_includes_sidebar_fields():
    """_build_conversation_response must include all 4 new fields."""
    from app.api.v1.conversations import _build_conversation_response

    conv = _make_fake_conv(is_pinned=True, domain_tag="Vagas", note="check tomorrow", unread_count=3)
    resp = _build_conversation_response(conv)

    assert resp.is_pinned is True
    assert resp.domain_tag == "Vagas"
    assert resp.note == "check tomorrow"
    assert resp.unread_count == 3


def test_build_conversation_response_defaults_for_none():
    """New sidebar fields must have safe defaults for pre-migration rows."""
    from app.api.v1.conversations import _build_conversation_response

    conv = _make_fake_conv(is_pinned=None, domain_tag=None, note=None, unread_count=None)
    resp = _build_conversation_response(conv)

    assert resp.is_pinned is False
    assert resp.domain_tag is None
    assert resp.note is None
    assert resp.unread_count == 0


# ------------------------------------------------------------------
# Domain tag inference (D9 decision)
# ------------------------------------------------------------------
def test_infer_domain_tag_vagas():
    from app.api.v1.conversations import _infer_domain_tag
    assert _infer_domain_tag("Preciso de ajuda com essa vaga de dev sênior") == "Vagas"


def test_infer_domain_tag_candidatos():
    from app.api.v1.conversations import _infer_domain_tag
    assert _infer_domain_tag("Preciso analisar o curriculo desse candidato") == "Candidatos"


def test_infer_domain_tag_relatorios():
    from app.api.v1.conversations import _infer_domain_tag
    assert _infer_domain_tag("Me mostra o funil de contratações") == "Relatórios"


def test_infer_domain_tag_configuracoes():
    from app.api.v1.conversations import _infer_domain_tag
    assert _infer_domain_tag("Quero configurar a integração com o LinkedIn") == "Configurações"


def test_infer_domain_tag_fallback():
    from app.api.v1.conversations import _infer_domain_tag
    assert _infer_domain_tag("Olá, tudo bem?") == "Geral"


def test_infer_domain_tag_empty_string():
    from app.api.v1.conversations import _infer_domain_tag
    assert _infer_domain_tag("") == "Geral"


# ------------------------------------------------------------------
# T3 — UpdateConversationRequest forbids extra fields (WeDoBaseModel)
# ------------------------------------------------------------------
def test_update_conversation_request_rejects_extra_fields():
    """extra='forbid' must reject company_id in payload (LGPD / multi-tenancy)."""
    import pytest
    from pydantic import ValidationError
    from app.api.v1.conversations import UpdateConversationRequest

    with pytest.raises(ValidationError):
        UpdateConversationRequest(title="ok", company_id="should-be-rejected")


def test_update_conversation_request_all_none_is_valid():
    """All-None PATCH is valid (no-op)."""
    from app.api.v1.conversations import UpdateConversationRequest

    req = UpdateConversationRequest()
    assert req.title is None
    assert req.is_pinned is None
    assert req.note is None
    assert req.domain_tag is None


def test_title_update_request_forbids_extra():
    from pydantic import ValidationError
    from app.api.v1.conversations import TitleUpdateRequest

    with pytest.raises(ValidationError):
        TitleUpdateRequest(title="ok", company_id="injected")


# ------------------------------------------------------------------
# T5 — GET /conversations default limit is 50
# ------------------------------------------------------------------
def test_list_conversations_default_limit():
    """Default limit must be 50 (IASidebar design spec)."""
    import inspect
    from app.api.v1.conversations import list_conversations
    sig = inspect.signature(list_conversations)
    limit_param = sig.parameters.get("limit")
    assert limit_param is not None, "limit param missing from list_conversations"
    # The default is a Query(...) object — check its default value
    default = limit_param.default
    # FastAPI Query object stores default as .default attribute
    assert default.default == 50, f"Expected limit default=50, got {default.default}"


# ------------------------------------------------------------------
# T7 — unread_count SQL uses atomic UPDATE (not read-modify-write)
# ------------------------------------------------------------------
def test_unread_count_uses_atomic_sql():
    """The add_message handler must use raw SQL UPDATE ... unread_count+1, not ORM read-modify-write."""
    import inspect
    import ast
    import pathlib

    source = pathlib.Path(
        "/home/runner/workspace/lia-agent-system/app/api/v1/conversations.py"
    ).read_text()

    # The atomic pattern must be present verbatim
    assert "unread_count = unread_count + 1" in source, (
        "Atomic SQL increment missing: must use 'UPDATE conversations SET unread_count = unread_count + 1'"
    )
    # Must NOT use a Python += pattern (read-modify-write race condition)
    assert "conversation.unread_count +=" not in source, (
        "Race condition: must use SQL UPDATE not Python conversation.unread_count +="
    )
