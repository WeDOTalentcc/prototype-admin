"""UC-P1-13: Unified ConsentManager facade.

Orchestrates all consent operations through a single interface:
  - GranularConsentService for AI processing purposes (AI_SCORING, AI_VIDEO_ANALYSIS, etc.)
  - CommunicationConsentGate for outbound channels (email, whatsapp, sms)
  - ConsentRepository for recording and querying consent events (ConsentEvent/ConsentVersion models)

Usage:
    manager = ConsentManager(db)
    allowed = await manager.check_ai_consent(candidate_id, company_id, "AI_SCORING")
    await manager.revoke_consent(candidate_id, company_id, "AI_SCORING")

Note: Both check_* methods are fail-closed — they return False on any upstream error to
prevent processing without confirmed consent (LGPD Art.7/8 principle of consent).
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ConsentManager:
    """Unified facade for all consent operations.

    Consolidates the 4 independent consent artifacts into a single entry point:
    - GranularConsentService (7 AI purposes)
    - CommunicationConsentGate (email/whatsapp/sms)
    - ConsentRepository (ConsentEvent/ConsentVersion persistence)
    - (Legacy) ConsentCheckerService is bypassed — its LGPDConsent model is superseded.
    """

    def __init__(self, db: Any = None):
        from app.domains.lgpd.services.granular_consent_service import GranularConsentService
        from app.domains.communication.services.consent_gate import CommunicationConsentGate

        self._granular = GranularConsentService(db)
        self._gate = CommunicationConsentGate(db)
        self._repo = self._build_repo(db)

    def _build_repo(self, db: Any) -> Any:
        try:
            from app.repositories.consent_repository import ConsentRepository
            return ConsentRepository(db)
        except ImportError:
            logger.warning("[ConsentManager] ConsentRepository not available — using stub")
            return _StubConsentRepository()

    # ------------------------------------------------------------------
    # AI consent checks (LGPD Art.7 — base legal: consentimento)
    # ------------------------------------------------------------------

    async def check_ai_consent(
        self, candidate_id: str, company_id: str, purpose: str
    ) -> bool:
        """Check if candidate has consented to AI processing for a given purpose.

        Delegates to GranularConsentService which maps 7 distinct AI purposes.
        Fail-closed: returns False on any error (never assume consent).

        Purposes: AI_SCORING, AI_VIDEO_ANALYSIS, AI_COMPARISON, SCREENING,
                  DATA_RETENTION, MARKETING, ANALYTICS
        """
        try:
            return await self._granular.check_purpose(candidate_id, company_id, purpose)
        except Exception as exc:
            logger.error("[ConsentManager] check_ai_consent error for %s/%s/%s: %s",
                         candidate_id, company_id, purpose, exc)
            return False

    # ------------------------------------------------------------------
    # Communication consent checks
    # ------------------------------------------------------------------

    async def check_communication_consent(
        self, candidate_id: str, company_id: str, channel: str
    ) -> bool:
        """Check if candidate can be contacted via a given channel.

        Delegates to CommunicationConsentGate (email, whatsapp, sms).
        Fail-closed: returns False on any error.
        """
        try:
            result = await self._gate.check(candidate_id, company_id, channel)
            return result.allowed
        except Exception as exc:
            logger.error("[ConsentManager] check_communication_consent error for %s/%s/%s: %s",
                         candidate_id, company_id, channel, exc)
            return False

    # ------------------------------------------------------------------
    # Consent recording
    # ------------------------------------------------------------------

    async def record_consent(
        self, candidate_id: str, company_id: str, consent_type: str, granted: bool
    ) -> None:
        """Record a consent grant or withdrawal event in the ConsentEvent store."""
        try:
            await self._repo.record_consent(candidate_id, company_id, consent_type, granted)
        except Exception as exc:
            logger.error("[ConsentManager] record_consent error for %s/%s/%s: %s",
                         candidate_id, company_id, consent_type, exc)

    async def revoke_consent(
        self, candidate_id: str, company_id: str, consent_type: str
    ) -> None:
        """Revoke consent for a specific purpose (LGPD Art.8 §5 — revogação a qualquer momento)."""
        try:
            await self._repo.record_revocation(candidate_id, company_id, consent_type)
        except Exception as exc:
            logger.error("[ConsentManager] revoke_consent error for %s/%s/%s: %s",
                         candidate_id, company_id, consent_type, exc)


class _StubConsentRepository:
    """Fallback stub when ConsentRepository is unavailable (e.g., in unit tests without DB)."""

    async def record_consent(self, *args: Any, **kwargs: Any) -> None:
        pass

    async def record_revocation(self, *args: Any, **kwargs: Any) -> None:
        pass
