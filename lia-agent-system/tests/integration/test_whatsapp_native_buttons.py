"""
Integration Tests — WhatsApp Native Interactive Buttons via Twilio (Task #64).

Exercita:
- TwilioWhatsAppService.get_template_sid(): resolve SID correto por nome de template
- TwilioWhatsAppService.send_interactive_buttons(): roteia para nativo vs text-fallback
- TwilioWhatsAppService._send_native_interactive(): payload correto (content_sid)
- TwilioWhatsAppService._send_interactive_text_fallback(): formato numerado correto
- send_screening_invitation: constrói convite de triagem com botões corretos
- send_interview_confirmation_request: constrói confirmação de entrevista
- send_feedback_result: constrói mensagem de feedback
- Fallback automático para texto numerado quando template não configurado
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BASE_ENV = {
    "TWILIO_ACCOUNT_SID": "ACtest123",
    "TWILIO_AUTH_TOKEN": "auth_token_test",
    "TWILIO_WHATSAPP_NUMBER": "whatsapp:+15005550006",
    "ENVIRONMENT": "production",
}


def _get_service_class():
    from app.domains.communication.services.whatsapp_twilio_service import TwilioWhatsAppService
    return TwilioWhatsAppService


def _make_mock_twilio_message(sid="SM_test_001", status="queued"):
    msg = MagicMock()
    msg.sid = sid
    msg.status = status
    return msg


def _patch_client_create(service, return_message):
    """
    Patch the Twilio client.messages.create on the service.
    Since `client` is a @property, we patch the underlying `_client` attribute
    or inject via the module-level singleton.
    """
    mock_client = MagicMock()
    mock_client.messages.create.return_value = return_message
    return patch.object(type(service), "client", new_callable=PropertyMock, return_value=mock_client), mock_client


# ---------------------------------------------------------------------------
# Seção 1 — get_template_sid(): resolução de SIDs por nome de template
# ---------------------------------------------------------------------------

class TestGetTemplateSid:

    def test_returns_none_when_env_not_set(self):
        with patch.dict("os.environ", BASE_ENV, clear=True):
            service = _get_service_class()()
            assert service.get_template_sid("triagem") is None
            assert service.get_template_sid("entrevista") is None
            assert service.get_template_sid("feedback") is None

    def test_returns_sid_when_env_set(self):
        env = {
            **BASE_ENV,
            "TWILIO_TEMPLATE_TRIAGEM_SID": "HX_triagem_001",
            "TWILIO_TEMPLATE_ENTREVISTA_SID": "HX_entrevista_002",
            "TWILIO_TEMPLATE_FEEDBACK_SID": "HX_feedback_003",
        }
        with patch.dict("os.environ", env, clear=True):
            service = _get_service_class()()
            assert service.get_template_sid("triagem") == "HX_triagem_001"
            assert service.get_template_sid("entrevista") == "HX_entrevista_002"
            assert service.get_template_sid("feedback") == "HX_feedback_003"

    def test_returns_none_for_unknown_template_name(self):
        with patch.dict("os.environ", BASE_ENV, clear=True):
            service = _get_service_class()()
            assert service.get_template_sid("unknown_template") is None


# ---------------------------------------------------------------------------
# Seção 2 — send_interactive_buttons(): roteamento nativo vs text-fallback
# ---------------------------------------------------------------------------

class TestSendInteractiveButtonsRouting:

    @pytest.mark.asyncio
    async def test_routes_to_text_fallback_when_no_template_sid(self):
        from app.domains.communication.services.whatsapp_provider import SendResult
        with patch.dict("os.environ", BASE_ENV, clear=True):
            service = _get_service_class()()

        with patch.object(service, "_send_interactive_text_fallback", new_callable=AsyncMock) as mock_fallback, \
             patch.object(service, "_send_native_interactive", new_callable=AsyncMock) as mock_native:
            mock_fallback.return_value = SendResult(success=True, provider="twilio")

            await service.send_interactive_buttons(
                to="+5511999999999",
                body_text="Deseja participar?",
                buttons=[{"title": "Sim"}, {"title": "Não"}],
                template_name="triagem",
            )

        mock_native.assert_not_called()
        mock_fallback.assert_called_once()

    @pytest.mark.asyncio
    async def test_routes_to_native_when_template_sid_configured(self):
        from app.domains.communication.services.whatsapp_provider import SendResult
        env = {**BASE_ENV, "TWILIO_TEMPLATE_TRIAGEM_SID": "HX_triagem_001"}
        with patch.dict("os.environ", env, clear=True):
            service = _get_service_class()()

        with patch.object(service, "_send_native_interactive", new_callable=AsyncMock) as mock_native, \
             patch.object(service, "_send_interactive_text_fallback", new_callable=AsyncMock) as mock_fallback:
            mock_native.return_value = SendResult(
                success=True,
                provider="twilio",
                metadata={"mode": "native_interactive", "template_sid": "HX_triagem_001"},
            )

            with patch.dict("os.environ", env, clear=True):
                await service.send_interactive_buttons(
                    to="+5511999999999",
                    body_text="Deseja participar?",
                    buttons=[{"title": "Sim"}, {"title": "Não"}],
                    template_name="triagem",
                    template_variables={"1": "João"},
                )

        mock_native.assert_called_once()
        mock_fallback.assert_not_called()
        call_kwargs = mock_native.call_args.kwargs
        assert call_kwargs.get("template_sid") == "HX_triagem_001"

    @pytest.mark.asyncio
    async def test_auto_fallback_to_text_when_native_send_fails(self):
        """
        When native Twilio template send fails (e.g. template pending approval),
        send_interactive_buttons() must automatically retry via numbered-text fallback.
        """
        from app.domains.communication.services.whatsapp_provider import SendResult
        env = {**BASE_ENV, "TWILIO_TEMPLATE_TRIAGEM_SID": "HX_pending_001"}
        with patch.dict("os.environ", env, clear=True):
            service = _get_service_class()()

        failed_native = SendResult(
            success=False, error="Template pending approval", error_code="63016", provider="twilio"
        )
        successful_fallback = SendResult(success=True, provider="twilio", metadata={"mode": "text_fallback"})

        with patch.object(service, "_send_native_interactive", new_callable=AsyncMock) as mock_native, \
             patch.object(service, "_send_interactive_text_fallback", new_callable=AsyncMock) as mock_fallback:
            mock_native.return_value = failed_native
            mock_fallback.return_value = successful_fallback

            with patch.dict("os.environ", env, clear=True):
                result = await service.send_interactive_buttons(
                    to="+5511999999999",
                    body_text="Deseja participar?",
                    buttons=[{"title": "Sim"}, {"title": "Não"}],
                    template_name="triagem",
                )

        mock_native.assert_called_once()
        mock_fallback.assert_called_once()
        assert result.success is True
        assert result.metadata.get("mode") == "text_fallback"

    @pytest.mark.asyncio
    async def test_routes_to_text_fallback_when_no_template_name(self):
        from app.domains.communication.services.whatsapp_provider import SendResult
        with patch.dict("os.environ", BASE_ENV, clear=True):
            service = _get_service_class()()

        with patch.object(service, "_send_interactive_text_fallback", new_callable=AsyncMock) as mock_fallback, \
             patch.object(service, "_send_native_interactive", new_callable=AsyncMock) as mock_native:
            mock_fallback.return_value = SendResult(success=True, provider="twilio")

            await service.send_interactive_buttons(
                to="+5511999999999",
                body_text="Texto qualquer",
                buttons=[{"title": "Opção 1"}, {"title": "Opção 2"}],
            )

        mock_native.assert_not_called()
        mock_fallback.assert_called_once()


# ---------------------------------------------------------------------------
# Seção 3 — _send_native_interactive(): payload Twilio Content API correto
# ---------------------------------------------------------------------------

class TestSendNativeInteractive:

    @pytest.mark.asyncio
    async def test_send_native_uses_content_sid(self):
        with patch.dict("os.environ", BASE_ENV, clear=True):
            service = _get_service_class()()

        mock_message = _make_mock_twilio_message("SM_native_001", "queued")
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message

        with patch.object(type(service), "client", new_callable=PropertyMock, return_value=mock_client):
            result = await service._send_native_interactive(
                formatted_to="whatsapp:+5511999999999",
                template_sid="HX_triagem_001",
                template_variables={"1": "João", "2": "RecrutadorX"},
            )

        assert result.success is True
        assert result.message_id == "SM_native_001"
        assert result.metadata.get("mode") == "native_interactive"
        assert result.metadata.get("template_sid") == "HX_triagem_001"

        create_kwargs = mock_client.messages.create.call_args.kwargs
        assert create_kwargs["content_sid"] == "HX_triagem_001"
        assert "content_variables" in create_kwargs
        cv = json.loads(create_kwargs["content_variables"])
        assert cv["1"] == "João"

    @pytest.mark.asyncio
    async def test_send_native_returns_failure_on_twilio_error(self):
        from twilio.base.exceptions import TwilioRestException
        with patch.dict("os.environ", BASE_ENV, clear=True):
            service = _get_service_class()()

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = TwilioRestException(
            status=400,
            uri="/Messages",
            msg="Template pending approval",
            code=63016,
        )

        with patch.object(type(service), "client", new_callable=PropertyMock, return_value=mock_client):
            result = await service._send_native_interactive(
                formatted_to="whatsapp:+5511999999999",
                template_sid="HX_pending",
                template_variables={},
            )

        assert result.success is False
        assert result.error is not None


# ---------------------------------------------------------------------------
# Seção 4 — _send_interactive_text_fallback(): formato numerado correto
# ---------------------------------------------------------------------------

class TestSendInteractiveTextFallback:

    @pytest.mark.asyncio
    async def test_fallback_formats_numbered_buttons(self):
        with patch.dict("os.environ", BASE_ENV, clear=True):
            service = _get_service_class()()

        mock_message = _make_mock_twilio_message("SM_fallback_001", "sent")
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message

        with patch.object(type(service), "client", new_callable=PropertyMock, return_value=mock_client):
            result = await service._send_interactive_text_fallback(
                formatted_to="whatsapp:+5511999999999",
                body_text="Deseja participar?",
                buttons=[
                    {"title": "Sim, quero participar"},
                    {"title": "Não tenho interesse"},
                ],
                footer_text="Responda com o número",
            )

        assert result.success is True
        assert result.metadata.get("mode") == "text_fallback"

        create_kwargs = mock_client.messages.create.call_args.kwargs
        body_sent = create_kwargs["body"]
        assert "1. Sim, quero participar" in body_sent
        assert "2. Não tenho interesse" in body_sent
        assert "_Responda com o número_" in body_sent

    @pytest.mark.asyncio
    async def test_fallback_includes_header_in_bold(self):
        with patch.dict("os.environ", BASE_ENV, clear=True):
            service = _get_service_class()()

        mock_message = _make_mock_twilio_message("SM_001", "sent")
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message

        with patch.object(type(service), "client", new_callable=PropertyMock, return_value=mock_client):
            await service._send_interactive_text_fallback(
                formatted_to="whatsapp:+5511999999999",
                body_text="Corpo da mensagem",
                buttons=[{"title": "Opção 1"}],
                header_text="Título Principal",
            )

        create_kwargs = mock_client.messages.create.call_args.kwargs
        body_sent = create_kwargs["body"]
        assert "*Título Principal*" in body_sent


# ---------------------------------------------------------------------------
# Seção 5 — Métodos de conveniência: screening, entrevista, feedback
# ---------------------------------------------------------------------------

class TestConvenienceMethods:

    @pytest.mark.asyncio
    async def test_send_screening_invitation_without_template(self):
        from app.domains.communication.services.whatsapp_provider import SendResult
        with patch.dict("os.environ", BASE_ENV, clear=True):
            service = _get_service_class()()

        with patch.object(service, "send_interactive_buttons", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = SendResult(success=True, provider="twilio")

            result = await service.send_screening_invitation(
                to="+5511999999999",
                candidate_name="João Silva",
                job_title="Dev Python",
                company_name="TechCorp",
                recruiter_name="Maria Santos",
            )

        assert result.success is True
        call_kwargs = mock_send.call_args.kwargs
        assert call_kwargs.get("template_name") == "triagem"
        buttons = call_kwargs.get("buttons", [])
        assert any("participar" in b["title"].lower() for b in buttons)
        assert any("não" in b["title"].lower() or "interesse" in b["title"].lower() for b in buttons)
        body = call_kwargs.get("body_text", "")
        assert "João Silva" in body
        assert "Dev Python" in body

    @pytest.mark.asyncio
    async def test_send_screening_invitation_uses_native_when_template_sid_configured(self):
        from app.domains.communication.services.whatsapp_provider import SendResult
        env = {**BASE_ENV, "TWILIO_TEMPLATE_TRIAGEM_SID": "HX_triagem_001"}

        with patch.dict("os.environ", env, clear=True):
            service = _get_service_class()()

        with patch.object(service, "_send_native_interactive", new_callable=AsyncMock) as mock_native:
            mock_native.return_value = SendResult(
                success=True,
                provider="twilio",
                metadata={"mode": "native_interactive"},
            )

            with patch.dict("os.environ", env, clear=True):
                result = await service.send_screening_invitation(
                    to="+5511999999999",
                    candidate_name="Ana Costa",
                    job_title="Product Manager",
                    company_name="StartupX",
                )

        assert result.success is True
        mock_native.assert_called_once()
        call_kwargs = mock_native.call_args.kwargs
        assert call_kwargs.get("template_sid") == "HX_triagem_001"
        tv = call_kwargs.get("template_variables", {})
        assert "Ana Costa" in tv.values()
        assert "Product Manager" in tv.values()

    @pytest.mark.asyncio
    async def test_send_interview_confirmation_request_buttons(self):
        from app.domains.communication.services.whatsapp_provider import SendResult
        with patch.dict("os.environ", BASE_ENV, clear=True):
            service = _get_service_class()()

        with patch.object(service, "send_interactive_buttons", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = SendResult(success=True, provider="twilio")

            await service.send_interview_confirmation_request(
                to="+5511999999999",
                candidate_name="Pedro Alves",
                job_title="Analista de Dados",
                interview_date="15/05/2026",
                interview_time="14:00",
                interview_location="Google Meet",
            )

        call_kwargs = mock_send.call_args.kwargs
        assert call_kwargs.get("template_name") == "entrevista"
        buttons = call_kwargs.get("buttons", [])
        titles = [b["title"].lower() for b in buttons]
        assert any("confirmar" in t for t in titles)
        assert any("reagendar" in t for t in titles)
        assert any("cancelar" in t for t in titles)

    @pytest.mark.asyncio
    async def test_send_feedback_result_approved(self):
        from app.domains.communication.services.whatsapp_provider import SendResult
        with patch.dict("os.environ", BASE_ENV, clear=True):
            service = _get_service_class()()

        with patch.object(service, "send_interactive_buttons", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = SendResult(success=True, provider="twilio")

            await service.send_feedback_result(
                to="+5511999999999",
                candidate_name="Carlos Lima",
                job_title="Scrum Master",
                result="Aprovado",
                feedback_message="Excelente comunicação e experiência relevante.",
            )

        call_kwargs = mock_send.call_args.kwargs
        assert call_kwargs.get("template_name") == "feedback"
        body = call_kwargs.get("body_text", "")
        assert "Carlos Lima" in body
        assert "Scrum Master" in body
        assert "Aprovado" in body
        buttons = call_kwargs.get("buttons", [])
        assert len(buttons) >= 1

    @pytest.mark.asyncio
    async def test_send_feedback_result_rejected(self):
        from app.domains.communication.services.whatsapp_provider import SendResult
        with patch.dict("os.environ", BASE_ENV, clear=True):
            service = _get_service_class()()

        with patch.object(service, "send_interactive_buttons", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = SendResult(success=True, provider="twilio")

            await service.send_feedback_result(
                to="+5511999999999",
                candidate_name="Maria Oliveira",
                job_title="DevOps Engineer",
                result="Não aprovado",
            )

        call_kwargs = mock_send.call_args.kwargs
        body = call_kwargs.get("body_text", "")
        assert "Maria Oliveira" in body
        assert "Não aprovado" in body


# ---------------------------------------------------------------------------
# Seção 6 — Development mode: nunca chama API Twilio real
# ---------------------------------------------------------------------------

class TestDevelopmentMode:

    @pytest.mark.asyncio
    async def test_send_interactive_buttons_dev_mode_does_not_call_api(self):
        dev_env = {
            **BASE_ENV,
            "ENVIRONMENT": "development",
            "TWILIO_TEMPLATE_TRIAGEM_SID": "HX_triagem_001",
        }
        with patch.dict("os.environ", dev_env, clear=True):
            service = _get_service_class()()

        assert service.is_development is True

        mock_client = MagicMock()
        with patch.object(type(service), "client", new_callable=PropertyMock, return_value=mock_client), \
             patch.dict("os.environ", dev_env, clear=True):
            result = await service.send_interactive_buttons(
                to="+5511999999999",
                body_text="Test",
                buttons=[{"title": "Sim"}, {"title": "Não"}],
                template_name="triagem",
            )

        mock_client.messages.create.assert_not_called()
        assert result.success is True
        assert result.metadata.get("mode") == "development"
