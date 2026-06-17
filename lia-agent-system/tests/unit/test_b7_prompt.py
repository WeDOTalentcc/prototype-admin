"""B7 (fix 2026-05-31): o agente NÃO deve narrar perguntas WSI — deve chamar a tool.

Sensor de regressão: garante que o system prompt do orquestrador mantém a
proibição de redigir perguntas + a regra anti-alucinação cobrindo perguntas WSI.
(Guard contra alguém remover a instrução; o comportamento real é do LLM.)
"""
import pytest

from app.domains.job_creation.orchestrator.wizard_orchestrator import _SYSTEM_PROMPT_BASE


@pytest.mark.medium
def test_prompt_proibe_narrar_perguntas():
    p = _SYSTEM_PROMPT_BASE.lower()
    # proibição explícita de escrever/enumerar as perguntas no chat
    assert "nunca escreva" in p or "não escreva" in p or "jamais redija" in p
    assert "generate_wsi_questions" in _SYSTEM_PROMPT_BASE
    # menciona que as perguntas aparecem no painel (via tool)
    assert "painel" in p


@pytest.mark.medium
def test_anti_alucinacao_cobre_perguntas_de_triagem():
    p = _SYSTEM_PROMPT_BASE.lower()
    # a regra anti-alucinação deve citar perguntas de triagem explicitamente
    assert "perguntas de triagem" in p
    assert "alucina" in p
