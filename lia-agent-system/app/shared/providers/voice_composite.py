"""
Composite Voice Provider — pipeline-based voice for providers without native voice.

Uses STT (Gemini) → LLM text (tenant's provider, e.g. Claude) → TTS (Gemini)
to deliver voice functionality for any LLM provider.

Strategy: COMPOSITE_PIPELINE
"""
import asyncio
import logging
import os
import time
from typing import Any, AsyncIterator

from app.shared.providers.voice_provider import (
    VoiceSessionConfig,
    VoiceSessionMetrics,
    VoiceStrategyType,
    VoiceStreamEvent,
    VoiceStreamProviderABC,
)

logger = logging.getLogger(__name__)


SILENCE_THRESHOLD = 500
SILENCE_DURATION_MS = 800
MIN_SPEECH_BYTES = 16000


class _CompositeSession:
    def __init__(self, session_id: str, config: VoiceSessionConfig):
        self.session_id = session_id
        self.config = config
        self.event_queue: asyncio.Queue[VoiceStreamEvent] = asyncio.Queue()
        self.turn_latencies_ms: list[float] = []
        self.token_usage: dict[str, int] = {"input": 0, "output": 0}
        self.started_at: float = time.monotonic()
        self.closed: bool = False
        self.conversation_history: list[dict[str, str]] = []
        self._processing_lock = asyncio.Lock()
        self._audio_buffer = bytearray()
        self._last_speech_time: float = time.monotonic()
        self._is_speaking: bool = False
        self._vad_task: asyncio.Task | None = None
        self._pipeline_running: bool = False


class CompositeVoiceProvider(VoiceStreamProviderABC):
    _provider_name = "composite"
    _strategy_type = VoiceStrategyType.COMPOSITE_PIPELINE

    def __init__(
        self,
        tenant_id: str | None = None,
        llm_provider_name: str = "claude",
    ):
        self._tenant_id = tenant_id
        self._llm_provider_name = llm_provider_name
        self._gemini_api_key = os.environ.get("AI_INTEGRATIONS_GEMINI_API_KEY")
        self._gemini_base_url = os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL")
        self._sessions: dict[str, _CompositeSession] = {}

    async def is_available(self) -> bool:
        if not self._gemini_api_key or not self._gemini_base_url:
            return False
        from app.shared.resilience.circuit_breaker import GEMINI_CIRCUIT
        return GEMINI_CIRCUIT.state.value != "open"

    async def create_session(self, config: VoiceSessionConfig) -> dict[str, Any]:
        session = _CompositeSession(config.session_id, config)
        self._sessions[config.session_id] = session

        logger.info(
            "[CompositeVoiceProvider] Session created: session=%s tenant=%s llm=%s",
            config.session_id, config.tenant_id, self._llm_provider_name,
        )

        return {
            "session_id": config.session_id,
            "provider": self._provider_name,
            "strategy": self._strategy_type,
            "stt_engine": "gemini",
            "llm_engine": self._llm_provider_name,
            "tts_engine": "gemini",
        }

    async def _stt_transcribe(self, audio_data: bytes) -> str:
        import functools

        from google.genai import types

        # === Tenant-aware Gemini client (LGPD compliance) ===
        from app.shared.tenant_llm_context import get_gemini_client_for_tenant
        client = get_gemini_client_for_tenant(self._tenant_id)

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            functools.partial(
                client.models.generate_content,
                model="gemini-2.5-flash",
                contents=[
                    "Transcreva este áudio em pt-BR com precisão. Forneça apenas a transcrição, sem introdução ou explicações.",
                    types.Part(
                        inline_data=types.Blob(
                            mime_type="audio/pcm;rate=16000",
                            data=audio_data,
                        )
                    ),
                ],
            ),
        )

        return (response.text or "").strip()

    async def _llm_generate(self, session: _CompositeSession, user_text: str) -> str:
        from app.shared.providers.llm_factory import get_provider_for_tenant

        container = get_provider_for_tenant(
            tenant_id=session.config.tenant_id,
            primary_provider=self._llm_provider_name,
        )

        system_prompt = session.config.system_prompt
        if not system_prompt:
            system_prompt = "Assistente de recrutamento. Responda de forma concisa e natural, otimizada para conversação por voz."

        session.conversation_history.append({"role": "user", "content": user_text})
        conversation_text = "\n".join(
            f"{'Candidato' if m['role'] == 'user' else 'LIA'}: {m['content']}"
            for m in session.conversation_history[-10:]
        )

        full_prompt = f"{conversation_text}\nLIA:"

        result = await container.generate_with_fallback(
            prompt=full_prompt,
            system=system_prompt,
            agent_type="VoiceCompositeAgent",
        )

        session.conversation_history.append({"role": "assistant", "content": result})
        return result

    async def _tts_synthesize(self, text: str, voice_name: str = "Aoede") -> bytes:
        import functools

        from google.genai import types

        # === Tenant-aware Gemini client (LGPD compliance) ===
        from app.shared.tenant_llm_context import get_gemini_client_for_tenant
        client = get_gemini_client_for_tenant(self._tenant_id)

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            functools.partial(
                client.models.generate_content,
                model="gemini-2.5-flash",
                contents=[f"Leia o seguinte texto em voz natural em pt-BR: {text}"],
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice_name,
                            )
                        )
                    ),
                ),
            ),
        )

        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    return part.inline_data.data

        return b""

    @staticmethod
    def _detect_speech(audio_data: bytes) -> bool:
        import struct

        if len(audio_data) < 2:
            return False
        num_samples = len(audio_data) // 2
        samples = struct.unpack(f"<{num_samples}h", audio_data[:num_samples * 2])
        rms = (sum(s * s for s in samples) / num_samples) ** 0.5
        return rms > SILENCE_THRESHOLD

    async def send_audio(self, session_id: str, audio_data: bytes) -> None:
        session = self._sessions.get(session_id)
        if not session or session.closed:
            raise RuntimeError(f"Session {session_id} not found or closed")

        if session._pipeline_running:
            return

        has_speech = self._detect_speech(audio_data)

        if has_speech:
            session._audio_buffer.extend(audio_data)
            session._last_speech_time = time.monotonic()
            session._is_speaking = True

            if session._vad_task is None or session._vad_task.done():
                session._vad_task = asyncio.create_task(
                    self._vad_monitor(session)
                )
        elif session._is_speaking:
            session._audio_buffer.extend(audio_data)

    async def _vad_monitor(self, session: _CompositeSession) -> None:
        while not session.closed:
            await asyncio.sleep(0.1)

            if not session._is_speaking:
                return

            silence_elapsed_ms = (time.monotonic() - session._last_speech_time) * 1000
            if silence_elapsed_ms >= SILENCE_DURATION_MS and len(session._audio_buffer) >= MIN_SPEECH_BYTES:
                buffered_audio = bytes(session._audio_buffer)
                session._audio_buffer.clear()
                session._is_speaking = False

                await self._run_pipeline(session, buffered_audio)
                return

    async def _run_pipeline(self, session: _CompositeSession, audio_data: bytes) -> None:
        session._pipeline_running = True
        turn_start = time.monotonic()

        try:
            transcription = await self._stt_transcribe(audio_data)
            if not transcription.strip():
                return

            await session.event_queue.put(VoiceStreamEvent(
                event_type="transcript",
                text=transcription,
                role="candidate",
            ))

            llm_response = await self._llm_generate(session, transcription)
            if not llm_response.strip():
                return

            await session.event_queue.put(VoiceStreamEvent(
                event_type="transcript",
                text=llm_response,
                role="lia",
                is_final=True,
            ))

            audio_response = await self._tts_synthesize(
                llm_response,
                session.config.voice_name,
            )
            if audio_response:
                await session.event_queue.put(VoiceStreamEvent(
                    event_type="audio",
                    data=audio_response,
                    mime_type="audio/pcm",
                ))

            latency_ms = (time.monotonic() - turn_start) * 1000
            session.turn_latencies_ms.append(latency_ms)

            await session.event_queue.put(VoiceStreamEvent(
                event_type="turn_complete",
                metadata={
                    "latency_ms": round(latency_ms, 1),
                    "tokens": dict(session.token_usage),
                    "pipeline": "stt→llm→tts",
                },
            ))

        except Exception as e:
            logger.error(
                "[CompositeVoiceProvider] Pipeline error session=%s: %s",
                session.session_id, e,
            )
            await session.event_queue.put(VoiceStreamEvent(
                event_type="error",
                text=f"Pipeline error: {e}",
            ))
        finally:
            session._pipeline_running = False

    async def send_text(self, session_id: str, text: str) -> None:
        session = self._sessions.get(session_id)
        if not session or session.closed:
            raise RuntimeError(f"Session {session_id} not found or closed")

        async with session._processing_lock:
            turn_start = time.monotonic()

            try:
                await session.event_queue.put(VoiceStreamEvent(
                    event_type="transcript",
                    text=text,
                    role="candidate",
                ))

                llm_response = await self._llm_generate(session, text)
                if not llm_response.strip():
                    return

                await session.event_queue.put(VoiceStreamEvent(
                    event_type="transcript",
                    text=llm_response,
                    role="lia",
                    is_final=True,
                ))

                audio_response = await self._tts_synthesize(
                    llm_response,
                    session.config.voice_name,
                )
                if audio_response:
                    await session.event_queue.put(VoiceStreamEvent(
                        event_type="audio",
                        data=audio_response,
                        mime_type="audio/pcm",
                    ))

                latency_ms = (time.monotonic() - turn_start) * 1000
                session.turn_latencies_ms.append(latency_ms)

                await session.event_queue.put(VoiceStreamEvent(
                    event_type="turn_complete",
                    metadata={
                        "latency_ms": round(latency_ms, 1),
                        "tokens": dict(session.token_usage),
                    },
                ))

            except Exception as e:
                logger.error(
                    "[CompositeVoiceProvider] Text pipeline error session=%s: %s",
                    session_id, e,
                )
                await session.event_queue.put(VoiceStreamEvent(
                    event_type="error",
                    text=f"Pipeline error: {e}",
                ))

    async def receive_events(self, session_id: str) -> AsyncIterator[VoiceStreamEvent]:
        session = self._sessions.get(session_id)
        if not session:
            raise RuntimeError(f"Session {session_id} not found")

        while not session.closed or not session.event_queue.empty():
            try:
                event = await asyncio.wait_for(session.event_queue.get(), timeout=1.0)
                yield event
                if event.event_type == "error":
                    break
            except TimeoutError:
                elapsed = time.monotonic() - session.started_at
                if elapsed > session.config.max_duration_seconds:
                    yield VoiceStreamEvent(
                        event_type="timeout",
                        text="Session expired (max duration reached)",
                    )
                    break
                continue

    async def close_session(self, session_id: str) -> VoiceSessionMetrics:
        session = self._sessions.pop(session_id, None)
        if not session:
            return VoiceSessionMetrics(
                session_id=session_id,
                provider=self._provider_name,
                strategy=self._strategy_type,
            )

        session.closed = True
        if session._vad_task and not session._vad_task.done():
            session._vad_task.cancel()
            try:
                await session._vad_task
            except asyncio.CancelledError:
                pass
        latencies = session.turn_latencies_ms
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0
        total_seconds = time.monotonic() - session.started_at

        logger.info(
            "[CompositeVoiceProvider] Session closed: session=%s turns=%d avg_latency=%.1fms llm=%s",
            session_id, len(latencies), avg_latency, self._llm_provider_name,
        )

        return VoiceSessionMetrics(
            session_id=session_id,
            provider=self._provider_name,
            strategy=self._strategy_type,
            turn_count=len(latencies),
            avg_latency_ms=round(avg_latency, 1),
            p95_latency_ms=round(p95_latency, 1),
            total_audio_seconds=round(total_seconds, 1),
            token_usage=session.token_usage,
        )

    def get_status(self) -> dict[str, Any]:
        return {
            "provider": self._provider_name,
            "strategy": self._strategy_type,
            "configured": bool(self._gemini_api_key and self._gemini_base_url),
            "llm_provider": self._llm_provider_name,
            "active_sessions": len(self._sessions),
        }
