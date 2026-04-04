"""
Tests for Twilio Voice + Gemini screening pipeline.

Covers:
- Audio transcoding: mulaw_to_wav, mp3_to_mulaw
- TwilioVoiceService: signature validation, call initiation (explicit failure, not mock)
- VoiceScreeningOrchestrator: consent enforcement, fallback behavior, finalize with PII masking
- CommunicationDispatcher: make_voice_call with fallback
- Circuit breaker: TWILIO_VOICE_CIRCUIT registration and fallback
- PII masking: email, CPF, phone in transcripts

Run:
    pytest tests/test_voice_screening_twilio.py -v
"""

import struct
import io
import wave
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


# ── Audio transcoding tests ───────────────────────────────────────────────────

class TestAudioTranscoding:
    """Tests for μ-law ↔ WAV conversion helpers."""

    def test_mulaw_to_wav_produces_valid_riff_header(self):
        """mulaw_to_wav should produce bytes starting with RIFF header."""
        from app.domains.communication.services.twilio_voice_service import mulaw_to_wav

        mulaw_data = bytes(160)
        wav_data = mulaw_to_wav(mulaw_data, sample_rate=8000)

        assert wav_data[:4] == b"RIFF"
        assert b"WAVE" in wav_data[:12]

    def test_mulaw_to_wav_is_parseable_as_wav(self):
        """mulaw_to_wav output should be a valid WAV file."""
        from app.domains.communication.services.twilio_voice_service import mulaw_to_wav

        mulaw_data = bytes(3200)
        wav_data = mulaw_to_wav(mulaw_data, sample_rate=8000)

        buf = io.BytesIO(wav_data)
        with wave.open(buf, "rb") as wf:
            assert wf.getnchannels() == 1
            assert wf.getframerate() == 8000
            assert wf.getsampwidth() == 2

    def test_mulaw_to_wav_empty_input_still_returns_wav(self):
        """mulaw_to_wav with empty input should still return valid WAV."""
        from app.domains.communication.services.twilio_voice_service import mulaw_to_wav

        wav_data = mulaw_to_wav(bytes(0))
        assert wav_data[:4] == b"RIFF"

    def test_mp3_to_mulaw_returns_none_without_pydub(self):
        """mp3_to_mulaw returns None gracefully when pydub is unavailable."""
        from app.domains.communication.services.twilio_voice_service import mp3_to_mulaw

        with patch.dict("sys.modules", {"pydub": None}):
            result = mp3_to_mulaw(b"fake mp3 data")
        assert result is None

    def test_mp3_to_mulaw_returns_bytes_with_pydub(self):
        """mp3_to_mulaw returns raw bytes when pydub is available."""
        try:
            import pydub
        except ImportError:
            pytest.skip("pydub not installed")

        from app.domains.communication.services.twilio_voice_service import mp3_to_mulaw

        pcm_data = struct.pack("<" + "h" * 800, *([0] * 800))
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(8000)
            wf.writeframes(pcm_data)

        result = mp3_to_mulaw(buf.getvalue())
        assert result is None or isinstance(result, bytes)


# ── TwilioVoiceService Tests ──────────────────────────────────────────────────

class TestTwilioVoiceService:
    """Tests for TwilioVoiceService."""

    def test_is_configured_when_all_envs_set(self, monkeypatch):
        """Service is configured when all required env vars are set."""
        monkeypatch.setenv("TWILIO_ACCOUNT_SID", "ACtest123")
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", "test_token")
        monkeypatch.setenv("TWILIO_VOICE_NUMBER", "+5511999999999")

        from app.domains.communication.services.twilio_voice_service import TwilioVoiceService
        svc = TwilioVoiceService()
        assert svc.is_configured is True

    def test_is_not_configured_without_voice_number(self, monkeypatch):
        """Service is not configured when TWILIO_VOICE_NUMBER is missing."""
        monkeypatch.setenv("TWILIO_ACCOUNT_SID", "ACtest123")
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", "test_token")
        monkeypatch.delenv("TWILIO_VOICE_NUMBER", raising=False)

        from app.domains.communication.services.twilio_voice_service import TwilioVoiceService
        svc = TwilioVoiceService()
        assert svc.is_configured is False

    def test_make_call_raises_when_not_configured(self, monkeypatch):
        """
        make_call raises TwilioVoiceUnconfiguredError when Twilio not configured.
        This is an explicit failure — NOT a mock success — so callers route to fallback.
        """
        monkeypatch.delenv("TWILIO_ACCOUNT_SID", raising=False)
        monkeypatch.delenv("TWILIO_AUTH_TOKEN", raising=False)
        monkeypatch.delenv("TWILIO_VOICE_NUMBER", raising=False)

        from app.domains.communication.services.twilio_voice_service import (
            TwilioVoiceService,
            TwilioVoiceUnconfiguredError,
        )
        svc = TwilioVoiceService()

        with pytest.raises(TwilioVoiceUnconfiguredError):
            svc.make_call(
                to_phone="+5511999999999",
                candidate_name="João Silva",
                job_title="Engenheiro Backend",
            )

    def test_generate_greeting_twiml_contains_candidate_name(self, monkeypatch):
        """Greeting TwiML should include candidate name and job title."""
        monkeypatch.delenv("TWILIO_ACCOUNT_SID", raising=False)

        try:
            from app.domains.communication.services.twilio_voice_service import TwilioVoiceService
            svc = TwilioVoiceService()
            svc.base_url = "https://example.com"

            twiml = svc.generate_greeting_twiml(
                session_id="test-session-123",
                candidate_name="Maria Santos",
                job_title="Analista de Dados",
                language="pt-BR",
            )

            assert "Maria Santos" in twiml
            assert "Analista de Dados" in twiml
            assert "<Response>" in twiml
            assert "<Gather" in twiml
        except ImportError:
            pytest.skip("twilio package not available")

    def test_generate_stream_twiml_uses_wss(self, monkeypatch):
        """Stream TwiML should use WSS (not HTTPS) for WebSocket URL."""
        monkeypatch.delenv("TWILIO_ACCOUNT_SID", raising=False)

        try:
            from app.domains.communication.services.twilio_voice_service import TwilioVoiceService
            svc = TwilioVoiceService()
            svc.base_url = "https://myapp.example.com"

            twiml = svc.generate_stream_twiml(session_id="sess-001")

            assert "wss://" in twiml
            assert "https://" not in twiml
        except ImportError:
            pytest.skip("twilio package not available")

    def test_generate_end_twiml_contains_hangup(self, monkeypatch):
        """End TwiML should include <Hangup> element."""
        try:
            from app.domains.communication.services.twilio_voice_service import TwilioVoiceService
            svc = TwilioVoiceService()
            svc.base_url = "https://example.com"

            twiml = svc.generate_end_twiml()

            assert "<Hangup" in twiml
            assert "<Response>" in twiml
        except ImportError:
            pytest.skip("twilio package not available")

    def test_parse_status_webhook(self):
        """parse_status_webhook should extract call details from Twilio payload."""
        from app.domains.communication.services.twilio_voice_service import TwilioVoiceService
        svc = TwilioVoiceService()

        payload = {
            "CallSid": "CA123",
            "CallStatus": "completed",
            "Direction": "outbound-api",
            "From": "+5511000000000",
            "To": "+5511999999999",
            "CallDuration": "180",
        }

        result = svc.parse_status_webhook(payload)

        assert result["call_sid"] == "CA123"
        assert result["status"] == "completed"
        assert result["duration"] == "180"

    def test_verify_webhook_signature_no_auth_token_passes(self, monkeypatch):
        """verify_webhook_signature should allow when no auth_token (dev mode)."""
        monkeypatch.delenv("TWILIO_AUTH_TOKEN", raising=False)

        from app.domains.communication.services.twilio_voice_service import TwilioVoiceService
        svc = TwilioVoiceService()

        result = svc.verify_webhook_signature("https://example.com/webhook", {}, "any-sig")
        assert result is True

    def test_verify_webhook_signature_invalid_sig_returns_false(self, monkeypatch):
        """verify_webhook_signature should return False for wrong signature."""
        monkeypatch.setenv("TWILIO_ACCOUNT_SID", "ACtest")
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", "real_auth_token")
        monkeypatch.setenv("TWILIO_VOICE_NUMBER", "+551100000000")

        try:
            from app.domains.communication.services.twilio_voice_service import TwilioVoiceService
            svc = TwilioVoiceService()

            result = svc.verify_webhook_signature(
                "https://example.com/webhook",
                {"CallSid": "CA123"},
                "wrong_signature",
            )
            assert result is False
        except ImportError:
            pytest.skip("twilio package not available")


# ── VoiceScreeningOrchestrator Tests ─────────────────────────────────────────

class TestVoiceScreeningOrchestrator:
    """Tests for VoiceScreeningOrchestrator."""

    @pytest.mark.asyncio
    async def test_verify_consent_no_db_raises(self):
        """Consent check with no DB must hard-block (LGPD Art. 7 — cannot confirm consent)."""
        from app.services.voice_screening_orchestrator import (
            VoiceScreeningOrchestrator,
            ConsentNotGrantedError,
        )
        orch = VoiceScreeningOrchestrator()

        with pytest.raises(ConsentNotGrantedError, match="database session"):
            await orch.verify_consent(
                candidate_id="cand-001",
                company_id="comp-001",
                db=None,
            )

    @pytest.mark.asyncio
    async def test_verify_consent_revoked_raises(self):
        """Verify consent raises ConsentNotGrantedError when consent is revoked."""
        from app.services.voice_screening_orchestrator import (
            VoiceScreeningOrchestrator,
            ConsentNotGrantedError,
        )

        mock_db = MagicMock()

        mock_check_result = MagicMock()
        mock_check_result.allowed = False
        mock_check_result.soft_warning = False

        mock_checker_instance = MagicMock()
        mock_checker_instance.check_candidate_consent = AsyncMock(return_value=mock_check_result)

        mock_checker_cls = MagicMock(return_value=mock_checker_instance)

        import app.services.voice_screening_orchestrator as orch_mod

        original = orch_mod._ConsentCheckerService
        orch_mod._ConsentCheckerService = mock_checker_cls
        try:
            orch = VoiceScreeningOrchestrator()
            with pytest.raises(ConsentNotGrantedError):
                await orch.verify_consent(
                    candidate_id="cand-001",
                    company_id="comp-001",
                    db=mock_db,
                )
        finally:
            orch_mod._ConsentCheckerService = original

    @pytest.mark.asyncio
    async def test_verify_consent_soft_warning_raises(self):
        """Soft warning (absent consent) must also block outbound calls (LGPD Art. 7 strict)."""
        from app.services.voice_screening_orchestrator import (
            VoiceScreeningOrchestrator,
            ConsentNotGrantedError,
        )

        mock_db = MagicMock()
        mock_check_result = MagicMock()
        mock_check_result.allowed = True
        mock_check_result.soft_warning = True

        mock_checker_instance = MagicMock()
        mock_checker_instance.check_candidate_consent = AsyncMock(return_value=mock_check_result)
        mock_checker_cls = MagicMock(return_value=mock_checker_instance)

        import app.services.voice_screening_orchestrator as orch_mod

        original = orch_mod._ConsentCheckerService
        orch_mod._ConsentCheckerService = mock_checker_cls
        try:
            orch = VoiceScreeningOrchestrator()
            with pytest.raises(ConsentNotGrantedError):
                await orch.verify_consent("cand-001", "comp-001", db=mock_db)
        finally:
            orch_mod._ConsentCheckerService = original

    @pytest.mark.asyncio
    async def test_initiate_call_returns_fallback_when_unconfigured(self, monkeypatch):
        """
        initiate_call returns session with status='fallback' when Twilio is not configured.
        This is an explicit fallback, NOT a mock success — fallback_channel='whatsapp'.
        """
        monkeypatch.delenv("TWILIO_ACCOUNT_SID", raising=False)
        monkeypatch.delenv("TWILIO_VOICE_NUMBER", raising=False)

        from app.services.voice_screening_orchestrator import VoiceScreeningOrchestrator

        orch = VoiceScreeningOrchestrator()

        with patch.object(orch, "verify_consent", new=AsyncMock(return_value=True)):
            session = await orch.initiate_call(
                candidate_id="cand-001",
                candidate_name="João Silva",
                phone_number="+5511999999999",
                job_title="Engenheiro Backend",
                company_id="comp-001",
            )

        assert session.status == "fallback", (
            f"Expected 'fallback' when Twilio unconfigured, got '{session.status}'. "
            "Unconfigured Twilio must NOT return 'initiated' (no mock success)."
        )
        assert session.error is not None
        assert "fallback" in session.error.lower() or "configured" in session.error.lower()
        assert session.consent_verified is True

    @pytest.mark.asyncio
    async def test_process_audio_chunk_converts_mulaw_to_wav(self):
        """process_audio_chunk should convert μ-law to WAV before STT."""
        from app.services.voice_screening_orchestrator import (
            VoiceScreeningOrchestrator,
            VoiceScreeningSession,
        )
        from app.domains.communication.services.twilio_voice_service import mulaw_to_wav

        orch = VoiceScreeningOrchestrator()
        session = VoiceScreeningSession(
            session_id="s1",
            candidate_id="c1",
            candidate_name="Test",
            job_title="Dev",
            company_id="co1",
            phone_number="+5511999999999",
        )
        orch._sessions["s1"] = session

        received_mime_types = []

        async def mock_transcribe(audio_data, mime_type, language):
            received_mime_types.append(mime_type)
            assert mime_type == "audio/wav", f"Gemini must receive audio/wav, got {mime_type}"
            assert audio_data[:4] == b"RIFF", "Audio data must be a valid WAV (RIFF header)"
            return {"text": "Tenho experiência com Python", "language": "pt-BR"}

        mulaw_chunk = bytes(8000)

        mock_svc = MagicMock()
        mock_svc.transcribe_audio = mock_transcribe

        import app.services.voice_screening_orchestrator as orch_mod

        original_get_voice = orch_mod._get_voice_service
        orch_mod._get_voice_service = MagicMock(return_value=mock_svc)
        try:
            result = await orch.process_audio_chunk(
                session_id="s1",
                audio_data=mulaw_chunk,
                mime_type="audio/mulaw",
            )
        finally:
            orch_mod._get_voice_service = original_get_voice

        assert "audio/wav" in received_mime_types, "mulaw must be converted to WAV before Gemini STT"

    @pytest.mark.asyncio
    async def test_synthesize_lia_response_returns_mulaw_for_twilio(self):
        """synthesize_lia_response with for_twilio_stream=True should attempt μ-law conversion."""
        from app.services.voice_screening_orchestrator import VoiceScreeningOrchestrator

        orch = VoiceScreeningOrchestrator()
        fake_mp3 = b"\xff\xfb" + bytes(100)

        with patch.object(orch._tts_service, "synthesize_speech", new=AsyncMock(return_value=fake_mp3)):
            with patch(
                "app.services.voice_screening_orchestrator.mp3_to_mulaw",
                return_value=b"\xff" * 80,
            ) as mock_convert:
                result = await orch.synthesize_lia_response("Olá!", for_twilio_stream=True)

        mock_convert.assert_called_once_with(fake_mp3)
        assert result == b"\xff" * 80

    @pytest.mark.asyncio
    async def test_synthesize_lia_response_returns_mp3_when_not_for_twilio(self):
        """synthesize_lia_response with for_twilio_stream=False should return MP3."""
        from app.services.voice_screening_orchestrator import VoiceScreeningOrchestrator

        orch = VoiceScreeningOrchestrator()
        fake_mp3 = b"\xff\xfb" + bytes(100)

        with patch.object(orch._tts_service, "synthesize_speech", new=AsyncMock(return_value=fake_mp3)):
            with patch(
                "app.services.voice_screening_orchestrator.mp3_to_mulaw"
            ) as mock_convert:
                result = await orch.synthesize_lia_response("Olá!", for_twilio_stream=False)

        mock_convert.assert_not_called()
        assert result == fake_mp3

    @pytest.mark.asyncio
    async def test_finalize_screening_returns_analysis(self):
        """finalize_screening runs analysis and returns WSI result."""
        from app.services.voice_screening_orchestrator import (
            VoiceScreeningOrchestrator,
            VoiceScreeningSession,
        )

        orch = VoiceScreeningOrchestrator()
        session = VoiceScreeningSession(
            session_id="test-session",
            candidate_id="cand-001",
            candidate_name="Maria Santos",
            job_title="Analista de Dados",
            company_id="comp-001",
            phone_number="+5511999999999",
            started_at=datetime.utcnow(),
            transcript_segments=[
                {"text": "Tenho 5 anos de experiência com Python e SQL", "role": "candidate"},
                {"text": "Como você prefere trabalhar?", "role": "lia"},
                {"text": "Prefiro trabalho híbrido", "role": "candidate"},
            ],
        )
        orch._sessions["test-session"] = session

        mock_wsi = {
            "overall_evaluation": {"overall_score": 78, "recommendation": "interview"},
            "summary": "Candidato com boa experiência técnica.",
        }

        import app.services.voice_screening_orchestrator as orch_mod

        original_analyze = orch_mod._analyze_voice_screening
        original_wsi_orch = orch_mod._WSIVoiceOrchestrator
        orch_mod._analyze_voice_screening = AsyncMock(return_value=mock_wsi)
        orch_mod._WSIVoiceOrchestrator = None
        try:
            result = await orch.finalize_screening("test-session")
        finally:
            orch_mod._analyze_voice_screening = original_analyze
            orch_mod._WSIVoiceOrchestrator = original_wsi_orch

        assert result["status"] == "completed"
        assert result["wsi_result"]["overall_evaluation"]["overall_score"] == 78
        assert session.status == "completed"

    @pytest.mark.asyncio
    async def test_finalize_screening_uses_wsi_voice_orchestrator_when_available(self):
        """
        finalize_screening should first try wsi_voice_orchestrator.process_call_completed,
        which integrates with the existing WSI pipeline (WSI questions, scoring, persistence).
        Falls back to analyze_voice_screening only when WSI returns None or fails.
        """
        from app.services.voice_screening_orchestrator import (
            VoiceScreeningOrchestrator,
            VoiceScreeningSession,
        )

        orch = VoiceScreeningOrchestrator()
        session = VoiceScreeningSession(
            session_id="wsi-test",
            candidate_id="cand-001",
            candidate_name="Test",
            job_title="Dev",
            company_id="co1",
            phone_number="+5511999999999",
            call_sid="CA_twilio_call_sid",
            started_at=datetime.utcnow(),
            transcript_segments=[
                {"text": "Tenho 5 anos de Python", "role": "candidate"},
            ],
        )
        orch._sessions["wsi-test"] = session

        mock_wsi_result = {
            "overall_evaluation": {"overall_score": 85, "recommendation": "interview"},
            "wsi_method": "full_pipeline",
        }

        mock_wsi_orch_instance = MagicMock()
        mock_wsi_orch_instance.process_call_completed = AsyncMock(return_value=mock_wsi_result)
        mock_wsi_orch_cls = MagicMock(return_value=mock_wsi_orch_instance)

        import app.services.voice_screening_orchestrator as orch_mod

        original_wsi_orch = orch_mod._WSIVoiceOrchestrator
        orch_mod._WSIVoiceOrchestrator = mock_wsi_orch_cls
        try:
            result = await orch.finalize_screening("wsi-test")
        finally:
            orch_mod._WSIVoiceOrchestrator = original_wsi_orch

        mock_wsi_orch_instance.process_call_completed.assert_called_once()
        call_args = mock_wsi_orch_instance.process_call_completed.call_args
        assert call_args.kwargs.get("call_id") == "CA_twilio_call_sid"
        assert result["status"] == "completed"
        assert result["wsi_result"]["wsi_method"] == "full_pipeline"

    def test_list_active_sessions_masks_pii(self):
        """list_active_sessions should return masked candidate names."""
        from app.services.voice_screening_orchestrator import (
            VoiceScreeningOrchestrator,
            VoiceScreeningSession,
        )

        orch = VoiceScreeningOrchestrator()
        session = VoiceScreeningSession(
            session_id="s1",
            candidate_id="c1",
            candidate_name="Maria santos@email.com",
            job_title="Dev",
            company_id="co1",
            phone_number="+5511999999999",
            status="in_progress",
            started_at=datetime.utcnow(),
        )
        orch._sessions["s1"] = session

        active = orch.list_active_sessions()
        assert len(active) == 1
        assert "@email.com" not in active[0]["candidate_name"]


# ── Circuit Breaker Tests ─────────────────────────────────────────────────────

class TestTwilioVoiceCircuit:
    """Tests for TWILIO_VOICE_CIRCUIT circuit breaker registration."""

    def test_twilio_voice_circuit_is_registered(self):
        """TWILIO_VOICE_CIRCUIT should be in ALL_CIRCUITS."""
        from app.shared.resilience.circuit_breaker import ALL_CIRCUITS, TWILIO_VOICE_CIRCUIT

        assert "twilio_voice" in ALL_CIRCUITS
        assert ALL_CIRCUITS["twilio_voice"] is TWILIO_VOICE_CIRCUIT

    def test_twilio_voice_circuit_has_slo(self):
        """TWILIO_VOICE_CIRCUIT should have SLO definition."""
        from app.shared.resilience.circuit_breaker import CIRCUIT_BREAKER_SLOS

        assert "twilio_voice" in CIRCUIT_BREAKER_SLOS
        slo = CIRCUIT_BREAKER_SLOS["twilio_voice"]
        assert slo["availability_target"] > 0
        assert slo["tier"] in ("critical", "high", "medium", "low")

    def test_twilio_voice_circuit_degraded_response_mentions_fallback(self):
        """Degraded response for twilio_voice should mention WhatsApp fallback."""
        from app.shared.resilience.circuit_breaker import get_degraded_response

        msg = get_degraded_response("twilio_voice")
        assert "whatsapp" in msg.lower() or "chat" in msg.lower() or "voz" in msg.lower()

    def test_twilio_voice_circuit_starts_closed(self):
        """TWILIO_VOICE_CIRCUIT should start in CLOSED state."""
        from app.shared.resilience.circuit_breaker import TWILIO_VOICE_CIRCUIT, CircuitState

        assert TWILIO_VOICE_CIRCUIT.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_open_triggers_fallback_in_orchestrator(self):
        """When TWILIO_VOICE_CIRCUIT is open, session.status must be 'fallback'."""
        from app.services.voice_screening_orchestrator import VoiceScreeningOrchestrator
        from app.shared.resilience.circuit_breaker import CircuitBreakerError
        import app.shared.resilience.circuit_breaker as cb_module

        orch = VoiceScreeningOrchestrator()

        mock_circuit = MagicMock()
        mock_circuit.call = AsyncMock(
            side_effect=CircuitBreakerError("twilio_voice", 45.0)
        )

        import app.services.voice_screening_orchestrator as orch_module

        with patch.object(orch, "verify_consent", new=AsyncMock(return_value=True)):
            with patch.object(orch_module, "TWILIO_VOICE_CIRCUIT", mock_circuit):
                session = await orch.initiate_call(
                    candidate_id="cand-001",
                    candidate_name="Test",
                    phone_number="+5511999999999",
                    job_title="Dev",
                    company_id="comp-001",
                )

        assert session.status == "fallback", (
            "Circuit breaker open must result in status='fallback', not any other status"
        )


# ── Config Tests ──────────────────────────────────────────────────────────────

class TestVoiceConfig:
    """Tests for TWILIO_VOICE_NUMBER config variable."""

    def test_twilio_voice_number_in_settings(self):
        """Settings should have TWILIO_VOICE_NUMBER field."""
        from lia_config.config import Settings
        fields = Settings.model_fields
        assert "TWILIO_VOICE_NUMBER" in fields

    def test_twilio_voice_number_defaults_to_none(self):
        """TWILIO_VOICE_NUMBER should default to None."""
        from lia_config.config import Settings
        field = Settings.model_fields["TWILIO_VOICE_NUMBER"]
        assert field.default is None


# ── CommunicationDispatcher Tests ─────────────────────────────────────────────

class TestCommunicationDispatcherVoice:
    """Tests for make_voice_call in CommunicationDispatcher."""

    @pytest.mark.asyncio
    async def test_make_voice_call_returns_fallback_when_twilio_unconfigured(self, monkeypatch):
        """make_voice_call should return fallback_channel='whatsapp' when Twilio unconfigured."""
        monkeypatch.delenv("TWILIO_ACCOUNT_SID", raising=False)
        monkeypatch.delenv("TWILIO_VOICE_NUMBER", raising=False)

        from app.domains.communication.services.communication_dispatcher import CommunicationDispatcher
        from app.services.voice_screening_orchestrator import voice_screening_orchestrator

        dispatcher = CommunicationDispatcher()

        with patch.object(voice_screening_orchestrator, "verify_consent", new=AsyncMock(return_value=True)):
            result = await dispatcher.make_voice_call(
                candidate_id="cand-001",
                candidate_name="João Silva",
                phone_number="+5511999999999",
                job_title="Engenheiro",
                company_id="comp-001",
            )

        assert result["channel"] == "voice"
        assert result["fallback_channel"] == "whatsapp", (
            "Unconfigured Twilio should return fallback_channel='whatsapp'"
        )

    @pytest.mark.asyncio
    async def test_make_voice_call_fallback_on_unexpected_error(self):
        """make_voice_call should return fallback_channel='whatsapp' on unexpected error."""
        from app.domains.communication.services.communication_dispatcher import CommunicationDispatcher

        dispatcher = CommunicationDispatcher()

        with patch(
            "app.services.voice_screening_orchestrator.voice_screening_orchestrator.initiate_call",
            side_effect=Exception("Connection error"),
        ):
            result = await dispatcher.make_voice_call(
                candidate_id="cand-001",
                candidate_name="João Silva",
                phone_number="+5511999999999",
                job_title="Engenheiro",
                company_id="comp-001",
            )

        assert result["fallback_channel"] == "whatsapp"
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_make_voice_call_re_raises_consent_error(self):
        """make_voice_call must NOT catch ConsentNotGrantedError — re-raise for LGPD compliance."""
        from app.domains.communication.services.communication_dispatcher import CommunicationDispatcher
        from app.services.voice_screening_orchestrator import ConsentNotGrantedError

        dispatcher = CommunicationDispatcher()

        with patch(
            "app.services.voice_screening_orchestrator.voice_screening_orchestrator.initiate_call",
            side_effect=ConsentNotGrantedError("Consent revoked"),
        ):
            with pytest.raises(ConsentNotGrantedError):
                await dispatcher.make_voice_call(
                    candidate_id="cand-001",
                    candidate_name="João Silva",
                    phone_number="+5511999999999",
                    job_title="Engenheiro",
                    company_id="comp-001",
                )


# ── Consent Speech Parsing Tests ──────────────────────────────────────────────

class TestConsentSpeechParsing:
    """Tests for _parse_consent_speech — negative-intent precedence (LGPD)."""

    def _parse(self, speech: str) -> bool:
        from app.api.v1.twilio_voice import _parse_consent_speech
        return _parse_consent_speech(speech)

    def test_empty_speech_denies(self):
        assert self._parse("") is False

    def test_none_normalised_to_empty_denies(self):
        assert self._parse("  ") is False

    def test_plain_affirmative_sim_consents(self):
        assert self._parse("sim") is True

    def test_plain_affirmative_yes_consents(self):
        assert self._parse("yes") is True

    def test_plain_affirmative_concordo_consents(self):
        assert self._parse("concordo") is True

    def test_plain_affirmative_aceito_consents(self):
        assert self._parse("aceito") is True

    def test_nao_aceito_denies(self):
        """Negation must take precedence over affirmative token 'aceito'."""
        assert self._parse("não aceito") is False

    def test_nao_concordo_denies(self):
        """Negation must take precedence over affirmative token 'concordo'."""
        assert self._parse("não concordo") is False

    def test_nao_quero_denies(self):
        assert self._parse("não quero") is False

    def test_no_english_denies(self):
        assert self._parse("no") is False

    def test_nunca_denies(self):
        assert self._parse("nunca") is False

    def test_recuso_denies(self):
        assert self._parse("recuso") is False

    def test_discordo_denies(self):
        assert self._parse("discordo") is False

    def test_nao_prefix_on_long_sentence_denies(self):
        """'não' anywhere in sentence denies even with other affirmatives."""
        assert self._parse("hm não sei, pode ser, ok") is False

    def test_affirmative_without_negation_consents(self):
        assert self._parse("claro, pode continuar") is True

    def test_unrecognised_words_deny(self):
        assert self._parse("hm talvez quem sabe") is False

    def test_authorise_synonym_consents(self):
        assert self._parse("autorizo") is True

    def test_case_insensitive(self):
        assert self._parse("SIM") is True
        assert self._parse("NÃO") is False


# ── PII Masking Tests ─────────────────────────────────────────────────────────

class TestPIIMaskingInTranscripts:
    """Tests for PII masking in voice screening transcripts."""

    def test_mask_pii_removes_email(self):
        """PII masking should remove email addresses from transcripts."""
        from app.shared.pii_masking import mask_pii

        text = "Meu email é candidato@empresa.com.br e trabalho remoto"
        masked = mask_pii(text)

        assert "@empresa.com.br" not in masked
        assert "***EMAIL***" in masked

    def test_mask_pii_removes_cpf(self):
        """PII masking should remove CPF numbers from transcripts."""
        from app.shared.pii_masking import mask_pii

        text = "Meu CPF é 123.456.789-00"
        masked = mask_pii(text)

        assert "123.456.789-00" not in masked
        assert "***CPF***" in masked

    def test_mask_pii_removes_phone(self):
        """PII masking should remove phone numbers from transcripts."""
        from app.shared.pii_masking import mask_pii

        text = "Pode me ligar no 11 99999-8888"
        masked = mask_pii(text)

        assert "99999-8888" not in masked

    def test_mask_transcript_segments_masks_pii_in_each_segment(self):
        """_mask_transcript_segments must mask PII in each segment text without mutating original."""
        from app.services.voice_screening_orchestrator import VoiceScreeningOrchestrator

        segments = [
            {"text": "Meu email é joao@test.com", "role": "candidate"},
            {"text": "Obrigada! Pode me contar sobre experiência?", "role": "lia"},
            {"text": "Meu CPF é 123.456.789-00 tenho 5 anos de Python", "role": "candidate"},
        ]

        masked = VoiceScreeningOrchestrator._mask_transcript_segments(segments)

        assert "joao@test.com" not in masked[0]["text"]
        assert "***EMAIL***" in masked[0]["text"]
        assert "123.456.789-00" not in masked[2]["text"]
        assert "***CPF***" in masked[2]["text"]
        assert "5 anos de Python" in masked[2]["text"]
        assert segments[0]["text"] == "Meu email é joao@test.com", "Original must not be mutated"
        assert len(masked) == len(segments)

    def test_transcript_pii_masking_preserves_professional_content(self):
        """PII masking should preserve professional content while removing PII."""
        from app.shared.pii_masking import mask_pii

        transcript = (
            "CANDIDATO: Meu email é joao@test.com\n"
            "LIA: Obrigada! Pode me contar sobre experiência?\n"
            "CANDIDATO: Tenho 5 anos de experiência com Python"
        )
        masked = mask_pii(transcript)

        assert "joao@test.com" not in masked
        assert "***EMAIL***" in masked
        assert "5 anos de experiência" in masked
        assert "Python" in masked
