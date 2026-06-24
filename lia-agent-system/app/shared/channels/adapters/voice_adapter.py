"""
Voice channel adapter — canonical wiring for Twilio PSTN/VoIP + Gemini Live.

Sprint 3.4 (W4-1 V2): exposes ``VoiceCoreOrchestrator`` as a
``ChannelAdapter``, enabling any caller (Agent Studio custom agent,
marketplace recipe, communication dispatcher, fallback router) to start a
voice session via the canonical channel interface.

Unlike ``WhatsAppChannelAdapter`` (text payload, sync delivery), this adapter
starts an *asynchronous voice session* — the call rings the candidate, who
answers, talks, and disconnects. Therefore ``send()`` returns
``DeliveryStatus.QUEUED`` once the session is created; final delivery state
is observed via webhook/session repository (Twilio call SID or Gemini Live
session id).

Multi-tenancy: ``company_id`` is required and validated. ``recipient_contact``
accepts E.164 phone numbers (PSTN) or ``voip:<session_id>`` prefixed strings
(browser VoIP).

Plugins: the adapter accepts an optional list of ``VoiceCorePlugin`` instances
(see ``app.domains.voice.protocols.voice_core_plugin``) which are installed in
the orchestrator. Pass ``[WSIVoicePlugin()]`` for screening, omit for generic
voice (Agent Studio custom agents will receive plugin support in Sprint 3.5).
"""
import logging
import re
import uuid
from typing import Any

from app.shared.channels.channel_adapter import (
    ChannelAdapter,
    ChannelMessage,
    ChannelType,
    DeliveryResult,
    DeliveryStatus,
)
from app.domains.voice.repositories.voice_session_redis_repository import (
    get_voice_session_repository,
)

logger = logging.getLogger(__name__)

# Mapping canonical: VoiceScreeningSession.status / VoiceCoreSession.status
# -> DeliveryStatus pro consumer do ChannelAdapter interface.
#
# Cobre estados atuais (pending/initiated/ready/analyzing/completed/
# analysis_failed/failed/fallback) + estados forward-compat do canonical
# voice core (consent_pending/ringing/in_progress/active/finalized) que
# podem aparecer quando Sprint 3.5+ unifica core orchestrator.
_VOICE_STATUS_TO_DELIVERY: dict[str, DeliveryStatus] = {
    # current VoiceScreeningSession
    "pending": DeliveryStatus.QUEUED,
    "initiated": DeliveryStatus.SENT,
    "ready": DeliveryStatus.DELIVERED,
    "analyzing": DeliveryStatus.DELIVERED,
    "completed": DeliveryStatus.READ,
    "analysis_failed": DeliveryStatus.FAILED,
    "failed": DeliveryStatus.FAILED,
    "fallback": DeliveryStatus.FAILED,
    # forward-compat canonical voice core
    "consent_pending": DeliveryStatus.QUEUED,
    "ringing": DeliveryStatus.SENT,
    "in_progress": DeliveryStatus.DELIVERED,
    "active": DeliveryStatus.DELIVERED,
    "finalized": DeliveryStatus.READ,
}


class VoiceChannelAdapter(ChannelAdapter):
    """Canonical voice channel adapter — Twilio PSTN/VoIP + Gemini Live.

    Sprint 3.4 W4-1 V2. Consumes ``VoiceCoreOrchestrator`` (the generic core
    delivered in Sprint 3.2), not ``VoiceScreeningOrchestrator`` (which is a
    WSI-specific subclass kept for legacy callers).
    """

    channel_type = ChannelType.VOICE

    _PHONE_REGEX = re.compile(r"^\+?\d{10,15}$")
    _VOIP_PREFIX = "voip:"

    def __init__(self, plugins: list[Any] | None = None) -> None:
        """
        Args:
            plugins: optional list of ``VoiceCorePlugin`` instances installed
                in the underlying orchestrator. Default ``None`` selects
                generic mode (no domain-specific behaviour). Pass
                ``[WSIVoicePlugin()]`` to operate the adapter in WSI screening
                mode.
        """
        self._plugins = plugins or []

    def validate_contact(self, contact: str) -> bool:
        """Accept E.164 phone OR ``voip:<session_id>`` VoIP prefix."""
        if not contact:
            return False
        if contact.startswith(self._VOIP_PREFIX):
            # voip:<non-empty session id>
            return len(contact) > len(self._VOIP_PREFIX)
        cleaned = re.sub(r"[\s\-\(\)]", "", contact)
        return bool(self._PHONE_REGEX.match(cleaned))

    async def is_available(self, company_id: str | None = None, db: "Any | None" = None) -> bool:
        """At least one of Twilio (PSTN) or Gemini Live (VoIP) must be configured."""
        twilio_ok = False
        gemini_ok = False
        try:
            from app.domains.communication.services.twilio_voice_service import (
                twilio_voice_service,
            )
            twilio_ok = bool(twilio_voice_service.is_configured)
        except Exception as exc:
            logger.warning("[VOICE_ADAPTER] twilio probe failed: %s", exc)
        try:
            from app.domains.voice.services.gemini_live_audio_service import (
                get_gemini_live_service,
            )
            gemini_ok = bool(get_gemini_live_service().is_available())
        except Exception as exc:
            logger.warning("[VOICE_ADAPTER] gemini-live probe failed: %s", exc)
        return twilio_ok or gemini_ok

    async def send(self, message: ChannelMessage) -> DeliveryResult:
        """Start a voice session via ``VoiceCoreOrchestrator``.

        ``ChannelMessage`` fields consumed:

        * ``recipient_contact`` — phone (E.164) or ``voip:<session_id>``.
        * ``recipient_id`` — propagated as ``candidate_id``.
        * ``recipient_name`` — propagated as ``candidate_name``.
        * ``company_id`` — required (multi-tenancy).
        * ``metadata`` — optional dict; ``job_id`` / ``job_title`` are
          forwarded to the orchestrator. ``candidate_id`` / ``candidate_name``
          inside metadata override the top-level fields when provided.
        * ``vacancy_id`` — fallback for ``job_id`` when metadata is absent.

        Returns ``DeliveryResult`` with ``DeliveryStatus.QUEUED`` on success
        (the call is asynchronous — delivery state evolves via webhook).
        """
        message_id = str(uuid.uuid4())

        if not self.validate_contact(message.recipient_contact):
            return DeliveryResult(
                success=False,
                channel=ChannelType.VOICE,
                message_id=message_id,
                status=DeliveryStatus.FAILED,
                error=f"Invalid contact: {message.recipient_contact!r}",
            )

        if not message.company_id:
            return DeliveryResult(
                success=False,
                channel=ChannelType.VOICE,
                message_id=message_id,
                status=DeliveryStatus.FAILED,
                error="company_id required (multi-tenancy)",
            )

        meta = message.metadata or {}
        candidate_id = meta.get("candidate_id") or message.recipient_id or ""
        candidate_name = meta.get("candidate_name") or message.recipient_name or ""
        job_id = meta.get("job_id") or message.vacancy_id
        job_title = meta.get("job_title") or message.subject or ""
        language = meta.get("language", "pt-BR")

        is_voip = message.recipient_contact.startswith(self._VOIP_PREFIX)

        try:
            # Sprint 3.4: import VoiceCoreOrchestrator from canonical module path.
            # The class is currently re-exported from voice_screening_orchestrator.py
            # for backward compat with Sprint 3.2-3.3 callers.
            from app.domains.voice.services.voice_screening_orchestrator import (
                VoiceCoreOrchestrator,
            )

            orchestrator = VoiceCoreOrchestrator(plugins=self._plugins)

            if is_voip:
                session = await orchestrator.initiate_voip_session(
                    candidate_id=candidate_id,
                    candidate_name=candidate_name,
                    job_title=job_title,
                    company_id=message.company_id,
                    job_id=job_id,
                    language=language,
                )
            else:
                session = await orchestrator.initiate_call(
                    candidate_id=candidate_id,
                    candidate_name=candidate_name,
                    phone_number=message.recipient_contact,
                    job_title=job_title,
                    company_id=message.company_id,
                    job_id=job_id,
                    language=language,
                )

            # Map orchestrator status → DeliveryStatus
            session_status = getattr(session, "status", "queued")
            if session_status == "fallback":
                # Provider unavailable — surface failure so ChannelRouter
                # can attempt fallback channels (chat/WhatsApp).
                return DeliveryResult(
                    success=False,
                    channel=ChannelType.VOICE,
                    message_id=message_id,
                    status=DeliveryStatus.FAILED,
                    error="voice provider unavailable (twilio/gemini-live fallback)",
                    metadata={
                        "session_id": session.session_id,
                        "is_voip": is_voip,
                    },
                )

            return DeliveryResult(
                success=True,
                channel=ChannelType.VOICE,
                message_id=message_id,
                status=DeliveryStatus.QUEUED,
                provider_id=session.session_id,
                metadata={
                    "session_id": session.session_id,
                    "call_sid": getattr(session, "call_sid", None),
                    "voice_provider": getattr(session, "voice_provider", None),
                    "is_voip": is_voip,
                },
            )

        except Exception as exc:
            logger.error(
                "[VOICE_ADAPTER] send failed for company=%s: %s",
                message.company_id, exc, exc_info=True,
            )
            return DeliveryResult(
                success=False,
                channel=ChannelType.VOICE,
                message_id=message_id,
                status=DeliveryStatus.FAILED,
                error=str(exc),
            )

    async def check_status(self, message_id: str) -> DeliveryStatus:
        """Look up session delivery status via ``VoiceSessionRedisRepository``.

        ``message_id`` is the session_id returned by :meth:`send`. Resolves
        company_id via the reverse index (never trusts external input -
        preserves multi-tenancy invariant), loads the session state, and maps
        the internal ``status`` field to a canonical ``DeliveryStatus``.

        Mapping (see ``_VOICE_STATUS_TO_DELIVERY`` for full table):
            - pending/consent_pending -> QUEUED
            - initiated/ringing       -> SENT
            - ready/analyzing/in_progress/active -> DELIVERED
            - completed/finalized     -> READ
            - failed/analysis_failed/fallback -> FAILED

        Graceful degradation:
            - empty/None message_id -> FAILED (no Redis hit)
            - session expired or not found -> FAILED
            - unknown internal status -> QUEUED (defensive default,
              avoids masking propagation bugs by hiding the session)
            - any Redis exception -> FAILED + log warning

        P1 backlog (was Sprint 3.4 placeholder retornando QUEUED sempre).
        """
        if not message_id:
            return DeliveryStatus.FAILED
        try:
            repo = get_voice_session_repository()
            company_id = await repo.find_company_id_for_session(
                session_id=message_id,
            )
            if not company_id:
                # Session expired (TTL 4h) or unknown id - treat as terminal failure
                # so caller stops polling.
                return DeliveryStatus.FAILED

            state = await repo.load_session_state(
                company_id=company_id,
                session_id=message_id,
            )
            if state is None:
                # Race: reverse-index still up, primary state TTL'd out.
                return DeliveryStatus.FAILED

            internal = state.get("status")
            if internal is None:
                # Malformed state (missing status key). Defensive default - do
                # not return FAILED (would mask serialization bug downstream).
                return DeliveryStatus.QUEUED
            return _VOICE_STATUS_TO_DELIVERY.get(internal, DeliveryStatus.QUEUED)
        except Exception as exc:
            logger.warning(
                "[VOICE_ADAPTER] check_status failed for message_id=%s: %s",
                message_id,
                exc,
                exc_info=True,
            )
            return DeliveryStatus.FAILED
