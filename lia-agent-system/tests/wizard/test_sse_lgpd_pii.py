"""TDD — gap LGPD: SSE deve mascarar PII inbound (harmonizar com WS).

Pina a invariante canônica de que strip_pii_for_llm_prompt (usado agora no
inbound do SSE) mascara email/CPF/telefone antes de qualquer LLM. O caminho
do wizard (content mascarado + raw em _raw_user_message para captura
determinística do email) já é coberto por
test_wizard_orchestrator_wiring::test_email_extracted_from_raw_context_bypassing_llm.
"""
from __future__ import annotations
import pytest
from app.shared.pii_masking import strip_pii_for_llm_prompt


@pytest.mark.easy
def test_email_masked():
    out = strip_pii_for_llm_prompt("contato pedro.silva@democompany.com.br aqui")
    assert "pedro.silva@democompany.com.br" not in out
    assert "REMOVIDO" in out


@pytest.mark.easy
def test_cpf_masked():
    out = strip_pii_for_llm_prompt("cpf 123.456.789-00")
    assert "123.456.789-00" not in out


@pytest.mark.easy
def test_phone_masked():
    out = strip_pii_for_llm_prompt("tel (11) 98765-4321")
    assert "98765-4321" not in out


@pytest.mark.easy
def test_no_pii_unchanged():
    t = "quero criar uma vaga de gerente de tesouraria pleno"
    assert strip_pii_for_llm_prompt(t) == t
