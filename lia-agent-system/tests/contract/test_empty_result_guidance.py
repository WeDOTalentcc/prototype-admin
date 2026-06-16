"""Sensor canonical P0.2 (2026-06-03) — autocorrecao em 0-resultados.

Regua Apollo: busca vazia NAO termina em "nada encontrado". O sistema relaxa o
filtro mais restritivo, roda de novo e oferece opcoes com contagem
("Opcao A 392 / Opcao B 1.662"). Extensao da REGRA 4 (anti-silent-fallback):
0-resultados retorna sinal ESTRUTURADO de relaxamento, nunca lista vazia muda.
"""
import pytest


def test_no_filters_returns_empty_signal():
    from app.orchestrator.context.empty_result_guidance import build_empty_result_guidance
    g = build_empty_result_guidance("candidato", {})
    assert g["empty"] is True
    assert g["relaxation_suggestions"] == []
    assert "candidato" in g["guidance"].lower()


def test_filters_produce_relaxation_suggestions():
    from app.orchestrator.context.empty_result_guidance import build_empty_result_guidance
    g = build_empty_result_guidance("candidato", {"location": "SP", "min_experience": 5})
    assert g["empty"] is True
    assert "location" in g["applied_filters"]
    assert g["applied_filters"]["location"] == "SP"
    # uma sugestao por filtro ativo
    assert any("location" in s for s in g["relaxation_suggestions"])
    assert any("min_experience" in s for s in g["relaxation_suggestions"])
    # guidance instrui relaxar + oferecer opcoes
    assert "relax" in g["guidance"].lower()


def test_empty_valued_filters_are_ignored():
    from app.orchestrator.context.empty_result_guidance import build_empty_result_guidance
    g = build_empty_result_guidance("vaga", {"location": "", "department": None, "seniority": "pleno"})
    assert list(g["applied_filters"].keys()) == ["seniority"]
    assert len(g["relaxation_suggestions"]) == 1


def test_none_filters_safe():
    from app.orchestrator.context.empty_result_guidance import build_empty_result_guidance
    g = build_empty_result_guidance("candidato", None)
    assert g["empty"] is True
    assert g["relaxation_suggestions"] == []
