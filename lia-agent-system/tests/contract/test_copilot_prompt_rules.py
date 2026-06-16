"""Sensor — guarda as regras de tool-use do federado (entidade nomeada + relax escopado).
GUIDE: prompt do recruiter_copilot. SENSOR: regras nao podem sumir silenciosamente.
Bug que originou (log 2026-06-05): agente chamava list_jobs status=all em vez de
filtrar pela vaga nomeada; e relaxava o filtro p/ nome -> dumpava 570 candidatos."""
from app.domains.recruiter_assistant.agents.recruiter_copilot_react_agent import (
    COPILOT_DOMAIN_SPECIFIC,
)


def test_prompt_tem_regra_entidade_nomeada():
    assert "ENTIDADE NOMEADA" in COPILOT_DOMAIN_SPECIFIC
    # busca por nome primeiro (perfil)
    assert "query=<Nome>" in COPILOT_DOMAIN_SPECIFIC
    # filtra vaga pelo titulo nomeado
    assert "ENCONTRE a vaga com" in COPILOT_DOMAIN_SPECIFIC


def test_prompt_relax_escopado_a_atributos():
    # relax NAO vale p/ nome exato / titulo (senao dumpa tudo)
    assert "NUNCA relaxe para listar todos" in COPILOT_DOMAIN_SPECIFIC
    assert "ATRIBUTOS" in COPILOT_DOMAIN_SPECIFIC
