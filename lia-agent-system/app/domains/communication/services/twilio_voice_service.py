"""
Twilio Voice Service — Programmable Voice for LIA screening calls.

Provides:
- Outbound call initiation via Twilio Programmable Voice
- TwiML generation for call flow control
- WebSocket audio stream management
- Twilio signature validation for webhook security
- Call status tracking
- Explicit failure (not mock) when unconfigured → callers route to fallback

Environment Variables:
- TWILIO_ACCOUNT_SID: Twilio Account SID
- TWILIO_AUTH_TOKEN: Twilio Auth Token
- TWILIO_VOICE_NUMBER: Twilio Voice phone number (e.g., +5511XXXXX)
- APP_BASE_URL: Public URL for TwiML callbacks
"""

import audioop
import io
import os
import logging
import struct
import wave
import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

try:
    from twilio.rest import Client as TwilioClient
    from twilio.base.exceptions import TwilioRestException
    from twilio.request_validator import RequestValidator
    from twilio.twiml.voice_response import VoiceResponse, Connect, Stream, Say, Pause, Gather
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    TwilioClient = None
    TwilioRestException = Exception
    RequestValidator = None
    VoiceResponse = None
    logger.warning("[TWILIO VOICE] twilio package not available — voice calls disabled")


class TwilioVoiceError(Exception):
    """Error during Twilio Voice operations."""
    pass


class TwilioVoiceUnconfiguredError(TwilioVoiceError):
    """Raised when Twilio Voice is not configured — triggers fallback."""
    pass


# ── Audio transcoding helpers ─────────────────────────────────────────────────

def mulaw_to_wav(mulaw_data: bytes, sample_rate: int = 8000) -> bytes:
    """
    Convert raw μ-law (G.711) bytes to a valid WAV file in-memory.

    Twilio Media Streams send raw μ-law audio at 8kHz, mono.
    Gemini (and most STT APIs) require a valid container format.

    Args:
        mulaw_data: Raw G.711 μ-law bytes
        sample_rate: Sample rate (Twilio default: 8000 Hz)

    Returns:
        WAV file bytes with proper RIFF header
    """
    try:
        pcm_data = audioop.ulaw2lin(mulaw_data, 2)
    except Exception as e:
        logger.warning("[AUDIO] audioop.ulaw2lin failed: %s — using raw data", e)
        pcm_data = mulaw_data

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return buf.getvalue()


def mp3_to_mulaw(mp3_data: bytes) -> Optional[bytes]:
    """
    Convert MP3 audio (from TTS) to raw μ-law for Twilio Media Stream.

    Twilio bidirectional Media Streams require raw μ-law/PCM payload,
    not MP3. This conversion uses pydub when available.

    Args:
        mp3_data: MP3 audio bytes

    Returns:
        Raw μ-law bytes at 8kHz mono, or None if conversion not available
    """
    try:
        from pydub import AudioSegment

        audio = AudioSegment.from_mp3(io.BytesIO(mp3_data))
        audio = audio.set_channels(1).set_frame_rate(8000).set_sample_width(2)
        pcm_data = audio.raw_data

        mulaw_data = audioop.lin2ulaw(pcm_data, 2)
        return mulaw_data

    except ImportError:
        logger.warning(
            "[AUDIO] pydub not available — cannot convert MP3→μ-law for Twilio stream. "
            "Install pydub for real-time TTS playback in calls."
        )
        return None
    except Exception as e:
        logger.error("[AUDIO] MP3→μ-law conversion failed: %s", e)
        return None


# ── TwilioVoiceService ────────────────────────────────────────────────────────

class TwilioVoiceService:
    """
    Twilio Programmable Voice service for candidate screening calls.

    When Twilio is not configured, ALL methods raise TwilioVoiceUnconfiguredError
    instead of returning mock data. Callers must handle this by routing to
    chat/WhatsApp fallback channel.

    Handles:
    - Outbound call initiation
    - TwiML response generation (greeting, consent, audio streaming, end)
    - Webhook signature validation (security)
    - Audio format transcoding helpers (μ-law ↔ WAV ↔ PCM)
    - Call status webhook parsing
    """

    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.voice_number = os.getenv("TWILIO_VOICE_NUMBER")
        self.base_url = os.getenv("APP_BASE_URL", "").rstrip("/")
        self._client: Optional[TwilioClient] = None
        self._validator: Optional[RequestValidator] = None

    @property
    def is_configured(self) -> bool:
        """Check if Twilio Voice is properly configured."""
        return bool(
            TWILIO_AVAILABLE
            and self.account_sid
            and self.auth_token
            and self.voice_number
        )

    @property
    def client(self) -> TwilioClient:
        """Get or create Twilio REST client (lazy init). Raises if not configured."""
        if not self.is_configured:
            raise TwilioVoiceUnconfiguredError(
                "Twilio Voice not configured — set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, "
                "and TWILIO_VOICE_NUMBER. Fallback to WhatsApp/chat screening."
            )
        if self._client is None:
            self._client = TwilioClient(self.account_sid, self.auth_token)
        return self._client

    @property
    def validator(self) -> Optional[RequestValidator]:
        """Get or create Twilio request validator for webhook signature checking."""
        if self._validator is None and self.auth_token and RequestValidator:
            self._validator = RequestValidator(self.auth_token)
        return self._validator

    def _twiml_url(self, path: str) -> str:
        """Build full TwiML callback URL."""
        return f"{self.base_url}/api/v1/twilio-voice{path}"

    def verify_webhook_signature(
        self, url: str, params: Dict[str, str], signature: str
    ) -> bool:
        """
        Verify Twilio webhook request signature (security guard).

        Args:
            url: Full webhook URL (must match exactly what Twilio has configured)
            params: POST form parameters dict
            signature: X-Twilio-Signature header value

        Returns:
            True if signature is valid (or if auth_token not configured — dev mode)
        """
        if not self.auth_token:
            logger.warning("[TWILIO VOICE] No auth_token — skipping webhook signature check (dev mode)")
            return True

        v = self.validator
        if not v:
            logger.warning("[TWILIO VOICE] Validator not available — allowing request")
            return True

        try:
            valid = v.validate(url, params, signature)
            if not valid:
                logger.error("[TWILIO VOICE] Webhook signature INVALID for url=%s", url)
            return valid
        except Exception as e:
            logger.error("[TWILIO VOICE] Signature validation error: %s", e)
            return False

    def make_call(
        self,
        to_phone: str,
        candidate_name: str,
        job_title: str,
        session_id: Optional[str] = None,
        language: str = "pt-BR",
    ) -> Dict[str, Any]:
        """
        Initiate an outbound screening call to a candidate.

        Args:
            to_phone: Candidate phone number (with country code)
            candidate_name: Candidate's name for greeting
            job_title: Job title for context
            session_id: Session ID (generated if not provided)
            language: Language for voice interaction

        Returns:
            Dict with call_sid, session_id, status, or error info.

        Raises:
            TwilioVoiceUnconfiguredError: If Twilio is not configured (callers must fallback)
        """
        session_id = session_id or str(uuid.uuid4())

        if not self.is_configured:
            raise TwilioVoiceUnconfiguredError(
                "Twilio Voice not configured. Use chat/WhatsApp fallback."
            )

        greeting_params = urlencode({
            "session_id": session_id,
            "candidate_name": candidate_name,
            "job_title": job_title,
            "language": language,
        })
        greeting_url = self._twiml_url(f"/greeting?{greeting_params}")
        status_url = self._twiml_url("/status")

        try:
            call = self.client.calls.create(
                to=to_phone,
                from_=self.voice_number,
                url=greeting_url,
                status_callback=status_url,
                status_callback_event=["initiated", "ringing", "answered", "completed"],
                status_callback_method="POST",
                timeout=30,
                record=False,
            )

            logger.info(
                "[TWILIO VOICE] Call initiated: sid=%s to=%s session=%s",
                call.sid,
                to_phone,
                session_id,
            )

            return {
                "success": True,
                "call_sid": call.sid,
                "session_id": session_id,
                "status": call.status,
                "provider": "twilio_voice",
                "timestamp": datetime.utcnow().isoformat(),
            }

        except TwilioRestException as e:
            logger.error("[TWILIO VOICE] API error %s: %s", e.code, e.msg)
            return {
                "success": False,
                "error": e.msg,
                "error_code": str(e.code),
                "session_id": session_id,
                "provider": "twilio_voice",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error("[TWILIO VOICE] Unexpected error: %s", e)
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id,
                "provider": "twilio_voice",
                "timestamp": datetime.utcnow().isoformat(),
            }

    def generate_greeting_twiml(
        self,
        session_id: str,
        candidate_name: str = "candidato",
        job_title: str = "a vaga",
        language: str = "pt-BR",
    ) -> str:
        """
        Generate TwiML for initial call greeting.

        Returns TwiML XML that:
        1. Greets the candidate by name (transparency/Crença #4)
        2. Collects YES/NO consent via Gather
        3. Streams audio to WebSocket after consent confirmed
        """
        if not TWILIO_AVAILABLE:
            raise TwilioVoiceError("Twilio SDK not available")

        response = VoiceResponse()

        lang_code = "pt-BR" if language.startswith("pt") else "en-US"
        voice_name = "Polly.Camila" if lang_code == "pt-BR" else "Polly.Joanna"

        greeting_text = (
            f"Olá, {candidate_name}! Aqui é a LIA, assistente de recrutamento da WeDO Talent. "
            f"Estou ligando para conduzir sua triagem inicial para a posição de {job_title}. "
            f"Esta conversa tem duração de aproximadamente 10 minutos. "
            f"Vou fazer algumas perguntas sobre sua experiência e motivações. "
            f"Podemos começar? Por favor, diga SIM para continuar ou NÃO para encerrar."
        )

        response.say(greeting_text, voice=voice_name, language=lang_code)

        gather = response.gather(
            input="speech",
            action=self._twiml_url(f"/consent-response?session_id={session_id}&language={language}"),
            method="POST",
            timeout=10,
            speech_timeout="auto",
            language=lang_code,
        )
        gather.say(
            "Aguardando sua resposta...",
            voice=voice_name,
            language=lang_code,
        )

        response.say(
            "Não recebemos sua resposta. Encerrando a ligação. Obrigado!",
            voice=voice_name,
            language=lang_code,
        )
        response.hangup()

        return str(response)

    def generate_stream_twiml(
        self,
        session_id: str,
        language: str = "pt-BR",
    ) -> str:
        """
        Generate TwiML to start bidirectional audio streaming via WebSocket.

        After consent is confirmed, this TwiML connects the call to our
        WebSocket endpoint for Gemini STT + LLM + TTS processing.
        Twilio streams bidirectional raw μ-law audio at 8kHz.
        """
        if not TWILIO_AVAILABLE:
            raise TwilioVoiceError("Twilio SDK not available")

        response = VoiceResponse()

        lang_code = "pt-BR" if language.startswith("pt") else "en-US"
        voice_name = "Polly.Camila" if lang_code == "pt-BR" else "Polly.Joanna"

        response.say(
            "Ótimo! Vamos começar a triagem. Fique à vontade para falar naturalmente.",
            voice=voice_name,
            language=lang_code,
        )

        connect = Connect()
        ws_url = (
            self._twiml_url("/audio-stream")
            .replace("https://", "wss://")
            .replace("http://", "ws://")
        )
        stream = Stream(url=f"{ws_url}?session_id={session_id}")
        connect.append(stream)
        response.append(connect)

        return str(response)

    def generate_end_twiml(
        self,
        message: str = (
            "Obrigado pela sua participação na triagem! "
            "Entraremos em contato em breve. Tenha um ótimo dia!"
        ),
        language: str = "pt-BR",
    ) -> str:
        """Generate TwiML to gracefully end a call."""
        if not TWILIO_AVAILABLE:
            raise TwilioVoiceError("Twilio SDK not available")

        response = VoiceResponse()
        lang_code = "pt-BR" if language.startswith("pt") else "en-US"
        voice_name = "Polly.Camila" if lang_code == "pt-BR" else "Polly.Joanna"

        response.say(message, voice=voice_name, language=lang_code)
        response.hangup()

        return str(response)

    def end_call(self, call_sid: str) -> Dict[str, Any]:
        """Programmatically terminate an active call."""
        try:
            call = self.client.calls(call_sid).update(status="completed")
            logger.info("[TWILIO VOICE] Call %s terminated", call_sid)
            return {"success": True, "call_sid": call_sid, "status": call.status}
        except TwilioVoiceUnconfiguredError as e:
            return {"success": False, "error": str(e), "call_sid": call_sid}
        except TwilioRestException as e:
            logger.error("[TWILIO VOICE] Failed to end call %s: %s", call_sid, e.msg)
            return {"success": False, "error": e.msg, "call_sid": call_sid}
        except Exception as e:
            logger.error("[TWILIO VOICE] End call error: %s", e)
            return {"success": False, "error": str(e), "call_sid": call_sid}

    def parse_status_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Twilio Voice call status callback payload."""
        return {
            "call_sid": payload.get("CallSid"),
            "status": payload.get("CallStatus"),
            "direction": payload.get("Direction"),
            "from_number": payload.get("From"),
            "to_number": payload.get("To"),
            "duration": payload.get("CallDuration"),
            "timestamp": datetime.utcnow().isoformat(),
        }


twilio_voice_service = TwilioVoiceService()
