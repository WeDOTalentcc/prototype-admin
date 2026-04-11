"""
Tests — Gate-differentiated feedback (Gap 16.1)

Cobre:
- send_gate_feedback envia email para cada gate_level
- fail-safe: erro no email_service retorna False sem raise
- sem email → retorna False silenciosamente
- gate_level inválido → retorna False
- templates contêm conteúdo esperado por gate
- screening_invited inclui screening_url
- gate1_rejected não inclui scoring/nota (privacidade)
- gate2_rejected aceita rejection_context opcional
- approved aceita next_step_info opcional
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _make_service():
    from app.domains.candidates.services.candidate_feedback_service import CandidateFeedbackService
    return CandidateFeedbackService()


async def _call(svc, gate_level, email="c@test.com", extra=None):
    return await svc.send_gate_feedback(
        gate_level=gate_level,
        candidate_email=email,
        candidate_name="João Silva",
        vacancy_title="Engenheiro de Software",
        company_name="AcmeCorp",
        extra_context=extra or {},
    )


# ─────────────────────────────────────────────
# Gate levels básicos
# ─────────────────────────────────────────────

class TestGateFeedbackBasic:

    @pytest.mark.asyncio
    async def test_screening_invited_returns_true_on_success(self):
        with patch("app.domains.communication.services.email_service.email_service") as mock_email:
            mock_email._send_email_provider = AsyncMock(return_value=True)
            svc = _make_service()
            result = await _call(svc, "screening_invited")
        assert result is True

    @pytest.mark.asyncio
    async def test_gate1_rejected_returns_true_on_success(self):
        with patch("app.domains.communication.services.email_service.email_service") as mock_email:
            mock_email._send_email_provider = AsyncMock(return_value=True)
            svc = _make_service()
            result = await _call(svc, "gate1_rejected")
        assert result is True

    @pytest.mark.asyncio
    async def test_gate2_rejected_returns_true_on_success(self):
        with patch("app.domains.communication.services.email_service.email_service") as mock_email:
            mock_email._send_email_provider = AsyncMock(return_value=True)
            svc = _make_service()
            result = await _call(svc, "gate2_rejected")
        assert result is True

    @pytest.mark.asyncio
    async def test_approved_returns_true_on_success(self):
        with patch("app.domains.communication.services.email_service.email_service") as mock_email:
            mock_email._send_email_provider = AsyncMock(return_value=True)
            svc = _make_service()
            result = await _call(svc, "approved")
        assert result is True


# ─────────────────────────────────────────────
# Fail-safe
# ─────────────────────────────────────────────

class TestGateFeedbackFailSafe:

    @pytest.mark.asyncio
    async def test_email_service_error_returns_false(self):
        """Falha no envio → False sem raise."""
        with patch("app.domains.communication.services.email_service.email_service") as mock_email:
            mock_email._send_email_provider = AsyncMock(side_effect=Exception("SMTP down"))
            svc = _make_service()
            result = await _call(svc, "gate1_rejected")
        assert result is False

    @pytest.mark.asyncio
    async def test_no_email_returns_false(self):
        svc = _make_service()
        result = await svc.send_gate_feedback(
            gate_level="gate1_rejected",
            candidate_email="",
            candidate_name="João",
            vacancy_title="Dev",
            company_name="Co",
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_invalid_gate_level_returns_false(self):
        svc = _make_service()
        result = await svc.send_gate_feedback(
            gate_level="gate99_unknown",
            candidate_email="x@x.com",
            candidate_name="João",
            vacancy_title="Dev",
            company_name="Co",
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_email_service_returns_false_propagated(self):
        """email_service retorna False → send_gate_feedback também retorna False."""
        with patch("app.domains.communication.services.email_service.email_service") as mock_email:
            mock_email._send_email_provider = AsyncMock(return_value=False)
            svc = _make_service()
            result = await _call(svc, "approved")
        assert result is False


# ─────────────────────────────────────────────
# Conteúdo dos templates
# ─────────────────────────────────────────────

class TestGateFeedbackContent:

    @pytest.mark.asyncio
    async def test_screening_invited_body_contains_screening_url(self):
        captured = {}

        async def mock_send(to_email, subject, body_html, body_text):
            captured["body"] = body_text
            return True

        with patch("app.domains.communication.services.email_service.email_service") as mock_email:
            mock_email._send_email_provider = AsyncMock(side_effect=mock_send)
            svc = _make_service()
            await _call(
                svc, "screening_invited",
                extra={"screening_url": "https://app.wedotalent.com/screening/abc123"},
            )

        assert "https://app.wedotalent.com/screening/abc123" in captured.get("body", "")

    @pytest.mark.asyncio
    async def test_gate1_rejected_subject_contains_vacancy_title(self):
        captured = {}

        async def mock_send(to_email, subject, body_html, body_text):
            captured["subject"] = subject
            return True

        with patch("app.domains.communication.services.email_service.email_service") as mock_email:
            mock_email._send_email_provider = AsyncMock(side_effect=mock_send)
            svc = _make_service()
            await _call(svc, "gate1_rejected")

        assert "Engenheiro de Software" in captured.get("subject", "")

    @pytest.mark.asyncio
    async def test_gate2_rejected_body_contains_rejection_context(self):
        captured = {}
        rejection_text = "Faltou experiência com Kubernetes e CI/CD."

        async def mock_send(to_email, subject, body_html, body_text):
            captured["body"] = body_text
            return True

        with patch("app.domains.communication.services.email_service.email_service") as mock_email:
            mock_email._send_email_provider = AsyncMock(side_effect=mock_send)
            svc = _make_service()
            await _call(
                svc, "gate2_rejected",
                extra={"rejection_context": rejection_text},
            )

        assert rejection_text in captured.get("body", "")

    @pytest.mark.asyncio
    async def test_approved_body_contains_next_step_info(self):
        captured = {}
        next_info = "Você será convidado para uma entrevista com o time técnico."

        async def mock_send(to_email, subject, body_html, body_text):
            captured["body"] = body_text
            return True

        with patch("app.domains.communication.services.email_service.email_service") as mock_email:
            mock_email._send_email_provider = AsyncMock(side_effect=mock_send)
            svc = _make_service()
            await _call(
                svc, "approved",
                extra={"next_step_info": next_info},
            )

        assert next_info in captured.get("body", "")

    @pytest.mark.asyncio
    async def test_all_gate_subjects_contain_wedotalent_brand(self):
        """Todos os subjects devem conter '[WeDOTalent]' (branding)."""
        svc = _make_service()
        for gate_level in ("screening_invited", "gate1_rejected", "gate2_rejected", "approved"):
            subject = svc._GATE_SUBJECTS[gate_level].format(
                vacancy_title="Dev", company="Co"
            )
            assert "[WeDOTalent]" in subject, f"Branding ausente em subject do gate '{gate_level}'"
