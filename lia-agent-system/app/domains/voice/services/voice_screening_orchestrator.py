"""
Voice Screening Orchestrator — Twilio Voice + Gemini + TTS pipeline.

Sprint 3.2/3.3 refactor (audit 2026-05-22 W4-1 V2): este modulo agora hospeda
TANTO o nucleo voz generico (VoiceCoreOrchestrator) quanto o subclass legacy
WSI-aware (VoiceScreeningOrchestrator). Decisao de arquitetura: manter classes
no MESMO MODULO PHYSICAL preserva module-level symbol binding usado por dezenas
de tests (patch("...voice_screening_orchestrator._get_voice_service") etc.) e
permite extrair core + plugins sem quebrar a API publica.

Para callers que querem usar VoiceCoreOrchestrator direto (Sprint 3.4+):
    from app.domains.voice.services.voice_core_orchestrator import VoiceCoreOrchestrator

Connects:
- Twilio Programmable Voice (telephony, μ-law audio stream)
- Gemini Flash 2.5 (STT via WAV + conversational LLM)
- OpenAI TTS → μ-law transcoding (for Twilio Media Stream playback)
- WSI pipeline (transcript analysis and scoring) — via WSIVoicePlugin (Sprint 3.3)
- Consent management (LGPD compliance — hard-block on revoke, soft-warn on absent)
- PII Masking (before any logging or persistence)
- FairnessGuard middleware — applied to all Gemini responses before delivery

Audio pipeline:
  Twilio → [raw μ-law 8kHz] → mulaw_to_wav() → [WAV] → Gemini STT → [text]
  Gemini LLM → [text] → FairnessGuard → OpenAI TTS → [MP3] → mp3_to_mulaw() → [μ-law] → Twilio

Compliance:
- LGPD Art. 7: Consentimento explícito verificado antes de iniciar ligação
- LGPD Art. 12 / SEG-3B: PII masked before logging
- Crença #4: Transparência — candidato informado sobre finalidade e duração
- Crença #11: Anti-sycophancy em 100% das interações IA
- LGPD absent consent → soft_warning logged, call proceeds
- LGPD revoked consent → ConsentNotGrantedError raised, call BLOCKED
- FairnessGuard: L1+L2 bias check on all LIA voice responses

Session persistence:
- Active sessions persisted in wsi_sessions.voice_session_state (JSONB)
- Session survives server restarts; loaded from DB on first request
"""


import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4


from app.domains.communication.services.twilio_voice_service import (
    TwilioVoiceUnconfiguredError,
    mp3_to_mulaw,
    mulaw_to_wav,
)
from app.domains.communication.services.twilio_voice_service import (
    twilio_voice_service as _twilio_voice_service,
)
from app.core.config import settings
from app.shared.services.voice_service import VoiceService
from app.shared.compliance.fairness_guard_middleware import check_fairness
from app.shared.pii_masking import mask_phone_preserve_tail, mask_pii, strip_pii_for_llm_prompt
from app.shared.prompts.anti_sycophancy_block import ANTI_SYCOPHANCY_OPERATIONAL
from app.shared.resilience.circuit_breaker import TWILIO_VOICE_CIRCUIT, CircuitBreakerError
from app.shared.services.automated_decision_logger import (
    PROTECTED_CRITERIA_PT,
    log_automated_decision,
)
from app.shared.compliance.audit_service import AuditService
from app.shared.runtime_context import RuntimeContext
from app.shared.prompt_injection import PromptInjectionGuard
from app.shared.messaging.platform_events import (
    PlatformEvent,
    publish_platform_event,
)

try:
    from app.shared.services.gemini_voice_service import get_voice_service as _get_voice_service
except ImportError:
    _get_voice_service = None  # type: ignore[assignment]

try:
    from app.services.voice.deepgram_service import deepgram_service as _deepgram_service
    from app.services.voice.deepgram_service import DeepgramUnconfiguredError as _DeepgramUnconfiguredError
except ImportError:
    _deepgram_service = None  # type: ignore[assignment]
    _DeepgramUnconfiguredError = Exception  # type: ignore[assignment,misc]

try:
    from app.shared.services.voice_screening_analysis import analyze_voice_screening as _analyze_voice_screening
except ImportError:
    _analyze_voice_screening = None  # type: ignore[assignment]

try:
    from app.shared.services.consent_checker_service import ConsentCheckerService as _ConsentCheckerService
except ImportError:
    _ConsentCheckerService = None  # type: ignore[assignment]

try:
    from app.domains.cv_screening.services.wsi_voice_orchestrator import WSIVoiceOrchestrator as _WSIVoiceOrchestrator
except ImportError:
    _WSIVoiceOrchestrator = None  # type: ignore[assignment]

# F-01 P0 fix (audit 2026-05-22): canonical llm_service singleton — used in
# generate_lia_response.generate_native_gemini_sync. Era ausente do __init__,
# AttributeError silenciado por except genérico → fallback scripted permanente.
from app.domains.ai.services.llm import llm_service as _canonical_llm_service

logger = logging.getLogger(__name__)

# F-08 P0 (audit 2026-05-22): canonical PromptInjectionGuard singleton.
# Voice path reuses chat canonical (decisão Paulo: NÃO criar voice-specific).
_voice_injection_guard = PromptInjectionGuard()


@dataclass
class VoiceScreeningSession:
    """State for an active voice screening call."""
    session_id: str
    candidate_id: str
    candidate_name: str
    job_title: str
    company_id: str
    phone_number: str
    job_id: str | None = None
    call_sid: str | None = None
    status: str = "pending"
    language: str = "pt-BR"
    transcript_segments: list[dict[str, Any]] = field(default_factory=list)
    questions_asked: list[str] = field(default_factory=list)
    started_at: datetime | None = None
    ended_at: datetime | None = None
    wsi_result: dict[str, Any] | None = None
    error: str | None = None
    consent_verified: bool = False
    job_context: dict[str, Any] | None = None
    presentation_done: bool = False
    voice_provider: str = "twilio"
    # P1 ticket #1 (2026-05-23): canonical Gemini LLM token tracking.
    # Acumulado por turn em generate_lia_response a partir do
    # response.usage_metadata. Lido em _record_voice_billing para
    # compute_voice_credits — antes era hardcoded 0 (billing ghost).
    llm_tokens_input: int = 0
    llm_tokens_output: int = 0
    # C.2 ticket (2026-05-23): canonical metadata field for plugin annotations
    # (e.g. studio_agent_id, plugin_name). Previously attached via setattr by
    # StudioVoicePlugin — works in-memory but did not survive Redis JSONB
    # round-trip. Now first-class field + serialized in _session_to_state.
    metadata: dict[str, Any] = field(default_factory=dict)


class VoiceScreeningOrchestratorError(Exception):
    """Error during voice screening orchestration."""
    pass


class ConsentNotGrantedError(VoiceScreeningOrchestratorError):
    """Raised when candidate has not granted consent for voice screening."""
    pass


class _LegacySessionsShim:
    """
    F-15 backward-compat shim: provides dict-like __setitem__/__getitem__/__contains__
    over the canonical VoiceSessionRedisRepository's in-memory fallback.

    Operates DIRECTLY on the repo's `_memory_fallback` + `_memory_active_index` +
    `_memory_reverse_index` dicts. SYNCHRONOUS (no asyncio.run nesting) — this
    is intentional: the shim exists for legacy unit tests that need a sync-dict
    interface, and Redis is bypassed entirely (tests should use real Redis via
    explicit fixtures if multi-worker behavior matters).

    Production code MUST NOT use this property. New code uses async
    `_store_session` / `_fetch_session`.
    """

    def __init__(self, orchestrator: "VoiceCoreOrchestrator") -> None:
        self._orch = orchestrator

    def _store_session_sync(self, session: "VoiceScreeningSession") -> None:
        """Synchronous in-memory write (mirrors VoiceSessionRedisRepository fallback path)."""
        import json
        state = self._orch._session_to_state(session)
        repo = self._orch._session_repo
        # Replicate the in-memory fallback writes verbatim.
        repo._memory_fallback[repo._session_key(session.company_id, session.session_id)] = (
            json.dumps(state, default=str)
        )
        repo._memory_active_index.setdefault(session.company_id, set()).add(session.session_id)
        repo._memory_reverse_index[session.session_id] = session.company_id

    def _fetch_session_sync(self, session_id: str) -> "VoiceScreeningSession | None":
        """Synchronous in-memory read with reverse-index resolution."""
        import json
        repo = self._orch._session_repo
        company_id = repo._memory_reverse_index.get(session_id)
        if not company_id:
            return None
        raw = repo._memory_fallback.get(repo._session_key(company_id, session_id))
        if not raw:
            return None
        return self._orch._state_to_session(json.loads(raw))

    def __setitem__(self, session_id: str, session: "VoiceScreeningSession") -> None:
        if session.session_id != session_id:
            session.session_id = session_id
        self._store_session_sync(session)

    def __getitem__(self, session_id: str) -> "VoiceScreeningSession":
        result = self._fetch_session_sync(session_id)
        if result is None:
            raise KeyError(session_id)
        return result

    def get(self, session_id: str, default=None):
        result = self._fetch_session_sync(session_id)
        return result if result is not None else default

    def __contains__(self, session_id: str) -> bool:
        return self._fetch_session_sync(session_id) is not None

    def __len__(self) -> int:
        return len(self._orch._session_repo._memory_fallback)

    def values(self):
        import json
        for raw in self._orch._session_repo._memory_fallback.values():
            try:
                yield self._orch._state_to_session(json.loads(raw))
            except Exception:
                continue

    def keys(self):
        for company_sessions in self._orch._session_repo._memory_active_index.values():
            yield from company_sessions


class VoiceCoreOrchestrator:
    """
    VoiceCoreOrchestrator — generic voice transport core (Sprint 3.2 canonical).

    Knows about audio I/O, consent, LLM dispatch, persistence, and plugin
    lifecycle hooks. Does NOT know about WSI screening, BigFive scoring, or
    any other domain-specific logic — those live in VoiceCorePlugin
    implementations (see app.domains.voice.protocols.voice_core_plugin).

    Flow:
    1. verify_consent() — check LGPD consent; BLOCK if revoked, warn if absent
    2. initiate_call() — start Twilio Voice call protected by TWILIO_VOICE_CIRCUIT
                         if Twilio unconfigured/circuit-open → status="fallback" (not mock)
       → invokes plugin hook on_session_initiated for each registered plugin
    3. handle_audio_stream() — μ-law → WAV → Gemini STT → transcript
    4. generate_lia_response() — Gemini LLM drives conversation
       → may invoke plugin get_next_question for scripted-fallback path
    5. synthesize_lia_response() — OpenAI TTS → MP3 → μ-law for Twilio stream
    6. finalize_screening() — PII-masked transcript → plugin completion hooks
       → invokes plugin hook on_session_finalized for each registered plugin
    7. Fallback: circuit_open/unconfigured → status="fallback" → chat/WhatsApp

    Circuit breaker: TWILIO_VOICE_CIRCUIT

    Plugin lifecycle:
    - `plugins` param accepts list[VoiceCorePlugin] (default None = generic mode).
    - Hooks fire in registration order; errors logged + swallowed (never block
      voice call).

    Backward-compat: see VoiceScreeningOrchestrator subclass at bottom of this
    module — preserves all existing callers' API.
    """

    SCREENING_QUESTIONS_PT = [
        "Pode me contar brevemente sobre sua experiência profissional mais recente?",
        "Por que você tem interesse nessa posição?",
        "Quais são suas principais habilidades técnicas relevantes para essa vaga?",
        "Como você prefere trabalhar: em equipe ou de forma mais independente?",
        "Qual sua disponibilidade de início? Está aberto a mudanças ou trabalho remoto?",
    ]

    def __init__(self, plugins: list | None = None):
        # F-15 P0 fix (audit 2026-05-22): _sessions dict in-process era race risk
        # em FastAPI multi-worker (cada worker dict próprio → callbacks Twilio
        # iam para worker errado). Substituído por VoiceSessionRedisRepository
        # canonical com TTL 4h. Repo tem fallback in-memory para dev/testes.
        # Sessions ativas durante deploy são perdidas (janela <1h tipicamente).
        from app.domains.voice.repositories.voice_session_redis_repository import (
            VoiceSessionRedisRepository,
        )
        # F-15: each orchestrator gets its OWN repo instance (not the canonical
        # singleton) so tests have isolated state. Production callers should
        # use the module-level `voice_screening_orchestrator` singleton.
        self._session_repo = VoiceSessionRedisRepository()
        self._tts_service = VoiceService()
        # F-01 P0 fix (audit 2026-05-22 AUDIT_VOICE_SCREENING_ORCHESTRATOR.md):
        # canonical llm_service singleton — referenced by generate_lia_response:1109
        # for generate_native_gemini_sync. Era ausente; AttributeError silenciado
        # pelo except genérico → fallback scripted permanente em produção.
        self._llm_service = _canonical_llm_service

        # Sprint 3.2: plugin lifecycle. Plugins implement VoiceCorePlugin
        # (app.domains.voice.protocols.voice_core_plugin). Generic mode
        # (no plugins) makes the core behave as a pure voice transport.
        # Subclasses (e.g., VoiceScreeningOrchestrator) pre-install their
        # canonical plugins in their own __init__.
        self._plugins: list = list(plugins) if plugins else []

    async def _store_session(self, session: "VoiceScreeningSession") -> None:
        """
        F-15 canonical: persist session state to Redis (or in-mem fallback).
        Replaces `self._sessions[session.session_id] = session` direct dict ops.
        """
        if not session or not session.session_id or not session.company_id:
            logger.warning(
                "[VOICE SCREENING] _store_session called without "
                "session_id+company_id; skipping (session=%s)",
                session.session_id if session else None,
            )
            return
        state = self._session_to_state(session)
        await self._session_repo.save_session_state(
            company_id=session.company_id,
            session_id=session.session_id,
            state=state,
        )

    @property
    def _sessions(self) -> "dict[str, VoiceScreeningSession]":
        """
        F-15 backward-compat shim for legacy tests.

        Returns a dict-like view backed by the canonical Redis repository's
        in-memory fallback (active in unit tests where Redis is unavailable).
        Writes go through __setitem__ which delegates to `_store_session`
        running synchronously on a fresh event loop.

        Production code must NOT use this property. New code should use
        `await self._store_session(session)` / `await self._fetch_session(id)`.
        """
        return _LegacySessionsShim(self)

    async def _fetch_session(
        self,
        session_id: str,
        company_id: str | None = None,
        db: Any = None,
    ) -> "VoiceScreeningSession | None":
        """
        F-15 canonical: load session state from Redis.
        Returns None if not found. Replaces `self._sessions.get(session_id)`.

        Lookup strategy:
          1. If company_id provided: read Redis directly (fast path, multi-worker safe).
          2. Else: resolve company_id via reverse index in Redis, then read state.
             (Multi-tenancy preserved — reverse index stores canonical company_id
             from session-creation time, never trusts external input.)
          3. Else if db provided: load from DB; rehydrate Redis cache.
          4. Else: return None.
        """
        if not session_id:
            return None

        # Step 1: fast path with explicit company_id.
        resolved_company_id = company_id
        if not resolved_company_id:
            # Step 2: resolve via reverse index (session_id → company_id).
            resolved_company_id = await self._session_repo.find_company_id_for_session(
                session_id=session_id,
            )

        if resolved_company_id:
            state = await self._session_repo.load_session_state(
                company_id=resolved_company_id,
                session_id=session_id,
            )
            if state is not None:
                return self._state_to_session(state)

        # Step 3: DB fallback. Rehydrate Redis cache on hit.
        if db is not None:
            session = await self._load_session_from_db(session_id, db)
            if session is not None and session.company_id:
                try:
                    await self._store_session(session)
                except Exception as exc:
                    logger.warning(
                        "[VOICE SCREENING] Redis rehydrate failed session=%s: %s",
                        session_id, exc,
                    )
                return session

        return None

    # ── Session persistence helpers ──────────────────────────────────────────

    def _session_to_state(self, session: "VoiceScreeningSession") -> dict[str, Any]:
        """Serialize VoiceScreeningSession to JSON-serializable dict for DB storage.

        F-07 P0 LGPD Art. 11: phone_number persisted in JSONB is masked
        (preserve country+DDD+last 4 digits). At-rest masking prevents leak
        in backups / audit dumps. Plaintext phone is needed only during the
        active outbound call (in-memory `session.phone_number`).
        """
        return {
            "session_id": session.session_id,
            "candidate_id": session.candidate_id,
            "candidate_name": session.candidate_name,
            "job_title": session.job_title,
            "company_id": session.company_id,
            # F-07 P0 LGPD Art. 11: mask before persisting to JSONB at rest.
            "phone_number": mask_phone_preserve_tail(session.phone_number),
            "job_id": session.job_id,
            "call_sid": session.call_sid,
            "status": session.status,
            "language": session.language,
            "transcript_segments": session.transcript_segments,
            "questions_asked": session.questions_asked,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "wsi_result": session.wsi_result,
            "error": session.error,
            "consent_verified": session.consent_verified,
            "job_context": session.job_context,
            "presentation_done": session.presentation_done,
            "voice_provider": session.voice_provider,
            # P1 ticket #1: canonical Gemini LLM token tracking persisted
            # in Redis for cross-process billing read in finalize_screening.
            "llm_tokens_input": session.llm_tokens_input,
            "llm_tokens_output": session.llm_tokens_output,
            # C.2: persist plugin metadata round-trip (studio_agent_id, etc.).
            "metadata": dict(session.metadata) if session.metadata else {},
        }

    def _state_to_session(self, state: dict[str, Any]) -> "VoiceScreeningSession":
        """Deserialize DB state dict back to VoiceScreeningSession."""
        return VoiceScreeningSession(
            session_id=state["session_id"],
            candidate_id=state["candidate_id"],
            candidate_name=state["candidate_name"],
            job_title=state["job_title"],
            company_id=state["company_id"],
            phone_number=state["phone_number"],
            job_id=state.get("job_id"),
            call_sid=state.get("call_sid"),
            status=state.get("status", "pending"),
            language=state.get("language", "pt-BR"),
            transcript_segments=state.get("transcript_segments", []),
            questions_asked=state.get("questions_asked", []),
            started_at=(
                datetime.fromisoformat(state["started_at"])
                if state.get("started_at") else None
            ),
            ended_at=(
                datetime.fromisoformat(state["ended_at"])
                if state.get("ended_at") else None
            ),
            wsi_result=state.get("wsi_result"),
            error=state.get("error"),
            consent_verified=state.get("consent_verified", False),
            job_context=state.get("job_context"),
            presentation_done=state.get("presentation_done", False),
            voice_provider=state.get("voice_provider", "twilio"),
            # P1 ticket #1: backward-compat defaults 0 for legacy sessions
            # in Redis that pre-date token tracking.
            llm_tokens_input=int(state.get("llm_tokens_input", 0) or 0),
            llm_tokens_output=int(state.get("llm_tokens_output", 0) or 0),
            # C.2: backward compat for legacy sessions in Redis without metadata.
            metadata=dict(state.get("metadata", {}) or {}),
        )

    async def persist_session_state(self, session: "VoiceScreeningSession", db) -> None:
        """Persist session state to wsi_sessions.voice_session_state (JSONB).

        F-09 P2 fix (audit 2026-05-22): renamed from _persist_session_state to public.
        _-prefix alias preserved below for backward compat (callers in twilio_voice.py,
        gemini_voice.py being migrated).
        """
        if db is None:
            return
        try:
            # F-13 (audit 2026-05-22): canonical write via WsiRepository (ADR-001).
            from app.domains.voice.repositories.wsi_repository import WsiRepository
            state_dict = self._session_to_state(session)
            state_json = json.dumps(state_dict)
            await WsiRepository(db).update_voice_session_state(
                session_id=session.session_id,
                state_json=state_json,
            )
            await db.commit()
            logger.debug(
                "[VOICE SCREENING] Session state persisted session=%s status=%s",
                session.session_id, session.status,
            )
        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.error(
                "[VOICE SCREENING] FAILED to persist session state session=%s: %s — "
                "session will not survive restart",
                session.session_id, e,
            )

    async def _persist_session_state(self, session: "VoiceScreeningSession", db) -> None:
        """F-09 P2 backward-compat alias. Use persist_session_state (public) for new code.

        Deprecated 2026-05-22. Removal scheduled after callers em twilio_voice.py +
        gemini_voice.py forem migrados (Sprint 3.2+).
        """
        return await self.persist_session_state(session, db)


    async def _load_session_from_db(self, session_id: str, db) -> Optional["VoiceScreeningSession"]:
        """Try to load a session from wsi_sessions.voice_session_state."""
        if db is None:
            return None
        try:
            # F-13 (audit 2026-05-22): canonical read via WsiRepository (ADR-001).
            from app.domains.voice.repositories.wsi_repository import WsiRepository
            stored = await WsiRepository(db).get_voice_session_state(session_id)
            if stored:
                state = stored if isinstance(stored, dict) else json.loads(stored)
                session = self._state_to_session(state)
                logger.info(
                    "[VOICE SCREENING] Session recovered from DB: session=%s status=%s",
                    session_id, session.status,
                )
                return session
        except Exception as e:
            logger.warning(
                "[VOICE SCREENING] Failed to load session from DB session=%s: %s",
                session_id, e,
            )
        return None

    # Sprint 3.3: _load_wsi_questions_for_session IMPLEMENTATION moved to
    # WSIVoicePlugin (app.domains.voice.plugins.wsi_voice_plugin._load_wsi_questions_for_session_impl).
    # Method name preserved on the core class as a thin domain-agnostic
    # dispatcher (delegates to plugins). VoiceScreeningOrchestrator subclass
    # overrides with an explicit thin delegate for tests that patch the method.

    async def _load_wsi_questions_for_session(
        self, session_id: str, db: Any
    ) -> list[str]:
        """
        Sprint 3.3: generic dispatcher to plugins providing question pools.

        Backward-compat semantics: same signature + return type as the original
        method. Generic mode (no plugins, or no plugin with WSI impl) returns
        [] — caller falls back to scripted SCREENING_QUESTIONS_PT.

        Subclasses override this to provide explicit backward-compat hooks for
        test patches (see VoiceScreeningOrchestrator._load_wsi_questions_for_session).
        """
        return await self._plugin_load_question_pool(session_id, db)

    async def _plugin_load_question_pool(
        self, session_id: str, db: Any
    ) -> list[str]:
        """
        Sprint 3.3 helper: domain-agnostic question pool lookup.

        Iterates registered plugins looking for one that exposes
        `_load_wsi_questions_for_session_impl` (WSIVoicePlugin pattern). Returns
        the first non-empty result, or [] when no plugin provides questions
        (generic-mode safe — caller falls back to scripted SCREENING_QUESTIONS_PT).
        """
        for plugin in self._plugins:
            impl = getattr(plugin, "_load_wsi_questions_for_session_impl", None)
            if impl is None:
                continue
            try:
                questions = await impl(session_id, db)
                if questions:
                    return questions
            except Exception as plugin_err:  # noqa: BLE001 — best-effort
                logger.warning(
                    "[VOICE CORE] plugin=%s question pool load failed (non-blocking) "
                    "session=%s: %s",
                    getattr(plugin, "plugin_name", "unknown"),
                    session_id,
                    plugin_err,
                )
        return []

    async def _fetch_job_context_from_db(
        self,
        job_id: str,
        db,
        company_id: str,
    ) -> dict[str, Any] | None:
        """
        Fetch job vacancy context from the database by job_id.

        Returns a dict with the fields relevant for LIA's job presentation:
        title, description, requirements, benefits, work_model, salary, location,
        employment_type, seniority_level, behavioral_competencies.

        Tenant isolation (fail-closed): company_id is MANDATORY. The query always
        includes AND company_id = :company_id so a voice screening session can never
        read vacancy data belonging to a different tenant. Returns None when
        company_id is absent rather than falling back to an unscoped query.
        Always pass session.company_id.

        Returns None if the job is not found, DB is unavailable, or company_id absent.
        """
        if db is None or not job_id:
            return None
        if not company_id:
            logger.error(
                "[VOICE SCREENING] _fetch_job_context_from_db called without company_id "
                "for job_id=%s — refusing to fetch (tenant isolation fail-closed)",
                job_id,
            )
            return None
        try:
            # F-13 (audit 2026-05-22): canonical read via JobVacancyCrudRepository (ADR-001).
            # Multi-tenancy: get_vacancy_by_id_and_company enforces both id + company_id.
            from app.domains.job_management.repositories.job_vacancy_crud_repository import (
                JobVacancyCrudRepository,
            )
            vacancy = await JobVacancyCrudRepository(db).get_vacancy_by_id_and_company(
                job_id, company_id,
            )
            if not vacancy:
                logger.info(
                    "[VOICE SCREENING] No job vacancy found for job_id=%s company_id=%s",
                    job_id, company_id,
                )
                return None

            requirements = getattr(vacancy, "requirements", None) or []
            benefits = getattr(vacancy, "benefits", None) or []
            behavioral_competencies = getattr(vacancy, "behavioral_competencies", None) or []

            context: dict[str, Any] = {
                "title": getattr(vacancy, "title", "") or "",
                "description": getattr(vacancy, "description", "") or "",
                "requirements": requirements if isinstance(requirements, list) else [],
                "benefits": benefits if isinstance(benefits, list) else [],
                "work_model": getattr(vacancy, "work_model", "") or "",
                "salary": getattr(vacancy, "salary", "") or "",
                "location": getattr(vacancy, "location", "") or "",
                "employment_type": getattr(vacancy, "employment_type", "") or "",
                "seniority_level": getattr(vacancy, "seniority_level", "") or "",
                "behavioral_competencies": (
                    behavioral_competencies
                    if isinstance(behavioral_competencies, list)
                    else []
                ),
            }
            logger.info(
                "[VOICE SCREENING] Job context fetched for job_id=%s company_id=%s title=%r",
                job_id, company_id, context["title"],
            )
            return context

        except Exception as e:
            logger.warning(
                "[VOICE SCREENING] Failed to fetch job context for job_id=%s: %s",
                job_id, e,
            )
            return None

    @staticmethod
    def _build_job_context_summary(job_context: dict[str, Any]) -> str:
        """
        Build a concise, voice-friendly summary of the job context for the system prompt.

        Includes only fields that are available and non-empty.
        """
        lines = []
        if job_context.get("title"):
            lines.append(f"Título da vaga: {job_context['title']}")
        if job_context.get("seniority_level"):
            lines.append(f"Senioridade: {job_context['seniority_level']}")
        if job_context.get("location"):
            lines.append(f"Localização: {job_context['location']}")
        if job_context.get("work_model"):
            lines.append(f"Formato de trabalho: {job_context['work_model']}")
        if job_context.get("employment_type"):
            lines.append(f"Contratação: {job_context['employment_type']}")
        if job_context.get("salary"):
            lines.append(f"Remuneração: {job_context['salary']}")
        if job_context.get("description"):
            desc = job_context["description"]
            # Keep full description up to 2000 chars — truncate only very long JDs
            # to avoid exhausting Gemini context unnecessarily, while preserving
            # enough content for the model to accurately answer candidate questions.
            if len(desc) > 2000:
                desc = desc[:2000] + "..."
            lines.append(f"Descrição da vaga:\n{desc}")
        if job_context.get("requirements"):
            reqs = job_context["requirements"]
            if reqs:
                req_text = ", ".join(str(r) for r in reqs[:20])
                lines.append(f"Requisitos principais: {req_text}")
        if job_context.get("benefits"):
            bens = job_context["benefits"]
            if bens:
                ben_text = ", ".join(str(b) for b in bens[:15])
                lines.append(f"Benefícios: {ben_text}")
        if job_context.get("behavioral_competencies"):
            comps = job_context["behavioral_competencies"]
            if comps:
                comp_names = []
                for c in comps[:15]:
                    if isinstance(c, dict):
                        comp_names.append(c.get("name", str(c)))
                    else:
                        comp_names.append(str(c))
                if comp_names:
                    lines.append(f"Competências comportamentais: {', '.join(comp_names)}")
        return "\n".join(lines) if lines else f"Título da vaga: {job_context.get('title', 'não especificado')}"

    async def _log_consent_audit_safe(
        self,
        company_id: str,
        candidate_id: str,
        decision: str,
        reason: str,
    ) -> None:
        """F-04 P0 LGPD: Audit canonical trail for every voice consent decision.

        LGPD Art. 7 + Lei 13.853/2019 + EU AI Act Art. 13 exigem trail imutável
        de toda decisão automatizada de consent (allowed/blocked). Antes deste
        helper, verify_consent só fazia logger.warning/error — sem persist em
        audit_logs table (queries forenses + DPO trail impossíveis).

        Best-effort: AuditService.log_decision pode falhar silenciosamente se DB
        não estiver disponível ou se houver outro problema. Nunca bloqueia o
        path de consent — apenas garante o trail quando possível.

        Args:
            company_id: tenant UUID
            candidate_id: candidato UUID
            decision: "allowed" | "blocked" (canonical AuditService vocab)
            reason: motivo legivel (consent_revoked, consent_absent_soft_warning,
                    consent_check_exception:<ExcType>, etc)
        """
        try:
            await AuditService().log_decision(
                company_id=company_id,
                agent_name="voice_screening_orchestrator",
                decision_type="voice_consent_check",
                action="consent_verification",
                decision=decision,
                reasoning=[f"reason={reason}", "lgpd_art_7_explicit_consent"],
                criteria_used=["lgpd_art_7_explicit_consent", "tenant_isolation"],
                criteria_ignored=list(PROTECTED_CRITERIA_PT),
                candidate_id=candidate_id,
                human_review_required=False,
            )
        except Exception as audit_exc:  # noqa: BLE001
            # F-04: fail-safe — audit failure NEVER blocks consent path.
            # Logged with full context for SIEM / forensic reconstruction.
            logger.error(
                "[VOICE SCREENING][AUDIT-FAIL] log_decision failed candidate=%s "
                "decision=%s reason=%s exc=%s",
                mask_pii(candidate_id),
                decision,
                reason,
                audit_exc,
                exc_info=True,
            )

    async def verify_consent(
        self,
        candidate_id: str,
        company_id: str,
        db=None,
    ) -> bool:
        """
        Verify LGPD consent before initiating voice call.

        LGPD Art. 7 + Crença #4: Prior explicit consent is MANDATORY for outbound calls.

        - Confirmed consent (allowed=True) → returns True, call proceeds
        - Absent consent (soft_warning)    → raises ConsentNotGrantedError (BLOCKED)
        - Revoked consent (allowed=False)  → raises ConsentNotGrantedError (BLOCKED)
        - No DB session provided           → raises ConsentNotGrantedError (BLOCKED)
        - ConsentCheckerService unavailable → raises ConsentNotGrantedError (BLOCKED)

        This is a hard-block: if we cannot confirm consent, the call is not placed.
        Outbound phone calls without confirmed consent violate LGPD Art. 7 and Lei 13.853/2019.

        Args:
            candidate_id: Candidate UUID
            company_id: Company UUID (tenant) — falls back to RuntimeContext.company_id
                from authenticated JWT (ADR-029 R-008) when caller passes empty.
            db: SQLAlchemy async session. REQUIRED — without it, call is blocked.

        Returns:
            True only when explicit consent is confirmed

        Raises:
            ConsentNotGrantedError: If consent cannot be confirmed (any reason)
        """
        # F-14 (audit 2026-05-22): RuntimeContext fallback when caller forgot
        # company_id. ADR-029 R-008 canonical pattern — defense-in-depth.
        # Inline fallback because @with_runtime_context decorator only works
        # with **kwargs-only handlers (this method has positional signature).
        if not company_id:
            ctx = RuntimeContext.from_contextvars()
            company_id = ctx.company_id or ""
        if db is None:
            logger.error(
                "[VOICE SCREENING] BLOCKED: No DB session provided — cannot verify consent "
                "for candidate %s. Outbound calls require confirmed LGPD consent (Art. 7).",
                mask_pii(candidate_id),
            )
            # F-04 best-effort audit attempt (no db → AuditService can't persist;
            # we still construct an in-memory log_decision call which falls through to logger).
            await self._log_consent_audit_safe(
                company_id=company_id,
                candidate_id=candidate_id,
                decision="blocked",
                reason="no_db_session",
            )
            raise ConsentNotGrantedError(
                "Cannot verify LGPD consent: no database session provided. "
                "Outbound calls require confirmed prior consent (LGPD Art. 7)."
            )

        ConsentCheckerService = _ConsentCheckerService
        if ConsentCheckerService is None:
            logger.error(
                "[VOICE SCREENING] BLOCKED: ConsentCheckerService unavailable — cannot verify "
                "consent for candidate %s. Outbound calls require confirmed consent.",
                mask_pii(candidate_id),
            )
            await self._log_consent_audit_safe(
                company_id=company_id,
                candidate_id=candidate_id,
                decision="blocked",
                reason="consent_service_unavailable",
            )
            raise ConsentNotGrantedError(
                "Cannot verify LGPD consent: ConsentCheckerService not available. "
                "Outbound calls require confirmed prior consent (LGPD Art. 7)."
            )

        try:
            # F-23 (audit 2026-05-22): purpose="voice_screening" canonical.
            # Distinto de "ai_screening" generic para diferenciacao de audit trail
            # (LGPD Art. 37). PURPOSE_TO_CONSENT_TYPE mapeia para SCREENING por
            # backward compat — granular consent_type proprio = ticket separado
            # de refactor cross-domain ConsentCheckerService.
            checker = ConsentCheckerService(db)
            result = await checker.check_candidate_consent(
                candidate_id=candidate_id,
                company_id=company_id,
                purpose="voice_screening",
            )

            if not result.allowed:
                logger.warning(
                    "[VOICE SCREENING] BLOCKED: Consent REVOKED for candidate %s company=%s",
                    mask_pii(candidate_id),
                    company_id,
                )
                await self._log_consent_audit_safe(
                    company_id=company_id,
                    candidate_id=candidate_id,
                    decision="blocked",
                    reason="consent_revoked",
                )
                raise ConsentNotGrantedError(
                    "Candidate consent revoked for voice screening (LGPD Art. 18)"
                )

            if hasattr(result, "soft_warning") and result.soft_warning:
                logger.error(
                    "[VOICE SCREENING] BLOCKED: Consent ABSENT for candidate %s company=%s. "
                    "Outbound calls require confirmed prior consent — soft_warning is not sufficient.",
                    mask_pii(candidate_id),
                    company_id,
                )
                await self._log_consent_audit_safe(
                    company_id=company_id,
                    candidate_id=candidate_id,
                    decision="blocked",
                    reason="consent_absent_soft_warning",
                )
                raise ConsentNotGrantedError(
                    "Candidate has not explicitly granted consent for voice screening. "
                    "Outbound calls require confirmed prior consent (LGPD Art. 7)."
                )

            logger.info(
                "[VOICE SCREENING] Consent CONFIRMED for candidate %s company=%s",
                mask_pii(candidate_id),
                company_id,
            )
            await self._log_consent_audit_safe(
                company_id=company_id,
                candidate_id=candidate_id,
                decision="allowed",
                reason="explicit_consent_confirmed",
            )
            return True

        except ConsentNotGrantedError:
            raise
        except Exception as e:
            logger.error(
                "[VOICE SCREENING] BLOCKED: Consent check error for candidate %s: %s. "
                "Blocking call — cannot confirm consent.",
                mask_pii(candidate_id),
                e,
            )
            await self._log_consent_audit_safe(
                company_id=company_id,
                candidate_id=candidate_id,
                decision="blocked",
                reason=f"consent_check_exception:{type(e).__name__}",
            )
            raise ConsentNotGrantedError(
                f"Consent check failed with error: {e}. "
                "Outbound calls blocked until consent is confirmed."
            )

    async def initiate_call(
        self,
        candidate_id: str,
        candidate_name: str,
        phone_number: str,
        job_title: str,
        company_id: str,
        job_id: str | None = None,
        language: str = "pt-BR",
        db=None,
    ) -> VoiceScreeningSession:
        """
        Verify consent and initiate an outbound voice screening call.

        If Twilio is not configured or the circuit is open, the session is
        created with status='fallback' — callers must route to chat/WhatsApp.
        This is an explicit failure, NOT a transparent mock.

        Multi-tenancy: ``company_id`` is required. When the caller passes
        empty, falls back to ``RuntimeContext.company_id`` from the
        authenticated JWT (ADR-029 R-008).

        Args:
            candidate_id: Candidate UUID
            candidate_name: Candidate's display name
            phone_number: Candidate's phone (with country code)
            job_title: Job title for screening context
            company_id: Company/tenant UUID
            job_id: Optional job vacancy UUID
            language: Conversation language (default: pt-BR)
            db: SQLAlchemy async session for consent check.
                When None, consent check is skipped (soft failure).

        Returns:
            VoiceScreeningSession. Check session.status:
            - 'initiated' → call placed successfully
            - 'fallback'  → Twilio unavailable, use chat/WhatsApp
            - 'failed'    → API error during call placement

        Raises:
            ConsentNotGrantedError: If consent has been explicitly revoked
        """
        # F-14 (audit 2026-05-22): RuntimeContext fallback for company_id (ADR-029 R-008).
        if not company_id:
            ctx = RuntimeContext.from_contextvars()
            company_id = ctx.company_id or ""

        await self.verify_consent(candidate_id, company_id, db)

        session = VoiceScreeningSession(
            session_id=str(uuid4()),  # Bug #102 fix (phone test 2026-05-23): plain UUID required by wsi_sessions.id UUID column
            candidate_id=candidate_id,
            candidate_name=candidate_name,
            job_title=job_title,
            job_id=job_id,
            company_id=company_id,
            phone_number=phone_number,
            language=language,
            started_at=datetime.utcnow(),
            consent_verified=True,
        )

        try:
            call_result = await TWILIO_VOICE_CIRCUIT.call(
                _twilio_voice_service.make_call,
                to_phone=phone_number,
                candidate_name=candidate_name,
                job_title=job_title,
                session_id=session.session_id,
                language=language,
            )

            if call_result.get("success"):
                session.call_sid = call_result.get("call_sid")
                session.status = "initiated"
                logger.info(
                    "[VOICE SCREENING] Call initiated: session=%s call_sid=%s",
                    session.session_id,
                    session.call_sid,
                )
                if db is not None and session.call_sid:
                    # Sprint 3.3: plugin lifecycle hook owns WSI registration.
                    # VoiceScreeningOrchestrator subclass pre-installs WSIVoicePlugin;
                    # its on_session_initiated calls _register_wsi_session_impl
                    # (the WSI work). Generic VoiceCoreOrchestrator (no plugin) →
                    # no-op (safe).
                    await self._on_session_initiated(session, db)
            else:
                session.status = "failed"
                session.error = call_result.get("error", "Unknown Twilio error")
                logger.error(
                    "[VOICE SCREENING] Call failed: session=%s error=%s",
                    session.session_id,
                    session.error,
                )

        except TwilioVoiceUnconfiguredError as e:
            logger.warning(
                "[VOICE SCREENING] Twilio Voice not configured — returning 'fallback' status. "
                "session=%s Reason: %s",
                session.session_id,
                e,
            )
            session.status = "fallback"
            session.error = (
                "Twilio Voice not configured — use chat/WhatsApp fallback channel"
            )

        except CircuitBreakerError as e:
            logger.warning(
                "[VOICE SCREENING] TWILIO_VOICE_CIRCUIT open — returning 'fallback' status. "
                "session=%s retry_after=%.1fs",
                session.session_id,
                e.retry_after,
            )
            session.status = "fallback"
            session.error = (
                f"Twilio Voice circuit open (retry in {e.retry_after:.0f}s) — "
                "use chat/WhatsApp fallback"
            )

        except Exception as e:
            logger.error("[VOICE SCREENING] Unexpected call error: %s", e)
            session.status = "failed"
            session.error = str(e)

        # F-15: persist to Redis (multi-worker safe) + DB (durable).
        await self._store_session(session)
        if db is not None and session.session_id:
            await self.persist_session_state(session, db)

        # F-03 P1 (audit 2026-05-22): canonical audit trail. LGPD Art. 20 +
        # EU AI Act Art. 12 — voice_call_initiated e decisao automatizada com
        # efeitos significativos (interacao direta com candidato via call).
        await self._log_initiate_call_audit(session)

        return session

    async def _log_initiate_call_audit(self, session: VoiceScreeningSession) -> None:
        """F-03 P1: registra log_decision canonical pos initiate_call.

        Best-effort: nunca propaga exception (audit failure NUNCA bloqueia call).
        """
        try:
            twilio_circuit_state = "unknown"
            try:
                twilio_circuit_state = TWILIO_VOICE_CIRCUIT.state.name
            except Exception:
                pass

            if session.status == "initiated" and session.call_sid:
                action = "outbound_call_placed"
                decision = "approved"
            elif session.status == "fallback":
                action = "fallback_to_chat"
                decision = "degraded_fallback"
            else:
                action = "call_failed"
                decision = "blocked"

            await AuditService().log_decision(
                company_id=session.company_id,
                agent_name="voice_screening_orchestrator",
                decision_type="voice_call_initiated",
                action=action,
                decision=decision,
                reasoning=[
                    f"twilio_call_sid={session.call_sid or 'none'}",
                    f"job_id={session.job_id or 'unscoped'}",
                    f"candidate_phone_hash={mask_phone_preserve_tail(session.phone_number)}",
                    f"circuit_state={twilio_circuit_state}",
                    f"session_status={session.status}",
                ],
                criteria_used=["lgpd_consent_verified", "tenant_isolation"],
                criteria_ignored=list(PROTECTED_CRITERIA_PT),
                candidate_id=session.candidate_id,
                job_vacancy_id=session.job_id,
                human_review_required=False,
            )
        except Exception as audit_err:
            logger.warning(
                "[F-03 AUDIT-FAIL] initiate_call audit log failed (non-blocking): %s",
                audit_err,
            )

    async def initiate_voip_session(
        self,
        candidate_id: str,
        candidate_name: str,
        job_title: str,
        company_id: str,
        job_id: str | None = None,
        language: str = "pt-BR",
        db=None,
    ) -> VoiceScreeningSession:
        """
        Create a VoIP (browser) voice screening session using Gemini Live Audio.

        Provider strategy:
        - VoIP (browser) → Gemini Live Audio (new pipeline, sub-second latency)
        - PSTN (phone) → Twilio pipeline (existing, via initiate_call)

        This method is used when the candidate uses the browser VoIP button.
        It verifies consent, creates the session, and returns it ready for
        WebSocket connection to /gemini-voice/live-stream.

        Fallback: If Gemini Live is unavailable, session status='fallback'
        suggesting the caller try the Twilio pipeline or chat/WhatsApp.

        Args:
            candidate_id: Candidate UUID
            candidate_name: Candidate's display name
            job_title: Job title for screening context
            company_id: Company/tenant UUID
            job_id: Optional job vacancy UUID
            language: Conversation language (default: pt-BR)
            db: SQLAlchemy async session for consent check

        Returns:
            VoiceScreeningSession with voice_provider='gemini_live'

        Raises:
            ConsentNotGrantedError: If consent has been explicitly revoked
        """
        # F-14 (audit 2026-05-22): RuntimeContext fallback for company_id (ADR-029 R-008).
        if not company_id:
            ctx = RuntimeContext.from_contextvars()
            company_id = ctx.company_id or ""

        await self.verify_consent(candidate_id, company_id, db)

        session = VoiceScreeningSession(
            session_id=str(uuid4()),
            candidate_id=candidate_id,
            candidate_name=candidate_name,
            job_title=job_title,
            job_id=job_id,
            company_id=company_id,
            phone_number="voip",
            language=language,
            started_at=datetime.utcnow(),
            consent_verified=True,
            voice_provider="gemini_live",
        )

        try:
            from app.shared.services.gemini_live_audio_service import get_gemini_live_service
            from app.shared.resilience.circuit_breaker import GEMINI_LIVE_CIRCUIT

            live_service = get_gemini_live_service()

            if not live_service.is_available:
                logger.warning(
                    "[VOICE SCREENING] Gemini Live Audio not available — returning fallback. "
                    "session=%s",
                    session.session_id,
                )
                session.status = "fallback"
                session.voice_provider = "fallback"
                session.error = "Gemini Live Audio not configured — use Twilio or chat/WhatsApp"
            elif GEMINI_LIVE_CIRCUIT.state.value == "open":
                logger.warning(
                    "[VOICE SCREENING] GEMINI_LIVE_CIRCUIT open — returning fallback. "
                    "session=%s",
                    session.session_id,
                )
                session.status = "fallback"
                session.voice_provider = "fallback"
                session.error = "Gemini Live Audio circuit open — use Twilio or chat/WhatsApp"
            else:
                live_session = live_service.create_session(
                    candidate_id=candidate_id,
                    candidate_name=candidate_name,
                    job_title=job_title,
                    company_id=company_id,
                    job_id=job_id,
                    language=language,
                )
                session.session_id = live_session.session_id
                session.status = "ready"

                if db is not None:
                    job_context = await self._fetch_job_context_from_db(
                        job_id or "", db, company_id=company_id
                    )
                    if job_context:
                        session.job_context = job_context
                        live_session.job_context = job_context

                    # Sprint 3.3: plugin lifecycle hook owns WSI registration
                    # (see initiate_call sister-comment). Generic mode → no-op.
                    await self._on_session_initiated(session, db)

                logger.info(
                    "[VOICE SCREENING] VoIP session created via Gemini Live: session=%s",
                    session.session_id,
                )

        except Exception as e:
            logger.error(
                "[VOICE SCREENING] VoIP session creation failed: %s", e
            )
            session.status = "fallback"
            session.voice_provider = "fallback"
            session.error = str(e)

        # F-15: persist to Redis (multi-worker safe) + DB (durable).
        await self._store_session(session)
        if db is not None:
            await self.persist_session_state(session, db)
        return session

    async def process_audio_chunk(
        self,
        session_id: str,
        audio_data: bytes,
        mime_type: str = "audio/mulaw",
    ) -> str | None:
        """
        Process an incoming audio chunk from Twilio's bidirectional Media Stream.

        Audio pipeline:
          raw μ-law bytes → WAV with RIFF header → Gemini STT → transcript text

        Twilio Media Streams deliver raw G.711 μ-law at 8kHz mono.
        Gemini requires a valid audio container (WAV). This method performs
        the transcoding before forwarding to STT.

        PII is masked before logging.

        Args:
            session_id: Active screening session ID
            audio_data: Raw μ-law bytes from Twilio WebSocket media event
            mime_type: Original MIME type hint (expected "audio/mulaw")

        Returns:
            Transcribed text segment, or None if insufficient audio/no speech
        """
        if not audio_data or len(audio_data) < 160:
            return None

        try:
            wav_data = mulaw_to_wav(audio_data, sample_rate=8000)
            language = await self._get_session_language(session_id)
            text: str | None = None

            # Primary STT: Gemini Flash
            if _get_voice_service is not None:
                try:
                    voice_svc = _get_voice_service()
                    result = await voice_svc.transcribe_audio(
                        audio_data=wav_data,
                        mime_type="audio/wav",
                        language=language,
                    )
                    text = result.get("text", "").strip() or None
                except Exception as gemini_exc:
                    logger.warning(
                        "[VOICE SCREENING] Gemini STT failed session=%s — attempting Deepgram fallback: %s",
                        session_id,
                        gemini_exc,
                    )

            # Fallback STT: Deepgram nova-2 (if Gemini unavailable or failed)
            if text is None and _deepgram_service is not None:
                try:
                    if _deepgram_service.is_configured():
                        dg_result = await _deepgram_service.transcribe(
                            audio_data=wav_data,
                            mime_type="audio/wav",
                            language=language if language in ("pt-BR", "en-US") else "pt-BR",
                        )
                        text = dg_result.get("transcript", "").strip() or None
                        if text:
                            logger.debug(
                                "[VOICE SCREENING] Deepgram STT fallback success session=%s chars=%d",
                                session_id,
                                len(text),
                            )
                except _DeepgramUnconfiguredError:
                    pass  # Deepgram not configured — continue without transcript
                except Exception as dg_exc:
                    logger.warning(
                        "[VOICE SCREENING] Deepgram STT fallback failed session=%s: %s",
                        session_id,
                        dg_exc,
                    )

            if text is None:
                logger.warning(
                    "[VOICE SCREENING] All STT providers failed or unavailable session=%s",
                    session_id,
                )
                return None

            masked_text = mask_pii(text)
            logger.debug(
                "[VOICE SCREENING] STT segment session=%s: %s",
                session_id,
                masked_text[:100],
            )

            # F-15: load from Redis (no company_id available here — pass None,
            # we rely on session_id PK uniqueness). Falls back to None if not
            # cached; mutation only happens if Redis has the session.
            session = await self._fetch_session(session_id)
            if session:
                # W3-018 (2026-05-23): PII strip ANTES de armazenar.
                # transcript_segments é lido em conversation_history (linha 1606)
                # enviado ao Gemini LLM — armazenar raw vaza PII pra LLM.
                session.transcript_segments.append({
                    "text": strip_pii_for_llm_prompt(text),
                    "timestamp": datetime.utcnow().isoformat(),
                    "role": "candidate",
                })
                # F-15: write back transcript update to Redis.
                await self._store_session(session)

            return text

        except Exception as e:
            logger.error(
                "[VOICE SCREENING] Audio processing error session=%s: %s",
                session_id,
                e,
            )
            return None

    async def generate_lia_response(
        self,
        session_id: str,
        candidate_utterance: str,
        db=None,
    ) -> str:
        """
        Generate LIA's next question/response using Gemini conversational LLM.

        Drives the screening conversation based on:
        - What the candidate said
        - WSI questions loaded from the database (per session)
        - Job requirements context

        Compliance:
        - System prompt includes ANTI_SYCOPHANCY_OPERATIONAL and fairness guardrails
        - All LIA responses pass through FairnessGuard (L1+L2) before delivery
        - Falls back to SCREENING_QUESTIONS_PT only if BOTH WSI questions AND Gemini fail

        Args:
            session_id: Active screening session ID
            candidate_utterance: What the candidate just said
            db: Optional async DB session (used to load WSI questions)

        Returns:
            LIA's next response text (ready for TTS), fairness-checked
        """
        # F-15: load from Redis with reverse-index resolution + DB fallback.
        session = await self._fetch_session(session_id, db=db)
        if not session:
            return "Desculpe, ocorreu um erro. Podemos encerrar a triagem."

        # F-15: ensure mutations (transcript_segments, questions_asked,
        # presentation_done) are written back to Redis on every return path.
        try:
            return await self._generate_lia_response_inner(
                session, candidate_utterance, session_id, db,
            )
        finally:
            try:
                await self._store_session(session)
            except Exception as _exc:
                logger.warning(
                    "[VOICE SCREENING] F-15 Redis writeback failed session=%s: %s",
                    session_id, _exc,
                )

    async def _generate_lia_response_inner(
        self,
        session: "VoiceScreeningSession",
        candidate_utterance: str,
        session_id: str,
        db,
    ) -> str:
        """F-15: extracted body of generate_lia_response to enable try/finally writeback."""
        # F-08 P0 (audit 2026-05-22): PromptInjectionGuard canonical.
        # Candidate utterance (STT output) DEVE passar pelo guard ANTES de
        # virar parte do conversation_history enviado ao Gemini.
        # Fail-CLOSED: guard exception → bloqueia (não vaza raw para LLM).
        if candidate_utterance and candidate_utterance.strip():
            _inj_blocked = False
            _inj_patterns: list[str] = []
            _inj_risk = "none"
            try:
                _inj_result = _voice_injection_guard.check(candidate_utterance)
                if _inj_result.is_suspicious or _inj_result.risk_level == "high":
                    _inj_blocked = True
                    _inj_patterns = list(_inj_result.matched_patterns)
                    _inj_risk = _inj_result.risk_level
            except Exception as _inj_exc:
                # Fail-CLOSED: guard crash → bloqueia mesmo assim.
                logger.warning(
                    "[F-08 VOICE GUARD] PromptInjectionGuard crashed, fail-CLOSED "
                    "session=%s err=%s",
                    session_id, _inj_exc,
                )
                _inj_blocked = True
                _inj_patterns = ["guard_exception"]
                _inj_risk = "high"

            if _inj_blocked:
                logger.warning(
                    "[F-08 VOICE GUARD] PromptInjection blocked session=%s "
                    "patterns=%s risk=%s",
                    session_id, _inj_patterns, _inj_risk,
                )
                # Replace any candidate transcript segment with the raw
                # payload by a safe marker — keeps the LLM's view of
                # conversation_history sanitized for subsequent turns too.
                _marker = "[utterance blocked by guard]"
                for _seg in session.transcript_segments:
                    if _seg.get("role") == "candidate" and _seg.get("text") == candidate_utterance:
                        _seg["text"] = _marker
                        _seg["blocked_reason"] = "prompt_injection"
                # Audit canonical log (LGPD Art. 20 trail). Best-effort —
                # don't let audit failure bypass guard.
                try:
                    await AuditService().log_decision(
                        company_id=session.company_id,
                        agent_name="voice_screening_orchestrator",
                        decision_type="prompt_injection_blocked",
                        action="utterance_filtered",
                        decision="blocked",
                        reasoning=[
                            f"session={session_id}",
                            f"risk={_inj_risk}",
                            f"patterns={','.join(_inj_patterns)}",
                        ],
                        criteria_used=["prompt_injection_guard"],
                        criteria_ignored=[],
                        candidate_id=session.candidate_id,
                        job_vacancy_id=session.job_id,
                        human_review_required=False,
                    )
                except Exception as _audit_exc:
                    logger.error(
                        "[F-08] audit log failed session=%s: %s",
                        session_id, _audit_exc,
                    )
                # Fail-CLOSED: return scripted fallback (não invoca LLM).
                # Load domain question pool for the fallback if not yet cached.
                # Sprint 3.3: _plugin_load_question_pool is the canonical
                # generic-safe dispatcher (delegates to WSIVoicePlugin when present).
                _fallback_qs = getattr(session, "_wsi_questions_cache", None)
                if _fallback_qs is None:
                    _fallback_qs = await self._load_wsi_questions_for_session(session_id, db)
                    if _fallback_qs:
                        session._wsi_questions_cache = _fallback_qs  # type: ignore[attr-defined]
                return self._get_next_scripted_question(session, _fallback_qs)

        wsi_questions = getattr(session, "_wsi_questions_cache", None)
        has_wsi_questions = True
        if wsi_questions is None:
            # Sprint 3.3: _load_wsi_questions_for_session resolves via subclass
            # delegate (VoiceScreeningOrchestrator) → WSIVoicePlugin impl, OR
            # _plugin_load_question_pool on generic core (returns []).
            wsi_questions = await self._load_wsi_questions_for_session(session_id, db)
            if wsi_questions:
                session._wsi_questions_cache = wsi_questions  # type: ignore[attr-defined]
            else:
                has_wsi_questions = False
                logger.info(
                    "[VOICE SCREENING] No WSI questions in DB for session=%s — "
                    "Gemini will generate contextual questions autonomously",
                    session_id,
                )

        # Load job context from DB if not yet available in session
        if session.job_context is None and session.job_id:
            session.job_context = await self._fetch_job_context_from_db(
                session.job_id, db, company_id=session.company_id
            )
            if session.job_context:
                logger.info(
                    "[VOICE SCREENING] Job context loaded for session=%s job_id=%s",
                    session_id, session.job_id,
                )

        try:
            from google.genai import types  # W3-027-EXEMPT: google.genai.types for type building — client via get_gemini_client_for_tenant

            # === Tenant-aware Gemini client (LGPD compliance) ===
            try:
                from app.shared.tenant_llm_context import get_gemini_client_for_tenant
                client = get_gemini_client_for_tenant(session.company_id)
            except (ValueError, Exception) as _client_err:
                logger.warning("[VoiceOrchestrator] Gemini unavailable: %s", _client_err)
                if not session.presentation_done:
                    session.presentation_done = True
                    return self._build_fallback_job_presentation(session)
                return self._get_next_scripted_question(session, wsi_questions if has_wsi_questions else None)

            questions_asked = session.questions_asked
            next_q_index = len(questions_asked)

            total_questions = len(wsi_questions) if has_wsi_questions else 5
            is_last = next_q_index >= total_questions - 1

            # Compliance and fairness guardrails injected into system prompt
            fairness_instructions = (
                "\n=== COMPLIANCE E FAIRNESS — REGRAS ABSOLUTAS ===\n"
                "PERGUNTAS PROIBIDAS (nunca pergunte):\n"
                "- Idade, data de nascimento, geração\n"
                "- Gênero, identidade de gênero, orientação sexual\n"
                "- Raça, cor, etnia, naturalidade\n"
                "- Estado civil, filhos, gravidez, planos de família\n"
                "- Religião, crenças, filiação política ou sindical\n"
                "- Condições de saúde, deficiências, uso de medicamentos\n"
                "- Situação financeira pessoal, endereço residencial\n"
                "- Aparência física, peso, altura\n"
                "\nPERGUNTAS DO CANDIDATO — O QUE VOCÊ PODE RESPONDER:\n"
                "- Sobre benefícios, salário, formato de trabalho, localização → responda com base no job description acima\n"
                "- Sobre a descrição do cargo, responsabilidades, competências → responda com base no job description acima\n"
                "- Sobre as etapas do processo seletivo → explique que é uma triagem inicial e que a empresa entrará em contato\n"
                "- Sobre a empresa, cultura → use informações do job description se disponíveis; caso contrário, diga que não tem essa informação\n"
                "\nPERGUNTAS QUE VOCÊ DEVE REDIRECIONAR COM EDUCAÇÃO:\n"
                "- Sobre informações não presentes no job description → diga 'Não tenho essa informação disponível, mas posso encaminhar sua dúvida ao recrutador.'\n"
                "- Fora do escopo da triagem → redirecione gentilmente: 'Essa é uma ótima pergunta! Recomendo tirá-la diretamente com o time de RH. Posso continuar com a triagem?'\n"
                "\nINFORMAÇÕES QUE VOCÊ DEVE RECUSAR:\n"
                "- Qualquer dado que não foi disponibilizado pela empresa (ex: salário do CEO, detalhes internos)\n"
                "- Comparações entre candidatos\n"
                "- Previsão de resultado da triagem ou probabilidade de aprovação\n"
                "\nANTI-SYCOPHANCY: Nunca elogie excessivamente as respostas do candidato. Valide de forma breve e neutra.\n"
                "LGPD: Não solicite dados pessoais além dos necessários para a triagem.\n"
                "(LGPD, CLT Art. 5º, CF Art. 5º, Lei 9.029/95, Lei 13.146/15)\n"
            )

            # Build job description context for the system prompt (Task 2)
            if session.job_context:
                job_context_block = (
                    "\n=== JOB DESCRIPTION — CONTEXTO DA VAGA ===\n"
                    + self._build_job_context_summary(session.job_context)
                    + "\n\nUse APENAS estas informações ao responder perguntas do candidato sobre a vaga. "
                    "Não invente ou presuma informações não presentes acima.\n"
                )
            else:
                job_context_block = (
                    f"\n=== CONTEXTO DA VAGA ===\n"
                    f"Título: {session.job_title}\n"
                    f"(Informações detalhadas da vaga não disponíveis. Use apenas o título.)\n"
                )

            if has_wsi_questions:
                question_guidance = (
                    f"Progresso da triagem: {next_q_index} de {len(wsi_questions)} perguntas realizadas.\n"
                    f"{'ÚLTIMA PERGUNTA: encerre a triagem com cordialidade após a resposta do candidato.' if is_last else ''}\n"
                )
            else:
                question_guidance = (
                    f"Progresso da triagem: {next_q_index} de ~{total_questions} perguntas realizadas.\n"
                    f"{'ÚLTIMA PERGUNTA: encerre a triagem com cordialidade após a resposta do candidato.' if is_last else ''}\n"
                    "IMPORTANTE: Gere perguntas comportamentais e técnicas relevantes para a vaga.\n"
                    "Use a metodologia STAR (Situação, Tarefa, Ação, Resultado).\n"
                )

            # === F-10 + F-11 (audit 2026-05-22) ===
            # Build voice system prompt via canonical SystemPromptBuilder so
            # per-tenant AI Persona (E2.3 name+tone) + lia_field_toggles
            # filter (build_company_agent_context) are honored in voice.
            # Pre-fix this surface bypassed both → ghost setting parcial.
            from app.shared.prompts.voice_system_prompt import (
                build_voice_system_prompt,
            )

            try:
                canonical_prompt = await build_voice_system_prompt(
                    company_id=session.company_id,
                    db=db,
                    job_context=session.job_context,
                )
            except Exception as _prompt_err:  # noqa: BLE001
                # Should be impossible (helper itself catches and degrades),
                # but defense in depth: voice MUST NOT crash if canonical
                # build hiccups — fall back to legacy static persona.
                logger.warning(
                    "[VOICE SCREENING] build_voice_system_prompt failed for "
                    "session=%s company=%s; using legacy static persona. Reason: %s",
                    session.session_id, session.company_id, _prompt_err,
                )
                canonical_prompt = (
                    "Recrutadora inteligente da WeDO Talent. Conduza a triagem por voz "
                    "com naturalidade, empatia e profissionalismo."
                )

            # Build the system prompt: canonical persona + lia_field_toggles +
            # voice-specific block FIRST, then runtime job-context/progress/
            # fairness/anti-sycophancy. Order matters — LLM weights early
            # sections more heavily; persona override sits above fairness.
            system_prompt = (
                f"{canonical_prompt}\n\n"
                f"=== CONTEXTO DESTA TRIAGEM ===\n"
                f"IDIOMA: {session.language}\n\n"
                f"CANDIDATO: {session.candidate_name}\n"
                f"{job_context_block}\n"
                f"PROGRESSO:\n{question_guidance}\n"
                f"INSTRUÇÕES DE CONDUTA (runtime):\n"
                f"- Faça UMA pergunta por vez — nunca empilhe perguntas\n"
                f"- Valide brevemente a resposta anterior com uma transição natural (ex: 'Entendi!', 'Ótimo, obrigada!')\n"
                f"- Se o candidato fizer uma pergunta sobre a vaga, responda com base no job description antes de continuar\n"
                f"- Se o candidato quiser pular a apresentação ou ir direto às perguntas, respeite e inicie as perguntas\n"
                f"- Conduza a conversa com fluidez — valide, faça follow-up quando relevante, depois avance\n"
                f"- Ao encerrar, agradeça, informe que o time entrará em contato, e despeça-se com cordialidade\n"
                f"{fairness_instructions}\n"
                f"{ANTI_SYCOPHANCY_OPERATIONAL}"
            )

            conversation_history = []
            for seg in session.transcript_segments[-8:]:
                role = "user" if seg.get("role") == "candidate" else "model"
                conversation_history.append(
                    types.Content(role=role, parts=[types.Part(text=seg["text"])])
                )

            if not conversation_history or conversation_history[-1].role != "user":
                conversation_history.append(
                    types.Content(
                        role="user",
                        parts=[types.Part(text=candidate_utterance)],
                    )
                )

            # First turn after consent: present the vacancy before starting questions.
            # Capture presentation state before generation so we can correctly determine
            # whether to count this as a question turn when updating questions_asked.
            is_presentation_turn = not session.presentation_done
            if is_presentation_turn:
                next_prompt = self._build_job_presentation_instruction(session)
            elif is_last:
                next_prompt = (
                    "O candidato acabou de responder à última pergunta. "
                    "Agradeça de forma calorosa e natural, informe que o processo continua e que a empresa entrará em contato. "
                    "Despeça-se profissionalmente."
                )
            elif has_wsi_questions:
                next_q = wsi_questions[next_q_index]
                next_prompt = (
                    f"Valide brevemente a resposta do candidato com uma transição natural, "
                    f"depois faça esta pergunta exatamente: {next_q}"
                )
            else:
                next_prompt = (
                    "Valide brevemente a resposta do candidato com uma transição natural. "
                    "Depois gere a próxima pergunta comportamental ou técnica relevante para a vaga. "
                    "Use metodologia STAR. Faça UMA pergunta apenas."
                )

            conversation_history.append(
                types.Content(
                    role="user",
                    parts=[types.Part(text=f"[INSTRUÇÃO INTERNA — NÃO REPITA]: {next_prompt}")],
                )
            )

            response = self._llm_service.generate_native_gemini_sync(
                contents=conversation_history,
                model="gemini-2.5-flash",
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.7,
                    max_output_tokens=300,
                ),
            )

            # P1 ticket #1 (2026-05-23): canonical Gemini LLM token tracking
            # for billing. Best-effort: ausencia de usage_metadata (mock,
            # streaming partial) NAO bloqueia path principal — defaults 0.
            try:
                usage = getattr(response, "usage_metadata", None)
                if usage is not None:
                    prompt_count = getattr(usage, "prompt_token_count", 0) or 0
                    candidates_count = getattr(usage, "candidates_token_count", 0) or 0
                    session.llm_tokens_input += int(prompt_count)
                    session.llm_tokens_output += int(candidates_count)
            except Exception as token_err:  # noqa: BLE001
                logger.debug(
                    "[VOICE SCREENING] token accumulation failed session=%s "
                    "(non-blocking): %s",
                    session_id,
                    token_err,
                )

            lia_text = response.text.strip() if response.text else ""

            if lia_text:
                fairness_result = check_fairness(
                    texts={"lia_voice_response": lia_text},
                    context="voice_screening",
                    company_id=session.company_id,
                )
                if fairness_result.is_blocked:
                    logger.warning(
                        "[VOICE SCREENING] FairnessGuard BLOCKED LIA response session=%s "
                        "category=%s — using safe fallback question",
                        session_id,
                        fairness_result.blocked_result.category if fairness_result.blocked_result else "unknown",
                    )
                    # Mark presentation done even on blocked to avoid loop
                    if not session.presentation_done:
                        session.presentation_done = True
                    return self._get_next_scripted_question(session, wsi_questions if has_wsi_questions else None)

                # Mark presentation as done after first successful turn
                if is_presentation_turn:
                    session.presentation_done = True
                    # Persist immediately so restart doesn't repeat presentation
                    await self.persist_session_state(session, db)
                else:
                    # Only track question progress on actual question turns (not presentation)
                    if has_wsi_questions and not is_last and next_q_index < len(wsi_questions):
                        session.questions_asked.append(wsi_questions[next_q_index])
                    elif not has_wsi_questions and not is_last:
                        session.questions_asked.append(lia_text[:200])

                session.transcript_segments.append({
                    # W3-018: defense-in-depth · LIA response também pode
                    # ter PII (echo de candidate, name/email mention).
                    "text": strip_pii_for_llm_prompt(lia_text),
                    "timestamp": datetime.utcnow().isoformat(),
                    "role": "lia",
                })

            if lia_text:
                return lia_text

            # Fallback: if Gemini returned empty, use scripted question
            if not session.presentation_done:
                session.presentation_done = True
                return self._build_fallback_job_presentation(session)
            return self._get_next_scripted_question(session, wsi_questions if has_wsi_questions else None)

        except Exception as e:
            logger.error(
                "[VOICE SCREENING] Gemini response generation failed session=%s: %s",
                session_id,
                e,
            )
            if not session.presentation_done:
                session.presentation_done = True
                return self._build_fallback_job_presentation(session)
            return self._get_next_scripted_question(session, wsi_questions if has_wsi_questions else None)

    @staticmethod
    def _build_job_presentation_instruction(session: "VoiceScreeningSession") -> str:
        """
        Build the Gemini instruction for the job presentation phase (Task 4).

        This is injected as the first turn instruction: LIA presents the job
        description, asks if the candidate has questions, and offers to skip.
        """
        job = session.job_context or {}

        parts = [
            "Apresente a vaga ao candidato de forma natural e envolvente (como uma recrutadora experiente, não um leitor de script). "
            "Use as informações do job description disponíveis no contexto do sistema. "
            "Inclua: título da vaga, principais responsabilidades/atividades, formato de trabalho (remoto/híbrido/presencial) "
            "e benefícios principais se disponíveis. "
            "Seja concisa e conversacional — o candidato está ouvindo por telefone, então seja clara e organizada. "
            "Após a apresentação, pergunte de forma natural: 'Você tem alguma dúvida sobre a vaga antes de começarmos as perguntas? "
            "Ou prefere ir direto às perguntas?' — isso permite que o candidato escolha pular a apresentação se quiser."
        ]

        if not job:
            parts.append(
                f"Se não houver detalhes no job description, mencione apenas o título '{session.job_title}' "
                f"e diga que a vaga oferece uma oportunidade de crescimento. Não invente benefícios ou responsabilidades."
            )

        return " ".join(parts)

    @staticmethod
    def _build_fallback_job_presentation(session: "VoiceScreeningSession") -> str:
        """
        Build a static fallback job presentation when Gemini is unavailable (Task 4).

        Uses job_context if available, otherwise falls back to job_title only.
        """
        job = session.job_context or {}
        title = job.get("title") or session.job_title

        parts = [f"Ótimo, vou te contar um pouco sobre a vaga de {title}."]

        work_model = job.get("work_model")
        if work_model:
            parts.append(f"O formato de trabalho é {work_model}.")

        location = job.get("location")
        if location:
            parts.append(f"A posição é em {location}.")

        benefits = job.get("benefits") or []
        if benefits:
            ben_text = ", ".join(str(b) for b in benefits[:4])
            parts.append(f"Entre os benefícios, temos: {ben_text}.")

        salary = job.get("salary")
        if salary:
            parts.append(f"A remuneração é {salary}.")

        parts.append(
            "Você tem alguma dúvida sobre a vaga antes de começarmos? "
            "Ou prefere ir direto às perguntas da triagem?"
        )

        return " ".join(parts)

    def _get_next_scripted_question(
        self,
        session: VoiceScreeningSession,
        questions: list[str] | None = None,
    ) -> str:
        """
        Fallback: return next question when Gemini is unavailable or FairnessGuard blocks.

        Uses `questions` list (WSI questions from DB) when provided;
        falls back to SCREENING_QUESTIONS_PT only as last resort.

        All returned text passes through FairnessGuard before delivery.
        """
        question_pool = questions if questions else self.SCREENING_QUESTIONS_PT
        asked = len(session.questions_asked)
        if asked < len(question_pool):
            q = question_pool[asked]
            q = self._check_fairness_on_response(q, session)
            session.questions_asked.append(q)
            session.transcript_segments.append({
                # W3-018: canned questions são low-PII mas mantém pattern
                "text": strip_pii_for_llm_prompt(q),
                "timestamp": datetime.utcnow().isoformat(),
                "role": "lia",
            })
            return q
        closing = (
            "Muito obrigada pela sua participação! Encerramos a triagem por aqui. "
            "Nossa equipe entrará em contato em breve. Tenha um ótimo dia!"
        )
        return self._check_fairness_on_response(closing, session)

    # F-16 P1 fail-CLOSED safe neutral fallback (Decisao Paulo 2026-05-22).
    # Constante de modulo para reuso sem recursao em _get_next_scripted_question.
    _FAIRNESS_SAFE_NEUTRAL_FALLBACK = (
        "Poderia me contar mais sobre sua experiência profissional "
        "e como ela se relaciona com esta vaga?"
    )

    def _check_fairness_on_response(self, text: str, session: VoiceScreeningSession) -> str:
        """
        Run FairnessGuard on any outbound LIA text. Returns safe replacement if blocked
        OU se o engine falhar (F-16 P1 fail-CLOSED, Decisao Paulo 2026-05-22).

        Antes: exception -> texto raw passava (risco fairness violation em outage transitorio).
        Depois: exception -> safe neutral fallback + audit canonical (LGPD Art. 20 trail).
        """
        try:
            result = check_fairness(
                texts={"lia_voice_response": text},
                context="voice_screening",
                company_id=session.company_id,
            )
            if result.is_blocked:
                logger.warning(
                    "[VOICE SCREENING] FairnessGuard BLOCKED scripted/fallback response "
                    "session=%s — replacing with neutral prompt",
                    session.session_id,
                )
                return self._FAIRNESS_SAFE_NEUTRAL_FALLBACK
            return text
        except Exception as e:
            # F-16 P1 fail-CLOSED: nao retornar raw text. Substituir por safe neutral
            # E registrar audit canonical para LGPD/EU AI Act trail.
            logger.error(
                "[F-16 FAIL-CLOSED] FairnessGuard check failed session=%s: %s — "
                "using scripted safe fallback (fail-CLOSED Decisao Paulo 2026-05-22)",
                session.session_id, e, exc_info=True,
            )
            # Best-effort audit canonical — engine failure exigi rastreabilidade
            try:
                import asyncio

                from app.shared.compliance.audit_service import AuditService

                _err_captured = e  # closure capture (e is deleted on except exit)
                async def _log_canonical():
                    try:
                        await AuditService().log_decision(
                            company_id=session.company_id,
                            agent_name="voice_screening_orchestrator",
                            decision_type="fairness_guard_failure",
                            action="utterance_filtered_failclosed",
                            decision="blocked_failclosed",
                            reasoning=[
                                f"engine_error={type(_err_captured).__name__}: {str(_err_captured)[:200]}",
                                f"session={session.session_id}",
                                f"failclosed_fallback_used=safe_neutral",
                            ],
                            criteria_used=["fail_closed_safety", "lgpd_art_20"],
                            criteria_ignored=[],
                            candidate_id=session.candidate_id,
                            job_vacancy_id=session.job_id,
                            human_review_required=True,
                        )
                    except Exception:
                        # Audit failure must NOT bypass fail-CLOSED behavior
                        logger.exception("[F-16] Audit log failed (non-blocking)")

                # Schedule audit best-effort: prefer loop.create_task if running, else
                # spin up isolated loop, else give up silently (fail-CLOSED ja ativo).
                try:
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(_log_canonical())
                    except RuntimeError:
                        # No running loop in current thread — use a one-off
                        asyncio.run(_log_canonical())
                except Exception:
                    # Best-effort: audit failure must not bypass fail-CLOSED
                    pass
            except Exception:
                # Module import failure: still fail-CLOSED, just no audit
                pass
            return self._FAIRNESS_SAFE_NEUTRAL_FALLBACK

    async def synthesize_lia_response(
        self,
        text: str,
        voice: str = "nova",
        for_twilio_stream: bool = True,
    ) -> bytes | None:
        """
        Convert LIA's response text to audio for Twilio Media Stream playback.

        Audio pipeline:
          text → OpenAI TTS → MP3 → mp3_to_mulaw() → raw μ-law 8kHz → Twilio

        Twilio bidirectional Media Streams require raw μ-law/PCM payload;
        MP3 is transcoded via pydub. If transcoding is unavailable, None is
        returned and caller should use TwiML <Say> instead of streaming.

        Args:
            text: LIA response text to synthesize
            voice: OpenAI TTS voice name
            for_twilio_stream: If True, returns μ-law bytes for Twilio stream.
                               If False, returns MP3 bytes for other uses.

        Returns:
            Audio bytes (μ-law for Twilio stream, MP3 otherwise), or None if
            synthesis or transcoding fails.
        """
        try:
            audio_mp3 = await self._tts_service.synthesize_speech(
                text=text,
                voice=voice,
                speed=1.0,
                model="tts-1",
            )

            if not for_twilio_stream:
                return audio_mp3

            mulaw_bytes = mp3_to_mulaw(audio_mp3)
            if mulaw_bytes is None:
                logger.warning(
                    "[VOICE SCREENING] TTS→μ-law transcoding unavailable — "
                    "caller should use TwiML <Say> as fallback"
                )
            return mulaw_bytes

        except Exception as e:
            logger.warning("[VOICE SCREENING] TTS synthesis failed (non-blocking): %s", e)
            return None

    async def finalize_screening(
        self,
        session_id: str,
        db=None,
    ) -> dict[str, Any]:
        """
        Finalize screening session: run WSI analysis on full transcript.

        - Merges all transcript segments into full transcript
        - Applies PII masking before logging/storage (LGPD Art. 12)
        - Runs WSI voice analysis pipeline (analyze_voice_screening)
        - Updates session status

        Args:
            session_id: Screening session ID
            db: SQLAlchemy async session (optional — for WSI persistence)

        Returns:
            Analysis result dict with WSI scores and recommendation
        """
        # F-15: load from Redis (with reverse-index lookup) + DB fallback.
        session = await self._fetch_session(session_id, db=db)
        if not session:
            logger.error("[VOICE SCREENING] Session not found: %s", session_id)
            return {"error": "Session not found", "session_id": session_id}

        session.ended_at = datetime.utcnow()
        session.status = "analyzing"

        full_transcript = "\n".join(
            f"{'CANDIDATO' if seg.get('role') == 'candidate' else 'LIA'}: {seg['text']}"
            for seg in session.transcript_segments
        )

        masked_transcript = mask_pii(full_transcript)
        logger.info(
            "[VOICE SCREENING] Finalizing session=%s transcript_chars=%d",
            session_id,
            len(full_transcript),
        )

        duration_seconds = None
        if session.started_at and session.ended_at:
            duration_seconds = int(
                (session.ended_at - session.started_at).total_seconds()
            )

        masked_segments = self._mask_transcript_segments(session.transcript_segments)

        # F-17 P1 canonical WSI completion strategy: PRIMARY / FALLBACK / SKIP.
        # Single rastreamento de qual estrategia foi usada (telemetria + audit).
        wsi_strategy = "skip"  # default: nem PRIMARY nem FALLBACK conseguiram
        wsi_strategy_error: str | None = None

        try:
            wsi_result = None

            # PRIMARY: wsi_voice_orchestrator (canonical full pipeline)
            if _WSIVoiceOrchestrator is not None and session.call_sid:
                try:
                    wsi_orch = _WSIVoiceOrchestrator()
                    wsi_result = await wsi_orch.process_call_completed(
                        call_id=session.call_sid,
                        transcript=masked_transcript,
                        transcript_object=masked_segments,
                        db=db,
                    )
                    if wsi_result is not None:
                        wsi_strategy = "primary"
                        logger.info(
                            "[F-17 WSI-STRATEGY] PRIMARY wsi_voice_orchestrator complete session=%s",
                            session_id,
                        )
                except Exception as wsi_err:
                    wsi_strategy_error = f"primary_failed: {type(wsi_err).__name__}: {wsi_err}"
                    logger.warning(
                        "[F-17 WSI-STRATEGY] PRIMARY (wsi_voice_orchestrator) failed session=%s, "
                        "trying FALLBACK: %s",
                        session_id, wsi_err,
                    )

            # FALLBACK: analyze_voice_screening (standalone LLM)
            if wsi_result is None:
                analyze_fn = _analyze_voice_screening
                if analyze_fn is None:
                    raise ImportError(
                        "Neither wsi_voice_orchestrator nor analyze_voice_screening available"
                    )

                try:
                    wsi_result = await analyze_fn(
                        transcript=masked_transcript,
                        transcript_object=masked_segments,
                        job_title=session.job_title,
                        candidate_name=None,
                        duration_seconds=duration_seconds,
                    )
                    if wsi_result is not None:
                        wsi_strategy = "fallback"
                        logger.info(
                            "[F-17 WSI-STRATEGY] FALLBACK analyze_voice_screening complete session=%s",
                            session_id,
                        )
                except Exception as fallback_err:
                    if wsi_strategy_error:
                        wsi_strategy_error = f"{wsi_strategy_error}; fallback_failed: {fallback_err}"
                    else:
                        wsi_strategy_error = f"fallback_failed: {fallback_err}"
                    logger.error(
                        "[F-17 WSI-STRATEGY] FALLBACK also failed session=%s — SKIP strategy: %s",
                        session_id, fallback_err,
                    )

            if wsi_result is None:
                # SKIP: ambos falharam. RuntimeError canonical.
                raise RuntimeError(
                    f"WSI completion SKIP — both strategies failed: {wsi_strategy_error or 'no diagnostic'}"
                )

            score = (
                wsi_result.get("overall_evaluation", {}).get("overall_score", "?")
                if isinstance(wsi_result, dict)
                else "?"
            )
            session.wsi_result = wsi_result if isinstance(wsi_result, dict) else wsi_result.dict() if hasattr(wsi_result, "dict") else str(wsi_result)
            session.status = "completed"

            logger.info(
                "[VOICE SCREENING] Analysis complete session=%s score=%s",
                session_id,
                score,
            )

            await self.persist_session_state(session, db)
            # F-15: writeback to Redis (durable cache for ongoing reads).
            await self._store_session(session)

            # F-03 P1: canonical audit trail (LGPD Art. 20 + EU AI Act Art. 12)
            await self._log_finalize_screening_audit(
                session=session,
                wsi_score=score,
                duration_seconds=duration_seconds,
                wsi_available=True,
                wsi_strategy=wsi_strategy,
            )

            # F-19 P1: canonical billing via agent_pricing.compute_voice_credits
            await self._record_voice_billing(
                session=session,
                duration_seconds=duration_seconds,
                db=db,
            )

            # Agent J: emit canonical event candidate_screened (event-driven loop).
            # Fail-safe: publish_platform_event swallows RabbitMQ errors (logs only).
            try:
                await publish_platform_event(
                    PlatformEvent(
                        event_type="candidate_screened",
                        company_id=str(session.company_id),
                        payload={
                            "candidate_id": str(session.candidate_id),
                            "session_id": str(session.session_id),
                            "score": score,
                            "wsi_strategy": wsi_strategy,
                            "completed_at": datetime.utcnow().isoformat(),
                        },
                        source_api="lia-agent-system",
                    )
                )
            except Exception as emit_err:
                logger.warning(
                    "[VOICE SCREENING] publish_platform_event candidate_screened failed: %s",
                    emit_err,
                )

            return {
                "session_id": session_id,
                "status": "completed",
                "duration_seconds": duration_seconds,
                "transcript_length": len(full_transcript),
                "wsi_result": session.wsi_result,
                "wsi_strategy": wsi_strategy,
                "provider": "twilio_voice_gemini",
            }

        except Exception as e:
            logger.error(
                "[VOICE SCREENING] WSI analysis failed session=%s: %s", session_id, e
            )
            session.status = "analysis_failed"
            session.error = str(e)
            await self.persist_session_state(session, db)
            # F-15: writeback to Redis.
            await self._store_session(session)

            # F-03 P1: canonical audit trail mesmo em failure path
            await self._log_finalize_screening_audit(
                session=session,
                wsi_score=None,
                duration_seconds=duration_seconds,
                wsi_available=False,
                error=str(e),
                wsi_strategy="skip",
            )

            return {
                "session_id": session_id,
                "status": "analysis_failed",
                "error": str(e),
                "transcript_length": len(full_transcript),
                "wsi_strategy": "skip",
            }

    async def _record_voice_billing(
        self,
        session: VoiceScreeningSession,
        duration_seconds: int | None,
        db,
    ) -> None:
        """F-19 P1: canonical billing via agent_pricing.compute_voice_credits.

        Voice usa Twilio + Deepgram + Gemini + OpenAI TTS — todos cobram por
        minuto/tokens, mas voice era billing ghost. Esta funcao computa custo
        real e registra via agent_marketplace_service.record_execution.

        Best-effort: nunca propaga exception (billing failure NUNCA bloqueia
        finalize). Log warning para observability.

        P1 ticket #1 (2026-05-23): tokens canonical lidos de
        session.llm_tokens_input/llm_tokens_output (acumulado em
        generate_lia_response via usage_metadata). Antes era hardcoded 0
        (billing ghost). Backward-compat: legacy sessions sem tracking
        defaults 0, billing por audio+twilio inalterado.
        """
        if duration_seconds is None or duration_seconds <= 0:
            return  # Nada para cobrar
        try:
            # Best-effort import (evita hard fail em testes que nao mockam marketplace)
            from app.services.agent_marketplace_service import agent_marketplace_service
            from app.services.agent_pricing import compute_voice_credits

            # Pricing tier — default 'pro' ate query canonical do company
            pricing_tier = await self._resolve_pricing_tier(session.company_id, db)

            credits = compute_voice_credits(
                total_audio_seconds=duration_seconds,
                # P1 ticket #1: canonical Gemini LLM tokens (was hardcoded 0)
                tokens_input=int(getattr(session, "llm_tokens_input", 0) or 0),
                tokens_output=int(getattr(session, "llm_tokens_output", 0) or 0),
                tier=pricing_tier,
            )

            if credits > 0 and db is not None:
                # voice_screening_orchestrator agent_id = sentinel constante
                await agent_marketplace_service.record_execution(
                    db=db,
                    agent_id="voice_screening_orchestrator",
                    company_id=session.company_id,
                    credits_consumed=credits,
                    pricing_tier=pricing_tier,
                )
                logger.info(
                    "[F-19 BILLING] Voice session billed session=%s credits=%d duration=%ds tier=%s",
                    session.session_id, credits, duration_seconds, pricing_tier,
                )
        except Exception as billing_err:
            logger.warning(
                "[F-19 BILLING] Voice billing failed (non-blocking) session=%s: %s",
                session.session_id, billing_err,
            )

    async def _resolve_pricing_tier(self, company_id: str, db) -> str:
        """F-19: best-effort lookup company pricing tier; default 'pro'."""
        if db is None or not company_id:
            return "pro"
        try:
            # F-13 (audit 2026-05-22): canonical read via TenantRepository (ADR-001).
            from app.domains.company.repositories.tenant_repository import TenantRepository
            tier = await TenantRepository(db).get_pricing_tier(company_id)
            if tier:
                return tier
        except Exception:
            pass
        return "pro"

    async def _log_finalize_screening_audit(
        self,
        session: VoiceScreeningSession,
        wsi_score,
        duration_seconds: int | None,
        wsi_available: bool,
        error: str | None = None,
        wsi_strategy: str = "unknown",
    ) -> None:
        """F-03 P1: registra log_decision canonical pos finalize_screening.

        F-17 P1: agora inclui wsi_strategy no reasoning (primary/fallback/skip).

        Best-effort: nunca propaga exception (audit failure NUNCA bloqueia finalize).
        """
        try:
            if wsi_available and wsi_score not in (None, "?"):
                action = "wsi_score_computed"
                decision = "completed"
            else:
                action = "session_closed_no_score"
                decision = "completed_no_score"

            reasoning = [
                f"session_id={session.session_id}",
                f"wsi_score={wsi_score if wsi_score is not None else 'none'}",
                f"wsi_strategy={wsi_strategy}",
                f"transcript_turns={len(session.transcript_segments)}",
                f"duration_seconds={duration_seconds or 0}",
            ]
            if error:
                reasoning.append(f"error={error[:200]}")

            await AuditService().log_decision(
                company_id=session.company_id,
                agent_name="voice_screening_orchestrator",
                decision_type="voice_screening_finalized",
                action=action,
                decision=decision,
                reasoning=reasoning,
                criteria_used=["wsi_evaluation_canonical", "fairness_validated_outbound"],
                criteria_ignored=list(PROTECTED_CRITERIA_PT),
                candidate_id=session.candidate_id,
                job_vacancy_id=session.job_id,
                human_review_required=False,
            )
        except Exception as audit_err:
            logger.warning(
                "[F-03 AUDIT-FAIL] finalize_screening audit log failed (non-blocking): %s",
                audit_err,
            )

    async def get_session(self, session_id: str) -> VoiceScreeningSession | None:
        """Get an active screening session by ID.

        F-15: now async + Redis-backed (multi-worker safe). Resolves company_id
        via reverse index, then reads canonical state. Returns None if not found.
        """
        return await self._fetch_session(session_id)

    async def get_or_restore_session(
        self, session_id: str, db=None
    ) -> VoiceScreeningSession | None:
        """
        Get session from Redis cache or restore from PostgreSQL if not found.

        This supports server-restart + multi-worker recovery: if the session is
        not in Redis (e.g. after a deploy / TTL expiry), it is loaded from
        wsi_sessions.voice_session_state and rehydrated into Redis.

        Args:
            session_id: Screening session ID
            db: Async DB session for DB lookup

        Returns:
            VoiceScreeningSession or None if not found anywhere
        """
        # F-15: unified path — _fetch_session does Redis-first then DB fallback,
        # with opportunistic Redis rehydrate on DB hit.
        return await self._fetch_session(session_id, db=db)

    async def _get_session_language(self, session_id: str) -> str:
        # F-15: async Redis lookup with reverse-index resolution.
        session = await self._fetch_session(session_id)
        return session.language if session else "pt-BR"

    async def list_active_sessions(
        self, company_id: str | None = None
    ) -> list[dict[str, Any]]:
        """List all active (non-completed) screening sessions.

        F-15: now async + Redis-backed. When company_id provided, scopes the
        listing to that tenant (canonical multi-tenancy). When None, returns
        empty list with warning — cross-tenant enumeration is disallowed.
        """
        if not company_id:
            logger.warning(
                "[VOICE SCREENING] list_active_sessions() called without "
                "company_id; cross-tenant enumeration disallowed (returning [])"
            )
            return []

        session_ids = await self._session_repo.list_active_session_ids(
            company_id=company_id,
        )
        results: list[dict[str, Any]] = []
        for sid in session_ids:
            state = await self._session_repo.load_session_state(
                company_id=company_id, session_id=sid,
            )
            if not state:
                continue
            status = state.get("status")
            if status in ("completed", "failed"):
                continue
            started_at = state.get("started_at")
            results.append(
                {
                    "session_id": state.get("session_id"),
                    "candidate_name": mask_pii(state.get("candidate_name", "")),
                    "job_title": state.get("job_title"),
                    "status": status,
                    "started_at": started_at,
                }
            )
        return results

    # Sprint 3.3: _register_wsi_session + _generate_and_store_wsi_questions
    # MOVED to WSIVoicePlugin (_register_wsi_session_impl +
    # _generate_and_store_wsi_questions_impl). VoiceScreeningOrchestrator
    # subclass (below) keeps thin delegate methods of the same name for
    # backward compatibility with tests that patch them. Generic
    # VoiceCoreOrchestrator without a WSI plugin = no WSI registration
    # (intentional — generic mode is pure voice transport).

    @staticmethod
    def _mask_transcript_segments(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Return a copy of transcript_segments with PII masked in text fields.

        Ensures no unmasked PII reaches WSI persistence layer (LGPD Art. 12 / SEG-3B).
        """
        masked = []
        for seg in segments:
            masked.append({
                **seg,
                "text": mask_pii(seg.get("text", "")),
            })
        return masked

    # ── Sprint 3.2 plugin lifecycle hooks ──────────────────────────────────
    #
    # Invoked at canonical lifecycle points by core methods. Each iterates all
    # registered plugins in order. Errors are caught + logged but NEVER block
    # the voice call (best-effort semantics — production voice traffic must
    # not fail because a plugin misbehaved).

    async def _on_session_initiated(
        self,
        session: "VoiceScreeningSession",
        db: Any,
    ) -> None:
        """Fan out to all plugins' on_session_initiated hook (best-effort).

        C.3 (2026-05-23): also pre-computes the bootstrap initial_greeting via
        ``_plugin_next_question`` and caches it in
        ``session.metadata["initial_greeting"]``. Downstream consumers
        (Studio runtime, frontend /voice/initiate response, Twilio TwiML
        callback) can render the "agent talks first" UX without making an
        extra round-trip.

        Only inserts the key when a plugin actually returns a non-empty
        greeting — avoids surfacing noise when running without plugins.
        """
        for plugin in self._plugins:
            try:
                await plugin.on_session_initiated(session, db)
            except Exception as plugin_err:  # noqa: BLE001 — best-effort
                logger.warning(
                    "[VOICE CORE] plugin=%s on_session_initiated failed (non-blocking) "
                    "session=%s: %s",
                    getattr(plugin, "plugin_name", "unknown"),
                    session.session_id,
                    plugin_err,
                )

        # C.3 ticket: surface bootstrap greeting via session.metadata.
        try:
            if self._plugins:
                greeting = await self._plugin_next_question(session, db)
                if isinstance(greeting, str) and greeting.strip():
                    # Ensure metadata is a dict (canonical field as of C.2).
                    if not isinstance(getattr(session, "metadata", None), dict):
                        session.metadata = {}
                    session.metadata["initial_greeting"] = greeting.strip()
        except Exception as greet_err:  # noqa: BLE001 — best-effort
            logger.warning(
                "[VOICE CORE] C.3 initial_greeting cache failed (non-blocking) "
                "session=%s: %s",
                session.session_id,
                greet_err,
            )

    async def _plugin_next_question(
        self,
        session: "VoiceScreeningSession",
        db: Any,
    ) -> str | None:
        """Return FIRST non-None plugin-provided question, or None to fall through."""
        for plugin in self._plugins:
            try:
                result = await plugin.get_next_question(session, db)
                if result:
                    return result
            except Exception as plugin_err:  # noqa: BLE001 — best-effort
                logger.warning(
                    "[VOICE CORE] plugin=%s get_next_question failed (non-blocking) "
                    "session=%s: %s",
                    getattr(plugin, "plugin_name", "unknown"),
                    session.session_id,
                    plugin_err,
                )
        return None

    async def _on_session_finalized(
        self,
        session: "VoiceScreeningSession",
        db: Any,
        transcript: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Aggregate plugin completion results (last-wins on key conflicts)."""
        merged: dict[str, Any] = {}
        for plugin in self._plugins:
            try:
                result = await plugin.on_session_finalized(session, db, transcript)
                if isinstance(result, dict):
                    merged.update(result)
            except Exception as plugin_err:  # noqa: BLE001 — best-effort
                logger.warning(
                    "[VOICE CORE] plugin=%s on_session_finalized failed (non-blocking) "
                    "session=%s: %s",
                    getattr(plugin, "plugin_name", "unknown"),
                    session.session_id,
                    plugin_err,
                )
        return merged


class VoiceScreeningOrchestrator(VoiceCoreOrchestrator):
    """
    Backward-compat WSI-aware orchestrator (Sprint 3.3 final).

    Subclass de VoiceCoreOrchestrator que pre-instala WSIVoicePlugin no
    constructor e mantem 3 thin delegate methods (_register_wsi_session,
    _generate_and_store_wsi_questions, _load_wsi_questions_for_session) que
    encaminham para a plugin. Esses delegates existem PARA PRESERVAR a API
    privada esperada por ~240 tests que usam
    `patch.object(orch, '_register_wsi_session', new=AsyncMock())` etc.

    Callers existentes (todos UNTOUCHED apos Sprint 3.2/3.3):
    - app.api.v1.triagem
    - app.api.v1.twilio_voice
    - app.api.v1.gemini_voice
    - app.domains.communication.services.communication_dispatcher
    - app.domains.voice.services.gemini_live_audio_service

    Para usar o nucleo voz generico (sem WSI hardcoded) em Sprint 3.4+, importar:
        from app.domains.voice.services.voice_core_orchestrator import VoiceCoreOrchestrator
        core = VoiceCoreOrchestrator(plugins=[MyCustomPlugin()])
    """

    def __init__(self):
        # Sprint 3.3: pre-install canonical WSI plugin. Lifecycle hook
        # _on_session_initiated (in initiate_call / initiate_voip_session)
        # now drives WSI registration via this plugin.
        from app.domains.voice.plugins.wsi_voice_plugin import WSIVoicePlugin
        self._wsi_plugin = WSIVoicePlugin(orchestrator=self)
        super().__init__(plugins=[self._wsi_plugin])

    # ── Sprint 3.3 backward-compat delegates ─────────────────────────────
    #
    # These 3 methods existed historically on VoiceScreeningOrchestrator and
    # are patched by ~240 tests via `patch.object(orch, '_x', new=AsyncMock())`.
    # Sprint 3.3 moved the IMPLEMENTATIONS to WSIVoicePlugin._*_impl; these
    # delegates preserve the instance-level API so test patches still take
    # effect (Python patch.object overrides the bound method directly).

    async def _register_wsi_session(
        self,
        session: "VoiceScreeningSession",
        db,
    ) -> None:
        """Backward-compat delegate → WSIVoicePlugin._register_wsi_session_impl."""
        await self._wsi_plugin._register_wsi_session_impl(session, db)

    async def _generate_and_store_wsi_questions(
        self,
        session: "VoiceScreeningSession",
        db,
    ) -> None:
        """Backward-compat delegate → WSIVoicePlugin._generate_and_store_wsi_questions_impl."""
        await self._wsi_plugin._generate_and_store_wsi_questions_impl(session, db)

    async def _load_wsi_questions_for_session(
        self,
        session_id: str,
        db,
    ) -> list[str]:
        """Backward-compat delegate → WSIVoicePlugin._load_wsi_questions_for_session_impl."""
        return await self._wsi_plugin._load_wsi_questions_for_session_impl(session_id, db)


voice_screening_orchestrator = VoiceScreeningOrchestrator()
