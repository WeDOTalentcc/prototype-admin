# GAP-07-008: RFC 2822 email threading headers (In-Reply-To / References)
"""
Email threading utilities for RFC 2822 compliance.

Provides deterministic Message-ID generation so that all emails
sent to the same candidate+company+vacancy are grouped into a single
thread by email clients (Gmail, Outlook, Apple Mail).

Design decisions:
- Thread root ID is DETERMINISTIC (sha256 of composite key) — no DB lookup needed.
- Per-message ID is UNIQUE (uuid4) — RFC 2822 §3.6.4 requirement.
- First email in a thread: only Message-ID header is set.
- Subsequent emails:      Message-ID + In-Reply-To + References headers.
- Callers are responsible for knowing whether an email is the "first"
  in a thread. The helper `build_threading_headers` accepts an
  `is_reply` flag (default: True) — set it to False for first emails
  when the caller has explicit knowledge, or leave True to always
  thread (Gmail/Outlook deduplicate correctly even if In-Reply-To
  points to an as-yet-unsent thread root).

The deterministic-thread-root approach (no DB) is intentional:
  - Zero migration required.
  - Idempotent: same inputs always produce the same thread root.
  - Caveat: if vacancy_id is None, all "general" emails to a candidate
    from the same company share one thread — acceptable for support/
    onboarding flows.
"""
import hashlib
from uuid import uuid4


_DOMAIN = "wedotalent.cc"


def get_thread_message_id(
    candidate_id: str,
    company_id: str,
    vacancy_id: str | None = None,
) -> str:
    """
    Return a deterministic Message-ID that acts as the thread root
    for all emails sent to a given candidate+company+vacancy combination.

    The same arguments always produce the same ID, so callers do not
    need to persist anything to reconstruct the thread root.

    Args:
        candidate_id: Candidate UUID or legacy integer ID (as string).
        company_id:   Tenant company UUID.
        vacancy_id:   Job vacancy UUID, or None for general communications.

    Returns:
        RFC 2822 Message-ID string, e.g.
        ``<thread-a3f1...@wedotalent.cc>``
    """
    key = f"{company_id}:{candidate_id}:{vacancy_id or 'general'}"
    digest = hashlib.sha256(key.encode()).hexdigest()[:32]
    return f"<thread-{digest}@{_DOMAIN}>"


def get_email_message_id() -> str:
    """
    Return a unique Message-ID for a single outgoing email.

    Each call generates a new UUID4-based ID, satisfying the RFC 2822
    requirement that every message in a thread has a distinct Message-ID.

    Returns:
        RFC 2822 Message-ID string, e.g.
        ``<550e8400-e29b-...@wedotalent.cc>``
    """
    return f"<{uuid4()}@{_DOMAIN}>"


def build_threading_headers(
    candidate_id: str,
    company_id: str,
    vacancy_id: str | None = None,
    is_reply: bool = True,
) -> dict[str, str]:
    """
    Build the RFC 2822 threading headers for an outgoing email.

    Args:
        candidate_id: Candidate UUID or legacy ID string.
        company_id:   Tenant UUID.
        vacancy_id:   Job vacancy UUID, or None for general comms.
        is_reply:     If True (default), add In-Reply-To and References
                      pointing to the thread root. Set to False only for
                      the very first email in a thread when you want a
                      clean thread start (no In-Reply-To).

    Returns:
        Dict of header name → value pairs ready to merge into the
        provider's ``headers`` argument.

    Example::

        headers = build_threading_headers(
            candidate_id="cand-123",
            company_id="co-456",
            vacancy_id="vac-789",
        )
        # {'Message-ID': '<uuid@wedotalent.cc>',
        #  'In-Reply-To': '<thread-abc...@wedotalent.cc>',
        #  'References': '<thread-abc...@wedotalent.cc>'}
    """
    message_id = get_email_message_id()
    headers: dict[str, str] = {"Message-ID": message_id}

    if is_reply:
        thread_root = get_thread_message_id(candidate_id, company_id, vacancy_id)
        headers["In-Reply-To"] = thread_root
        headers["References"] = thread_root

    return headers
