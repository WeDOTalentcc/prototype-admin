"""
Voice Screening Orchestrator regression sentinels (Sprint 3.1 pre-refactor).

Protege os invariantes críticos do fluxo de triagem WSI por voz ANTES do refactor
do monolito `voice_screening_orchestrator.py` (77.9 KB) em core voz + WSI plugin +
adapter de canal (Sprint 3.2+).

Invariantes cobertos:
- I1  Consent verification: bloqueia call sem consentimento confirmado (LGPD Art. 7)
- I2  Multi-tenancy: company_id é sempre parametro explicito (nunca lido do payload)
- I3  STT fallback: Gemini primario -> Deepgram fallback quando Gemini falha
- I4  Fairness guard: chamado em TODO outbound LIA (generate_lia_response + scripted)
- I5  Fairness blocking: substitui resposta por scripted fallback quando blocked
- I6  PII redaction: transcript segments mascarados ANTES de persist (LGPD Art. 12)
- I7  Session persistence: round-trip _persist -> _load preserva estado canonical
- I8  WSI completion hook: finalize_screening chama wsi_voice_orchestrator quando call_sid existe
- I9  Twilio fallback: status=fallback quando circuito aberto OU twilio nao configurado

Cada teste documenta o invariante via docstring. Mocks usados para isolar deps
externas (DB, Gemini, Deepgram, TTS, Twilio, fairness guard).
"""
from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.voice.services.voice_screening_orchestrator import (
    ConsentNotGrantedError,
    VoiceScreeningOrchestrator,
    VoiceScreeningSession,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def orchestrator() -> VoiceScreeningOrchestrator:
    """Fresh orchestrator instance with empty in-memory session map."""
    return VoiceScreeningOrchestrator()


@pytest.fixture
def mock_db() -> AsyncMock:
    """AsyncMock simulating SQLAlchemy AsyncSession."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def consented_session(orchestrator) -> VoiceScreeningSession:
    """A VoiceScreeningSession in a post-consent / mid-call state."""
    session = VoiceScreeningSession(
        session_id="test-session-uuid-001",
        candidate_id="cand-uuid-001",
        candidate_name="Maria Test",
        job_title="Senior Backend Engineer",
        job_id="job-uuid-001",
        company_id="company-uuid-001",
        phone_number="+5511999999999",
        call_sid="CA1234567890abcdef",
        status="initiated",
        consent_verified=True,
        started_at=datetime.utcnow(),
        transcript_segments=[
            {"text": "Ola, sou a LIA.", "role": "lia", "timestamp": "2026-05-22T10:00:00"},
            {"text": "Me chamo Maria, +5511 91234-5678.", "role": "candidate", "timestamp": "2026-05-22T10:00:05"},
        ],
    )
    orchestrator._sessions[session.session_id] = session
    return session


# ─────────────────────────────────────────────────────────────────────────────
# I1 — Consent verification gate (LGPD Art. 7)
# ─────────────────────────────────────────────────────────────────────────────

class TestConsentVerificationGate:
    """I1: consent must be confirmed before any outbound call."""

    async def test_verify_consent_blocks_when_no_db_provided(self, orchestrator):
        """db=None -> ConsentNotGrantedError. Cannot confirm consent without DB."""
        with pytest.raises(ConsentNotGrantedError, match="no database session"):
            await orchestrator.verify_consent(
                candidate_id="cand-001",
                company_id="company-001",
                db=None,
            )

    async def test_verify_consent_blocks_when_consent_revoked(self, orchestrator, mock_db):
        """allowed=False -> ConsentNotGrantedError. LGPD Art. 18 revocation."""
        fake_result = MagicMock(allowed=False, soft_warning=False)
        with patch(
            "app.domains.voice.services.voice_screening_orchestrator._ConsentCheckerService"
        ) as mock_cs_cls:
            mock_checker = MagicMock()
            mock_checker.check_candidate_consent = AsyncMock(return_value=fake_result)
            mock_cs_cls.return_value = mock_checker

            with pytest.raises(ConsentNotGrantedError, match="revoked"):
                await orchestrator.verify_consent(
                    candidate_id="cand-001",
                    company_id="company-001",
                    db=mock_db,
                )

    async def test_verify_consent_blocks_when_soft_warning(self, orchestrator, mock_db):
        """soft_warning=True (consent absent) -> ConsentNotGrantedError. No silent pass."""
        fake_result = MagicMock(allowed=True, soft_warning=True)
        with patch(
            "app.domains.voice.services.voice_screening_orchestrator._ConsentCheckerService"
        ) as mock_cs_cls:
            mock_checker = MagicMock()
            mock_checker.check_candidate_consent = AsyncMock(return_value=fake_result)
            mock_cs_cls.return_value = mock_checker

            with pytest.raises(ConsentNotGrantedError, match="not explicitly granted"):
                await orchestrator.verify_consent(
                    candidate_id="cand-001",
                    company_id="company-001",
                    db=mock_db,
                )

    async def test_verify_consent_allows_when_confirmed(self, orchestrator, mock_db):
        """allowed=True + soft_warning=False -> returns True. Happy path."""
        fake_result = MagicMock(allowed=True, soft_warning=False)
        with patch(
            "app.domains.voice.services.voice_screening_orchestrator._ConsentCheckerService"
        ) as mock_cs_cls:
            mock_checker = MagicMock()
            mock_checker.check_candidate_consent = AsyncMock(return_value=fake_result)
            mock_cs_cls.return_value = mock_checker

            result = await orchestrator.verify_consent(
                candidate_id="cand-001",
                company_id="company-001",
                db=mock_db,
            )
            assert result is True
            # Verify checker received company_id explicitly (multi-tenancy invariant)
            mock_checker.check_candidate_consent.assert_awaited_once()
            call_kwargs = mock_checker.check_candidate_consent.await_args.kwargs
            assert call_kwargs["company_id"] == "company-001"
            assert call_kwargs["candidate_id"] == "cand-001"


# ─────────────────────────────────────────────────────────────────────────────
# I2 — Multi-tenancy: company_id is explicit parameter, not from payload
# ─────────────────────────────────────────────────────────────────────────────

class TestMultiTenancyInvariant:
    """I2: company_id MUST be parameter in every public method that touches tenant data."""

    def test_public_methods_require_company_id_in_signature(self, orchestrator):
        """All methods that touch tenant data declare company_id in their signature."""
        import inspect

        # Methods that touch tenant data (read or persist) MUST declare company_id
        methods_requiring_company_id = [
            "verify_consent",
            "initiate_call",
            "initiate_voip_session",
        ]
        for name in methods_requiring_company_id:
            method = getattr(orchestrator, name)
            sig = inspect.signature(method)
            assert "company_id" in sig.parameters, (
                f"{name} does not declare company_id parameter — "
                f"multi-tenancy invariant broken. signature={sig}"
            )

    async def test_initiate_call_creates_session_with_supplied_company_id(self, orchestrator, mock_db):
        """initiate_call passes the supplied company_id into the session (no payload override)."""
        fake_consent = MagicMock(allowed=True, soft_warning=False)
        with patch(
            "app.domains.voice.services.voice_screening_orchestrator._ConsentCheckerService"
        ) as mock_cs_cls, patch(
            "app.domains.voice.services.voice_screening_orchestrator._twilio_voice_service"
        ) as mock_twilio, patch.object(orchestrator, "_register_wsi_session", new=AsyncMock()), \
             patch.object(orchestrator, "_persist_session_state", new=AsyncMock()):
            mock_checker = MagicMock()
            mock_checker.check_candidate_consent = AsyncMock(return_value=fake_consent)
            mock_cs_cls.return_value = mock_checker
            mock_twilio.make_call = AsyncMock(return_value={"success": True, "call_sid": "CAxxx"})

            session = await orchestrator.initiate_call(
                candidate_id="cand-001",
                candidate_name="John",
                phone_number="+5511",
                job_title="SWE",
                company_id="tenant-A-uuid",
                db=mock_db,
            )
            assert session.company_id == "tenant-A-uuid"
            assert session.status == "initiated"
            assert session.consent_verified is True


# ─────────────────────────────────────────────────────────────────────────────
# I3 — STT fallback: Gemini primary -> Deepgram fallback
# ─────────────────────────────────────────────────────────────────────────────

class TestSTTFallbackChain:
    """I3: STT pipeline uses Gemini primary, Deepgram as fallback on failure."""

    async def test_process_audio_chunk_uses_gemini_when_available(
        self, orchestrator, consented_session
    ):
        """Happy path: Gemini transcribes successfully -> Deepgram never called."""
        # Need >= 160 bytes to bypass early return
        audio = b"\x00" * 200

        fake_voice_svc = MagicMock()
        fake_voice_svc.transcribe_audio = AsyncMock(return_value={"text": "hello world"})

        fake_dg = MagicMock()
        fake_dg.is_configured = MagicMock(return_value=True)
        fake_dg.transcribe = AsyncMock(return_value={"transcript": "should-not-be-called"})

        with patch(
            "app.domains.voice.services.voice_screening_orchestrator._get_voice_service",
            return_value=fake_voice_svc,
        ), patch(
            "app.domains.voice.services.voice_screening_orchestrator._deepgram_service",
            fake_dg,
        ):
            text = await orchestrator.process_audio_chunk(
                session_id=consented_session.session_id,
                audio_data=audio,
            )
            assert text == "hello world"
            fake_voice_svc.transcribe_audio.assert_awaited_once()
            fake_dg.transcribe.assert_not_awaited()

    async def test_process_audio_chunk_falls_back_to_deepgram_on_gemini_failure(
        self, orchestrator, consented_session
    ):
        """Gemini raises -> Deepgram is called as fallback."""
        audio = b"\x00" * 200

        fake_voice_svc = MagicMock()
        fake_voice_svc.transcribe_audio = AsyncMock(side_effect=RuntimeError("gemini down"))

        fake_dg = MagicMock()
        fake_dg.is_configured = MagicMock(return_value=True)
        fake_dg.transcribe = AsyncMock(return_value={"transcript": "from deepgram"})

        with patch(
            "app.domains.voice.services.voice_screening_orchestrator._get_voice_service",
            return_value=fake_voice_svc,
        ), patch(
            "app.domains.voice.services.voice_screening_orchestrator._deepgram_service",
            fake_dg,
        ):
            text = await orchestrator.process_audio_chunk(
                session_id=consented_session.session_id,
                audio_data=audio,
            )
            assert text == "from deepgram"
            fake_dg.transcribe.assert_awaited_once()


# ─────────────────────────────────────────────────────────────────────────────
# I4 + I5 — FairnessGuard on outbound LIA text
# ─────────────────────────────────────────────────────────────────────────────

class TestFairnessGuardInvariant:
    """I4: outbound LIA text passes through fairness guard. I5: blocked -> safe scripted fallback."""

    def test_check_fairness_on_response_calls_check_fairness(
        self, orchestrator, consented_session
    ):
        """Helper invokes check_fairness with company_id and voice_screening context."""
        fake_result = MagicMock(is_blocked=False, blocked_result=None)
        with patch(
            "app.domains.voice.services.voice_screening_orchestrator.check_fairness",
            return_value=fake_result,
        ) as mock_cf:
            out = orchestrator._check_fairness_on_response("test text", consented_session)
            assert out == "test text"
            mock_cf.assert_called_once()
            kwargs = mock_cf.call_args.kwargs
            assert kwargs["company_id"] == consented_session.company_id
            assert kwargs["context"] == "voice_screening"

    def test_check_fairness_on_response_returns_safe_replacement_when_blocked(
        self, orchestrator, consented_session
    ):
        """is_blocked=True -> returns neutral fallback (not original text)."""
        fake_blocked = MagicMock(is_blocked=True, blocked_result=MagicMock(category="age"))
        with patch(
            "app.domains.voice.services.voice_screening_orchestrator.check_fairness",
            return_value=fake_blocked,
        ):
            out = orchestrator._check_fairness_on_response(
                "Quantos anos você tem?", consented_session
            )
            assert "Quantos anos" not in out
            assert "experiência profissional" in out

    def test_get_next_scripted_question_passes_through_fairness_guard(
        self, orchestrator, consented_session
    ):
        """Scripted fallback path also goes through fairness guard."""
        fake_result = MagicMock(is_blocked=False, blocked_result=None)
        with patch(
            "app.domains.voice.services.voice_screening_orchestrator.check_fairness",
            return_value=fake_result,
        ) as mock_cf:
            q = orchestrator._get_next_scripted_question(consented_session)
            assert q
            # check_fairness must have been called for outbound text
            assert mock_cf.called


# ─────────────────────────────────────────────────────────────────────────────
# I6 — PII redaction before persistence
# ─────────────────────────────────────────────────────────────────────────────

class TestPIIRedactionInvariant:
    """I6: transcript segments must be PII-masked BEFORE persistence (LGPD Art. 12 / SEG-3B)."""

    def test_mask_transcript_segments_redacts_text_in_each_segment(self, orchestrator):
        """_mask_transcript_segments returns a copy with text masked."""
        raw = [
            {"text": "Meu telefone é +5511 91234-5678", "role": "candidate", "ts": "t1"},
            {"text": "Email maria@example.com", "role": "candidate", "ts": "t2"},
        ]
        masked = orchestrator._mask_transcript_segments(raw)
        assert len(masked) == 2
        # Neither raw phone nor email should appear in the masked text
        for seg in masked:
            assert "91234-5678" not in seg["text"]
            assert "maria@example.com" not in seg["text"]
        # Original segments untouched (immutability)
        assert "91234-5678" in raw[0]["text"]

    async def test_finalize_screening_masks_transcript_before_wsi(
        self, orchestrator, consented_session, mock_db
    ):
        """finalize_screening passes MASKED transcript to WSI orchestrator."""
        consented_session.transcript_segments = [
            {"text": "Meu CPF é 123.456.789-00", "role": "candidate", "ts": "t1"},
        ]

        fake_wsi = MagicMock()
        fake_wsi.process_call_completed = AsyncMock(
            return_value={"overall_evaluation": {"overall_score": 8.0}}
        )
        fake_wsi_cls = MagicMock(return_value=fake_wsi)

        with patch(
            "app.domains.voice.services.voice_screening_orchestrator._WSIVoiceOrchestrator",
            fake_wsi_cls,
        ), patch.object(orchestrator, "_persist_session_state", new=AsyncMock()):
            result = await orchestrator.finalize_screening(
                session_id=consented_session.session_id,
                db=mock_db,
            )
            assert result["status"] == "completed"
            fake_wsi.process_call_completed.assert_awaited_once()
            call_kwargs = fake_wsi.process_call_completed.await_args.kwargs
            # transcript_object MUST be masked — no raw CPF
            for seg in call_kwargs["transcript_object"]:
                assert "123.456.789-00" not in seg["text"]


# ─────────────────────────────────────────────────────────────────────────────
# I7 — Session persistence round-trip
# ─────────────────────────────────────────────────────────────────────────────

class TestSessionPersistenceRoundTrip:
    """I7: _session_to_state -> _state_to_session preserves canonical fields.

    Post-F-07 (commit 5543c6b3f, 2026-05-22): phone_number is masked at rest
    via mask_phone_preserve_tail. Round-trip is identity for all canonical
    fields EXCEPT phone_number, which is preserved as its masked form.
    """

    def test_session_state_round_trip_preserves_fields(self, orchestrator):
        """state -> session -> state is identity for canonical fields.

        Phone is asserted separately as preserved-as-masked (F-07 canonical).
        """
        original = VoiceScreeningSession(
            session_id="sess-rt-001",
            candidate_id="cand-rt-001",
            candidate_name="Joao da Silva",
            job_title="DevOps",
            job_id="job-rt-001",
            company_id="company-rt-001",
            phone_number="+5511999",
            call_sid="CA_rt_abc",
            status="initiated",
            language="pt-BR",
            consent_verified=True,
            presentation_done=True,
            started_at=datetime(2026, 5, 22, 10, 0, 0),
            questions_asked=["q1", "q2"],
            transcript_segments=[{"text": "ola", "role": "lia"}],
            voice_provider="twilio",
        )

        state = orchestrator._session_to_state(original)
        # Must be JSON-serializable
        json_str = json.dumps(state)
        rehydrated_state = json.loads(json_str)
        restored = orchestrator._state_to_session(rehydrated_state)

        # F-07 P0 LGPD Art. 11 masking (commit 5543c6b3f): phone_number is
        # masked via mask_phone_preserve_tail at rest. Round-trip canonical
        # behavior post-F-07 preserves the MASKED form, not the raw number.
        # Plaintext phone exists only in-memory during the active outbound call.
        # Excluded from identity round-trip; asserted separately below.
        canonical_fields = [
            "session_id", "candidate_id", "candidate_name", "job_title",
            "job_id", "company_id", "call_sid", "status",
            "language", "consent_verified", "presentation_done",
            "questions_asked", "voice_provider",
        ]
        for f in canonical_fields:
            assert getattr(restored, f) == getattr(original, f), (
                f"Field {f} did not round-trip: original={getattr(original, f)!r} "
                f"restored={getattr(restored, f)!r}"
            )
        # F-07 P0 LGPD Art. 11: phone_number is preserved as MASKED form at rest.
        from app.shared.pii_masking import mask_phone_preserve_tail
        assert restored.phone_number == mask_phone_preserve_tail(original.phone_number), (
            f"phone_number must be masked at rest post-F-07: "
            f"expected={mask_phone_preserve_tail(original.phone_number)!r} "
            f"got={restored.phone_number!r}"
        )
        # transcript_segments preserved as list of dicts
        assert restored.transcript_segments == original.transcript_segments


# ─────────────────────────────────────────────────────────────────────────────
# I8 — WSI completion hook
# ─────────────────────────────────────────────────────────────────────────────

class TestWSICompletionHook:
    """I8: finalize_screening calls wsi_voice_orchestrator when call_sid present."""

    async def test_finalize_screening_invokes_wsi_orchestrator_when_call_sid_present(
        self, orchestrator, consented_session, mock_db
    ):
        """call_sid present -> WSIVoiceOrchestrator.process_call_completed is called."""
        fake_wsi = MagicMock()
        fake_wsi.process_call_completed = AsyncMock(
            return_value={"overall_evaluation": {"overall_score": 7.5}}
        )
        fake_wsi_cls = MagicMock(return_value=fake_wsi)

        with patch(
            "app.domains.voice.services.voice_screening_orchestrator._WSIVoiceOrchestrator",
            fake_wsi_cls,
        ), patch.object(orchestrator, "_persist_session_state", new=AsyncMock()):
            result = await orchestrator.finalize_screening(
                session_id=consented_session.session_id,
                db=mock_db,
            )
            assert result["status"] == "completed"
            fake_wsi.process_call_completed.assert_awaited_once()
            call_kwargs = fake_wsi.process_call_completed.await_args.kwargs
            assert call_kwargs["call_id"] == consented_session.call_sid

    async def test_finalize_screening_falls_back_to_standalone_analysis_when_wsi_unavailable(
        self, orchestrator, consented_session, mock_db
    ):
        """WSIVoiceOrchestrator=None -> uses analyze_voice_screening fallback."""
        fake_analyze = AsyncMock(
            return_value={"overall_evaluation": {"overall_score": 6.0}}
        )

        with patch(
            "app.domains.voice.services.voice_screening_orchestrator._WSIVoiceOrchestrator",
            None,
        ), patch(
            "app.domains.voice.services.voice_screening_orchestrator._analyze_voice_screening",
            fake_analyze,
        ), patch.object(orchestrator, "_persist_session_state", new=AsyncMock()):
            result = await orchestrator.finalize_screening(
                session_id=consented_session.session_id,
                db=mock_db,
            )
            assert result["status"] == "completed"
            fake_analyze.assert_awaited_once()


# ─────────────────────────────────────────────────────────────────────────────
# I9 — Twilio fallback semantics
# ─────────────────────────────────────────────────────────────────────────────

class TestTwilioFallbackSemantics:
    """I9: status=fallback when twilio unconfigured or circuit open (NOT mock)."""

    async def test_initiate_call_returns_fallback_when_twilio_unconfigured(
        self, orchestrator, mock_db
    ):
        """TwilioVoiceUnconfiguredError -> session.status='fallback' with explicit error."""
        from app.domains.communication.services.twilio_voice_service import (
            TwilioVoiceUnconfiguredError,
        )

        fake_consent = MagicMock(allowed=True, soft_warning=False)
        with patch(
            "app.domains.voice.services.voice_screening_orchestrator._ConsentCheckerService"
        ) as mock_cs_cls, patch(
            "app.domains.voice.services.voice_screening_orchestrator._twilio_voice_service"
        ) as mock_twilio, patch.object(orchestrator, "_persist_session_state", new=AsyncMock()):
            mock_checker = MagicMock()
            mock_checker.check_candidate_consent = AsyncMock(return_value=fake_consent)
            mock_cs_cls.return_value = mock_checker
            mock_twilio.make_call = AsyncMock(
                side_effect=TwilioVoiceUnconfiguredError("test: not configured")
            )

            session = await orchestrator.initiate_call(
                candidate_id="cand-001",
                candidate_name="Test",
                phone_number="+5511",
                job_title="SWE",
                company_id="company-001",
                db=mock_db,
            )
            assert session.status == "fallback"
            assert session.error is not None
            assert "fallback" in session.error.lower() or "chat/whatsapp" in session.error.lower()


# ─────────────────────────────────────────────────────────────────────────────
# Session restoration
# ─────────────────────────────────────────────────────────────────────────────

class TestSessionRestoration:
    """get_or_restore_session: graceful fallback when missing."""

    async def test_get_or_restore_session_returns_in_memory_first(
        self, orchestrator, consented_session
    ):
        """In-memory hit short-circuits DB load.

        F-15 (2026-05-22): session is now rehydrated from Redis cache, so
        identity check (`is`) replaced by field equality. Cache hit still
        bypasses DB.
        """
        result = await orchestrator.get_or_restore_session(
            session_id=consented_session.session_id, db=None
        )
        assert result is not None
        assert result.session_id == consented_session.session_id
        assert result.candidate_id == consented_session.candidate_id

    async def test_get_or_restore_session_returns_none_when_not_found(
        self, orchestrator, mock_db
    ):
        """Missing session + DB returns no row -> None (no crash)."""
        # Make execute().fetchone() return None
        fake_result = MagicMock()
        fake_result.fetchone = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=fake_result)

        result = await orchestrator.get_or_restore_session(
            session_id="missing-id", db=mock_db
        )
        assert result is None

    async def test_get_or_restore_session_caches_restored_session_in_memory(
        self, orchestrator, mock_db
    ):
        """Session loaded from DB is added to _sessions cache."""
        state = {
            "session_id": "restored-001",
            "candidate_id": "c-001",
            "candidate_name": "Restored",
            "job_title": "QA",
            "company_id": "tenant-r-001",
            "phone_number": "+55",
            "status": "in_progress",
            "language": "pt-BR",
            "consent_verified": True,
            "presentation_done": False,
            "questions_asked": [],
            "transcript_segments": [],
            "voice_provider": "twilio",
        }
        fake_row = (state,)
        fake_result = MagicMock()
        fake_result.fetchone = MagicMock(return_value=fake_row)
        mock_db.execute = AsyncMock(return_value=fake_result)

        result = await orchestrator.get_or_restore_session(
            session_id="restored-001", db=mock_db
        )
        assert result is not None
        assert result.session_id == "restored-001"
        # F-15: cached in Redis (via in-memory fallback in tests).
        assert "restored-001" in orchestrator._sessions
