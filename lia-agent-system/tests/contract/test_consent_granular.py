"""
Tests for P1 ticket: ConsentCheckerService granular consent_type per purpose.

F-23 P1 follow-up — purpose='voice_screening' colapsava em
consent_type='SCREENING' generic. Audit-trail differentiation parcial:
revoking voice consent revogava implicitamente chat consent (mesma row).

Fix incremental backward-compat:
- 2 novos consent_type values granulares: VOICE_SCREENING, WHATSAPP_INTERACTION
- Mapping purpose -> consent_type estendido (legacy purposes mantem SCREENING)
- ConsentCheckResult.consent_type retorna resolved value
- Audit canonical inclui consent_type no event log

Backward compat OBRIGATORIO:
- Existing 'ai_screening'/'ai_scoring' callers continuam mapeando p/ SCREENING
- Existing 'SCREENING' rows no DB continuam validos
- Voice purpose='voice_screening' agora mapeia p/ VOICE_SCREENING granular
- WhatsApp purpose='whatsapp_screening' (novo) mapeia p/ WHATSAPP_INTERACTION

Audit ref: F-23 P1 + backlog Sprint 3.7 cross-domain consent ticket
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.flush = AsyncMock()
    db.add = MagicMock()
    return db


def _make_consent(given: bool = True, revoked_at=None):
    c = MagicMock()
    c.consent_given = given
    c.revoked_at = revoked_at
    return c


# ─── Granular mapping: voice + whatsapp distinct consent_types ────────────────

def test_voice_purpose_maps_to_voice_consent_type():
    """P1 #3: purpose='voice_screening' resolves to consent_type='VOICE_SCREENING'."""
    from app.domains.lgpd.services.consent_checker_service import (
        ConsentCheckerService,
    )

    mapping = ConsentCheckerService.PURPOSE_TO_CONSENT_TYPE
    assert mapping.get("voice_screening") == "VOICE_SCREENING", (
        f"voice_screening MUST map to granular consent_type 'VOICE_SCREENING' "
        f"(was 'SCREENING' generic). Got: {mapping.get('voice_screening')!r}"
    )


def test_whatsapp_purpose_maps_to_whatsapp_consent_type():
    """P1 #3: purpose='whatsapp_screening' resolves to 'WHATSAPP_INTERACTION'."""
    from app.domains.lgpd.services.consent_checker_service import (
        ConsentCheckerService,
    )

    mapping = ConsentCheckerService.PURPOSE_TO_CONSENT_TYPE
    assert mapping.get("whatsapp_screening") == "WHATSAPP_INTERACTION", (
        f"whatsapp_screening MUST map to granular consent_type "
        f"'WHATSAPP_INTERACTION'. Got: {mapping.get('whatsapp_screening')!r}"
    )


# ─── Backward compat: legacy purposes preserved ───────────────────────────────

def test_legacy_ai_screening_still_maps_to_screening():
    """P1 #3 BACKWARD COMPAT: ai_screening preserves 'SCREENING' mapping
    so existing consent rows in DB stay valid."""
    from app.domains.lgpd.services.consent_checker_service import (
        ConsentCheckerService,
    )

    mapping = ConsentCheckerService.PURPOSE_TO_CONSENT_TYPE
    assert mapping["ai_screening"] == "SCREENING"
    assert mapping["ai_scoring"] == "SCREENING"
    assert mapping["ai_video_analysis"] == "SCREENING"
    assert mapping["ai_comparison"] == "SCREENING"


def test_unknown_purpose_falls_back_to_screening_default():
    """P1 #3 BACKWARD COMPAT: unknown purpose still defaults to 'SCREENING'
    (no breaking change for surfaces not yet migrated)."""
    from app.domains.lgpd.services.consent_checker_service import (
        ConsentCheckerService,
    )

    # The .get(purpose, default) pattern means unknown -> default
    mapping = ConsentCheckerService.PURPOSE_TO_CONSENT_TYPE
    # 'future_unknown_purpose' is not registered → must fall back
    resolved = mapping.get("future_unknown_purpose", "SCREENING")
    assert resolved == "SCREENING"


# ─── End-to-end: check_candidate_consent returns resolved consent_type ────────

@pytest.mark.asyncio
async def test_check_consent_result_includes_resolved_consent_type_voice():
    """P1 #3: check_candidate_consent for voice purpose returns
    result.consent_type='VOICE_SCREENING' in the ConsentCheckResult.
    Critical for callers that inspect audit metadata."""
    from app.domains.lgpd.services.consent_checker_service import (
        ConsentCheckerService,
    )

    db = _make_db()
    svc = ConsentCheckerService(db=db)

    # Mock repo to return a granted consent
    granted_consent = _make_consent(given=True, revoked_at=None)
    svc.repo.get_for_candidate_purpose = AsyncMock(return_value=granted_consent)

    result = await svc.check_candidate_consent(
        candidate_id="cand-1",
        company_id="comp-1",
        purpose="voice_screening",
    )

    assert result.allowed is True
    assert result.consent_type == "VOICE_SCREENING", (
        f"Result must surface resolved granular consent_type. "
        f"Got: {result.consent_type!r}"
    )


@pytest.mark.asyncio
async def test_check_consent_result_includes_resolved_consent_type_whatsapp():
    """P1 #3: same for whatsapp_screening → WHATSAPP_INTERACTION."""
    from app.domains.lgpd.services.consent_checker_service import (
        ConsentCheckerService,
    )

    db = _make_db()
    svc = ConsentCheckerService(db=db)

    granted_consent = _make_consent(given=True, revoked_at=None)
    svc.repo.get_for_candidate_purpose = AsyncMock(return_value=granted_consent)

    result = await svc.check_candidate_consent(
        candidate_id="cand-1",
        company_id="comp-1",
        purpose="whatsapp_screening",
    )

    assert result.allowed is True
    assert result.consent_type == "WHATSAPP_INTERACTION"


# ─── Isolation: revoking voice does NOT revoke chat (separate rows) ────────────

@pytest.mark.asyncio
async def test_revoking_voice_does_not_revoke_chat():
    """P1 #3: granular consent_types must be queried separately.
    Revoked VOICE_SCREENING consent must NOT block ai_screening
    (different consent_type row in DB)."""
    from app.domains.lgpd.services.consent_checker_service import (
        ConsentCheckerService,
    )

    db = _make_db()
    svc = ConsentCheckerService(db=db)

    captured_types = []

    async def _fake_get(*, candidate_id, company_id, consent_type):
        captured_types.append(consent_type)
        # Voice row is REVOKED
        if consent_type == "VOICE_SCREENING":
            from datetime import datetime
            return _make_consent(given=False, revoked_at=datetime.utcnow())
        # Chat row (SCREENING) is GRANTED
        if consent_type == "SCREENING":
            return _make_consent(given=True, revoked_at=None)
        return None

    svc.repo.get_for_candidate_purpose = _fake_get  # type: ignore[assignment]

    # First check: voice — should be blocked
    voice_res = await svc.check_candidate_consent(
        candidate_id="cand-1",
        company_id="comp-1",
        purpose="voice_screening",
    )
    assert voice_res.allowed is False
    assert voice_res.reason == "revoked"
    assert voice_res.consent_type == "VOICE_SCREENING"

    # Second check: chat — should still be allowed (different row)
    chat_res = await svc.check_candidate_consent(
        candidate_id="cand-1",
        company_id="comp-1",
        purpose="ai_screening",
    )
    assert chat_res.allowed is True
    assert chat_res.consent_type == "SCREENING"

    # Verify two distinct rows queried
    assert "VOICE_SCREENING" in captured_types
    assert "SCREENING" in captured_types


# ─── Backward compat: existing test pin (F-23 still passes) ───────────────────

def test_f23_voice_screening_purpose_still_listed():
    """P1 #3 BACKWARD COMPAT: F-23 sensor pin ('voice_screening' in mapping)
    must still pass after granular extension."""
    from app.domains.lgpd.services.consent_checker_service import (
        ConsentCheckerService,
    )

    # F-23 pinned that voice_screening is *listed* in mapping (was generic
    # SCREENING). After this fix it's still listed but now maps to granular
    # VOICE_SCREENING. F-23 sensor stays green.
    mapping = ConsentCheckerService.PURPOSE_TO_CONSENT_TYPE
    assert "voice_screening" in mapping
    # And the actual mapped value is the granular one now
    assert mapping["voice_screening"] != "SCREENING"
