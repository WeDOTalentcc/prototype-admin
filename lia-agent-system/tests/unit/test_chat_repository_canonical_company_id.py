"""Canonical contract for ChatRepository.create_conversation multi-tenancy.

Audit 2026-05-23 found that POST /chat → create_conversation INSERT was
failing with  because the repo accepted only
user_id and never set company_id on the Conversation model. RLS policy
required company_id to match the tenant context.

This sensor enforces the canonical contract:
1. create_conversation MUST accept company_id as required positional/kwarg
2. Empty/None company_id MUST raise ValueError (fail-closed before reaching DB)
3. Conversation model MUST have company_id set after construction

Pairs with the AST sensor 
that walks repositories/*.py looking for the same anti-pattern across all
RLS-bearing tables. This test pins the contract for the canonical caller
that triggered the audit.
"""
from __future__ import annotations

import inspect
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.repositories.chat_repository import ChatRepository


TENANT_A = "11111111-1111-4111-a111-111111111111"
USER_A = "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa"


def _make_mock_db() -> MagicMock:
    db = MagicMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    return db


class TestCreateConversationCanonicalContract:
    """Contract pins for the canonical fix (V2)."""

    def test_signature_requires_company_id(self):
        """create_conversation MUST declare company_id as a parameter.

        Failure mode if missing: caller cannot pass company_id, so it stays
        None on the Conversation model, RLS rejects the INSERT, chat hangs.
        """
        sig = inspect.signature(ChatRepository.create_conversation)
        params = sig.parameters
        assert "company_id" in params, (
            "ChatRepository.create_conversation must accept company_id. "
            "Without it, the INSERT into conversations (RLS-bearing) fails "
            "with InsufficientPrivilegeError. See audit 2026-05-23."
        )

    def test_signature_company_id_is_required(self):
        """company_id MUST NOT default to None/empty (fail-closed canonical).

        Per CLAUDE.md REGRA 1 + ADR-001 §3: every public repo method touching
        a tenant-scoped table must enforce company_id presence. Default=None
        re-opens the bug for any future caller that forgets the kwarg.
        """
        sig = inspect.signature(ChatRepository.create_conversation)
        param = sig.parameters["company_id"]
        # Either no default, or a sentinel that triggers raise downstream.
        # We accept "" only if combined with explicit raise (see next test).
        assert param.default is inspect.Parameter.empty or param.default == "", (
            f"company_id must be required (no default) or  with raise. "
            f"Got default={param.default!r}. None/Optional is anti-pattern — "
            f"re-introduces the multi-tenancy gap."
        )

    @pytest.mark.asyncio
    async def test_raises_when_company_id_empty(self):
        """RED: empty company_id must raise ValueError before touching DB."""
        repo = ChatRepository(_make_mock_db())
        with pytest.raises((ValueError, TypeError), match="company_id"):
            await repo.create_conversation(user_id=USER_A, company_id="")

    @pytest.mark.asyncio
    async def test_raises_when_company_id_missing(self):
        """RED: omitting company_id must fail (TypeError if required kwarg,
        ValueError if defaulted-then-validated)."""
        repo = ChatRepository(_make_mock_db())
        with pytest.raises((ValueError, TypeError)):
            await repo.create_conversation(user_id=USER_A)  # type: ignore[call-arg]

    @pytest.mark.asyncio
    async def test_sets_company_id_on_conversation(self):
        """GREEN: with valid company_id, Conversation is constructed with it."""
        db = _make_mock_db()
        repo = ChatRepository(db)
        conv = await repo.create_conversation(user_id=USER_A, company_id=TENANT_A)
        assert conv.company_id == TENANT_A, (
            "Conversation.company_id must be set from the repo param. "
            "If None, RLS policy rejects INSERT."
        )
        assert conv.user_id == USER_A
        # db.add called once with the conversation
        assert db.add.call_count == 1
        db.flush.assert_awaited_once()
