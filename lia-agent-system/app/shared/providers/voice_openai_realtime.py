"""
OpenAI Realtime Voice Provider — native multimodal bidirectional streaming.

Uses the OpenAI Realtime API for bidirectional voice conversations.
Strategy: NATIVE_MULTIMODAL (single WebSocket handles STT + LLM + TTS)
"""
import asyncio
import base64
import json
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

OPENAI_REALTIME_URL = "wss://api.openai.com/v1/realtime"
# Canonical model 2026-05-22. gpt-4o-realtime-preview was DEPRECATED by OpenAI 2026-05-12.
# gpt-realtime (GA since 2025-09-08) is the supported successor; gpt-realtime-2 (~20% cheaper) is the
# next iteration. Do NOT regress to gpt-4o-realtime-preview — covered by sensor
# scripts/check_realtime_uses_canonical_model.py (BLOCKING).
OPENAI_REALTIME_MODEL = "gpt-realtime"


class _OpenAIRealtimeSession:
    def __init__(self, session_id: str, config: VoiceSessionConfig):
        self.session_id = session_id
        self.config = config
        self.ws: Any = None
        self.event_queue: asyncio.Queue[VoiceStreamEvent] = asyncio.Queue()
        self.receive_task: asyncio.Task | None = None
        self.turn_latencies_ms: list[float] = []
        self.token_usage: dict[str, int] = {"input": 0, "output": 0}
        self.started_at: float = time.monotonic()
        self.closed: bool = False
        self._current_turn_start: float = 0.0


class OpenAIRealtimeVoiceProvider(VoiceStreamProviderABC):
    _provider_name = "openai_realtime"
    _strategy_type = VoiceStrategyType.NATIVE_MULTIMODAL

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
        self._sessions: dict[str, _OpenAIRealtimeSession] = {}

    async def is_available(self) -> bool:
        if not self._api_key:
            return False
        from app.shared.resilience.circuit_breaker import OPENAI_CIRCUIT
        return OPENAI_CIRCUIT.state.value != "open"

    async def create_session(self, config: VoiceSessionConfig) -> dict[str, Any]:
        from app.shared.resilience.circuit_breaker import OPENAI_CIRCUIT
        if OPENAI_CIRCUIT.state.value == "open":
            raise RuntimeError("OpenAI circuit breaker is open")

        try:
            import websockets
        except ImportError:
            raise RuntimeError("websockets package required for OpenAI Realtime")

        model = config.extra.get("model", OPENAI_REALTIME_MODEL)
        url = f"{OPENAI_REALTIME_URL}?model={model}"

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "OpenAI-Beta": "realtime=v1",
        }

        ws = await websockets.connect(url, additional_headers=headers)

        session_update = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": config.system_prompt,
                "voice": self._map_voice_name(config.voice_name),
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500,
                },
                "input_audio_transcription": {
                    "model": "whisper-1",
                },
            },
        }
        await ws.send(json.dumps(session_update))

        session = _OpenAIRealtimeSession(config.session_id, config)
        session.ws = ws
        self._sessions[config.session_id] = session

        session.receive_task = asyncio.create_task(
            self._receive_loop(session)
        )

        logger.info(
            "[OpenAIRealtimeVoiceProvider] Session created: session=%s tenant=%s model=%s",
            config.session_id, config.tenant_id, model,
        )

        return {
            "session_id": config.session_id,
            "provider": self._provider_name,
            "strategy": self._strategy_type,
            "model": model,
        }

    @staticmethod
    def _map_voice_name(voice_name: str) -> str:
        voice_map = {
            "Aoede": "alloy",
            "alloy": "alloy",
            "echo": "echo",
            "shimmer": "shimmer",
            "ash": "ash",
            "ballad": "ballad",
            "coral": "coral",
            "sage": "sage",
            "verse": "verse",
        }
        return voice_map.get(voice_name, "alloy")

    async def _receive_loop(self, session: _OpenAIRealtimeSession) -> None:
        from app.shared.resilience.circuit_breaker import OPENAI_CIRCUIT

        try:
            async for raw_msg in session.ws:
                if session.closed:
                    break

                try:
                    event = json.loads(raw_msg)
                except json.JSONDecodeError:
                    # T-04 Tipo D: OpenAI Realtime WebSocket occasionally
                    # sends non-JSON frames (binary audio, keepalive); skip
                    # and read next frame. Logging here would be spammy.
                    continue

                event_type = event.get("type", "")

                if event_type == "response.audio.delta":
                    audio_b64 = event.get("delta", "")
                    if audio_b64:
                        audio_bytes = base64.b64decode(audio_b64)
                        await session.event_queue.put(VoiceStreamEvent(
                            event_type="audio",
                            data=audio_bytes,
                            mime_type="audio/pcm",
                        ))

                elif event_type == "response.audio_transcript.done":
                    transcript = event.get("transcript", "")
                    if transcript:
                        await session.event_queue.put(VoiceStreamEvent(
                            event_type="transcript",
                            text=transcript,
                            role="lia",
                            is_final=True,
                        ))

                elif event_type == "conversation.item.input_audio_transcription.completed":
                    transcript = event.get("transcript", "")
                    if transcript:
                        await session.event_queue.put(VoiceStreamEvent(
                            event_type="transcript",
                            text=transcript,
                            role="candidate",
                        ))

                elif event_type == "input_audio_buffer.speech_started":
                    session._current_turn_start = time.monotonic()

                elif event_type == "response.done":
                    response_data = event.get("response", {})
                    usage = response_data.get("usage", {})
                    if usage:
                        session.token_usage["input"] += usage.get("input_tokens", 0)
                        session.token_usage["output"] += usage.get("output_tokens", 0)

                    if session._current_turn_start > 0:
                        latency_ms = (time.monotonic() - session._current_turn_start) * 1000
                        session.turn_latencies_ms.append(latency_ms)
                        session._current_turn_start = 0.0
                    else:
                        latency_ms = 0

                    await session.event_queue.put(VoiceStreamEvent(
                        event_type="turn_complete",
                        metadata={
                            "latency_ms": round(latency_ms, 1),
                            "tokens": dict(session.token_usage),
                        },
                    ))

                elif event_type == "error":
                    error_data = event.get("error", {})
                    error_msg = error_data.get("message", "Unknown OpenAI Realtime error")
                    logger.error(
                        "[OpenAIRealtimeVoiceProvider] Error session=%s: %s",
                        session.session_id, error_msg,
                    )
                    await session.event_queue.put(VoiceStreamEvent(
                        event_type="error",
                        text=error_msg,
                    ))

            await OPENAI_CIRCUIT.record_success()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(
                "[OpenAIRealtimeVoiceProvider] Receive error session=%s: %s",
                session.session_id, e,
            )
            try:
                await OPENAI_CIRCUIT.record_failure()
            except Exception:
                # T-04 Tipo B: circuit breaker telemetry must not mask the
                # original receive error — log + continue to propagate the
                # error event to the session queue below.
                logger.warning(
                    "[OpenAIRealtimeVoiceProvider] circuit record_failure failed",
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

        audio_b64 = base64.b64encode(audio_data).decode()
        msg = {
            "type": "input_audio_buffer.append",
            "audio": audio_b64,
        }
        await session.ws.send(json.dumps(msg))

    async def send_text(self, session_id: str, text: str) -> None:
        session = self._sessions.get(session_id)
        if not session or session.closed:
            raise RuntimeError(f"Session {session_id} not found or closed")

        msg = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": text}],
            },
        }
        await session.ws.send(json.dumps(msg))
        await session.ws.send(json.dumps({"type": "response.create"}))

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

        if session.ws:
            try:
                await session.ws.close()
            except Exception:
                # T-04 Tipo C: websocket close is best-effort teardown;
                # peer may already have closed or be unreachable.
                logger.debug(
                    "[OpenAIRealtimeVoiceProvider] ws close failed (best-effort)",
                    exc_info=True,
                )

        latencies = session.turn_latencies_ms
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0
        total_seconds = time.monotonic() - session.started_at

        logger.info(
            "[OpenAIRealtimeVoiceProvider] Session closed: session=%s turns=%d avg_latency=%.1fms",
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
            "configured": bool(self._api_key),
            "active_sessions": len(self._sessions),
        }
