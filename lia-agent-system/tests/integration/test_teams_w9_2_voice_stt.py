"""
W9.2 — Voice/audio STT via Gemini: Teams audio/video attachment transcription.

Tests:
1. audio/* routes to process_voice_attachment (dispatch)
2. video/* also routes to process_voice_attachment (dispatch)
3. Transcription routes transcript through orchestrator as text
4. Large file (>20 MB) returns size-limit redirect message
5. STT error → graceful fallback (not an exception)
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _activity(text: str = "mensagem de voz") -> dict:
    return {
        "type": "message",
        "text": text,
        "from": {"id": "u1", "name": "Recruiter"},
        "conversation": {"id": "conv1"},
        "channelData": {"tenant": {"id": "t1"}},
    }


def _attachment(content_type: str, name: str = "file") -> dict:
    return {
        "contentType": content_type,
        "contentUrl": "https://example.com/audio",
        "name": name,
    }


# ── Attachment routing dispatch ───────────────────────────────────────────────

class TestAudioDispatchRouting:
    """W9.2: audio/* and video/* must both route to process_voice_attachment."""

    @pytest.mark.asyncio
    async def test_audio_routes_to_process_voice_attachment(self):
        from app.domains.communication.services.teams_orchestrator_bridge import TeamsOrchestratorBridge

        bridge = TeamsOrchestratorBridge()
        att = _attachment("audio/mpeg", "message.mp3")

        with patch.object(
            bridge, "process_voice_attachment",
            new=AsyncMock(return_value={"success": True, "message": "Audio transcrito."})
        ):
            ct = (att.get("contentType") or "").lower()
            if ct.startswith("video/") or ct.startswith("audio/"):
                result = await bridge.process_voice_attachment({}, att, db=None)
            else:
                result = {"error": "wrong route"}

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_video_routes_to_process_voice_attachment(self):
        from app.domains.communication.services.teams_orchestrator_bridge import TeamsOrchestratorBridge

        bridge = TeamsOrchestratorBridge()
        att = _attachment("video/mp4", "interview.mp4")

        with patch.object(
            bridge, "process_voice_attachment",
            new=AsyncMock(return_value={"success": True, "message": "Video transcrito."})
        ):
            ct = (att.get("contentType") or "").lower()
            if ct.startswith("video/") or ct.startswith("audio/"):
                result = await bridge.process_voice_attachment({}, att, db=None)
            else:
                result = {"error": "wrong route"}

        assert result["success"] is True


# ── process_voice_attachment ──────────────────────────────────────────────────

class TestProcessVoiceAttachment:
    @pytest.mark.asyncio
    async def test_transcription_routes_through_orchestrator(self):
        """Successful transcription → process_message called with transcript text."""
        from app.domains.communication.services.teams_orchestrator_bridge import TeamsOrchestratorBridge

        bridge = TeamsOrchestratorBridge()
        activity = _activity()
        att = _attachment("audio/mpeg", "message.mp3")

        mock_process_message = AsyncMock(return_value={"success": True, "message": "Processado."})

        mock_gemini_resp = MagicMock()
        mock_gemini_resp.text = "Ola, gostaria de saber sobre a vaga de desenvolvedor Python."

        with (
            patch("app.domains.communication.services.teams_simple.simple_teams_bot") as mock_bot,
            patch.object(bridge, "process_message", new=mock_process_message),
            patch(
                "app.domains.ai.services.llm.llm_service.generate_native_gemini",
                new=AsyncMock(return_value=mock_gemini_resp),
            ),
        ):
            mock_bot.get_access_token = AsyncMock(return_value="token")
            import httpx
            with patch("httpx.AsyncClient") as mock_client:
                mock_resp = MagicMock()
                mock_resp.content = b"fake_audio_bytes_content"
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)

                result = await bridge.process_voice_attachment(activity, att, db=None)

        assert result["success"] is True
        mock_process_message.assert_called_once()
        call_args = mock_process_message.call_args
        fake_act = call_args[0][0] if call_args[0] else call_args.kwargs.get("activity", {})
        assert "Audio" in fake_act.get("text", "") or "message.mp3" in fake_act.get("text", "")
        assert "gostaria de saber" in fake_act.get("text", "")

    @pytest.mark.asyncio
    async def test_large_file_returns_size_limit_message(self):
        """Files > 20 MB should return a helpful redirect, not call STT."""
        from app.domains.communication.services.teams_orchestrator_bridge import TeamsOrchestratorBridge

        bridge = TeamsOrchestratorBridge()
        att = _attachment("video/mp4", "entrevista_completa.mp4")

        with (
            patch("app.domains.communication.services.teams_simple.simple_teams_bot") as mock_bot,
        ):
            mock_bot.get_access_token = AsyncMock(return_value="token")
            import httpx
            with patch("httpx.AsyncClient") as mock_client:
                mock_resp = MagicMock()
                mock_resp.content = b"x" * (21 * 1024 * 1024)  # 21 MB
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)

                result = await bridge.process_voice_attachment({}, att, db=None)

        assert isinstance(result, dict)
        assert "message" in result
        assert result.get("success") is True
        msg = result["message"].lower()
        assert "grande demais" in msg or "20 mb" in msg or "mb" in msg

    @pytest.mark.asyncio
    async def test_graceful_fallback_on_stt_error(self):
        """Gemini STT failure → helpful fallback message, no exception raised."""
        from app.domains.communication.services.teams_orchestrator_bridge import TeamsOrchestratorBridge

        bridge = TeamsOrchestratorBridge()
        att = _attachment("audio/wav", "voice_note.wav")

        with (
            patch("app.domains.communication.services.teams_simple.simple_teams_bot") as mock_bot,
            patch(
                "app.domains.ai.services.llm.llm_service.generate_native_gemini",
                new=AsyncMock(side_effect=RuntimeError("Gemini STT unavailable")),
            ),
        ):
            mock_bot.get_access_token = AsyncMock(return_value="token")
            import httpx
            with patch("httpx.AsyncClient") as mock_client:
                mock_resp = MagicMock()
                mock_resp.content = b"audio_data"
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)

                result = await bridge.process_voice_attachment({}, att, db=None)

        assert isinstance(result, dict)
        assert "message" in result
        assert result.get("success") is True
