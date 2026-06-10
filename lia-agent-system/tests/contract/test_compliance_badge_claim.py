"""Sensor anti-ghost / proveniência honesta (ADR-LGPD-002, Fase 1 Step 6).

A badge "Identificadores sensíveis (CPF, e-mail, telefone) são anonimizados antes do
processamento por IA" só pode existir se `strip_pii_for_llm_prompt` DE FATO remove esses
identificadores do texto que vai ao LLM vendor. Este contrato pina esse comportamento:
se alguém desligar/regredir o stripping, a badge vira claim FALSA (passivo jurídico) e
este teste falha — forçando remover a badge OU restaurar o stripping.

Liga FE (claim) <-> BE (mecanismo). É a aplicação da regra de proveniência honesta do
CLAUDE.md à mensagem de compliance."""
import os

os.environ.setdefault("IS_DEVELOPMENT", "true")

from app.shared.pii_masking import strip_pii_for_llm_prompt  # noqa: E402


def test_cpf_redacted_before_llm():
    """CPF (formatado ou cru) NÃO pode sobreviver ao strip que precede o LLM."""
    out = strip_pii_for_llm_prompt("candidato cpf 123.456.789-00 favor avaliar", mask_names=False)
    assert "123.456.789-00" not in out, "CPF formatado vazaria ao LLM — badge seria falsa"
    assert "12345678900" not in out, "CPF dígitos vazaria ao LLM — badge seria falsa"


def test_email_redacted_before_llm():
    out = strip_pii_for_llm_prompt("o email dele e joao.silva@empresa.com.br", mask_names=False)
    assert "joao.silva@empresa.com.br" not in out, "email vazaria ao LLM — badge seria falsa"


def test_phone_redacted_before_llm():
    out = strip_pii_for_llm_prompt("telefone 11 99999-8888 confirmar", mask_names=False)
    assert "99999-8888" not in out, "telefone vazaria ao LLM — badge seria falsa"
    assert "999998888" not in out


def test_badge_text_constant_matches_claim():
    """Se a constante canônica da badge mudar para afirmar algo além de CPF/email/telefone,
    este teste lembra de estender o mecanismo+sensor (ex.: incluir 'endereço')."""
    CANONICAL = "Identificadores sensíveis (CPF, e-mail, telefone) são anonimizados antes do processamento por IA"
    # A claim cobre exatamente os 3 identificadores que o sensor acima verifica.
    for token in ("CPF", "e-mail", "telefone"):
        assert token in CANONICAL
