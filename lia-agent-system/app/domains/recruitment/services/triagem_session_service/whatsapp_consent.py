"""triagem_whatsapp_consent_service.py — Phase 1b WhatsApp consent flow for triagem.

After the initial screening invitation (send_screening_invitation), before the triagem
starts, the candidate must give explicit LGPD consent via WhatsApp.

Flow:
  [invited] → send_consent_request() → [awaiting_consent]
  candidate replies SIM → create ConsentRecord + advance → [started]
  candidate replies NÃO → send decline message → [consent_declined]

This service is the producer for the consent gate in the WhatsApp triagem channel.
Callers: automation_handlers.py (after queue promotion) and the WhatsApp webhook
         response handler (when session is in awaiting_consent state).
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.triagem import (
    TRIAGEM_STATUS_AWAITING_CONSENT,
    TRIAGEM_STATUS_CONSENT_DECLINED,
    TRIAGEM_STATUS_STARTED,
    TriagemSession,
)

from app.domains.recruitment.repositories.triagem_session_repository import (
    TriagemSessionRepository,
)
from lia_models.observability import ConsentRecord
from app.templates.communication_templates import WhatsAppTemplates

logger = logging.getLogger(__name__)

# Normalised SIM/NÃO sets (WhatsApp free-text is noisy)
_SIM_RESPONSES = frozenset(["SIM", "S", "YES", "Y", "ACEITO", "CONCORDO", "OK", "QUERO"])
_NAO_RESPONSES = frozenset(["NAO", "NÃO", "N", "NO", "RECUSO", "NAO ACEITO", "NENHUM"])

CONSENT_VERSION = "1.1"
CONSENT_LEGAL_BASIS = "Art. 7º, I — LGPD"  # Art. 7º, I — LGPD


class TriagemWhatsAppConsentService:
    """Manages the LGPD consent request / response cycle for WhatsApp triagem sessions."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def send_consent_request(
        self,
        session: TriagemSession,
        whatsapp_provider,
        is_affirmative: bool = False,
        affirmative_type: str | None = None,
    ) -> dict[str, Any]:
        """Send the LGPD consent request message and transition session to AWAITING_CONSENT.

        Args:
            session: The TriagemSession ORM object (must be in 'invited' status).
            whatsapp_provider: An async WhatsApp provider with send_text_message(to, text).
            is_affirmative: Whether the vacancy is an affirmative action vaga.
            affirmative_type: Type label for affirmative action ('pcd'|'racial'|'gender').

        Returns:
            dict with keys: success, status, error (on failure).
        """
        job_title = session.job_title or "a vaga"
        phone = self._get_phone(session)
        if not phone:
            logger.warning(
                "[TriagemConsent] session %s has no candidate phone — cannot send consent request",
                session.id,
            )
            return {"success": False, "error": "no_phone"}

        consent_text = WhatsAppTemplates.consent_request(
            job_title=job_title,
            is_affirmative=is_affirmative,
            affirmative_type=affirmative_type,
        )

        try:
            result = await whatsapp_provider.send_text_message(phone, consent_text)
        except Exception as exc:
            logger.error(
                "[TriagemConsent] Failed to send consent request for session %s: %s",
                session.id, exc, exc_info=True,
            )
            return {"success": False, "error": str(exc)}

        if getattr(result, "success", False) or (hasattr(result, "error") and not result.error):
            session.status = TRIAGEM_STATUS_AWAITING_CONSENT
            # Store consent_text in metadata so we can attach it to the ConsentRecord later
            meta = dict(session.metadata_json or {})
            meta["whatsapp_consent"] = {
                "consent_text": consent_text,
                "consent_version": CONSENT_VERSION,
                "sent_at": datetime.utcnow().isoformat(),
                "is_affirmative": is_affirmative,
                "affirmative_type": affirmative_type,
            }
            session.metadata_json = meta
            await self._db.flush()
            logger.info("[TriagemConsent] Consent request sent, session %s → awaiting_consent", session.id)
            return {"success": True, "status": TRIAGEM_STATUS_AWAITING_CONSENT}
        else:
            err = getattr(result, "error", "unknown send error")
            logger.error("[TriagemConsent] WhatsApp send failed for session %s: %s", session.id, err)
            return {"success": False, "error": err}

    async def handle_consent_response(
        self,
        session: TriagemSession,
        message_body: str,
        whatsapp_provider,
        candidate_phone: str,
    ) -> dict[str, Any]:
        """Process candidate SIM/NÃO response to the consent request.

        - SIM: creates ConsentRecord, transitions session to 'started'.
        - NÃO: sends closing message, transitions session to 'consent_declined'.

        Returns dict with keys: consent_given (bool), status, error (on failure).
        """
        normalised = message_body.strip().upper()

        if normalised in _SIM_RESPONSES:
            return await self._handle_sim(session, whatsapp_provider, candidate_phone)
        elif normalised in _NAO_RESPONSES:
            return await self._handle_nao(session, whatsapp_provider, candidate_phone)
        else:
            # Unrecognised — prompt again
            logger.info(
                "[TriagemConsent] Unrecognised response '%s' for session %s", message_body, session.id
            )
            job_title = session.job_title or "a vaga"
            try:
                await whatsapp_provider.send_text_message(
                    candidate_phone,
                    f"Desculpe, não entendi. Responda *SIM* para consentir e participar da triagem de "
                    f"*{job_title}*, ou *NÃO* para recusar.",
                )
            except Exception as exc:
                logger.warning("[TriagemConsent] Could not re-prompt candidate: %s", exc)
            return {"consent_given": None, "status": TRIAGEM_STATUS_AWAITING_CONSENT}

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _handle_sim(
        self,
        session: TriagemSession,
        whatsapp_provider,
        candidate_phone: str,
    ) -> dict[str, Any]:
        """Candidate consented — create ConsentRecord and advance to 'started'."""
        meta = dict(session.metadata_json or {})
        consent_meta = meta.get("whatsapp_consent", {})
        consent_text = consent_meta.get("consent_text", "")
        consent_version = consent_meta.get("consent_version", CONSENT_VERSION)

        # Build ConsentRecord (append-only — no mutation after creation)
        vaga_id = None
        try:
            if session.job_id:
                vaga_id = UUID(str(session.job_id))
        except (ValueError, AttributeError):
            pass

        candidate_id_uuid = None
        try:
            candidate_id_uuid = UUID(str(session.candidate_id))
        except (ValueError, AttributeError):
            pass

        company_id_uuid = None
        try:
            company_id_uuid = UUID(str(session.company_id))
        except (ValueError, AttributeError):
            pass

        now = datetime.utcnow()
        consent_record = ConsentRecord(
            id=uuid.uuid4(),
            company_id=company_id_uuid,
            candidate_id=candidate_id_uuid,
            consent_type="consentimento_audio",
            version=consent_version,
            canal="whatsapp",
            vaga_id=vaga_id,
            processo_id=session.id,
            granted_at=now,
            is_active=True,
            legal_basis=CONSENT_LEGAL_BASIS,
            consent_text=consent_text,
            versao_disclaimer=consent_version,
            source="whatsapp_triagem",
        )
        self._db.add(consent_record)

        # Advance session
        session.status = TRIAGEM_STATUS_STARTED
        session.started_at = now

        # Record in metadata
        meta["whatsapp_consent"]["sim_received_at"] = now.isoformat()
        meta["whatsapp_consent"]["consent_record_id"] = str(consent_record.id)
        session.metadata_json = meta

        await self._db.flush()

        # Confirm to candidate
        job_title = session.job_title or "a vaga"
        try:
            await whatsapp_provider.send_text_message(
                candidate_phone,
                WhatsAppTemplates.screening_start(
                    candidate_name=session.candidate_name or "Candidato",
                    job_title=job_title,
                ),
            )
        except Exception as exc:
            logger.warning("[TriagemConsent] Could not send screening_start after consent: %s", exc)

        logger.info(
            "[TriagemConsent] Consent granted, ConsentRecord %s created, session %s → started",
            consent_record.id, session.id,
        )
        return {
            "consent_given": True,
            "status": TRIAGEM_STATUS_STARTED,
            "consent_record_id": str(consent_record.id),
        }

    async def _handle_nao(
        self,
        session: TriagemSession,
        whatsapp_provider,
        candidate_phone: str,
    ) -> dict[str, Any]:
        """Candidate declined consent — record and close gracefully."""
        now = datetime.utcnow()
        meta = dict(session.metadata_json or {})
        meta.setdefault("whatsapp_consent", {})["nao_received_at"] = now.isoformat()
        session.metadata_json = meta
        session.status = TRIAGEM_STATUS_CONSENT_DECLINED

        await self._db.flush()

        try:
            await whatsapp_provider.send_text_message(
                candidate_phone,
                "Entendemos! Sua decisão foi registrada. "
                "Você pode solicitar acesso aos seus dados pelo e-mail "
                "privacidadededados@wedotalent.cc.",
            )
        except Exception as exc:
            logger.warning("[TriagemConsent] Could not send decline ack: %s", exc)

        logger.info("[TriagemConsent] Consent declined, session %s → consent_declined", session.id)
        return {"consent_given": False, "status": TRIAGEM_STATUS_CONSENT_DECLINED}

    @staticmethod
    def _get_phone(session: TriagemSession) -> str | None:
        """Try to extract candidate phone from session metadata."""
        meta = session.metadata_json or {}
        return (
            meta.get("candidate_phone")
            or meta.get("phone")
            or meta.get("whatsapp_phone")
        )


async def maybe_send_expiry_reminder(
    session: TriagemSession,
    whatsapp_provider,
    candidate_phone: str,
    hours_threshold: int = 4,
) -> bool:
    """Send a pre-expiry reminder if session is AWAITING_CONSENT and expiry < hours_threshold away.

    Returns True if a reminder was sent, False otherwise.
    Called from the expiry scan routine before marking a session as expired.
    """
    if session.status != TRIAGEM_STATUS_AWAITING_CONSENT:
        return False

    if not session.expires_at:
        return False

    hours_left = (session.expires_at - datetime.utcnow()).total_seconds() / 3600
    if hours_left > hours_threshold or hours_left <= 0:
        return False

    # Guard: only send once per session
    meta = dict(session.metadata_json or {})
    consent_meta = meta.get("whatsapp_consent", {})
    if consent_meta.get("reminder_sent"):
        return False

    job_title = session.job_title or "a vaga"
    try:
        await whatsapp_provider.send_text_message(
            candidate_phone,
            WhatsAppTemplates.expiry_reminder(
                job_title=job_title,
                hours_left=int(max(1, hours_left)),
            ),
        )
        meta.setdefault("whatsapp_consent", {})["reminder_sent"] = datetime.utcnow().isoformat()
        session.metadata_json = meta
        logger.info(
            "[TriagemConsent] Expiry reminder sent for session %s (%.1fh left)", session.id, hours_left
        )
        return True
    except Exception as exc:
        logger.warning("[TriagemConsent] Could not send expiry reminder for session %s: %s", session.id, exc)
        return False
