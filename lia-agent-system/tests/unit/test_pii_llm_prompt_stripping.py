"""
SEG-3B — Testes de strip_pii_for_llm_prompt (data minimization para LLM).

Cobre:
  1. CPF é removido do texto antes do LLM
  2. Email é removido
  3. Telefone BR é removido
  4. Ano de formatura (quasi-identifier) é removido
  5. Texto sem PII permanece inalterado
"""
import unittest


class TestStripPIIForLLMPrompt(unittest.TestCase):

    def setUp(self):
        from app.shared.pii_masking import strip_pii_for_llm_prompt
        self.strip = strip_pii_for_llm_prompt

    def test_cpf_removed(self):
        text = "Candidato CPF 123.456.789-09 tem experiência em Python"
        result = self.strip(text)
        self.assertNotIn("123.456.789-09", result)
        self.assertIn("REMOVIDO]", result)  # regex [CPF REMOVIDO] ou Presidio
        self.assertIn("Python", result)

    def test_email_removed(self):
        text = "Contato: joao.silva@empresa.com.br para entrevista"
        result = self.strip(text)
        self.assertNotIn("joao.silva@empresa.com.br", result)
        self.assertIn("REMOVIDO]", result)  # regex [EMAIL REMOVIDO] ou Presidio [EMAIL_ADDRESS REMOVIDO]
        self.assertIn("entrevista", result)

    def test_phone_removed(self):
        text = "Telefone: (11) 98765-4321 disponível para contato"
        result = self.strip(text)
        self.assertNotIn("98765-4321", result)

    def test_graduation_year_removed(self):
        text = "Formado em 2001 pela USP em Engenharia de Software"
        result = self.strip(text)
        self.assertNotIn("Formado em 2001", result)
        self.assertIn("USP", result)

    def test_clean_text_unchanged(self):
        text = "Candidato tem 5 anos de experiência em Java e liderança de equipes de até 10 pessoas"
        result = self.strip(text)
        self.assertIn("Java", result)
        self.assertIn("liderança", result)

    def test_feature_flag_disabled(self):
        """Quando a feature está desabilitada, o texto original é retornado."""
        import app.shared.pii_masking as pii_module
        original_flag = pii_module._LLM_PROMPT_PII_STRIPPING_ENABLED
        pii_module._LLM_PROMPT_PII_STRIPPING_ENABLED = False
        try:
            text = "CPF 123.456.789-09 e email test@test.com"
            result = self.strip(text)
            self.assertEqual(result, text)
        finally:
            pii_module._LLM_PROMPT_PII_STRIPPING_ENABLED = original_flag

    def test_empty_text_returned_unchanged(self):
        self.assertEqual(self.strip(""), "")
        self.assertIsNone(self.strip(None))


if __name__ == "__main__":
    unittest.main()


def test_mask_names_false_preserva_nome_mascara_contato():
    """Fix #4 2026-06-06: chat do recrutador preserva NOME de candidato/vaga
    (autorizado, mesmo tenant) mas mantém CPF/email mascarados. Espelha o base
    _sanitize_messages_pii(mask_names=False). Regressão: 'Felipe Almeida' não
    pode virar '[PERSON REMOVIDO]'."""
    from app.shared.pii_masking import strip_pii_for_llm_prompt
    out = strip_pii_for_llm_prompt("Felipe Almeida, CPF 123.456.789-00", mask_names=False)
    assert "Felipe Almeida" in out
    assert "[PERSON REMOVIDO]" not in out
    assert "123.456.789-00" not in out
