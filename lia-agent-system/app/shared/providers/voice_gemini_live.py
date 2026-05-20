"""
Gemini Live Voice Provider — native multimodal bidirectional streaming.

Wraps the existing GeminiLiveAudioService within the VoiceStreamProviderABC
abstraction, adding tenant isolation and circuit breaker integration.

Strategy: NATIVE_MULTIMODAL (single Gemini Live connection handles STT + LLM + TTS)
"""
import asyncio
import base64
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


class _GeminiLiveSession:
    def __init__(self, session_id: str, config: VoiceSessionConfig):
        self.session_id = session_id
        self.config = config
        self.gemini_session: Any = None
        self.connection_ctx: Any = None
        self.event_queue: asyncio.Queue[VoiceStreamEvent] = asyncio.Queue()
        self.receive_task: asyncio.Task | None = None
        self.turn_latencies_ms: list[float] = []
        self.token_usage: dict[str, int] = {"input": 0, "output": 0}
        self.started_at: float = time.monotonic()
        self.closed: bool = False


class GeminiLiveVoiceProvider(VoiceStreamProviderABC):
    _provider_name = "gemini_live"
    _strategy_type = VoiceStrategyType.NATIVE_MULTIMODAL

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self._api_key = api_key or os.environ.get("AI_INTEGRATIONS_GEMINI_API_KEY")
        self._base_url = base_url or os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL")
        self._sessions: dict[str, _GeminiLiveSession] = {}

    async def is_available(self) -> bool:
        if not self._api_key or not self._base_url:
            return False
        from app.shared.resilience.circuit_breaker import GEMINI_LIVE_CIRCUIT
        return GEMINI_LIVE_CIRCUIT.state.value != "open"

    async def create_session(self, config: VoiceSessionConfig) -> dict[str, Any]:
        from app.shared.resilience.circuit_breaker import GEMINI_LIVE_CIRCUIT
        if GEMINI_LIVE_CIRCUIT.state.value == "open":
            raise RuntimeError("Gemini Live circuit breaker is open")

        from google.genai import types

        # === Tenant-aware Gemini client (LGPD compliance) ===
        from app.shared.tenant_llm_context import get_gemini_client_for_tenant
        client = get_gemini_client_for_tenant(
            config.tenant_id if config else None
        )

        live_config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=config.voice_name,
                    )
                )
            ),
            system_instruction=types.Content(
                parts=[types.Part(text=config.system_prompt)]
            ) if config.system_prompt else None,
        )

        model = config.extra.get("model", "gemini-2.5-flash")
        connection_ctx = client.aio.live.connect(
            model=model,
            config=live_config,
        )
        gemini_session = await connection_ctx.__aenter__()

        session = _GeminiLiveSession(config.session_id, config)
        session.gemini_session = gemini_session
        session.connection_ctx = connection_ctx
        self._sessions[config.session_id] = session

        session.receive_task = asyncio.create_task(
            self._receive_loop(session)
        )

        logger.info(
            "[GeminiLiveVoiceProvider] Session created: session=%s tenant=%s model=%s",
            config.session_id, config.tenant_id, model,
        )

        return {
            "session_id": config.session_id,
            "provider": self._provider_name,
            "strategy": self._strategy_type,
            "model": model,
        }

    async def _receive_loop(self, session: _GeminiLiveSession) -> None:
        from app.shared.resilience.circuit_breaker import GEMINI_LIVE_CIRCUIT

        try:
            while not session.closed:
                turn_start = time.monotonic()
                turn_audio_chunks: list[bytes] = []
                turn_text_parts: list[str] = []

                async for response in session.gemini_session.receive():
                    if session.closed:
                        break

                    if response.data:
                        turn_audio_chunks.append(response.data)

                    if response.text:
                        turn_text_parts.append(response.text)

                    if (
                        response.server_content
                        and hasattr(response.server_content, "input_transcription")
                        and response.server_content.input_transcription
                    ):
                        candidate_text = response.server_content.input_transcription
                        if isinstance(candidate_text, str) and candidate_text.strip():
                            await session.event_queue.put(VoiceStreamEvent(
                                event_type="transcript",
                                text=candidate_text,
                                role="candidate",
                            ))

                    if hasattr(response, "usage_metadata") and response.usage_metadata:
                        um = response.usage_metadata
                        if hasattr(um, "prompt_token_count") and um.prompt_token_count:
                            session.token_usage["input"] += um.prompt_token_count
                        if hasattr(um, "candidates_token_count") and um.candidates_token_count:
                            session.token_usage["output"] += um.candidates_token_count

                    if (
                        response.server_content
                        and hasattr(response.server_content, "turn_complete")
                        and response.server_content.turn_complete
                    ):
                        turn_text = "".join(turn_text_parts)
                        latency_ms = (time.monotonic() - turn_start) * 1000
                        session.turn_latencies_ms.append(latency_ms)

                        for audio_chunk in turn_audio_chunks:
                            await session.event_queue.put(VoiceStreamEvent(
                                event_type="audio",
                                data=audio_chunk,
                                mime_type="audio/pcm",
                            ))

                        if turn_text:
                            await session.event_queue.put(VoiceStreamEvent(
                                event_type="transcript",
                                text=turn_text,
                                role="lia",
                                is_final=True,
                            ))

                        await session.event_queue.put(VoiceStreamEvent(
                            event_type="turn_complete",
                            metadata={
                                "latency_ms": round(latency_ms, 1),
                                "tokens": dict(session.token_usage),
                            },
                        ))

                        turn_audio_chunks.clear()
                        turn_text_parts.clear()
                        break

            await GEMINI_LIVE_CIRCUIT.record_success()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(
                "[GeminiLiveVoiceProvider] Receive error session=%s: %s",
                session.session_id, e,
            )
            try:
                await GEMINI_LIVE_CIRCUIT.record_failure()
            except Exception:
                # T-04 Tipo B: circuit breaker telemetry must not mask the
                # original receive error — log + continue to propagate the
                # error event to the session queue below.
                logger.warning(
                    "[GeminiLiveVoiceProvider] circuit record_failure failed",
                    exc_info=True,
                )
            await session.event_queue.put(VoiceStreamEvent(
                event_type="error",
                text=str(e),
            ))

    async def send_audio(self, session_id: str, audio_data: bytes) -> None:
        session = self._sessions.get(session_id)
        if not session or session.closed:
            raise RuntimeError(f"Session {session_id} not found or closed")

        from google.genai import types
        await session.gemini_session.send(
            input=types.LiveClientRealtimeInput(
                media_chunks=[
                    types.Blob(
                        data=audio_data,
                        mime_type=f"audio/pcm;rate={session.config.sample_rate}",
                    )
                ]
            )
        )

    async def send_text(self, session_id: str, text: str) -> None:
        session = self._sessions.get(session_id)
        if not session or session.closed:
            raise RuntimeError(f"Session {session_id} not found or closed")

        await session.gemini_session.send(input=text, end_of_turn=True)

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
        if session.receive_task:
            session.receive_task.cancel()
            try:
                await session.receive_task
            except asyncio.CancelledError:
                pass

        if session.connection_ctx:
            try:
                await session.connection_ctx.__aexit__(None, None, None)
            except Exception:
                # T-04 Tipo C: connection context teardown is best-effort;
                # remote may already be disconnected.
                logger.debug(
                    "[GeminiLiveVoiceProvider] connection_ctx __aexit__ failed (best-effort)",
                    exc_info=True,
                )

        latencies = session.turn_latencies_ms
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0
        total_seconds = time.monotonic() - session.started_at

        logger.info(
            "[GeminiLiveVoiceProvider] Session closed: session=%s turns=%d avg_latency=%.1fms",
            session_id, len(latencies), avg_latency,
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
            "configured": bool(self._api_key and self._base_url),
            "active_sessions": len(self._sessions),
        }
