"""Sensor — proveniência honesta na frase de salário do intake_gate (2026-06-03).

Liga o fix P0 de salário (6633cb592) à camada de UX-writing: a mensagem
salary_with_mode afirmava "o mercado pratica em torno de X-Y" mesmo quando o
benchmark era estimativa não-verificada (is_estimate). Agora ramifica:
verificado → "mercado pratica"; estimativa → "não-verificada, sem fonte externa".
Em ambos a escolha de modo (Compacto/Completo) é preservada.
"""
from app.domains.job_creation.nodes.intake_gate import _build_permission_message


def test_verified_benchmark_claims_market():
    out = _build_permission_message(
        {"min": 25000, "max": 40000, "is_estimate": False},
        "Diretor de Pesquisa Clínica", "Diretoria", "híbrido",
    )
    low = out.lower()
    assert "mercado pratica" in low
    assert "não-verificada" not in low
    assert "Compacto" in out and "Completo" in out


def test_estimate_benchmark_is_labeled_unverified():
    out = _build_permission_message(
        {"min": 25000, "max": 40000, "is_estimate": True},
        "Diretor de Pesquisa Clínica", "Diretoria", "híbrido",
    )
    low = out.lower()
    assert "não-verificada" in low
    assert "mercado pratica" not in low, "estimativa não pode afirmar 'o mercado pratica'"
    assert "Compacto" in out and "Completo" in out


def test_no_benchmark_falls_back_with_mode():
    out = _build_permission_message(None, "Analista", "Pleno", "remoto")
    assert "Compacto" in out and "Completo" in out
    assert "mercado pratica" not in out.lower()
