"""
Twilio Voice webhooks PUBLIC contract (Paulo 2026-05-23).

P0 production blocker pre-phone-test:
- 6 endpoints `/api/v1/twilio-voice/*` callados externamente por Twilio (e
  por monitoring externo no caso de /health) DEVEM ser PUBLIC. Sem isso, o
  middleware retornava HTTP 401 quando Twilio fizesse o request real durante
  phone test físico — call mudo / fallback / falha de discovery.

Fix canonical aplicado:
1. PUBLIC_REGEX_PATHS estendido com 6 patterns específicos (greeting,
   consent-response, status, audio-stream, voip-connect, health).
2. Endpoints admin (/initiate, /end-call, /sessions/{sid}, /voip-token)
   PRESERVAM Depends(require_company_id) — recrutador autenticado obrigatório.
3. Segurança canonical nos PUBLIC: X-Twilio-Signature header (HMAC-SHA1 com
   auth_token) validado via twilio_voice_service.verify_webhook_signature.

Sensores deste arquivo:
- 6 endpoints PUBLIC matcham PUBLIC_REGEX_PATHS (positive).
- 4 endpoints admin NÃO matcham PUBLIC_REGEX_PATHS (negative — pin contra
  regressão acidental que liberaria endpoint administrativo).
"""
from __future__ import annotations

import pytest

from app.middleware.auth_enforcement import PUBLIC_REGEX_PATHS


def _matches_public(path: str) -> bool:
    return any(p.match(path) for p in PUBLIC_REGEX_PATHS)


class TestTwilioWebhooksPublicRegex:
    """6 endpoints chamados externamente por Twilio/monitoring DEVEM ser PUBLIC."""

    def test_greeting_endpoint_matches_public_regex(self):
        assert _matches_public("/api/v1/twilio-voice/greeting"), \
            "greeting é callback Twilio canonical — DEVE ser PUBLIC"

    def test_consent_response_matches_public_regex(self):
        assert _matches_public("/api/v1/twilio-voice/consent-response"), \
            "consent-response recebe Twilio Gather speech — DEVE ser PUBLIC"

    def test_status_endpoint_matches_public_regex(self):
        assert _matches_public("/api/v1/twilio-voice/status"), \
            "status é Twilio status callback — DEVE ser PUBLIC"

    def test_audio_stream_matches_public_regex(self):
        assert _matches_public("/api/v1/twilio-voice/audio-stream"), \
            "audio-stream é WebSocket Twilio Media Stream — DEVE ser PUBLIC"

    def test_voip_connect_matches_public_regex(self):
        assert _matches_public("/api/v1/twilio-voice/voip-connect"), \
            "voip-connect é Twilio VoIP TwiML callback — DEVE ser PUBLIC"

    def test_health_matches_public_regex(self):
        assert _matches_public("/api/v1/twilio-voice/health"), \
            "health é endpoint monitoring externo — DEVE ser PUBLIC"


class TestTwilioAdminEndpointsRemainProtected:
    """4 endpoints administrativos NÃO podem matchar PUBLIC_REGEX_PATHS."""

    def test_initiate_NOT_in_public_regex(self):
        assert not _matches_public("/api/v1/twilio-voice/initiate"), \
            "initiate é admin (recrutador inicia) — JWT obrigatório"

    def test_end_call_NOT_in_public_regex(self):
        assert not _matches_public("/api/v1/twilio-voice/end-call/CA1234567890"), \
            "end-call é admin (recrutador encerra) — JWT obrigatório"

    def test_sessions_NOT_in_public_regex(self):
        assert not _matches_public(
            "/api/v1/twilio-voice/sessions/550e8400-e29b-41d4-a716-446655440000"
        ), "sessions é admin polling — JWT obrigatório"

    def test_voip_token_NOT_in_public_regex(self):
        assert not _matches_public("/api/v1/twilio-voice/voip-token"), \
            "voip-token gera token VoIP pro recrutador — JWT obrigatório"


class TestPublicRegexDoesNotOverMatch:
    """Sanity: padrões Twilio NÃO matcham paths não-relacionados."""

    def test_does_not_match_unrelated_path(self):
        assert not _matches_public("/api/v1/twilio-voice/")
        assert not _matches_public("/api/v1/twilio-voice/greeting/extra/path")
        assert not _matches_public("/api/v1/twilio/greeting")  # missing -voice
        assert not _matches_public("/api/v1/twilio-voice-fake/greeting")
