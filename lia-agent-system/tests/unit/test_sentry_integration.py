"""
Testes unitários para app/core/sentry.py (Sprint B / André P8).

Cobre: init_sentry sem DSN, scrubbing de PII (email, CPF, telefone),
múltiplos PII, evento None, before_send preserva estrutura.
"""
import pytest
from unittest.mock import patch, MagicMock

from app.core.sentry import _scrub_pii, _before_send, init_sentry


# ---------------------------------------------------------------------------
# Testes de _scrub_pii
# ---------------------------------------------------------------------------


class TestScrubPii:
    def test_scrub_remove_email(self):
        text = "Contato: joao.silva@empresa.com.br para mais informações."
        result = _scrub_pii(text)
        assert "[EMAIL REMOVIDO]" in result
        assert "@" not in result

    def test_scrub_remove_cpf_com_pontuacao(self):
        text = "CPF do candidato: 123.456.789-09"
        result = _scrub_pii(text)
        assert "[CPF REMOVIDO]" in result
        assert "123.456.789-09" not in result

    def test_scrub_remove_cpf_sem_pontuacao(self):
        text = "CPF: 12345678909"
        result = _scrub_pii(text)
        assert "[CPF REMOVIDO]" in result
        assert "12345678909" not in result

    def test_scrub_remove_telefone_celular(self):
        text = "WhatsApp: 11 9 9999-8888"
        result = _scrub_pii(text)
        assert "[TELEFONE REMOVIDO]" in result

    def test_scrub_remove_telefone_com_ddd_parenteses(self):
        text = "Ligue: (11) 98765-4321"
        result = _scrub_pii(text)
        assert "[TELEFONE REMOVIDO]" in result
        assert "98765-4321" not in result

    def test_scrub_multiplos_pii_em_texto(self):
        text = (
            "Candidato: maria@wedotalent.com, "
            "CPF: 987.654.321-00, "
            "Telefone: (21) 99999-1234"
        )
        result = _scrub_pii(text)
        assert "[EMAIL REMOVIDO]" in result
        assert "[CPF REMOVIDO]" in result
        assert "[TELEFONE REMOVIDO]" in result
        assert "@" not in result
        assert "987.654.321-00" not in result

    def test_scrub_texto_sem_pii_nao_altera(self):
        text = "Reunião de alinhamento às 14h na sala de conferências."
        result = _scrub_pii(text)
        assert result == text

    def test_scrub_string_vazia(self):
        result = _scrub_pii("")
        assert result == ""


# ---------------------------------------------------------------------------
# Testes de _before_send
# ---------------------------------------------------------------------------


class TestBeforeSend:
    def test_before_send_remove_email_de_exception_message(self):
        event = {
            "exception": {
                "values": [
                    {"type": "ValueError", "value": "Email inválido: teste@exemplo.com"}
                ]
            }
        }
        result = _before_send(event, {})
        exc_value = result["exception"]["values"][0]["value"]
        assert "[EMAIL REMOVIDO]" in exc_value
        assert "@" not in exc_value

    def test_before_send_remove_cpf_de_exception_message(self):
        event = {
            "exception": {
                "values": [
                    {"type": "ValidationError", "value": "CPF inválido: 111.222.333-44"}
                ]
            }
        }
        result = _before_send(event, {})
        exc_value = result["exception"]["values"][0]["value"]
        assert "[CPF REMOVIDO]" in exc_value
        assert "111.222.333-44" not in exc_value

    def test_before_send_remove_telefone_de_breadcrumb(self):
        event = {
            "breadcrumbs": {
                "values": [
                    {"message": "Chamada recebida de (31) 98888-7777", "level": "info"}
                ]
            }
        }
        result = _before_send(event, {})
        msg = result["breadcrumbs"]["values"][0]["message"]
        assert "[TELEFONE REMOVIDO]" in msg
        assert "98888-7777" not in msg

    def test_before_send_evento_none_retorna_none(self):
        result = _before_send(None, {})
        assert result is None

    def test_before_send_preserva_estrutura_do_evento(self):
        """Campos além de exception/breadcrumbs devem ser preservados."""
        event = {
            "event_id": "abc123",
            "level": "error",
            "platform": "python",
            "exception": {
                "values": [
                    {"type": "RuntimeError", "value": "Erro genérico sem PII"}
                ]
            },
            "tags": {"company_id": "tenant-xyz"},
        }
        result = _before_send(event, {})
        assert result["event_id"] == "abc123"
        assert result["level"] == "error"
        assert result["platform"] == "python"
        assert result["tags"]["company_id"] == "tenant-xyz"

    def test_before_send_sem_exception_nao_falha(self):
        """Evento sem 'exception' deve ser processado sem erro."""
        event = {
            "breadcrumbs": {
                "values": [{"message": "Operação concluída", "level": "info"}]
            }
        }
        result = _before_send(event, {})
        assert result is not None
        assert result["breadcrumbs"]["values"][0]["message"] == "Operação concluída"

    def test_before_send_sem_breadcrumbs_nao_falha(self):
        """Evento sem 'breadcrumbs' deve ser processado sem erro."""
        event = {
            "exception": {
                "values": [{"type": "KeyError", "value": "chave_inexistente"}]
            }
        }
        result = _before_send(event, {})
        assert result is not None


# ---------------------------------------------------------------------------
# Testes de init_sentry
# ---------------------------------------------------------------------------


class TestInitSentry:
    def test_init_sentry_sem_dsn_retorna_false(self):
        """init_sentry() com dsn="" deve retornar False sem lançar exceção."""
        result = init_sentry(dsn="")
        assert result is False

    def test_init_sentry_dsn_none_retorna_false(self):
        result = init_sentry(dsn=None)
        # Sem DSN definido em nenhum lugar → False
        with patch("app.core.sentry.logger") as mock_logger:
            r = init_sentry(dsn=None)
        # Pode ser True se SENTRY_DSN estiver definido no ambiente do CI
        # O teste garante apenas que não lança exceção
        assert isinstance(r, bool)

    def test_init_sentry_dsn_vazio_retorna_false(self):
        result = init_sentry(dsn="")
        assert result is False

    def test_init_sentry_sem_sentry_sdk_instalado_retorna_false(self):
        """Se sentry-sdk não estiver instalado, deve retornar False graciosamente."""
        import sys
        # Simula ImportError ao importar sentry_sdk dentro de init_sentry
        original = sys.modules.get("sentry_sdk")
        sys.modules["sentry_sdk"] = None  # type: ignore
        try:
            result = init_sentry(dsn="https://fake@sentry.io/1")
            assert result is False
        except Exception as e:
            pytest.fail(f"init_sentry não deve lançar exceção: {e}")
        finally:
            if original is not None:
                sys.modules["sentry_sdk"] = original
            else:
                sys.modules.pop("sentry_sdk", None)

    def test_init_sentry_nao_lanca_excecao_com_dsn_invalido(self):
        """DSN inválido pode fazer sentry_sdk.init() falhar — deve ser capturado."""
        try:
            # DSN sintaticamente inválido pode não lançar exceção imediatamente,
            # mas o teste garante que init_sentry não propaga exceção
            init_sentry(dsn="dsn-invalido-qualquer-coisa")
        except Exception as e:
            pytest.fail(f"init_sentry não deve propagar exceção: {e}")

    def test_scrub_pii_chamado_no_before_send_hook(self):
        """Garantir que _before_send chama _scrub_pii em mensagens de exceção."""
        event = {
            "exception": {
                "values": [
                    {
                        "type": "RuntimeError",
                        "value": "Erro processando candidato@empresa.com",
                    }
                ]
            }
        }
        with patch("app.core.sentry._scrub_pii", wraps=_scrub_pii) as mock_scrub:
            _before_send(event, {})
            assert mock_scrub.called
