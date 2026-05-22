"""
F-23 sensor (audit 2026-05-22 AUDIT_VOICE_SCREENING_ORCHESTRATOR.md):

Voice orchestrator MUST use purpose-specific consent — `purpose="voice_screening"`
— so that the audit trail (LGPD Art. 37 / Resolução CD/ANPD nº 2/2022) can
distinguish voice consent from chat / video / generic screening.

Pre-fix: voice path called `check_candidate_consent(purpose="ai_screening")`,
making voice consent indistinguishable from any other AI screening type in
the audit trail. F-23 hard-gates this at the source so future cross-domain
ConsentChecker refactor (separate ticket) can differentiate.

Decision Paulo 2026-05-22: voice consent gate hard agora + ticket separado
pra refactor cross-domain ConsentChecker forcing purpose-specific gates.
"""
from __future__ import annotations

import re
from pathlib import Path

VOICE_ORCH = Path(__file__).resolve().parents[2] / (
    "app/domains/voice/services/voice_screening_orchestrator.py"
)
CONSENT_SVC = Path(__file__).resolve().parents[2] / (
    "app/domains/lgpd/services/consent_checker_service.py"
)


def test_voice_uses_purpose_voice_screening():
    """F-23: voice orchestrator must call check_candidate_consent with
    purpose='voice_screening' — NOT the generic 'ai_screening' that
    other surfaces use.
    """
    src = VOICE_ORCH.read_text()
    # Look for the purpose= kwarg in the verify_consent / check_candidate_consent call
    m = re.search(
        r"check_candidate_consent\([^)]*?purpose\s*=\s*\"([^\"]+)\"",
        src,
        re.DOTALL,
    )
    assert m, "voice orchestrator must call check_candidate_consent with purpose= kwarg"
    purpose = m.group(1)
    assert purpose == "voice_screening", (
        f"F-23: voice purpose must be 'voice_screening' (got {purpose!r}). "
        f"Generic 'ai_screening' makes audit trail unable to distinguish "
        f"voice consent from other AI surfaces."
    )


def test_consent_checker_maps_voice_screening():
    """F-23: ConsentCheckerService.PURPOSE_TO_CONSENT_TYPE must accept
    'voice_screening' so the new purpose doesn't fall through to the
    silent default (which would mask the canonical change in audit logs).
    """
    src = CONSENT_SVC.read_text()
    assert "\"voice_screening\"" in src, (
        "ConsentCheckerService PURPOSE_TO_CONSENT_TYPE must list 'voice_screening'"
    )


def test_voice_orchestrator_documents_f23_purpose_choice():
    """F-23: a comment must point at the audit doc so the canonical
    intent of purpose='voice_screening' is not silently reverted later.
    """
    src = VOICE_ORCH.read_text()
    assert "F-23" in src or "voice_screening" in src, (
        "voice orchestrator should reference F-23 / 'voice_screening' canonical"
    )


def test_consent_checker_documents_voice_purpose():
    """F-23: ConsentCheckerService docstring should advertise voice_screening
    as a known purpose so other callers don't reintroduce 'ai_screening' for
    voice.
    """
    src = CONSENT_SVC.read_text()
    assert "voice_screening" in src.lower(), (
        "ConsentCheckerService source must reference 'voice_screening' "
        "(at minimum in PURPOSE_TO_CONSENT_TYPE; docstring is bonus)"
    )
