"""
GAP-07-008: RFC 2822 email threading header tests.

Verifies deterministic thread-root Message-ID, uniqueness of per-email
Message-IDs, and correct header assembly for first vs. reply emails.
"""
import re
import pytest

from app.domains.communication.services.email_threading import (
    build_threading_headers,
    get_email_message_id,
    get_thread_message_id,
)

# ---------------------------------------------------------------------------
# Constants used across tests
# ---------------------------------------------------------------------------
_CANDIDATE = "cand-aaaa-1111"
_COMPANY   = "co-bbbb-2222"
_VACANCY   = "vac-cccc-3333"

_MSG_ID_RE = re.compile(r"^<[^@>]+@wedotalent\.cc>$")


class TestGetThreadMessageId:
    """get_thread_message_id — deterministic thread-root ID."""

    def test_is_deterministic(self):
        """Same inputs MUST produce the same ID every time."""
        id1 = get_thread_message_id(_CANDIDATE, _COMPANY, _VACANCY)
        id2 = get_thread_message_id(_CANDIDATE, _COMPANY, _VACANCY)
        assert id1 == id2

    def test_different_candidates_different_ids(self):
        id_a = get_thread_message_id("cand-A", _COMPANY, _VACANCY)
        id_b = get_thread_message_id("cand-B", _COMPANY, _VACANCY)
        assert id_a != id_b

    def test_different_vacancies_different_ids(self):
        id_a = get_thread_message_id(_CANDIDATE, _COMPANY, "vac-111")
        id_b = get_thread_message_id(_CANDIDATE, _COMPANY, "vac-222")
        assert id_a != id_b

    def test_different_companies_different_ids(self):
        id_a = get_thread_message_id(_CANDIDATE, "co-AAA", _VACANCY)
        id_b = get_thread_message_id(_CANDIDATE, "co-BBB", _VACANCY)
        assert id_a != id_b

    def test_none_vacancy_uses_general_bucket(self):
        id_none = get_thread_message_id(_CANDIDATE, _COMPANY, None)
        id_explicit = get_thread_message_id(_CANDIDATE, _COMPANY, "general")
        # None maps to the literal string "general" — both should be equal
        assert id_none == id_explicit

    def test_format_is_rfc2822_message_id(self):
        """Must match <local-part@domain> shape."""
        msg_id = get_thread_message_id(_CANDIDATE, _COMPANY, _VACANCY)
        assert _MSG_ID_RE.match(msg_id), f"Bad format: {msg_id!r}"

    def test_contains_wedotalent_domain(self):
        msg_id = get_thread_message_id(_CANDIDATE, _COMPANY, _VACANCY)
        assert "@wedotalent.cc>" in msg_id


class TestGetEmailMessageId:
    """get_email_message_id — unique per-message ID."""

    def test_each_call_is_unique(self):
        ids = {get_email_message_id() for _ in range(200)}
        assert len(ids) == 200, "Collision detected in 200 samples"

    def test_format_is_rfc2822_message_id(self):
        msg_id = get_email_message_id()
        assert _MSG_ID_RE.match(msg_id), f"Bad format: {msg_id!r}"

    def test_distinct_from_thread_root(self):
        """Per-email ID must differ from deterministic thread root."""
        thread_root = get_thread_message_id(_CANDIDATE, _COMPANY, _VACANCY)
        per_email   = get_email_message_id()
        assert thread_root != per_email


class TestBuildThreadingHeaders:
    """build_threading_headers — assembles complete header dict."""

    # ---- first email (is_reply=False) -----------------------------------

    def test_first_email_has_message_id(self):
        headers = build_threading_headers(
            _CANDIDATE, _COMPANY, _VACANCY, is_reply=False
        )
        assert "Message-ID" in headers

    def test_first_email_has_no_in_reply_to(self):
        headers = build_threading_headers(
            _CANDIDATE, _COMPANY, _VACANCY, is_reply=False
        )
        assert "In-Reply-To" not in headers

    def test_first_email_has_no_references(self):
        headers = build_threading_headers(
            _CANDIDATE, _COMPANY, _VACANCY, is_reply=False
        )
        assert "References" not in headers

    # ---- reply email (is_reply=True, the default) -----------------------

    def test_reply_email_has_message_id(self):
        headers = build_threading_headers(_CANDIDATE, _COMPANY, _VACANCY)
        assert "Message-ID" in headers

    def test_reply_email_has_in_reply_to(self):
        headers = build_threading_headers(_CANDIDATE, _COMPANY, _VACANCY)
        assert "In-Reply-To" in headers

    def test_reply_email_has_references(self):
        headers = build_threading_headers(_CANDIDATE, _COMPANY, _VACANCY)
        assert "References" in headers

    def test_in_reply_to_equals_thread_root(self):
        thread_root = get_thread_message_id(_CANDIDATE, _COMPANY, _VACANCY)
        headers = build_threading_headers(_CANDIDATE, _COMPANY, _VACANCY)
        assert headers["In-Reply-To"] == thread_root

    def test_references_equals_thread_root(self):
        thread_root = get_thread_message_id(_CANDIDATE, _COMPANY, _VACANCY)
        headers = build_threading_headers(_CANDIDATE, _COMPANY, _VACANCY)
        assert headers["References"] == thread_root

    def test_references_chain_is_consistent(self):
        """In-Reply-To and References both point to the same thread root."""
        headers = build_threading_headers(_CANDIDATE, _COMPANY, _VACANCY)
        assert headers["In-Reply-To"] == headers["References"]

    def test_two_replies_have_different_message_ids(self):
        """Each call produces a unique per-email Message-ID."""
        h1 = build_threading_headers(_CANDIDATE, _COMPANY, _VACANCY)
        h2 = build_threading_headers(_CANDIDATE, _COMPANY, _VACANCY)
        assert h1["Message-ID"] != h2["Message-ID"]

    def test_two_replies_share_same_thread_root(self):
        """Both replies reference the identical thread root."""
        h1 = build_threading_headers(_CANDIDATE, _COMPANY, _VACANCY)
        h2 = build_threading_headers(_CANDIDATE, _COMPANY, _VACANCY)
        assert h1["In-Reply-To"] == h2["In-Reply-To"]

    def test_is_reply_defaults_to_true(self):
        """Default behaviour is to thread (is_reply=True)."""
        headers_default  = build_threading_headers(_CANDIDATE, _COMPANY, _VACANCY)
        headers_explicit = build_threading_headers(
            _CANDIDATE, _COMPANY, _VACANCY, is_reply=True
        )
        # Structure must be identical (message-id values differ but keys match)
        assert set(headers_default.keys()) == set(headers_explicit.keys())

    def test_none_vacancy_threads_correctly(self):
        """vacancy_id=None should still produce valid threading headers."""
        headers = build_threading_headers(_CANDIDATE, _COMPANY, vacancy_id=None)
        assert "Message-ID" in headers
        assert "In-Reply-To" in headers
        # In-Reply-To must match the deterministic root for None vacancy
        expected_root = get_thread_message_id(_CANDIDATE, _COMPANY, None)
        assert headers["In-Reply-To"] == expected_root
