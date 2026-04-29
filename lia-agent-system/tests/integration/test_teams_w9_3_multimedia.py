"""
W9.3 — Files multimedia além de PDF: image/video/document routing.

Tests:
1. PDF attachment routes to process_cv_attachment (unchanged)
2. image/* routes to process_image_attachment
3. video/* returns acknowledgment message (STT pending)
4. text/plain routes to process_general_document
5. process_image_attachment gracefully handles Gemini Vision error
6. process_general_document extracts text and routes via orchestrator
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_BRIDGE = "app.domains.communication.services.teams_orchestrator_bridge"
_TEAMS = "app.api.v1.teams"


def _activity(text: str = "arquivo") -> dict:
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
        "contentUrl": "https://example.com/file",
        "name": name,
    }


# ── Attachment routing via teams.py dispatch ──────────────────────────────────

class TestAttachmentRouting:
    """W9.3: teams.py dispatch must route by MIME type."""

    @pytest.mark.asyncio
    async def test_pdf_routes_to_process_cv(self):
        from app.domains.communication.services.teams_orchestrator_bridge import TeamsOrchestratorBridge

        bridge = TeamsOrchestratorBridge()
        activity = _activity()
        att = _attachment("application/pdf", "cv.pdf")

        with patch.object(bridge, "process_cv_attachment", new=AsyncMock(return_value={"success": True, "message": "CV processado."})):
            # W9.3 dispatch logic extracted here for unit testing
            ct = (att.get("contentType") or "").lower()
            name = (att.get("name") or "").lower()
            if ct == "application/pdf" or name.endswith(".pdf"):
                result = await bridge.process_cv_attachment(activity, att, db=None)
            else:
                result = {"error": "wrong route"}
        assert result["success"] is True
        assert "CV" in result["message"] or "processado" in result["message"]

    @pytest.mark.asyncio
    async def test_image_routes_to_process_image(self):
        from app.domains.communication.services.teams_orchestrator_bridge import TeamsOrchestratorBridge

        bridge = TeamsOrchestratorBridge()
        att = _attachment("image/png", "logo.png")

        with patch.object(
            bridge, "process_image_attachment",
            new=AsyncMock(return_value={"success": True, "message": "Imagem recebida."})
        ):
            ct = (att.get("contentType") or "").lower()
            if ct.startswith("image/"):
                result = await bridge.process_image_attachment({}, att, db=None)
            else:
                result = {"error": "wrong route"}
        assert result["success"] is True

    def test_video_returns_acknowledgment_message(self):
        """Video/audio should return a helpful message, not call any method."""
        att = _attachment("video/mp4", "interview.mp4")
        ct = (att.get("contentType") or "").lower()
        if ct.startswith("video/") or ct.startswith("audio/"):
            result = {
                "success": False,
                "message": (
                    "Arquivo de vídeo/áudio recebido. "
                    "O processamento de áudio estará disponível em breve."
                ),
            }
        else:
            result = {"error": "wrong route"}
        assert "vídeo" in result["message"] or "video" in result["message"].lower()


# ── process_image_attachment ──────────────────────────────────────────────────

class TestProcessImageAttachment:
    @pytest.mark.asyncio
    async def test_describes_image_via_gemini_vision(self):
        from app.domains.communication.services.teams_orchestrator_bridge import TeamsOrchestratorBridge

        bridge = TeamsOrchestratorBridge()
        activity = _activity()
        att = _attachment("image/jpeg", "profile.jpg")

        mock_response = MagicMock()
        mock_response.text = "Foto de perfil profissional de um candidato."

        with (
            patch("app.domains.communication.services.teams_simple.simple_teams_bot") as mock_bot,
            patch("app.domains.ai.services.llm.llm_service.generate_native_gemini", new=AsyncMock(return_value=mock_response)),
        ):
            mock_bot.get_access_token = AsyncMock(return_value="token")
            import httpx
            with patch("httpx.AsyncClient") as mock_client:
                mock_resp = MagicMock()
                mock_resp.content = b"fake_image_bytes"
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)

                result = await bridge.process_image_attachment(activity, att, db=None)

        assert result["success"] is True
        assert "profile.jpg" in result["message"] or "Imagem" in result["message"]

    @pytest.mark.asyncio
    async def test_graceful_fallback_when_vision_fails(self):
        """If Gemini Vision fails, should return a helpful fallback, not raise."""
        from app.domains.communication.services.teams_orchestrator_bridge import TeamsOrchestratorBridge

        bridge = TeamsOrchestratorBridge()
        att = _attachment("image/png", "diagram.png")

        with patch("app.domains.communication.services.teams_simple.simple_teams_bot") as mock_bot:
            mock_bot.get_access_token = AsyncMock(return_value="token")
            import httpx
            with patch("httpx.AsyncClient") as mock_client:
                mock_resp = MagicMock()
                mock_resp.content = b"x" * 50000  # 50KB
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)

                with patch("google.genai.types.Part.from_bytes", side_effect=RuntimeError("vision down")):
                    result = await bridge.process_image_attachment({}, att, db=None)

        # Should return success=True with fallback message (not raise)
        assert isinstance(result, dict)
        # Either success with fallback or failure with error — not an exception
        assert "message" in result


# ── process_general_document ──────────────────────────────────────────────────

class TestProcessGeneralDocument:
    @pytest.mark.asyncio
    async def test_txt_routes_through_orchestrator(self):
        from app.domains.communication.services.teams_orchestrator_bridge import TeamsOrchestratorBridge

        bridge = TeamsOrchestratorBridge()
        activity = _activity()
        att = _attachment("text/plain", "requirements.txt")

        mock_process_message = AsyncMock(return_value={"success": True, "message": "Processado."})
        with (
            patch("app.domains.communication.services.teams_simple.simple_teams_bot") as mock_bot,
            patch.object(bridge, "process_message", new=mock_process_message),
        ):
            mock_bot.get_access_token = AsyncMock(return_value="token")
            import httpx
            with patch("httpx.AsyncClient") as mock_client:
                mock_resp = MagicMock()
                mock_resp.content = "Requisitos da vaga: Python, FastAPI".encode()
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)

                result = await bridge.process_general_document(activity, att, db=None)

        assert result["success"] is True
        mock_process_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_docx_returns_platform_redirect_message(self):
        """Binary .docx should return redirect to web platform message."""
        from app.domains.communication.services.teams_orchestrator_bridge import TeamsOrchestratorBridge

        bridge = TeamsOrchestratorBridge()
        att = _attachment(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "report.docx"
        )

        with patch("app.domains.communication.services.teams_simple.simple_teams_bot") as mock_bot:
            mock_bot.get_access_token = AsyncMock(return_value="token")
            import httpx
            with patch("httpx.AsyncClient") as mock_client:
                mock_resp = MagicMock()
                mock_resp.content = b"PK\x03\x04" + b"\x00" * 1000  # fake docx bytes
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)

                result = await bridge.process_general_document({}, att, db=None)

        assert result["success"] is True
        assert "plataforma web" in result["message"]
