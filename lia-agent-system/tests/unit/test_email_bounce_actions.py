"""
LOTE-009 — Contract tests for email bounce/spam/unsubscribe ACTION logic.

Tests:
1. Hard bounce (5xx) adds "email_hard_bounce" to channel_opt_out
2. Soft bounce (4xx) — no change
3. Spam complaint adds "marketing_email" to channel_opt_out
4. Unsubscribe event adds "marketing_email" to channel_opt_out
5. Unknown email — silently no-ops (no exception)
6. Flag idempotent (not added twice)
7. RFC 8058 List-Unsubscribe URL includes ?email= param (dispatcher)
8. RFC 8058 List-Unsubscribe URL includes ?email= param (mailgun provider)
9. RFC 8058 List-Unsubscribe URL includes ?email= param (resend provider)
"""
import hashlib
import importlib
import os
import sys
import types
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# ---------------------------------------------------------------------------
# Minimal stubs so we can import the tracking module without a full app boot
# ---------------------------------------------------------------------------

def _make_candidate_stub(email_hash, channel_opt_out=None):
    c = MagicMock()
    c.email_hash = email_hash
    c.channel_opt_out = channel_opt_out or []
    return c


def _email_hash(email: str) -> str:
    return hashlib.sha256(email.lower().strip().encode()).hexdigest()


# ---------------------------------------------------------------------------
# Tests for _handle_email_delivery_action (email_tracking.py)
# ---------------------------------------------------------------------------

class TestHandleEmailDeliveryAction(unittest.IsolatedAsyncioTestCase):
    """Tests for the _handle_email_delivery_action helper."""

    async def _run(self, action, email, raw_event, candidates):
        from app.api.v1.email_tracking import _handle_email_delivery_action

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = candidates

        db = AsyncMock()
        db.execute = AsyncMock(return_value=mock_result)
        db.commit = AsyncMock()

        await _handle_email_delivery_action(db, action, email, raw_event)
        return db

    async def test_hard_bounce_adds_flag(self):
        email = "candidate@example.com"
        candidate = _make_candidate_stub(_email_hash(email))
        db = await self._run(
            action="bounce",
            email=email,
            raw_event={"delivery-status": {"code": 550}},
            candidates=[candidate],
        )
        assert "email_hard_bounce" in candidate.channel_opt_out
        db.commit.assert_awaited_once()

    async def test_soft_bounce_no_change(self):
        email = "candidate@example.com"
        candidate = _make_candidate_stub(_email_hash(email))
        db = await self._run(
            action="bounce",
            email=email,
            raw_event={"delivery-status": {"code": 421}},
            candidates=[candidate],
        )
        assert "email_hard_bounce" not in candidate.channel_opt_out
        db.commit.assert_not_awaited()

    async def test_spam_complaint_adds_marketing_flag(self):
        email = "candidate@example.com"
        candidate = _make_candidate_stub(_email_hash(email))
        db = await self._run(
            action="spam",
            email=email,
            raw_event={},
            candidates=[candidate],
        )
        assert "marketing_email" in candidate.channel_opt_out
        db.commit.assert_awaited_once()

    async def test_unsubscribe_adds_marketing_flag(self):
        email = "candidate@example.com"
        candidate = _make_candidate_stub(_email_hash(email))
        db = await self._run(
            action="unsubscribe",
            email=email,
            raw_event={},
            candidates=[candidate],
        )
        assert "marketing_email" in candidate.channel_opt_out
        db.commit.assert_awaited_once()

    async def test_unknown_email_no_exception(self):
        db = await self._run(
            action="bounce",
            email="nobody@example.com",
            raw_event={"delivery-status": {"code": 550}},
            candidates=[],
        )
        db.commit.assert_not_awaited()

    async def test_flag_is_idempotent(self):
        email = "candidate@example.com"
        candidate = _make_candidate_stub(
            _email_hash(email), channel_opt_out=["marketing_email"]
        )
        db = await self._run(
            action="unsubscribe",
            email=email,
            raw_event={},
            candidates=[candidate],
        )
        # Should NOT add duplicate
        assert candidate.channel_opt_out.count("marketing_email") == 1


# ---------------------------------------------------------------------------
# Tests for List-Unsubscribe URL containing per-recipient ?email= param
# ---------------------------------------------------------------------------

class TestListUnsubscribeUrlIncludesEmail(unittest.TestCase):
    """Ensure all three email paths embed ?email= in List-Unsubscribe header."""

    def test_dispatcher_list_unsubscribe_contains_email_param(self):
        """communication_dispatcher.py must embed ?email= in List-Unsubscribe."""
        path = os.path.join(
            os.path.dirname(__file__),
            "../../app/domains/communication/services/communication_dispatcher.py",
        )
        with open(os.path.realpath(path)) as f:
            src = f.read()
        assert "?email=" in src, (
            "communication_dispatcher.py: List-Unsubscribe URL must include ?email= "
            "for RFC 8058 per-recipient one-click unsubscribe."
        )

    def test_mailgun_provider_list_unsubscribe_contains_email_param(self):
        path = os.path.join(
            os.path.dirname(__file__),
            "../../app/domains/communication/services/"
            "email_providers/mailgun_provider.py",
        )
        with open(os.path.realpath(path)) as f:
            src = f.read()
        assert "?email=" in src, (
            "mailgun_provider.py: List-Unsubscribe URL must include ?email="
        )

    def test_resend_provider_list_unsubscribe_contains_email_param(self):
        path = os.path.join(
            os.path.dirname(__file__),
            "../../app/domains/communication/services/"
            "email_providers/resend_provider.py",
        )
        with open(os.path.realpath(path)) as f:
            src = f.read()
        assert "?email=" in src, (
            "resend_provider.py: List-Unsubscribe URL must include ?email="
        )


if __name__ == "__main__":
    unittest.main()
