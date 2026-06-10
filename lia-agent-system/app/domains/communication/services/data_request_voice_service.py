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

FASE 3 (LGPD consent gate — FAIL-CLOSED): before placing the call,
``start_collection`` verifies candidate consent via ``ConsentCheckerService``
(purpose="voice_screening"). NO consent → the call is NOT placed and an explicit
``voice_collection_no_consent`` status is returned (never a fake success). The
in-call LGPD recording notice is spoken as the FIRST utterance by the
``DataCollectionVoicePlugin`` (its ``RECORDING_NOTICE``).

FASE 4 (canonical persistence): the ``DataCollectionVoicePlugin`` is constructed
WITH ``data_request_id`` so its ``on_session_finalized`` persists the VALID
collected answers back into the DataRequest via the SAME canonical producer
WhatsApp uses (``DataRequestResponse`` row + append to
``DataRequest.fields_completed`` with ``source="voice_collection"``).
``needs_followup`` fields are NEVER persisted as answered (CLAUDE.md REGRA 4).

Anti-silent-fallback (CLAUDE.md REGRA 4): start_collection NEVER reports a fake
"completed" collection. It returns an explicit status:
- ``voice_collection_initiated``  → orchestrator placed the call (status=initiated)
- ``voice_collection_fallback``   → Twilio unavailable / circuit open → route to
                                    chat/WhatsApp (orchestrator status=fallback/failed)
- ``voice_collection_prepared``   → script built, but no live call placed
- ``voice_collection_no_consent`` → LGPD consent gate failed-closed; call NOT placed

IMPORTANT — lazy import: the voice orchestrator AND the DataCollectionVoicePlugin
are imported INSIDE ``start_collection``, never at module top. Importing
``voice_screening_orchestrator`` at module load is heavy (drops the Replit SSH
session in test/CI). Lazy import keeps this module cheap to import and lets
tests mock the orchestrator/plugin without triggering the real import.

Multi-tenancy: ``company_id`` is read from the persisted DataRequest row
(authoritative, never from a request payload), mirroring the WhatsApp service.
"""
import logging
from datetime import UTC, datetime
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



# -- Gap A: Monthly voice call budget -------------------------------------------
# Default limit: 100 voice calls/month per tenant (~$6.50 at $0.065/call).
# Mirrors token_budget:  key  = f"token_budget:{company_id}:{YYYY-MM-DD}"
# Voice key format:             f"voice_calls:{company_id}:{YYYY-MM}"
VOICE_CALLS_MONTHLY_DEFAULT_LIMIT: int = 100
_VOICE_REDIS_TTL: int = 33 * 24 * 3600  # 33 days -- outlives the longest month


def _voice_redis_key(company_id: str) -> str:
    """Monthly voice-call counter key. Format: ``voice_calls:{company_id}:YYYY-MM``."""
    ym = datetime.now(UTC).strftime("%Y-%m")
    return f"voice_calls:{company_id}:{ym}"


async def _check_voice_budget(
    company_id: str,
    limit: int = VOICE_CALLS_MONTHLY_DEFAULT_LIMIT,
) -> tuple[bool, int]:
    """Check monthly voice-call budget for a tenant.

    Returns (allowed, current_count).
    FAIL-OPEN: Redis unavailable -> returns (True, 0) so Redis downtime does not
    block all voice calls.
    """
    try:
        import redis.asyncio as _aioredis
        from lia_config.config import settings as _settings
        _r = _aioredis.from_url(_settings.REDIS_URL)
        try:
            key = _voice_redis_key(company_id)
            raw = await _r.get(key)
            current = int(raw) if raw else 0
            allowed = current < limit
            if not allowed:
                logger.warning(
                    "[VoiceBudget] Budget esgotado: company_id=%s calls=%d limit=%d",
                    company_id,
                    current,
                    limit,
                )
            return allowed, current
        finally:
            await _r.aclose()
    except Exception as _exc:
        logger.warning(
            "[VoiceBudget] Redis indisponivel em check -- permitindo chamada "
            "(company_id=%s): %s",
            company_id,
            _exc,
        )
        return True, 0


async def _increment_voice_calls(company_id: str) -> int:
    """Increment monthly voice-call counter after a successful call.

    Returns new total. Fail-silent if Redis unavailable.
    """
    try:
        import redis.asyncio as _aioredis
        from lia_config.config import settings as _settings
        _r = _aioredis.from_url(_settings.REDIS_URL)
        try:
            key = _voice_redis_key(company_id)
            new_total = await _r.incr(key)
            await _r.expire(key, _VOICE_REDIS_TTL)
            logger.debug(
                "[VoiceBudget] Incrementado: company_id=%s -> %d calls este mes",
                company_id,
                new_total,
            )
            return new_total
        finally:
            await _r.aclose()
    except Exception as _exc:
        logger.warning(
            "[VoiceBudget] Redis indisponivel em increment (company_id=%s): %s",
            company_id,
            _exc,
        )
        return 0

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

        # ── LGPD consent gate — TRI-STATE (consent-first capture) ─────────────
        # An outbound voice call that collects personal data REQUIRES consent
        # (LGPD Art. 7). Three outcomes, each fail-closed in its own way:
        #   - "granted"  → prior explicit consent → proceed as today
        #                  (require_verbal_consent=False).
        #   - "absent"   → no prior consent (and NOT revoked) → DO NOT hard-block;
        #                  instead place a CONSENT-FIRST call: the plugin asks for
        #                  verbal authorization first, and a verbal "yes" is
        #                  recorded as valid LGPD consent (provenance=voice) before
        #                  any field is collected.
        #   - "revoked"  → consent explicitly revoked → STILL hard-block. A revoked
        #                  consent must NEVER be re-solicited by an outbound call.
        #                  Fail-closed on revocation.
        # check_error / service unavailable also fail-closed (treated as block).
        consent_state = await self._classify_consent(
            db=db,
            candidate_id=str(data_request.candidate_id),
            company_id=company_id,
        )

        if consent_state == "revoked":
            logger.warning(
                "Voice collection: BLOCKED — consent REVOKED for data request "
                "%s (candidate=%s, company=%s) — call NOT placed (no re-solicit).",
                data_request_id,
                data_request.candidate_id,
                company_id,
            )
            return {
                "status": "voice_collection_no_consent",
                "channel": "voice",
                "fields": voice_fields,
                "portal_fallback_fields": portal_redirect_fields,
                "note": "lgpd_consent_revoked_call_not_placed",
            }

        # "absent" → consent-first call; "granted" → today's behavior.
        require_verbal_consent = consent_state == "absent"

        # -- Gap A: Monthly voice call budget gate --------------------------------
        # Gate BEFORE placing the call. Exceeding budget -> explicit status +
        # note to route to non-voice channels. Never a fake success.
        _budget_allowed, _call_count = await _check_voice_budget(company_id)
        if not _budget_allowed:
            logger.warning(
                "Voice collection: BLOCKED -- monthly budget exceeded "
                "company=%s calls_this_month=%d limit=%d. "
                "Route to non-voice channels.",
                company_id,
                _call_count,
                VOICE_CALLS_MONTHLY_DEFAULT_LIMIT,
            )
            return {
                "status": "voice_collection_budget_exceeded",
                "channel": "voice",
                "fields": voice_fields,
                "portal_fallback_fields": portal_redirect_fields,
                "note": "monthly_voice_call_limit_reached",
                "calls_this_month": _call_count,
                "limit": VOICE_CALLS_MONTHLY_DEFAULT_LIMIT,
            }

        # Construct the data-collection orchestrator. Mirrors how
        # VoiceScreeningOrchestrator installs WSIVoicePlugin (plugins=[plugin]),
        # but with the collection plugin fed the SAME pending fields the script
        # was built from. When require_verbal_consent=True the plugin asks for
        # verbal authorization first and gates field collection on a verbal
        # "yes" (recorded as LGPD consent at finalize via register_consent).
        collection_plugin = DataCollectionVoicePlugin(
            fields=data_request.fields_requested or [],
            completed_names=completed_names,
            data_request_id=data_request_id,
            require_verbal_consent=require_verbal_consent,
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
            # Call placed WITH the DataCollectionVoicePlugin installed. When the
            # call started in consent-first mode (no prior consent), report a
            # distinct, honest status so callers know verbal consent is pending.
            status = (
                "voice_collection_initiated_consent_first"
                if require_verbal_consent
                else "voice_collection_initiated"
            )
            data_request.collection_method = "voice"
            await _increment_voice_calls(company_id)
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

    async def _classify_consent(
        self,
        db: AsyncSession,
        candidate_id: str,
        company_id: str,
    ) -> str:
        """
        Classify LGPD consent state before placing an outbound collection call.

        Returns one of:
          - "granted" → candidate has explicit, valid prior consent → proceed.
          - "absent"  → no prior consent recorded AND not revoked → eligible for
                        a CONSENT-FIRST call (verbal authorization captured live).
          - "revoked" → consent explicitly revoked → HARD-BLOCK, never
                        re-solicited by an outbound call (fail-closed).

        FAIL-CLOSED on uncertainty: an unavailable ConsentCheckerService or any
        unexpected error returns "revoked" (the safest non-soliciting outcome —
        no call is placed). A revoked consent is NEVER downgraded to "absent".

        company_id is the authoritative tenant id from the persisted DataRequest
        row (never a payload). Mirrors the canonical voice purpose
        (purpose="voice_screening" → consent_type VOICE_SCREENING).

        LAZY import: ConsentCheckerService lives in the lgpd domain; import it
        inside the method to keep this module cheap and let tests patch it.
        """
        try:
            from app.domains.lgpd.services.consent_checker_service import (
                ConsentCheckerService,
            )
        except Exception as e:  # pragma: no cover - import failure → fail closed
            logger.error(
                "Voice collection: ConsentCheckerService unavailable — failing "
                "closed (no call). candidate=%s company=%s: %s",
                candidate_id,
                company_id,
                e,
            )
            return "revoked"

        try:
            checker = ConsentCheckerService(db)
            result = await checker.check_candidate_consent(
                candidate_id=candidate_id,
                company_id=company_id,
                # Closest correct LGPD purpose: voice channel processing
                # candidate data (PURPOSE_TO_CONSENT_TYPE → VOICE_SCREENING).
                purpose="voice_screening",
            )
        except Exception as e:
            logger.error(
                "Voice collection: consent check error — failing closed (no "
                "call). candidate=%s company=%s: %s",
                candidate_id,
                company_id,
                e,
            )
            return "revoked"

        # Map the canonical ConsentCheckResult into the tri-state.
        #   reason == "revoked"                → "revoked" (hard-block, no re-solicit)
        #   allowed + not soft_warning         → "granted"
        #   absent (allowed=True soft_warning, OR allowed=False reason="absent",
        #           OR a fail-open check_error) → "absent" (eligible consent-first)
        reason = getattr(result, "reason", None)
        if reason == "revoked":
            logger.info(
                "Voice collection: consent REVOKED — hard-block, no re-solicit. "
                "candidate=%s company=%s",
                candidate_id,
                company_id,
            )
            return "revoked"
        if getattr(result, "allowed", False) and not getattr(
            result, "soft_warning", False
        ):
            return "granted"
        logger.info(
            "Voice collection: consent ABSENT — eligible for consent-first call. "
            "candidate=%s company=%s (reason=%s)",
            candidate_id,
            company_id,
            reason,
        )
        return "absent"


data_request_voice_service = DataRequestVoiceService()
