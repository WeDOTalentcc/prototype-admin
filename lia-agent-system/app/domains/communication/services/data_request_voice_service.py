"""
Data Request Voice Collection Service (Fase 2 — plugin wired).

Service for managing data collection via an outbound LIA voice call.
Mirrors the structure of DataRequestWhatsAppService:
- parameterless constructor (db session passed per-method);
- ``start_collection`` resolves the pending fields, builds the canonical voice
  collection script (``voice_collection_script.build_collection_script``), and
  hands off to a voice orchestrator (constructed WITH the
  ``DataCollectionVoicePlugin``) to place the call.

FASE 2 (this file): start_collection builds the script AND constructs a
``VoiceCoreOrchestrator(plugins=[DataCollectionVoicePlugin(fields=...)])`` so the
live call collects THESE DataRequest fields (instead of WSI screening
questions). The plugin owns the conversational flow: it asks each
voice-collectable field in order and, at finalize, extracts + normalizes the
spoken answers. Because the plugin reports ``plugin_name == 'data_collection'``
(NOT ``'wsi_screening'``), the orchestrator's Fase 0.5 gate correctly does NOT
run the WSI scoring path on these calls.

⚠️ FASE 4 (still deferred): persistence of the plugin's per-field extracted
answers back into the DataRequest, plus in-call LGPD consent, is wired in
Fase 4. Fase 2 places the call with the collection plugin; the plugin returns a
structured ``collected``/``needs_followup`` dict at finalize but does NOT yet
persist it.

Anti-silent-fallback (CLAUDE.md REGRA 4): start_collection NEVER reports a fake
"completed" collection. It returns an explicit status:
- ``voice_collection_initiated``  → orchestrator placed the call (status=initiated)
- ``voice_collection_fallback``   → Twilio unavailable / circuit open → route to
                                    chat/WhatsApp (orchestrator status=fallback/failed)
- ``voice_collection_prepared``   → script built, but no live call placed (e.g.
                                    orchestrator wiring deferred to Fase 2)

IMPORTANT — lazy import: the voice orchestrator AND the DataCollectionVoicePlugin
are imported INSIDE ``start_collection``, never at module top. Importing
``voice_screening_orchestrator`` at module load is heavy (drops the Replit SSH
session in test/CI). Lazy import keeps this module cheap to import and lets
tests mock the orchestrator/plugin without triggering the real import.

Multi-tenancy: ``company_id`` is read from the persisted DataRequest row
(authoritative, never from a request payload), mirroring the WhatsApp service.
"""
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.communication.services.voice_collection_script import (
    build_collection_script,
    portal_only_fields,
)
from lia_models.candidate import Candidate
from lia_models.data_request import DataRequest

logger = logging.getLogger(__name__)


class DataRequestVoiceService:
    """Service for voice-call-based data collection (Fase 1 skeleton)."""

    def __init__(self):
        # Mirrors DataRequestWhatsAppService: stateless; db passed per method.
        # The voice orchestrator is intentionally NOT held here — it is imported
        # lazily inside start_collection (heavy import; see module docstring).
        pass

    async def start_collection(
        self,
        db: AsyncSession,
        data_request_id: UUID,
        candidate_phone: str,
    ) -> dict[str, Any]:
        """
        Start a voice-call data collection flow.

        Fase 1: resolve pending fields → build the canonical voice script →
        invoke the voice orchestrator entry point (``initiate_call``) to place
        the outbound call. The orchestrator itself fails LOUD (status='fallback'
        when Twilio is unavailable) — we surface that explicitly and never fake
        success.

        Args:
            db: Database session.
            data_request_id: Data request ID.
            candidate_phone: Candidate's phone number (with country code).

        Returns:
            Structured result dict with an explicit ``status`` (never
            "completed"), the resolved ``fields``, the ``channel`` marker, and —
            when applicable — the orchestrator ``session_id``/``portal_fallback``.
        """
        data_request = await db.get(DataRequest, data_request_id)
        if not data_request:
            logger.error("Voice collection: data request %s not found", data_request_id)
            return {
                "status": "error",
                "channel": "voice",
                "error": "data_request_not_found",
                "fields": [],
            }

        candidate = await db.get(Candidate, data_request.candidate_id)
        if not candidate:
            logger.error(
                "Voice collection: candidate %s not found", data_request.candidate_id
            )
            return {
                "status": "error",
                "channel": "voice",
                "error": "candidate_not_found",
                "fields": [],
            }

        # Resolve pending fields → canonical voice prompt script.
        completed_names = [
            f.get("name") for f in (data_request.fields_completed or []) if f.get("name")
        ]
        script = build_collection_script(
            data_request.fields_requested or [], completed_names
        )
        voice_fields = [p.name for p in script if p.voice_collectable]
        portal_redirect_fields = [p.name for p in portal_only_fields(script)]

        if not voice_fields and not portal_redirect_fields:
            # Nothing pending — explicit, NOT a fake "completed" success.
            logger.info(
                "Voice collection: no pending fields for data request %s",
                data_request_id,
            )
            return {
                "status": "voice_collection_prepared",
                "channel": "voice",
                "fields": [],
                "portal_fallback_fields": [],
                "note": "no_pending_fields",
            }

        # Multi-tenancy: company_id comes from the persisted row, never a payload.
        company_id = str(data_request.company_id)
        candidate_name = getattr(candidate, "name", None) or "Candidato"

        # LAZY import — never at module top (heavy import; see module docstring).
        # Fase 2: build a VoiceCoreOrchestrator WITH the DataCollectionVoicePlugin
        # so the live call collects THESE DataRequest fields. The plugin reports
        # plugin_name == 'data_collection' (NOT 'wsi_screening'), so the
        # orchestrator's Fase 0.5 gate does NOT run the WSI scoring path.
        try:
            from app.domains.voice.plugins.data_collection_voice_plugin import (
                DataCollectionVoicePlugin,
            )
            from app.domains.voice.services.voice_screening_orchestrator import (
                VoiceCoreOrchestrator,
            )
        except Exception as e:  # pragma: no cover - import failure is explicit
            # Fail loud: do NOT fake success. Script is built; live call deferred.
            logger.error(
                "Voice collection: orchestrator/plugin import failed for data request %s: %s",
                data_request_id,
                e,
                exc_info=True,
            )
            return {
                "status": "voice_collection_prepared",
                "channel": "voice",
                "fields": voice_fields,
                "portal_fallback_fields": portal_redirect_fields,
                "note": "orchestrator_unavailable_call_deferred",
                "error": str(e),
            }

        # Construct the data-collection orchestrator. Mirrors how
        # VoiceScreeningOrchestrator installs WSIVoicePlugin (plugins=[plugin]),
        # but with the collection plugin fed the SAME pending fields the script
        # was built from. Fase 4 wires persistence of the plugin's extracted
        # answers back into the DataRequest.
        collection_plugin = DataCollectionVoicePlugin(
            fields=data_request.fields_requested or [],
            completed_names=completed_names,
        )
        collection_orchestrator = VoiceCoreOrchestrator(plugins=[collection_plugin])

        try:
            session = await collection_orchestrator.initiate_call(
                candidate_id=str(data_request.candidate_id),
                candidate_name=candidate_name,
                phone_number=candidate_phone,
                job_title="Coleta de dados",
                company_id=company_id,
                db=db,
            )
        except Exception as e:
            logger.error(
                "Voice collection: initiate_call failed for data request %s: %s",
                data_request_id,
                e,
                exc_info=True,
            )
            return {
                "status": "voice_collection_fallback",
                "channel": "voice",
                "fields": voice_fields,
                "portal_fallback_fields": portal_redirect_fields,
                "error": str(e),
                "note": "call_failed_route_to_chat_or_whatsapp",
            }

        orch_status = getattr(session, "status", None)
        session_id = getattr(session, "session_id", None)

        if orch_status == "initiated":
            # Call placed WITH the DataCollectionVoicePlugin installed.
            status = "voice_collection_initiated"
            data_request.collection_method = "voice"
            await db.commit()
        else:
            # 'fallback' / 'failed' → Twilio unavailable. Explicit, not faked.
            status = "voice_collection_fallback"

        logger.info(
            "Voice collection for data request %s: status=%s (orchestrator=%s)",
            data_request_id,
            status,
            orch_status,
        )

        return {
            "status": status,
            "channel": "voice",
            "fields": voice_fields,
            "portal_fallback_fields": portal_redirect_fields,
            "session_id": session_id,
            "orchestrator_status": orch_status,
        }


data_request_voice_service = DataRequestVoiceService()
