"""
Contract tests: LGPD dispatch hours — P0-W1-04

Garante que:
1. _is_within_sending_hours() usa settings do tenant (sending_hours_start/end, respect_weekends, respect_holidays).
2. _get_next_sending_window() usa settings do tenant, nao hardcoded.
3. validate_can_send warning message mostra janela real do tenant.
4. process_queued_messages fast-path gate usa defaults conservadores corretos.

LGPD Art. 7 / Art. 11: limites configurados pelo responsavel devem ser respeitados.
Banner UI diz "A LIA respeita automaticamente estes horarios" -- contrato precisa ser honrado.

Sensor permanente -- nao deletar.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_service():
    """Instantiate CommunicationService sem providers reais."""
    from app.domains.communication.services.communication_service import CommunicationService
    svc = CommunicationService.__new__(CommunicationService)
    svc.notification_service = MagicMock()
    svc._email_providers = []
    svc._whatsapp_providers = []
    return svc


TENANT_SETTINGS_6_22 = {
    "sending_hours_start": 6,
    "sending_hours_end": 22,
    "respect_weekends": False,
    "respect_holidays": False,
    "timezone": "America/Sao_Paulo",
    "max_messages_per_day": 5,
    "max_messages_per_candidate": 10,
    "cooldown_hours_between_messages": 12,
}

TENANT_SETTINGS_WEEKENDS_BLOCKED = {
    "sending_hours_start": 8,
    "sending_hours_end": 20,
    "respect_weekends": True,
    "respect_holidays": False,
    "timezone": "America/Sao_Paulo",
    "max_messages_per_day": 3,
    "max_messages_per_candidate": 5,
    "cooldown_hours_between_messages": 24,
}


# ---------------------------------------------------------------------------
# 1. _is_within_sending_hours: tenant custom start/end
# ---------------------------------------------------------------------------

class Test_IsWithinSendingHours:
    """_is_within_sending_hours deve usar config do tenant, nao constantes 8/20."""

    def test_tenant_start_10_blocks_9h(self):
        """Tenant com start=10: hora 9 deve ser bloqueada (hardcoded 8 deixaria passar)."""
        svc = _make_service()
        settings = {**TENANT_SETTINGS_6_22, "sending_hours_start": 10, "sending_hours_end": 20}
        fake_now = datetime(2026, 5, 26, 9, 0)  # segunda-feira
        with patch(
            "app.shared.services.communication_settings_consumer.get_tenant_now",
            return_value=fake_now,
        ):
            result = svc._is_within_sending_hours(settings)
        assert result is False, "hora 9 deve ser bloqueada quando tenant start=10"

    def test_tenant_start_10_allows_10h(self):
        """Tenant com start=10: hora 10 deve ser permitida."""
        svc = _make_service()
        settings = {**TENANT_SETTINGS_6_22, "sending_hours_start": 10, "sending_hours_end": 20}
        fake_now = datetime(2026, 5, 26, 10, 0)  # segunda-feira
        with patch(
            "app.shared.services.communication_settings_consumer.get_tenant_now",
            return_value=fake_now,
        ):
            result = svc._is_within_sending_hours(settings)
        assert result is True, "hora 10 deve ser permitida quando tenant start=10"

    def test_tenant_end_22_allows_21h(self):
        """Tenant com end=22: hora 21 deve ser permitida (hardcoded 20 bloquearia)."""
        svc = _make_service()
        settings = {**TENANT_SETTINGS_6_22, "sending_hours_start": 6, "sending_hours_end": 22}
        fake_now = datetime(2026, 5, 26, 21, 30)  # segunda-feira
        with patch(
            "app.shared.services.communication_settings_consumer.get_tenant_now",
            return_value=fake_now,
        ):
            result = svc._is_within_sending_hours(settings)
        assert result is True, "hora 21 deve ser permitida quando tenant end=22"

    def test_tenant_end_22_blocks_22h(self):
        """Tenant com end=22: hora 22 deve ser bloqueada (intervalo eh start <= h < end)."""
        svc = _make_service()
        settings = {**TENANT_SETTINGS_6_22, "sending_hours_start": 6, "sending_hours_end": 22}
        fake_now = datetime(2026, 5, 26, 22, 0)
        with patch(
            "app.shared.services.communication_settings_consumer.get_tenant_now",
            return_value=fake_now,
        ):
            result = svc._is_within_sending_hours(settings)
        assert result is False, "hora 22 deve ser bloqueada quando tenant end=22 (exclusive)"

    def test_respect_weekends_true_blocks_saturday(self):
        """respect_weekends=True deve bloquear sabado."""
        svc = _make_service()
        saturday = datetime(2026, 5, 23, 10, 0)  # sabado
        assert saturday.weekday() == 5, "precisa ser sabado"
        with patch(
            "app.shared.services.communication_settings_consumer.get_tenant_now",
            return_value=saturday,
        ):
            result = svc._is_within_sending_hours(TENANT_SETTINGS_WEEKENDS_BLOCKED)
        assert result is False, "sabado deve ser bloqueado quando respect_weekends=True"

    def test_respect_weekends_false_allows_saturday(self):
        """respect_weekends=False deve permitir sabado (tenant quer enviar no fim de semana)."""
        svc = _make_service()
        saturday = datetime(2026, 5, 23, 10, 0)  # sabado
        settings = {**TENANT_SETTINGS_6_22, "respect_weekends": False}
        with patch(
            "app.shared.services.communication_settings_consumer.get_tenant_now",
            return_value=saturday,
        ):
            result = svc._is_within_sending_hours(settings)
        assert result is True, "sabado deve ser permitido quando respect_weekends=False"

    def test_no_settings_uses_defaults(self):
        """settings=None deve usar defaults 8h-20h (backward-compat)."""
        svc = _make_service()
        fake_now = datetime(2026, 5, 26, 14, 0)  # 14h segunda
        with patch.object(svc, "_get_brazil_now", return_value=fake_now):
            result = svc._is_within_sending_hours(None)
        assert result is True, "14h segunda deve ser permitido com defaults"


# ---------------------------------------------------------------------------
# 2. _get_next_sending_window: deve aceitar settings do tenant
# ---------------------------------------------------------------------------

class Test_GetNextSendingWindow:
    """_get_next_sending_window deve aceitar settings e usar horas do tenant."""

    def test_signature_accepts_settings_kwarg(self):
        """_get_next_sending_window deve aceitar settings= kwarg.
        
        Com settings, o metodo usa get_tenant_now (nao _get_brazil_now).
        Este teste verifica que a assinatura aceita o parametro.
        """
        svc = _make_service()
        fake_now = datetime(2026, 5, 26, 21, 0)  # 21h segunda
        # Com settings, get_tenant_now eh chamado em vez de _get_brazil_now
        with patch(
            "app.shared.services.communication_settings_consumer.get_tenant_now",
            return_value=fake_now,
        ):
            try:
                result = svc._get_next_sending_window(settings=TENANT_SETTINGS_6_22)
            except TypeError as e:
                pytest.fail(
                    f"_get_next_sending_window nao aceita settings=: {e}. "
                    f"Fix: adicionar 'settings: dict | None = None' a assinatura."
                )
        # 21h esta dentro da janela tenant 6-22, entao retorna fake_now
        assert result is not None

    def test_after_hardcoded_end_but_within_tenant_end_returns_now_or_close(self):
        """Se sao 21h e tenant.end=22, proxima janela deve ser agora (nao amanha 8h)."""
        svc = _make_service()
        fake_now = datetime(2026, 5, 26, 21, 0)  # 21h segunda
        # Com settings, get_tenant_now eh chamado
        with patch(
            "app.shared.services.communication_settings_consumer.get_tenant_now",
            return_value=fake_now,
        ):
            window = svc._get_next_sending_window(settings=TENANT_SETTINGS_6_22)
        # 21h esta dentro da janela tenant (6-22), entao a janela retorna fake_now (ou proximo)
        # Com settings, resultado eh hora local (sem offset UTC para desfazer)
        assert window <= fake_now + timedelta(hours=1), (
            f"21h com tenant.end=22 deve retornar janela proxima, nao {window}"
        )

    def test_hardcoded_constants_not_used_when_settings_provided(self):
        """Com settings.start=6 e end=22, a janela calculada nao deve usar 8/20.
        
        22h30: fora da janela tenant (end=22 exclusive) => proxima janela = amanha 6h.
        Sem o fix (hardcoded): retornaria amanha 8h (SENDING_START_HOUR=8).
        Com o fix (tenant-aware): retorna amanha 6h (settings.start=6).
        """
        svc = _make_service()
        fake_now = datetime(2026, 5, 26, 22, 30)  # 22h30 segunda
        # Com settings, get_tenant_now eh chamado
        with patch(
            "app.shared.services.communication_settings_consumer.get_tenant_now",
            return_value=fake_now,
        ):
            window = svc._get_next_sending_window(settings=TENANT_SETTINGS_6_22)
        # Com settings, resultado eh hora local (sem offset UTC)
        assert window.hour == 6, (
            f"Proxima janela deve ser 6h (tenant start=6), nao {window.hour}h. "
            f"(Se fosse 8h, a constante hardcoded SENDING_START_HOUR esta sendo usada)"
        )


# ---------------------------------------------------------------------------
# 3. validate_can_send: warning message deve mostrar janela do tenant
# ---------------------------------------------------------------------------

class Test_ValidateCanSendWarningMessage:
    """validate_can_send deve mostrar a janela real do tenant no warning outside_hours."""

    @pytest.mark.asyncio
    async def test_outside_hours_warning_shows_tenant_hours(self):
        """Warning outside_hours deve mostrar sending_hours_start/end do tenant, nao 8h-20h."""
        from app.domains.communication.services.communication_service import CommunicationService
        from app.enums.communication import MessageChannel, MessageType

        svc = CommunicationService.__new__(CommunicationService)
        svc.notification_service = MagicMock()
        svc._email_providers = []
        svc._whatsapp_providers = []

        company_id = "test-company-uuid"
        tenant_settings = {
            **TENANT_SETTINGS_6_22,
            "sending_hours_start": 10,
            "sending_hours_end": 18,
        }

        with patch(
            "app.shared.services.communication_settings_consumer.get_company_communication_settings",
            AsyncMock(return_value=tenant_settings),
        ), patch(
            "app.shared.services.communication_settings_consumer.check_cooldown_hours",
            AsyncMock(return_value=(True, None)),
        ), patch(
            "app.shared.services.communication_settings_consumer.check_max_per_candidate",
            AsyncMock(return_value=(True, None)),
        ), patch(
            "app.domains.communication.services.consent_gate.CommunicationConsentGate"
        ) as MockGate, patch.object(
            svc, "_check_opt_out", AsyncMock(return_value=(False, None))
        ), patch.object(
            svc, "_check_quarantine", AsyncMock(return_value=(False, None))
        ), patch.object(
            svc, "_check_rate_limit", AsyncMock(return_value=(True, 0))
        ), patch.object(
            svc, "_is_within_sending_hours", return_value=False
        ), patch.object(
            svc, "_is_holiday_now", return_value=False
        ):
            gate_instance = MagicMock()
            gate_instance.check = AsyncMock(return_value=MagicMock(allowed=True))
            MockGate.return_value = gate_instance

            mock_cm = MagicMock()
            mock_cm.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_cm.__aexit__ = AsyncMock(return_value=False)

            with patch(
                "app.domains.communication.services.communication_service._get_db",
                return_value=mock_cm,
            ):
                result = await svc.validate_can_send(
                    candidate_id="cand-uuid",
                    company_id=company_id,
                    channel=MessageChannel.EMAIL,
                    message_type=MessageType.SCREENING_REMINDER,
                    db=MagicMock(),
                )

        outside_hours_warnings = [
            w for w in result.get("warnings", []) if w.get("type") == "outside_hours"
        ]
        assert outside_hours_warnings, "Deve haver warning outside_hours"
        msg = outside_hours_warnings[0]["message"]
        # Deve mostrar a janela do tenant (10h-18h), NAO a hardcoded (8h-20h)
        assert "8h-20h" not in msg, (
            f"Warning message nao deve hardcodar '8h-20h' quando tenant configurou horario diferente. "
            f"Message atual: '{msg}'"
        )


# ---------------------------------------------------------------------------
# 4. process_queued_messages: fast-path gate usa defaults conservadores
# ---------------------------------------------------------------------------

class Test_ProcessQueuedMessagesFastPath:
    """process_queued_messages: o gate global usa defaults corretos."""

    def test_fast_path_gate_method_accepts_default_settings(self):
        """O fast-path gate usa _is_within_sending_hours(None) = defaults canonicos."""
        svc = _make_service()
        # 14h segunda = dentro da janela default
        fake_now = datetime(2026, 5, 26, 14, 0)
        with patch.object(svc, "_get_brazil_now", return_value=fake_now):
            result = svc._is_within_sending_hours(None)
        assert result is True, "Fast-path 14h segunda deve retornar True com defaults"

    def test_fast_path_gate_outside_hours_blocks(self):
        """Fast-path fora da janela default (21h) deve bloquear.
        
        Isso e CONSERVADOR e correto: tenants com janela estendida sao tratados
        no loop per-tenant dentro de process_queued_messages. O fast-path
        usa defaults 8h-20h como gate inicial.
        """
        svc = _make_service()
        fake_now = datetime(2026, 5, 26, 21, 0)  # 21h
        with patch.object(svc, "_get_brazil_now", return_value=fake_now):
            result = svc._is_within_sending_hours(None)
        assert result is False, "Fast-path 21h deve retornar False com defaults"
