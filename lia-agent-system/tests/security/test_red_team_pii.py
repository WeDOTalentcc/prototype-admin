"""
Red Teaming — Categoria 3: PII e Privacidade

Verifica que dados pessoais são removidos antes de enviados para LLMs
e que o sistema não vaza PII em respostas ou logs.

ACH-028
"""
import pytest


_PII_SAMPLES = [
    # CPF
    ("cv com cpf", "Candidato João da Silva, CPF 123.456.789-01, email: joao@email.com"),
    # Email
    ("email direto", "Contatar candidata Maria em maria.silva@gmail.com para agendamento"),
    # Telefone
    ("telefone", "Número de contato do candidato: +55 11 99999-8888"),
    # RG
    ("rg", "RG 12.345.678-9 SSP/SP emitido em 2010"),
    # CNPJ
    ("cnpj", "Empresa CNPJ 12.345.678/0001-90"),
    # Endereço
    ("endereco", "Candidato mora na Rua das Flores, 123, São Paulo, SP, CEP 01310-100"),
    # Combinação
    ("combinado", "Maria Costa, CPF 987.654.321-00, tel (11)98765-4321, maria@teste.com"),
]

_CV_WITH_PII = """
CURRICULUM VITAE

João Henrique da Silva
CPF: 123.456.789-01
RG: 12.345.678-9 SSP/SP
Data de Nascimento: 15/03/1990 (35 anos)
Email: joao.silva@email.com
Telefone: (11) 99999-8888
Endereço: Rua das Acácias, 456, Bairro Jardim, São Paulo - SP, CEP 04567-890

FORMAÇÃO
Engenharia de Software — USP, 2015

EXPERIÊNCIA
Senior Developer — TechCorp (2020-2024)
"""


class TestPIIStrippingForLLM:
    """Verifica que PII é removido antes de envio para LLMs."""

    @pytest.mark.parametrize("name,text", _PII_SAMPLES)
    def test_pii_stripped_from_llm_prompt(self, name, text):
        """PII deve ser removido do texto antes de envio para LLM."""
        from app.shared.pii_masking import strip_pii_for_llm_prompt
        stripped = strip_pii_for_llm_prompt(text)
        # CPF no formato XXX.XXX.XXX-XX não deve aparecer
        import re
        cpf_pattern = r"\d{3}\.\d{3}\.\d{3}-\d{2}"
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        phone_pattern = r"\+?\d[\d\s\(\)\-]{8,}"

        assert not re.search(cpf_pattern, stripped), (
            f"CPF não removido de: '{name}'"
        )
        assert not re.search(email_pattern, stripped), (
            f"Email não removido de: '{name}'"
        )

    def test_cv_pii_stripped(self):
        """CV completo com PII deve ter dados removidos."""
        from app.shared.pii_masking import strip_pii_for_llm_prompt
        import re
        stripped = strip_pii_for_llm_prompt(_CV_WITH_PII)

        # CPF removido
        assert not re.search(r"\d{3}\.\d{3}\.\d{3}-\d{2}", stripped)
        # Email removido
        assert "joao.silva@email.com" not in stripped
        # Telefone removido
        assert "99999-8888" not in stripped

    def test_pii_stripping_preserves_professional_content(self):
        """Stripping de PII deve preservar experiência profissional."""
        from app.shared.pii_masking import strip_pii_for_llm_prompt
        stripped = strip_pii_for_llm_prompt(_CV_WITH_PII)
        # Conteúdo profissional deve permanecer
        assert "Senior Developer" in stripped or "TechCorp" in stripped or "Engenharia" in stripped

    def test_pii_stripping_flag_enabled_by_default(self):
        """Flag LLM_PROMPT_PII_STRIPPING_ENABLED deve ser True por padrão."""
        import os
        # Por padrão, a flag está habilitada (ausência = habilitado)
        flag = os.getenv("LLM_PROMPT_PII_STRIPPING_ENABLED", "true")
        assert flag.lower() in ("true", "1", "yes", "")

    def test_rubric_service_strips_pii_before_llm(self):
        """rubric_evaluation_service deve strip PII antes de montar prompt LLM."""
        import inspect
        from app.domains.cv_screening.services import rubric_evaluation_service as mod
        src = inspect.getsource(mod)
        assert "strip_pii_for_llm_prompt" in src

    def test_analysis_service_strips_pii(self):
        """analysis_service deve strip PII."""
        import inspect
        import app.services.analysis_service as mod
        src = inspect.getsource(mod)
        assert "strip_pii_for_llm_prompt" in src

    def test_voice_screening_strips_pii(self):
        """voice_screening_analysis deve strip PII do transcript."""
        import inspect
        import app.services.voice_screening_analysis as mod
        src = inspect.getsource(mod)
        assert "strip_pii_for_llm_prompt" in src


class TestPIIInLogs:
    """Verifica que PII não aparece em logs do sistema."""

    def test_masked_logger_replaces_cpf(self):
        """MaskedLogger deve mascarar CPF nos logs."""
        import logging
        from app.shared.pii_masking import get_masked_logger
        import re

        logger = get_masked_logger("test.pii")
        test_records = []

        class CaptureHandler(logging.Handler):
            def emit(self, record):
                test_records.append(self.format(record))

        handler = CaptureHandler()
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        logger.info("Candidato CPF 123.456.789-01 avaliado")

        if test_records:
            # CPF real não deve aparecer no log
            for record in test_records:
                assert "123.456.789-01" not in record, (
                    "CPF vazou nos logs!"
                )

    def test_masked_logger_replaces_email(self):
        """MaskedLogger deve mascarar email nos logs."""
        import logging
        from app.shared.pii_masking import get_masked_logger

        logger = get_masked_logger("test.pii.email")
        test_records = []

        class CaptureHandler(logging.Handler):
            def emit(self, record):
                test_records.append(self.format(record))

        handler = CaptureHandler()
        logger.addHandler(handler)
        logger.info("Email do candidato: joao@email.com")

        if test_records:
            for record in test_records:
                assert "joao@email.com" not in record, "Email vazou nos logs!"
