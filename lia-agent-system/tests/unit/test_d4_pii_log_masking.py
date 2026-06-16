"""
D4 — PII Masking em Logs de Aplicação

Verifica que:
1. PIIMaskingFilter mascara CPF, email, telefone em record.msg
2. PIIMaskingFilter mascara args (tuple e dict)
3. PIIMaskingFilter mascara PII em exc_info (exception messages)
4. install_global_pii_masking() adiciona filtro nos handlers do root logger
5. Child loggers propagando para root handler têm PII mascarado
6. configure_logging() adiciona filtro no handler criado
7. Mensagem sem PII passa intacta
8. Log de stack trace com email é mascarado
"""
import logging
import pytest
from unittest.mock import MagicMock, patch

from app.shared.pii_masking import (
    PIIMaskingFilter,
    mask_pii,
    install_global_pii_masking,
    get_masked_logger,
)


class TestPIIMaskingFilter:
    """Testes unitários do filtro."""

    def _make_record(self, msg, args=None, exc_info=None):
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg=msg, args=args or (), exc_info=exc_info,
        )
        return record

    def test_masks_cpf_in_msg(self):
        f = PIIMaskingFilter()
        record = self._make_record("Candidato CPF 123.456.789-00 aprovado")
        f.filter(record)
        assert "123.456.789-00" not in record.msg
        assert "***CPF***" in record.msg

    def test_masks_email_in_msg(self):
        f = PIIMaskingFilter()
        record = self._make_record("Enviando email para joao@empresa.com")
        f.filter(record)
        assert "joao@empresa.com" not in record.msg
        assert "***EMAIL***" in record.msg

    def test_masks_phone_in_msg(self):
        f = PIIMaskingFilter()
        record = self._make_record("Telefone 11 98765-4321 registrado")
        f.filter(record)
        assert "98765-4321" not in record.msg

    def test_masks_args_tuple(self):
        f = PIIMaskingFilter()
        record = self._make_record("user %s logged in", args=("joao@example.com",))
        f.filter(record)
        assert "joao@example.com" not in str(record.args)

    def test_masks_args_dict(self):
        f = PIIMaskingFilter()
        record = self._make_record("event", args={"email": "maria@test.com", "action": "login"})
        f.filter(record)
        assert "maria@test.com" not in str(record.args)
        assert record.args["action"] == "login"  # não-PII preservado

    def test_masks_exc_info_message(self):
        f = PIIMaskingFilter()
        try:
            raise ValueError("Falha ao processar email joao@empresa.com")
        except ValueError as e:
            exc_info = (type(e), e, e.__traceback__)
        record = self._make_record("Erro", exc_info=exc_info)
        f.filter(record)
        assert "joao@empresa.com" not in str(record.exc_info[1])

    def test_clean_message_passes_intact(self):
        f = PIIMaskingFilter()
        record = self._make_record("Processo iniciado com sucesso")
        f.filter(record)
        assert record.msg == "Processo iniciado com sucesso"

    def test_filter_always_returns_true(self):
        """Filtro nunca bloqueia o log — apenas mascara."""
        f = PIIMaskingFilter()
        record = self._make_record("qualquer mensagem")
        assert f.filter(record) is True


class TestInstallGlobalPIIMasking:
    """install_global_pii_masking() deve cobrir logger E handlers."""

    def test_adds_filter_to_root_logger(self):
        root = logging.getLogger()
        # Limpar filtros PII existentes para testar isoladamente
        root.filters = [f for f in root.filters if not isinstance(f, PIIMaskingFilter)]
        install_global_pii_masking()
        assert any(isinstance(f, PIIMaskingFilter) for f in root.filters)

    def test_adds_filter_to_root_handlers(self):
        root = logging.getLogger()
        # Garantir que há um handler
        handler = logging.StreamHandler()
        root.addHandler(handler)
        # Limpar filtros PII dos handlers
        for h in root.handlers:
            h.filters = [f for f in h.filters if not isinstance(f, PIIMaskingFilter)]

        install_global_pii_masking()

        assert any(
            any(isinstance(f, PIIMaskingFilter) for f in h.filters)
            for h in root.handlers
        )
        root.removeHandler(handler)

    def test_idempotent_no_duplicate_filters(self):
        """Chamar duas vezes não duplica o filtro."""
        root = logging.getLogger()
        install_global_pii_masking()
        install_global_pii_masking()
        pii_count = sum(1 for f in root.filters if isinstance(f, PIIMaskingFilter))
        assert pii_count <= 1


class TestConfigureLogging:
    """configure_logging() deve instalar PIIMaskingFilter no handler."""

    def test_configure_logging_adds_pii_filter_to_handler(self):
        from app.core.logging_config import configure_logging
        configure_logging()
        root = logging.getLogger()
        has_filter = any(
            any(isinstance(f, PIIMaskingFilter) for f in h.filters)
            for h in root.handlers
        )
        assert has_filter, "configure_logging() deve adicionar PIIMaskingFilter ao handler"
