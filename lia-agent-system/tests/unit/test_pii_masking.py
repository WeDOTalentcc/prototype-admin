"""
Testes unitários para PII Masking (Sprint H — coverage gate 40%).

Cobertura:
  - mask_pii: CPF, email, telefone, nome em log
  - mask_pii: texto vazio/None
  - PIIMaskingFilter: msg string, args tuple, args dict
  - get_masked_logger: idempotência (não duplica filtros)
  - install_global_pii_masking: idempotência
"""
import logging
import pytest

pytestmark = pytest.mark.easy

from app.shared.pii_masking import (
    mask_pii,
    PIIMaskingFilter,
    get_masked_logger,
    install_global_pii_masking,
)


# ---------------------------------------------------------------------------
# mask_pii
# ---------------------------------------------------------------------------

class TestMaskPii:

    def test_masks_cpf_with_dots(self):
        result = mask_pii("CPF: 123.456.789-00")
        assert "123.456.789-00" not in result
        assert "***CPF***" in result

    def test_masks_cpf_without_dots(self):
        result = mask_pii("CPF 12345678900")
        assert "12345678900" not in result

    def test_masks_email(self):
        result = mask_pii("Email: joao@empresa.com.br")
        assert "joao@empresa.com.br" not in result
        assert "***EMAIL***" in result

    def test_masks_phone_br(self):
        result = mask_pii("Tel: (11) 98765-4321")
        assert "98765-4321" not in result

    def test_masks_name_in_log(self):
        result = mask_pii("candidato='Ana Lima'")
        assert "Ana Lima" not in result

    def test_empty_string_unchanged(self):
        assert mask_pii("") == ""

    def test_none_returns_none(self):
        assert mask_pii(None) is None  # type: ignore

    def test_no_pii_unchanged(self):
        original = "Vaga de desenvolvedor sênior disponível."
        assert mask_pii(original) == original

    def test_multiple_pii_types_masked(self):
        text = "CPF: 123.456.789-00, email: test@co.com"
        result = mask_pii(text)
        assert "123.456.789-00" not in result
        assert "test@co.com" not in result

    def test_email_with_subdomain(self):
        result = mask_pii("user@mail.example.org")
        assert "user@mail.example.org" not in result
        assert "***EMAIL***" in result


# ---------------------------------------------------------------------------
# PIIMaskingFilter
# ---------------------------------------------------------------------------

class TestPIIMaskingFilter:

    def _make_record(self, msg, args=None):
        record = logging.LogRecord(
            name="test", level=logging.INFO,
            pathname="", lineno=0, msg=msg, args=args or (), exc_info=None
        )
        return record

    def test_filter_masks_string_msg(self):
        f = PIIMaskingFilter()
        record = self._make_record("Candidato: cpf=123.456.789-00")
        f.filter(record)
        assert "123.456.789-00" not in record.msg

    def test_filter_masks_tuple_args(self):
        f = PIIMaskingFilter()
        record = self._make_record("Msg %s", args=("test@co.com",))
        f.filter(record)
        assert "test@co.com" not in record.args[0]

    def test_filter_masks_dict_args(self):
        # LogRecord não aceita dict em __init__; define args pós-construção.
        f = PIIMaskingFilter()
        record = self._make_record("Msg %(email)s")
        record.args = {"email": "x@y.com"}
        f.filter(record)
        assert "x@y.com" not in record.args["email"]

    def test_filter_returns_true(self):
        f = PIIMaskingFilter()
        record = self._make_record("OK")
        assert f.filter(record) is True

    def test_filter_non_string_args_unchanged(self):
        f = PIIMaskingFilter()
        record = self._make_record("Count %d", args=(42,))
        f.filter(record)
        assert record.args[0] == 42


# ---------------------------------------------------------------------------
# get_masked_logger
# ---------------------------------------------------------------------------

class TestGetMaskedLogger:

    def test_returns_logger(self):
        logger = get_masked_logger("test.pii.logger")
        assert isinstance(logger, logging.Logger)

    def test_has_pii_filter(self):
        logger = get_masked_logger("test.pii.filter.check")
        has_filter = any(isinstance(f, PIIMaskingFilter) for f in logger.filters)
        assert has_filter

    def test_idempotent_no_duplicate_filters(self):
        name = "test.pii.idempotent"
        get_masked_logger(name)
        get_masked_logger(name)
        logger = logging.getLogger(name)
        pii_filters = [f for f in logger.filters if isinstance(f, PIIMaskingFilter)]
        assert len(pii_filters) == 1


# ---------------------------------------------------------------------------
# install_global_pii_masking
# ---------------------------------------------------------------------------

class TestInstallGlobalPiiMasking:

    def test_installs_filter_on_root_logger(self):
        install_global_pii_masking()
        root = logging.getLogger()
        has_filter = any(isinstance(f, PIIMaskingFilter) for f in root.filters)
        assert has_filter

    def test_idempotent(self):
        install_global_pii_masking()
        install_global_pii_masking()
        root = logging.getLogger()
        pii_filters = [f for f in root.filters if isinstance(f, PIIMaskingFilter)]
        assert len(pii_filters) == 1


def test_mask_pii_outbound_preserva_por_default():
    """Fix PII-contato (2026-06-06): saida do chat do recrutador preserva
    CPF/email/telefone por default (recrutador autorizado ve)."""
    from app.shared.pii_masking import mask_pii_outbound
    txt = "Felipe Almeida, CPF 123.456.789-00, email felipe@x.com, fone (11) 98765-4321"
    assert mask_pii_outbound(txt) == txt


def test_mask_pii_outbound_mascara_quando_opt_in(monkeypatch):
    """Opt-in (config per-user futura / flag) mascara."""
    import app.shared.pii_masking as pii
    monkeypatch.setattr(pii, "_RECRUITER_CHAT_MASK_PII", True)
    out = pii.mask_pii_outbound("CPF 123.456.789-00 e email x@y.com")
    assert "123.456.789-00" not in out
    assert "x@y.com" not in out


def test_mask_pii_outbound_nao_str_passthrough():
    from app.shared.pii_masking import mask_pii_outbound
    assert mask_pii_outbound(None) is None
    assert mask_pii_outbound("") == ""
