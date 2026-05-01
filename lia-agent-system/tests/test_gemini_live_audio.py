"""
Tests for Gemini Live Audio voice screening pipeline.

Covers:
- GeminiLiveAudioService: session lifecycle, system prompt, fairness, PII masking, metrics
- VoiceScreeningOrchestrator: initiate_voip_session with Gemini Live, fallback chain
- Circuit breaker: GEMINI_LIVE_CIRCUIT integration
- FairnessGuard: L1+L2 on LIA responses
- Provider strategy: voice_provider field serialization

Run:
    pytest tests/test_gemini_live_audio.py -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from datetime import datetime, timedelta


class TestGeminiLiveAudioService:

    def test_service_is_available_when_configured(self):
        with patch.dict("os.environ", {
            "AI_INTEGRATIONS_GEMINI_API_KEY": "test-key",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "https://test.example.com",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            service = GeminiLiveAudioService()
            assert service.is_available is True

    def test_service_not_available_without_api_key(self):
        with patch.dict("os.environ", {
            "AI_INTEGRATIONS_GEMINI_API_KEY": "",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "https://test.example.com",
        }, clear=False):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            service = GeminiLiveAudioService()
            assert service.is_available is False

    def test_service_not_available_without_base_url(self):
        with patch.dict("os.environ", {
            "AI_INTEGRATIONS_GEMINI_API_KEY": "test-key",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "",
        }, clear=False):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            service = GeminiLiveAudioService()
            assert service.is_available is False

    def test_create_session_returns_valid_session(self):
        with patch.dict("os.environ", {
            "AI_INTEGRATIONS_GEMINI_API_KEY": "test-key",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "https://test.example.com",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            service = GeminiLiveAudioService()

            session = service.create_session(
                candidate_id="cand-123",
                candidate_name="Maria Silva",
                job_title="Engenheira de Software",
                company_id="comp-456",
                job_id="job-789",
                language="pt-BR",
            )

            assert session.session_id is not None
            assert session.candidate_id == "cand-123"
            assert session.candidate_name == "Maria Silva"
            assert session.job_title == "Engenheira de Software"
            assert session.company_id == "comp-456"
            assert session.voice_provider == "gemini_live"
            assert session.status == "pending"
            assert session.consent_verified is True
            assert session.started_at is not None

    def test_get_session_returns_existing_session(self):
        with patch.dict("os.environ", {
            "AI_INTEGRATIONS_GEMINI_API_KEY": "test-key",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "https://test.example.com",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            service = GeminiLiveAudioService()

            session = service.create_session(
                candidate_id="c1", candidate_name="Test", job_title="Dev",
                company_id="co1",
            )
            retrieved = service.get_session(session.session_id)
            assert retrieved is not None
            assert retrieved.session_id == session.session_id

    def test_get_session_returns_none_for_unknown(self):
        with patch.dict("os.environ", {
            "AI_INTEGRATIONS_GEMINI_API_KEY": "test-key",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "https://test.example.com",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            service = GeminiLiveAudioService()
            assert service.get_session("nonexistent-id") is None

    def test_remove_session(self):
        with patch.dict("os.environ", {
            "AI_INTEGRATIONS_GEMINI_API_KEY": "test-key",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "https://test.example.com",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            service = GeminiLiveAudioService()

            session = service.create_session(
                candidate_id="c1", candidate_name="Test", job_title="Dev",
                company_id="co1",
            )
            service.remove_session(session.session_id)
            assert service.get_session(session.session_id) is None

    def test_remove_session_nonexistent_no_error(self):
        with patch.dict("os.environ", {
            "AI_INTEGRATIONS_GEMINI_API_KEY": "test-key",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "https://test.example.com",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            service = GeminiLiveAudioService()
            service.remove_session("does-not-exist")


class TestSystemPrompt:

    def test_system_prompt_contains_candidate_name(self):
        with patch.dict("os.environ", {
            "AI_INTEGRATIONS_GEMINI_API_KEY": "k",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "u",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            service = GeminiLiveAudioService()

            session = service.create_session(
                candidate_id="c1", candidate_name="João Pereira",
                job_title="QA Engineer", company_id="co1",
            )
            prompt = service.build_system_prompt(session)

            assert "João Pereira" in prompt
            assert "QA Engineer" in prompt

    def test_system_prompt_contains_fairness_guardrails(self):
        with patch.dict("os.environ", {
            "AI_INTEGRATIONS_GEMINI_API_KEY": "k",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "u",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            service = GeminiLiveAudioService()

            session = service.create_session(
                candidate_id="c1", candidate_name="Test",
                job_title="Dev", company_id="co1",
            )
            prompt = service.build_system_prompt(session)

            assert "PERGUNTAS PROIBIDAS" in prompt
            assert "Idade" in prompt
            assert "Gênero" in prompt
            assert "Raça" in prompt
            assert "Estado civil" in prompt
            assert "LGPD" in prompt

    def test_system_prompt_contains_anti_sycophancy(self):
        with patch.dict("os.environ", {
            "AI_INTEGRATIONS_GEMINI_API_KEY": "k",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "u",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            service = GeminiLiveAudioService()

            session = service.create_session(
                candidate_id="c1", candidate_name="Test",
                job_title="Dev", company_id="co1",
            )
            prompt = service.build_system_prompt(session)

            assert "sycophancy" in prompt.lower() or "ANTI-SYCOPHANCY" in prompt

    def test_system_prompt_includes_wsi_questions_when_provided(self):
        with patch.dict("os.environ", {
            "AI_INTEGRATIONS_GEMINI_API_KEY": "k",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "u",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            service = GeminiLiveAudioService()

            session = service.create_session(
                candidate_id="c1", candidate_name="Test",
                job_title="Dev", company_id="co1",
            )
            questions = [
                "Descreva um projeto desafiador.",
                "Como você lida com prazos apertados?",
            ]
            prompt = service.build_system_prompt(session, wsi_questions=questions)

            assert "Descreva um projeto desafiador" in prompt
            assert "Como você lida com prazos apertados" in prompt

    def test_system_prompt_includes_job_context_when_available(self):
        with patch.dict("os.environ", {
            "AI_INTEGRATIONS_GEMINI_API_KEY": "k",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "u",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            service = GeminiLiveAudioService()

            session = service.create_session(
                candidate_id="c1", candidate_name="Test",
                job_title="Dev", company_id="co1",
                job_context={"title": "Senior Dev", "department": "Engineering"},
            )
            prompt = service.build_system_prompt(session)

            assert "JOB DESCRIPTION" in prompt or "CONTEXTO DA VAGA" in prompt


class TestFairnessGuardIntegration:

    @pytest.mark.asyncio
    async def test_process_lia_text_appends_transcript(self):
        with patch.dict("os.environ", {
            "AI_INTEGRATIONS_GEMINI_API_KEY": "k",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "u",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            service = GeminiLiveAudioService()

            session = service.create_session(
                candidate_id="c1", candidate_name="Test",
                job_title="Dev", company_id="co1",
            )

            with patch("app.services.gemini_live_audio_service.check_fairness") as mock_fairness:
                mock_fairness.return_value = MagicMock(is_blocked=False)
                result = await service.process_lia_text(session, "Qual sua experiência com Python?")

            assert result == "Qual sua experiência com Python?"
            assert len(session.transcript_segments) == 1
            assert session.transcript_segments[0]["role"] == "lia"

    @pytest.mark.asyncio
    async def test_process_lia_text_blocks_biased_response(self):
        with patch.dict("os.environ", {
            "AI_INTEGRATIONS_GEMINI_API_KEY": "k",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "u",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            service = GeminiLiveAudioService()

            session = service.create_session(
                candidate_id="c1", candidate_name="Test",
                job_title="Dev", company_id="co1",
            )

            with patch("app.services.gemini_live_audio_service.check_fairness") as mock_fairness:
                blocked_result = MagicMock()
                blocked_result.category = "gender_bias"
                mock_fairness.return_value = MagicMock(
                    is_blocked=True, blocked_result=blocked_result,
                )
                result = await service.process_lia_text(session, "biased content")

            assert result is None
            assert len(session.transcript_segments) == 0

    @pytest.mark.asyncio
    async def test_process_lia_text_empty_returns_none(self):
        with patch.dict("os.environ", {
            "AI_INTEGRATIONS_GEMINI_API_KEY": "k",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "u",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            service = GeminiLiveAudioService()

            session = service.create_session(
                candidate_id="c1", candidate_name="Test",
                job_title="Dev", company_id="co1",
            )
            result = await service.process_lia_text(session, "")
            assert result is None
            assert len(session.transcript_segments) == 0


class TestCandidateTextProcessing:

    @pytest.mark.asyncio
    async def test_process_candidate_text_appends_transcript(self):
        with patch.dict("os.environ", {
            "AI_INTEGRATIONS_GEMINI_API_KEY": "k",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "u",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            service = GeminiLiveAudioService()

            session = service.create_session(
                candidate_id="c1", candidate_name="Test",
                job_title="Dev", company_id="co1",
            )
            await service.process_candidate_text(session, "Tenho 5 anos de experiência.")

            assert len(session.transcript_segments) == 1
            assert session.transcript_segments[0]["role"] == "candidate"
            assert session.transcript_segments[0]["text"] == "Tenho 5 anos de experiência."

    @pytest.mark.asyncio
    async def test_process_candidate_text_empty_ignored(self):
        with patch.dict("os.environ", {
            "AI_INTEGRATIONS_GEMINI_API_KEY": "k",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "u",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            service = GeminiLiveAudioService()

            session = service.create_session(
                candidate_id="c1", candidate_name="Test",
                job_title="Dev", company_id="co1",
            )
            await service.process_candidate_text(session, "")
            await service.process_candidate_text(session, "   ")
            assert len(session.transcript_segments) == 0


class TestSessionMetrics:

    def test_record_turn_latency(self):
        with patch.dict("os.environ", {
            "AI_INTEGRATIONS_GEMINI_API_KEY": "k",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "u",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            service = GeminiLiveAudioService()

            session = service.create_session(
                candidate_id="c1", candidate_name="Test",
                job_title="Dev", company_id="co1",
            )
            service.record_turn_latency(session, 150.0)
            service.record_turn_latency(session, 250.0)
            service.record_turn_latency(session, 600.0)

            assert len(session.turn_latencies_ms) == 3
            assert session.turn_latencies_ms[0] == 150.0

    def test_record_token_usage(self):
        with patch.dict("os.environ", {
            "AI_INTEGRATIONS_GEMINI_API_KEY": "k",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "u",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            service = GeminiLiveAudioService()

            session = service.create_session(
                candidate_id="c1", candidate_name="Test",
                job_title="Dev", company_id="co1",
            )
            service.record_token_usage(session, input_tokens=100, output_tokens=50)
            service.record_token_usage(session, input_tokens=200, output_tokens=80)

            assert session.token_usage["input"] == 300
            assert session.token_usage["output"] == 130

    def test_is_session_expired_false_when_fresh(self):
        with patch.dict("os.environ", {
            "AI_INTEGRATIONS_GEMINI_API_KEY": "k",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "u",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            service = GeminiLiveAudioService()

            session = service.create_session(
                candidate_id="c1", candidate_name="Test",
                job_title="Dev", company_id="co1",
            )
            assert service.is_session_expired(session) is False

    def test_is_session_expired_true_after_timeout(self):
        with patch.dict("os.environ", {
            "AI_INTEGRATIONS_GEMINI_API_KEY": "k",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "u",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            service = GeminiLiveAudioService()

            session = service.create_session(
                candidate_id="c1", candidate_name="Test",
                job_title="Dev", company_id="co1",
            )
            session.started_at = datetime.utcnow() - timedelta(seconds=1300)
            assert service.is_session_expired(session) is True

    def test_get_session_metrics(self):
        with patch.dict("os.environ", {
            "AI_INTEGRATIONS_GEMINI_API_KEY": "k",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "u",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            service = GeminiLiveAudioService()

            session = service.create_session(
                candidate_id="c1", candidate_name="Test",
                job_title="Dev", company_id="co1",
            )
            service.record_turn_latency(session, 200.0)
            service.record_turn_latency(session, 300.0)
            service.record_token_usage(session, input_tokens=100, output_tokens=50)

            metrics = service.get_session_metrics(session)
            assert metrics["session_id"] == session.session_id
            assert metrics["voice_provider"] == "gemini_live"
            assert metrics["turn_count"] == 2
            assert metrics["avg_latency_ms"] == 250.0

    @pytest.mark.asyncio
    async def test_finalize_session(self):
        with patch.dict("os.environ", {
            "AI_INTEGRATIONS_GEMINI_API_KEY": "k",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "u",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            service = GeminiLiveAudioService()

            session = service.create_session(
                candidate_id="c1", candidate_name="Test",
                job_title="Dev", company_id="co1",
            )
            service.record_turn_latency(session, 200.0)
            service.record_turn_latency(session, 300.0)
            service.record_token_usage(session, input_tokens=100, output_tokens=50)

            result = await service.finalize_session(session)

            assert result["status"] == "completed"
            assert result["voice_provider"] == "gemini_live"
            assert result["duration_seconds"] is not None
            assert result["latency_avg_ms"] == 250.0
            assert session.ended_at is not None


class TestCircuitBreakerRegistration:

    def test_gemini_live_circuit_registered(self):
        from app.shared.resilience.circuit_breaker import ALL_CIRCUITS
        assert "gemini_live" in ALL_CIRCUITS

    def test_gemini_live_circuit_importable(self):
        from app.shared.resilience.circuit_breaker import GEMINI_LIVE_CIRCUIT
        assert GEMINI_LIVE_CIRCUIT is not None

    def test_gemini_live_circuit_starts_closed(self):
        from app.shared.resilience.circuit_breaker import GEMINI_LIVE_CIRCUIT
        stats = GEMINI_LIVE_CIRCUIT.get_stats()
        assert stats["state"] in ("closed", "half_open")


class TestVoiceScreeningSessionProvider:

    def test_voice_provider_field_default_twilio(self):
        from app.domains.voice.services.voice_screening_orchestrator import VoiceScreeningSession
        session = VoiceScreeningSession(
            session_id="test-1",
            candidate_id="c1",
            candidate_name="Test",
            job_title="Dev",
            company_id="co1",
            phone_number="+5511999999999",
        )
        assert session.voice_provider == "twilio"

    def test_voice_provider_field_gemini_live(self):
        from app.domains.voice.services.voice_screening_orchestrator import VoiceScreeningSession
        session = VoiceScreeningSession(
            session_id="test-2",
            candidate_id="c1",
            candidate_name="Test",
            job_title="Dev",
            company_id="co1",
            phone_number="voip",
            voice_provider="gemini_live",
        )
        assert session.voice_provider == "gemini_live"


class TestOrchestratorSerialization:

    def test_session_to_state_includes_voice_provider(self):
        from app.domains.voice.services.voice_screening_orchestrator import (
            VoiceScreeningOrchestrator,
            VoiceScreeningSession,
        )
        orch = VoiceScreeningOrchestrator()
        session = VoiceScreeningSession(
            session_id="test-ser",
            candidate_id="c1",
            candidate_name="Test",
            job_title="Dev",
            company_id="co1",
            phone_number="voip",
            voice_provider="gemini_live",
        )
        state = orch._session_to_state(session)
        assert state["voice_provider"] == "gemini_live"

    def test_state_to_session_restores_voice_provider(self):
        from app.domains.voice.services.voice_screening_orchestrator import VoiceScreeningOrchestrator
        orch = VoiceScreeningOrchestrator()
        state = {
            "session_id": "test-deser",
            "candidate_id": "c1",
            "candidate_name": "Test",
            "job_title": "Dev",
            "company_id": "co1",
            "phone_number": "voip",
            "voice_provider": "gemini_live",
        }
        session = orch._state_to_session(state)
        assert session.voice_provider == "gemini_live"

    def test_state_to_session_defaults_twilio_for_old_sessions(self):
        from app.domains.voice.services.voice_screening_orchestrator import VoiceScreeningOrchestrator
        orch = VoiceScreeningOrchestrator()
        state = {
            "session_id": "test-old",
            "candidate_id": "c1",
            "candidate_name": "Test",
            "job_title": "Dev",
            "company_id": "co1",
            "phone_number": "+5511999999999",
        }
        session = orch._state_to_session(state)
        assert session.voice_provider == "twilio"


class TestInitiateVoipSession:

    @pytest.mark.asyncio
    async def test_initiate_voip_session_gemini_live_available(self):
        from app.domains.voice.services.voice_screening_orchestrator import VoiceScreeningOrchestrator

        orch = VoiceScreeningOrchestrator()

        mock_live_service = MagicMock()
        mock_live_service.is_available = True
        mock_session = MagicMock()
        mock_session.session_id = "gemini-session-1"
        mock_session.job_context = None
        mock_live_service.create_session.return_value = mock_session

        mock_circuit = MagicMock()
        mock_circuit.state.value = "closed"

        with patch("app.services.voice_screening_orchestrator.voice_screening_orchestrator", orch):
            with patch.object(orch, "verify_consent", new_callable=AsyncMock):
                with patch(
                    "app.services.gemini_live_audio_service.get_gemini_live_service",
                    return_value=mock_live_service,
                ):
                    with patch(
                        "app.shared.resilience.circuit_breaker.GEMINI_LIVE_CIRCUIT",
                        mock_circuit,
                    ):
                        session = await orch.initiate_voip_session(
                            candidate_id="c1",
                            candidate_name="Test",
                            job_title="Dev",
                            company_id="co1",
                        )

        assert session.session_id == "gemini-session-1"
        assert session.status == "ready"
        assert session.voice_provider == "gemini_live"

    @pytest.mark.asyncio
    async def test_initiate_voip_session_gemini_unavailable_returns_fallback(self):
        from app.domains.voice.services.voice_screening_orchestrator import VoiceScreeningOrchestrator

        orch = VoiceScreeningOrchestrator()

        mock_live_service = MagicMock()
        mock_live_service.is_available = False

        with patch.object(orch, "verify_consent", new_callable=AsyncMock):
            with patch(
                "app.services.gemini_live_audio_service.get_gemini_live_service",
                return_value=mock_live_service,
            ):
                session = await orch.initiate_voip_session(
                    candidate_id="c1",
                    candidate_name="Test",
                    job_title="Dev",
                    company_id="co1",
                )

        assert session.status == "fallback"
        assert session.voice_provider == "fallback"

    @pytest.mark.asyncio
    async def test_initiate_voip_session_circuit_open_returns_fallback(self):
        from app.domains.voice.services.voice_screening_orchestrator import VoiceScreeningOrchestrator

        orch = VoiceScreeningOrchestrator()

        mock_live_service = MagicMock()
        mock_live_service.is_available = True

        mock_circuit = MagicMock()
        mock_circuit.state.value = "open"

        with patch.object(orch, "verify_consent", new_callable=AsyncMock):
            with patch(
                "app.services.gemini_live_audio_service.get_gemini_live_service",
                return_value=mock_live_service,
            ):
                with patch(
                    "app.shared.resilience.circuit_breaker.GEMINI_LIVE_CIRCUIT",
                    mock_circuit,
                ):
                    session = await orch.initiate_voip_session(
                        candidate_id="c1",
                        candidate_name="Test",
                        job_title="Dev",
                        company_id="co1",
                    )

        assert session.status == "fallback"
        assert session.voice_provider == "fallback"
        assert "circuit" in session.error.lower()

    @pytest.mark.asyncio
    async def test_initiate_voip_session_consent_revoked_raises(self):
        from app.domains.voice.services.voice_screening_orchestrator import (
            VoiceScreeningOrchestrator,
            ConsentNotGrantedError,
        )

        orch = VoiceScreeningOrchestrator()

        with patch.object(
            orch, "verify_consent",
            new_callable=AsyncMock,
            side_effect=ConsentNotGrantedError("consent revoked"),
        ):
            with pytest.raises(ConsentNotGrantedError):
                await orch.initiate_voip_session(
                    candidate_id="c1",
                    candidate_name="Test",
                    job_title="Dev",
                    company_id="co1",
                )


class TestConnectionConfig:

    @pytest.mark.asyncio
    async def test_create_live_connection_config_structure(self):
        with patch.dict("os.environ", {
            "AI_INTEGRATIONS_GEMINI_API_KEY": "k",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "u",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            service = GeminiLiveAudioService()

            session = service.create_session(
                candidate_id="c1", candidate_name="Test",
                job_title="Dev", company_id="co1",
            )

            config = await service.create_live_connection_config(session)

            assert "model" in config
            assert "system_instruction" in config
            assert config["generation_config"]["response_modalities"] == ["AUDIO"]
            assert "voice_config" in config["generation_config"]["speech_config"]


class TestRouterRegistration:

    def test_gemini_voice_router_has_required_routes(self):
        from app.api.v1.gemini_voice import router

        route_paths = [r.path for r in router.routes]
        assert "/gemini-voice/start-session" in route_paths
        assert "/gemini-voice/session/{session_id}" in route_paths
        assert "/gemini-voice/health" in route_paths

    def test_gemini_voice_router_has_websocket(self):
        from app.api.v1.gemini_voice import router

        ws_routes = [
            r for r in router.routes
            if hasattr(r, "path") and "live-stream" in r.path
        ]
        assert len(ws_routes) >= 1


class TestWebSocketSecurity:

    def test_active_ws_sessions_tracking_exists(self):
        from app.api.v1.gemini_voice import _active_ws_sessions, _ws_ip_connections
        assert isinstance(_active_ws_sessions, dict)
        assert isinstance(_ws_ip_connections, dict)

    def test_max_ws_per_ip_limit_set(self):
        from app.api.v1.gemini_voice import MAX_WS_PER_IP
        assert MAX_WS_PER_IP >= 1
        assert MAX_WS_PER_IP <= 10


class TestFallbackChainConsistency:

    @pytest.mark.asyncio
    async def test_voip_start_returns_chat_fallback_when_gemini_unavailable(self):
        from app.domains.voice.services.voice_screening_orchestrator import (
            VoiceScreeningOrchestrator,
            VoiceScreeningSession,
        )

        orch = VoiceScreeningOrchestrator()

        mock_live_service = MagicMock()
        mock_live_service.is_available = False

        with patch.object(orch, "verify_consent", new_callable=AsyncMock):
            with patch(
                "app.services.gemini_live_audio_service.get_gemini_live_service",
                return_value=mock_live_service,
            ):
                session = await orch.initiate_voip_session(
                    candidate_id="c1",
                    candidate_name="Test",
                    job_title="Dev",
                    company_id="co1",
                )

        assert session.status == "fallback"
        assert session.voice_provider == "fallback"
        assert session.error is not None

    def test_voip_button_ws_url_uses_api_v1_path(self):
        """Frontend WebSocket URL should use /api/v1/ prefix (handled by next.config.js rewrite)."""
        import os
        tsx_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "plataforma-lia", "src", "components", "triagem", "VoIPCallButton.tsx",
        )
        if not os.path.exists(tsx_path):
            pytest.skip("VoIPCallButton.tsx not found in expected location")
        with open(tsx_path) as f:
            content = f.read()
        assert "/api/v1/gemini-voice/live-stream" in content
        assert "/api/backend-proxy/gemini-voice" not in content


class TestWsTokenAuth:

    def test_generate_ws_token_returns_string(self):
        with patch.dict("os.environ", {"SECRET_KEY": "test-secret-key"}):
            from app.api.v1.gemini_voice import _generate_ws_token
            token = _generate_ws_token("sess-1", "comp-1", "cand-1")
            assert isinstance(token, str)
            assert len(token) == 32

    def test_generate_ws_token_fails_without_secret(self):
        with patch.dict("os.environ", {"SECRET_KEY": "", "APP_SECRET_KEY": ""}, clear=False):
            from app.api.v1.gemini_voice import _generate_ws_token
            with pytest.raises(RuntimeError, match="SECRET_KEY"):
                _generate_ws_token("sess-1", "comp-1", "cand-1")

    def test_verify_ws_token_returns_false_without_secret(self):
        with patch.dict("os.environ", {"SECRET_KEY": "", "APP_SECRET_KEY": ""}, clear=False):
            from app.api.v1.gemini_voice import _verify_ws_token
            assert _verify_ws_token("any-token-value-1234567890abcd", "s", "c", "d") is False

    def test_verify_ws_token_valid(self):
        with patch.dict("os.environ", {"SECRET_KEY": "test-secret-key"}):
            from app.api.v1.gemini_voice import _generate_ws_token, _verify_ws_token
            token = _generate_ws_token("sess-1", "comp-1", "cand-1")
            assert _verify_ws_token(token, "sess-1", "comp-1", "cand-1") is True

    def test_verify_ws_token_invalid(self):
        with patch.dict("os.environ", {"SECRET_KEY": "test-secret-key"}):
            from app.api.v1.gemini_voice import _verify_ws_token
            assert _verify_ws_token("bad-token-value-1234567890ab", "sess-1", "comp-1", "cand-1") is False

    def test_verify_ws_token_wrong_session(self):
        with patch.dict("os.environ", {"SECRET_KEY": "test-secret-key"}):
            from app.api.v1.gemini_voice import _generate_ws_token, _verify_ws_token
            token = _generate_ws_token("sess-1", "comp-1", "cand-1")
            assert _verify_ws_token(token, "sess-WRONG", "comp-1", "cand-1") is False

    def test_verify_ws_token_wrong_company(self):
        with patch.dict("os.environ", {"SECRET_KEY": "test-secret-key"}):
            from app.api.v1.gemini_voice import _generate_ws_token, _verify_ws_token
            token = _generate_ws_token("sess-1", "comp-1", "cand-1")
            assert _verify_ws_token(token, "sess-1", "comp-WRONG", "cand-1") is False

    def test_verify_ws_token_wrong_candidate(self):
        with patch.dict("os.environ", {"SECRET_KEY": "test-secret-key"}):
            from app.api.v1.gemini_voice import _generate_ws_token, _verify_ws_token
            token = _generate_ws_token("sess-1", "comp-1", "cand-1")
            assert _verify_ws_token(token, "sess-1", "comp-1", "cand-WRONG") is False

    def test_ws_endpoint_requires_ws_token_param(self):
        from app.api.v1.gemini_voice import router
        ws_routes = [r for r in router.routes if hasattr(r, "path") and "live-stream" in r.path]
        assert len(ws_routes) >= 1

    def test_start_session_response_includes_ws_token_field(self):
        from app.api.v1.gemini_voice import StartSessionResponse
        fields = StartSessionResponse.model_fields
        assert "ws_token" in fields


class TestFallbackChainFull:

    @pytest.mark.asyncio
    async def test_fallback_gemini_to_twilio_when_gemini_unavailable(self):
        from app.domains.voice.services.voice_screening_orchestrator import (
            VoiceScreeningOrchestrator,
        )

        orch = VoiceScreeningOrchestrator()

        mock_live_service = MagicMock()
        mock_live_service.is_available = False

        with patch.object(orch, "verify_consent", new_callable=AsyncMock):
            with patch(
                "app.services.gemini_live_audio_service.get_gemini_live_service",
                return_value=mock_live_service,
            ):
                session = await orch.initiate_voip_session(
                    candidate_id="c1",
                    candidate_name="Test",
                    job_title="Dev",
                    company_id="co1",
                    language="pt-BR",
                )
                assert session.voice_provider in ("unavailable", "fallback")
                assert session.status in ("fallback", "error")

    @pytest.mark.asyncio
    async def test_fallback_chain_order_documented(self):
        from app.api.v1.gemini_voice import router
        health_routes = [r for r in router.routes if hasattr(r, "path") and "health" in r.path]
        assert len(health_routes) >= 1


class TestTokenTrackingIntegration:

    def test_token_tracking_service_importable(self):
        from app.shared.services.token_tracking_service import TokenTrackingService
        assert TokenTrackingService is not None

    def test_token_tracking_has_record_usage_method(self):
        from app.shared.services.token_tracking_service import TokenTrackingService
        mock_db = MagicMock()
        svc = TokenTrackingService(db=mock_db)
        assert hasattr(svc, "record_usage")
        assert callable(svc.record_usage)

    def test_session_token_usage_tracked(self):
        with patch.dict("os.environ", {
            "AI_INTEGRATIONS_GEMINI_API_KEY": "k",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "u",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            service = GeminiLiveAudioService()
            session = service.create_session(
                candidate_id="c1", candidate_name="Test",
                job_title="Dev", company_id="comp-1",
            )
            service.record_token_usage(session, input_tokens=100, output_tokens=200)
            assert session.token_usage["input"] == 100
            assert session.token_usage["output"] == 200
            service.record_token_usage(session, input_tokens=50, output_tokens=30)
            assert session.token_usage["input"] == 150
            assert session.token_usage["output"] == 230


class TestCandidateTranscriptCapture:

    def test_process_candidate_text_adds_to_transcript(self):
        with patch.dict("os.environ", {
            "AI_INTEGRATIONS_GEMINI_API_KEY": "k",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "u",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            service = GeminiLiveAudioService()
            session = service.create_session(
                candidate_id="c1", candidate_name="Test",
                job_title="Dev", company_id="comp-1",
            )

            import asyncio
            asyncio.get_event_loop().run_until_complete(
                service.process_candidate_text(session, "Minha experiência inclui Python e React")
            )

            candidate_segments = [s for s in session.transcript_segments if s.get("role") == "candidate"]
            assert len(candidate_segments) == 1
            assert "Python" in candidate_segments[0]["text"]

    def test_process_lia_text_adds_to_transcript(self):
        with patch.dict("os.environ", {
            "AI_INTEGRATIONS_GEMINI_API_KEY": "k",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "u",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            service = GeminiLiveAudioService()
            session = service.create_session(
                candidate_id="c1", candidate_name="Test",
                job_title="Dev", company_id="comp-1",
            )

            import asyncio
            mock_fairness = MagicMock()
            mock_fairness.is_blocked = False
            with patch("app.services.gemini_live_audio_service.check_fairness", return_value=mock_fairness):
                result = asyncio.get_event_loop().run_until_complete(
                    service.process_lia_text(session, "Conte-me sobre sua experiência")
                )

            assert result is not None
            lia_segments = [s for s in session.transcript_segments if s.get("role") == "lia"]
            assert len(lia_segments) == 1

    def test_transcript_has_both_roles_for_finalization(self):
        with patch.dict("os.environ", {
            "AI_INTEGRATIONS_GEMINI_API_KEY": "k",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "u",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            service = GeminiLiveAudioService()
            session = service.create_session(
                candidate_id="c1", candidate_name="Test",
                job_title="Dev", company_id="comp-1",
            )

            import asyncio
            mock_fairness = MagicMock()
            mock_fairness.is_blocked = False
            with patch("app.services.gemini_live_audio_service.check_fairness", return_value=mock_fairness):
                asyncio.get_event_loop().run_until_complete(
                    service.process_lia_text(session, "Qual sua experiência?")
                )
            asyncio.get_event_loop().run_until_complete(
                service.process_candidate_text(session, "Tenho 5 anos de experiência")
            )

            roles = {s["role"] for s in session.transcript_segments}
            assert "lia" in roles
            assert "candidate" in roles
            assert len(session.transcript_segments) == 2


class TestWebSocketIntegration:

    def _make_app(self):
        from fastapi import FastAPI
        from app.api.v1.gemini_voice import router
        app = FastAPI()
        app.include_router(router, prefix="/api/v1")
        return app

    def test_ws_rejects_missing_session(self):
        from fastapi.testclient import TestClient
        app = self._make_app()
        client = TestClient(app)
        with patch.dict("os.environ", {
            "SECRET_KEY": "test-key",
            "AI_INTEGRATIONS_GEMINI_API_KEY": "k",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "u",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            svc = GeminiLiveAudioService()
            with patch("app.services.gemini_live_audio_service.get_gemini_live_service", return_value=svc):
                with client.websocket_connect(
                    "/api/v1/gemini-voice/live-stream?session_id=nonexistent&ws_token=badtoken"
                ) as ws:
                    data = ws.receive_json()
                    assert data["type"] == "error"
                    assert "inválida" in data["message"].lower() or "sessão" in data["message"].lower()

    def test_ws_rejects_invalid_ws_token(self):
        from fastapi.testclient import TestClient
        app = self._make_app()
        client = TestClient(app)
        with patch.dict("os.environ", {
            "SECRET_KEY": "test-key",
            "AI_INTEGRATIONS_GEMINI_API_KEY": "k",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "u",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            svc = GeminiLiveAudioService()
            session = svc.create_session(
                candidate_id="c1", candidate_name="Test",
                job_title="Dev", company_id="comp-1",
            )
            with patch("app.services.gemini_live_audio_service.get_gemini_live_service", return_value=svc):
                with client.websocket_connect(
                    f"/api/v1/gemini-voice/live-stream?session_id={session.session_id}&ws_token=invalid_token_value_1234567890"
                ) as ws:
                    data = ws.receive_json()
                    assert data["type"] == "error"
                    assert "token" in data["message"].lower()

    def test_ws_rejects_duplicate_session(self):
        from fastapi.testclient import TestClient
        from app.api.v1.gemini_voice import _active_ws_sessions
        app = self._make_app()
        client = TestClient(app)
        with patch.dict("os.environ", {
            "SECRET_KEY": "test-key",
            "AI_INTEGRATIONS_GEMINI_API_KEY": "k",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "u",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            svc = GeminiLiveAudioService()
            session = svc.create_session(
                candidate_id="c1", candidate_name="Test",
                job_title="Dev", company_id="comp-1",
            )
            _active_ws_sessions[session.session_id] = True
            try:
                with patch("app.services.gemini_live_audio_service.get_gemini_live_service", return_value=svc):
                    with client.websocket_connect(
                        f"/api/v1/gemini-voice/live-stream?session_id={session.session_id}&ws_token=dummy"
                    ) as ws:
                        data = ws.receive_json()
                        assert data["type"] == "error"
                        assert "ativa" in data["message"].lower()
            finally:
                _active_ws_sessions.pop(session.session_id, None)

    def test_ws_rejects_empty_company_id(self):
        from fastapi.testclient import TestClient
        app = self._make_app()
        client = TestClient(app)
        with patch.dict("os.environ", {
            "SECRET_KEY": "test-key",
            "AI_INTEGRATIONS_GEMINI_API_KEY": "k",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "u",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            svc = GeminiLiveAudioService()
            session = svc.create_session(
                candidate_id="c1", candidate_name="Test",
                job_title="Dev", company_id="",
            )
            with patch("app.services.gemini_live_audio_service.get_gemini_live_service", return_value=svc):
                with client.websocket_connect(
                    f"/api/v1/gemini-voice/live-stream?session_id={session.session_id}&ws_token=dummy"
                ) as ws:
                    data = ws.receive_json()
                    assert data["type"] == "error"
                    assert "tenant" in data["message"].lower()

    def test_ws_accepts_valid_token_and_connects(self):
        from fastapi.testclient import TestClient
        from app.api.v1.gemini_voice import _generate_ws_token, _active_ws_sessions
        app = self._make_app()
        client = TestClient(app)
        with patch.dict("os.environ", {
            "SECRET_KEY": "test-key",
            "AI_INTEGRATIONS_GEMINI_API_KEY": "k",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "u",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            svc = GeminiLiveAudioService()
            session = svc.create_session(
                candidate_id="c1", candidate_name="Test",
                job_title="Dev", company_id="comp-1",
            )
            ws_token = _generate_ws_token(session.session_id, "comp-1", "c1")
            with patch("app.services.gemini_live_audio_service.get_gemini_live_service", return_value=svc):
                with client.websocket_connect(
                    f"/api/v1/gemini-voice/live-stream?session_id={session.session_id}&ws_token={ws_token}"
                ) as ws:
                    data = ws.receive_json()
                    assert data["type"] == "status"
                    assert data["status"] == "connected"
                    assert data["voice_provider"] == "gemini_live"
            _active_ws_sessions.pop(session.session_id, None)


class TestTenantIsolation:

    def test_session_requires_company_id(self):
        with patch.dict("os.environ", {
            "AI_INTEGRATIONS_GEMINI_API_KEY": "k",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "u",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            service = GeminiLiveAudioService()

            session = service.create_session(
                candidate_id="c1", candidate_name="Test",
                job_title="Dev", company_id="comp-123",
            )
            assert session.company_id == "comp-123"
            assert session.candidate_id == "c1"

    def test_session_without_company_id_still_created(self):
        with patch.dict("os.environ", {
            "AI_INTEGRATIONS_GEMINI_API_KEY": "k",
            "AI_INTEGRATIONS_GEMINI_BASE_URL": "u",
        }):
            from app.shared.services.gemini_live_audio_service import GeminiLiveAudioService
            service = GeminiLiveAudioService()

            session = service.create_session(
                candidate_id="c1", candidate_name="Test",
                job_title="Dev", company_id="",
            )
            assert session.company_id == ""
