"""
CommunicationOptOutService — cross-channel opt-out synchronization (GAP-07-005).

LGPD principle: when a candidate opts out via ANY channel, ALL channels are opted out.
Re-consent (opt-in) does NOT auto-sync — LGPD requires explicit consent per channel.

This is the single source of truth for opt-out/opt-in operations. All callers
(email unsubscribe, WhatsApp STOP, API endpoints) MUST use this service instead
of writing CandidateOptOut records directly.
"""
from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.communication.repositories.communication_repository import (
    CommunicationRepository,
)
from app.domains.communication.services.communication_models import CandidateOptOut
from app.enums.communication import MessageChannel

logger = logging.getLogger(__name__)

# Channels that participate in cross-channel opt-out sync.
_SYNC_CHANNELS: tuple[MessageChannel, ...] = (MessageChannel.EMAIL, MessageChannel.WHATSAPP)


class CommunicationOptOutService:
    """
    Cross-channel opt-out service (LGPD Art. 18 V — revogação do consentimento).

    - revoke_all_channels: opt-out candidate from ALL channels (cross-sync).
    - reactivate_channel: opt-in for a SINGLE channel only (no auto-sync).
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def revoke_all_channels(
        self,
        *,
        company_id: str,
        candidate_id: str,
        source_channel: MessageChannel,
        reason: str,
        candidate_email: str | None = None,
        candidate_phone: str | None = None,
    ) -> dict:
        """
        Opt-out candidate from ALL communication channels.

        When a candidate opts out via any single channel (email unsubscribe link,
        WhatsApp STOP command, etc.), this method ensures all other channels are
        also marked as opted-out — the candidate clearly does not want to be
        contacted.

        Args:
            company_id: Multi-tenancy scope (required).
            candidate_id: The candidate revoking consent.
            source_channel: The channel through which the opt-out was initiated.
            reason: Human-readable reason for the opt-out.
            candidate_email: Optional email for the opt-out record.
            candidate_phone: Optional phone for the opt-out record.

        Returns:
            Dict with channels_opted_out list and channels_already_opted_out list.
        """
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")

        opted_out: list[str] = []
        already_opted_out: list[str] = []

        for channel in _SYNC_CHANNELS:
            via = f"cross_channel_sync:{source_channel.value}"
            try:
                await self._record_single_channel_optout(
                    company_id=company_id,
                    candidate_id=candidate_id,
                    channel=channel,
                    reason=reason,
                    opted_out_via=via,
                    candidate_email=candidate_email,
                    candidate_phone=candidate_phone,
                )
                opted_out.append(channel.value)
            except _AlreadyOptedOut:
                already_opted_out.append(channel.value)

        await self._db.commit()

        logger.info(
            "[OptOutSync] candidate=%s company=%s source=%s opted_out=%s already=%s",
            candidate_id,
            company_id,
            source_channel.value,
            opted_out,
            already_opted_out,
        )

        return {
            "success": True,
            "channels_opted_out": opted_out,
            "channels_already_opted_out": already_opted_out,
            "source_channel": source_channel.value,
        }

    async def reactivate_channel(
        self,
        *,
        company_id: str,
        candidate_id: str,
        channel: MessageChannel,
        reason: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict:
        """
        Re-consent for a SINGLE channel only.

        LGPD requires explicit consent per channel — opting back into email
        does NOT automatically opt back into WhatsApp. Each channel requires
        its own explicit re-consent action.
        """
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")

        await self._reactivate_single_channel(
            company_id=company_id,
            candidate_id=candidate_id,
            channel=channel,
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        await self._db.commit()

        logger.info(
            "[OptOutSync] reactivated candidate=%s company=%s channel=%s",
            candidate_id,
            company_id,
            channel.value,
        )

        return {"success": True, "channel_reactivated": channel.value}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _record_single_channel_optout(
        self,
        *,
        company_id: str,
        candidate_id: str,
        channel: MessageChannel,
        reason: str,
        opted_out_via: str,
        candidate_email: str | None = None,
        candidate_phone: str | None = None,
    ) -> None:
        """Record opt-out for a single channel. Raises _AlreadyOptedOut if exists."""
        repo = CommunicationRepository(self._db)
        existing = await repo.get_active_optout_for_channel(
            candidate_id=candidate_id,
            company_id=company_id,
            channel_value=channel.value,
        )
        if existing:
            raise _AlreadyOptedOut(channel.value)

        opt_out = CandidateOptOut(
            company_id=company_id,
            candidate_id=candidate_id,
            candidate_email=candidate_email,
            candidate_phone=candidate_phone,
            channel=channel.value,
            opt_out_type="cross_channel",
            opt_out_reason=reason,
            opted_out_via=opted_out_via,
        )
        self._db.add(opt_out)

    async def _reactivate_single_channel(
        self,
        *,
        company_id: str,
        candidate_id: str,
        channel: MessageChannel,
        reason: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Reactivate (un-opt-out) a single channel."""
        repo = CommunicationRepository(self._db)
        existing = await repo.get_active_optout_for_channel(
            candidate_id=candidate_id,
            company_id=company_id,
            channel_value=channel.value,
        )
        if existing:
            existing.is_active = False
            existing.reactivated_at = datetime.utcnow()
            existing.reactivated_by = reason
            existing.consent_given_at = datetime.utcnow()
            existing.consent_ip_address = ip_address
            existing.consent_user_agent = user_agent


class _AlreadyOptedOut(Exception):
    """Internal signal — channel already has active opt-out, skip."""

    def __init__(self, channel: str) -> None:
        self.channel = channel
        super().__init__(f"Already opted out: {channel}")
