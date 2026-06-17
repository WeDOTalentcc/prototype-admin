"""
Communication Consent Gate — LGPD fail-closed consent check for all outbound communication.

Maps communication channels to LGPD consent types and blocks sending when
consent is absent or revoked. Every check is logged for audit trail.

Usage:
    gate = CommunicationConsentGate(db)
    result = await gate.check(candidate_id, company_id, MessageChannel.EMAIL)
    if not result.allowed:
        # DO NOT SEND — return error to caller
"""
import logging
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.communication.repositories.optout_repository import OptoutRepository

from app.enums.communication import MessageChannel

logger = logging.getLogger(__name__)

# Map channel → LGPD consent_type in lgpd_consents table
_CHANNEL_TO_CONSENT_TYPE: dict[str, str] = {
    "email": "EMAIL_TRANSACTIONAL",
    "whatsapp": "WHATSAPP",
    "sms": "SMS",
}

# Marketing messages require separate consent type
_CHANNEL_TO_MARKETING_CONSENT: dict[str, str] = {
    "email": "EMAIL_MARKETING",
    "whatsapp": "WHATSAPP",
    "sms": "SMS",
}


@dataclass
class ConsentGateResult:
    allowed: bool
    reason: str  # "granted" | "absent" | "revoked" | "check_error"
    consent_type: str
    candidate_id: str
    channel: str


class CommunicationConsentGate:
    """
    Fail-closed consent gate for outbound communication.

    Checks lgpd_consents table directly (no caching) to ensure
    revocations take effect immediately.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check(
        self,
        candidate_id: str,
        company_id: str,
        channel: MessageChannel | str,
        is_marketing: bool = False,
    ) -> ConsentGateResult:
        """
        Check if we have consent to send to this candidate on this channel.

        Args:
            candidate_id: Target candidate
            company_id: Tenant
            channel: Communication channel (email, whatsapp, sms)
            is_marketing: True for marketing messages (stricter consent type)

        Returns:
            ConsentGateResult — allowed=False means DO NOT SEND.
        """
        channel_str = channel.value if isinstance(channel, MessageChannel) else channel
        consent_map = _CHANNEL_TO_MARKETING_CONSENT if is_marketing else _CHANNEL_TO_CONSENT_TYPE
        consent_type = consent_map.get(channel_str, "EMAIL_TRANSACTIONAL")

        try:
            repo = OptoutRepository(self.db)
            consent = await repo.get_lgpd_consent(
                candidate_id=candidate_id,
                company_id=company_id,
                consent_type=consent_type,
            )

            # Revoked → block
            if consent and not consent.consent_given:
                await self._audit(candidate_id, company_id, channel_str, consent_type, "blocked_revoked")
                return ConsentGateResult(
                    allowed=False,
                    reason="revoked",
                    consent_type=consent_type,
                    candidate_id=candidate_id,
                    channel=channel_str,
                )

            # Absent → block (fail-closed per LGPD Art. 7)
            if consent is None:
                await self._audit(candidate_id, company_id, channel_str, consent_type, "blocked_absent")
                return ConsentGateResult(
                    allowed=False,
                    reason="absent",
                    consent_type=consent_type,
                    candidate_id=candidate_id,
                    channel=channel_str,
                )

            # Granted → allow
            await self._audit(candidate_id, company_id, channel_str, consent_type, "allowed")
            return ConsentGateResult(
                allowed=True,
                reason="granted",
                consent_type=consent_type,
                candidate_id=candidate_id,
                channel=channel_str,
            )

        except Exception as e:
            # FAIL-CLOSED: error = block
            logger.error(
                "[ConsentGate] FAIL-CLOSED: check error candidate=%s channel=%s: %s",
                candidate_id, channel_str, e,
            )
            await self._audit(candidate_id, company_id, channel_str, consent_type, "blocked_error")
            return ConsentGateResult(
                allowed=False,
                reason="check_error",
                consent_type=consent_type,
                candidate_id=candidate_id,
                channel=channel_str,
            )

    async def check_batch(
        self,
        candidates: list[dict],
        company_id: str,
        channel: MessageChannel | str,
        is_marketing: bool = False,
    ) -> tuple[list[dict], list[dict], int]:
        """
        Check consent for a batch of candidates. Returns (allowed, blocked, skipped_count).

        Each candidate dict must have 'candidate_id' key.
        Logs aggregate counts for monitoring.
        """
        allowed = []
        blocked = []
        for candidate in candidates:
            cid = candidate.get("candidate_id", candidate.get("id", ""))
            if not cid:
                blocked.append(candidate)
                continue
            result = await self.check(cid, company_id, channel, is_marketing)
            if result.allowed:
                allowed.append(candidate)
            else:
                blocked.append(candidate)

        if blocked:
            logger.info(
                "[ConsentGate] Batch check: %d allowed, %d blocked (channel=%s, company=%s)",
                len(allowed), len(blocked),
                channel.value if isinstance(channel, MessageChannel) else channel,
                company_id,
            )
        return allowed, blocked, len(blocked)

    async def _audit(
        self,
        candidate_id: str,
        company_id: str,
        channel: str,
        consent_type: str,
        event: str,
    ) -> None:
        """Record consent check for audit trail (best-effort)."""
        try:
            # Use a lightweight log entry via the existing CommunicationLog or direct insert
            logger.info(
                "[ConsentGate] audit: candidate=%s company=%s channel=%s consent_type=%s result=%s",
                candidate_id, company_id, channel, consent_type, event,
            )
        except Exception:
            pass
