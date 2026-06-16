"""LGPD Art. 18: consent revocation MUST create a new audit record (INSERT)
rather than only updating the existing consent record.

LGPD Art. 18 grants data subjects the right to revoke consent. For accountability
(Art. 37 + ANPD enforcement), every revocation event must be traceable as a
discrete, immutable record — not a mutable overwrite of prior consent state.

This is a contract test. If it fails, the consent audit trail is broken.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime


# ---------------------------------------------------------------------------
# Helpers (same pattern as test_consent_hard_soft_flag.py)
# ---------------------------------------------------------------------------

def _make_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.flush = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    return db


def _make_result(consent_obj):
    result = MagicMock()
    result.scalar_one_or_none.return_value = consent_obj
    return result


def _make_existing_consent(consent_given: bool = True):
    """Return a mock LGPDConsent record representing existing DB state."""
    c = MagicMock()
    c.consent_given = consent_given
    c.consent_source = "web"
    c.updated_at = datetime.utcnow()
    c.consent_date = datetime.utcnow() if consent_given else None
    c.revoked_at = None
    c.revoked_by = None
    c.revoke_reason = None
    c.consent_text = None
    c.ip_address = None
    return c


# ---------------------------------------------------------------------------
# Contract tests
# ---------------------------------------------------------------------------

async def test_revocation_calls_audit_log_when_existing_record():
    """When revoking consent on an existing record, _record_audit_log must be called.

    LGPD Art. 18: every revocation must produce an immutable INSERT to consent_events,
    in addition to the current-state UPDATE on lgpd_consents.
    """
    db = _make_db()
    existing = _make_existing_consent(consent_given=True)
    db.execute.return_value = _make_result(existing)

    from app.shared.services.consent_checker_service import ConsentCheckerService
    svc = ConsentCheckerService(db=db)
    svc._record_audit_log = AsyncMock()

    await svc.register_consent(
        candidate_id="cand-uuid-123",
        company_id="co-uuid-456",
        consent_type="ai_screening",
        consent_given=False,
        consent_source="candidate_request",
    )

    assert svc._record_audit_log.called, (
        "LGPD Art. 18 VIOLATION: consent revocation must call _record_audit_log() "
        "to create an immutable audit INSERT in consent_events. "
        "Current implementation only UPDATEs the existing lgpd_consents record, "
        "destroying prior consent state history. "
        "Fix: call self._record_audit_log(..., event='consent_revoked') "
        "inside register_consent() when consent_given is False."
    )


async def test_revocation_audit_event_name_indicates_revocation():
    """The audit event recorded must use a name containing 'revok'."""
    db = _make_db()
    existing = _make_existing_consent(consent_given=True)
    db.execute.return_value = _make_result(existing)

    from app.shared.services.consent_checker_service import ConsentCheckerService
    svc = ConsentCheckerService(db=db)
    svc._record_audit_log = AsyncMock()

    await svc.register_consent(
        candidate_id="cand-uuid-123",
        company_id="co-uuid-456",
        consent_type="ai_screening",
        consent_given=False,
        consent_source="candidate_request",
    )

    svc._record_audit_log.assert_called_once()
    call_kwargs = svc._record_audit_log.call_args
    if call_kwargs.kwargs:
        event = call_kwargs.kwargs.get("event", "")
    else:
        event = call_kwargs.args[3] if len(call_kwargs.args) > 3 else ""

    assert "revok" in event.lower() or "revog" in event.lower(), (
        f"LGPD Art. 18: audit event must indicate revocation. Got: '{event}'. "
        "Expected something like 'consent_revoked'."
    )


async def test_grant_does_not_call_audit_log():
    """Granting consent (consent_given=True) must NOT call _record_audit_log.

    The revocation audit trail is the critical LGPD Art. 18 requirement.
    """
    db = _make_db()
    db.execute.return_value = _make_result(None)  # no existing record

    from app.shared.services.consent_checker_service import ConsentCheckerService
    svc = ConsentCheckerService(db=db)
    svc._record_audit_log = AsyncMock()
    svc.repo.add = AsyncMock(return_value=MagicMock())

    await svc.register_consent(
        candidate_id="cand-uuid-123",
        company_id="co-uuid-456",
        consent_type="ai_screening",
        consent_given=True,
        consent_source="web",
    )

    assert not svc._record_audit_log.called, (
        "Grant of consent must not trigger the revocation audit log path."
    )


async def test_revocation_existing_record_has_current_state_updated():
    """The existing lgpd_consents record must also be updated (current-state view).

    LGPD Art. 18 requires immutable audit trail (INSERT) AND current-state UPDATE.
    Both must happen on revocation.
    """
    db = _make_db()
    existing = _make_existing_consent(consent_given=True)
    db.execute.return_value = _make_result(existing)

    from app.shared.services.consent_checker_service import ConsentCheckerService
    svc = ConsentCheckerService(db=db)
    svc._record_audit_log = AsyncMock()

    await svc.register_consent(
        candidate_id="cand-uuid-123",
        company_id="co-uuid-456",
        consent_type="ai_screening",
        consent_given=False,
        consent_source="candidate_request",
    )

    assert existing.consent_given is False, (
        "Existing lgpd_consents record must reflect consent_given=False "
        "so that check_candidate_consent() sees the revoked state."
    )
    assert existing.revoked_at is not None, (
        "revoked_at must be set on the existing record."
    )
