"""
Sensor — camada de fairness/LGPD sobre o feedback gerado por IA ANTES do envio
(auditoria 2026-06-10). Reusa o guard canonico (fairness_guard_middleware).
Camada 2 (Unitario BE — pytest, sem DB).
"""
from app.domains.communication.services.transition_dispatch_service import (
    is_feedback_fairness_blocked,
)


class TestFeedbackFairnessGuard:
    def test_blocks_discriminatory_feedback(self):
        txt = "Olá, decidimos não seguir nesta etapa; prefiro homens para esta posição."
        assert is_feedback_fairness_blocked(txt, "co-1") is True

    def test_allows_clean_feedback(self):
        txt = (
            "Olá Maria, obrigado por participar do nosso processo. Seguimos com outro "
            "perfil mais aderente ao momento da vaga. Desejamos muito sucesso!"
        )
        assert is_feedback_fairness_blocked(txt, "co-1") is False

    def test_empty_not_blocked(self):
        assert is_feedback_fairness_blocked("", "co-1") is False
        assert is_feedback_fairness_blocked(None, "co-1") is False


class TestAiPersonalizationChannel:
    """W1 (decisao Paulo 2026-06-10): texto livre da IA so por email; WhatsApp
    exige template aprovado pela Meta (mensagem business-initiated)."""

    def test_email_allows_ai(self):
        from app.domains.communication.services.transition_dispatch_service import (
            ai_personalization_allowed_for_channel,
        )
        assert ai_personalization_allowed_for_channel("email") is True

    def test_whatsapp_blocks_ai(self):
        from app.domains.communication.services.transition_dispatch_service import (
            ai_personalization_allowed_for_channel,
        )
        assert ai_personalization_allowed_for_channel("whatsapp") is False
        assert ai_personalization_allowed_for_channel("WhatsApp") is False
        assert ai_personalization_allowed_for_channel("") is False
