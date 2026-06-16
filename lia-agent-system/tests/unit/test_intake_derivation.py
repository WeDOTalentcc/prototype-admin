"""Sensor — derivação determinística no intake (auditoria 2026-06-03).

Pina #2 (nome do gestor) + #8 (senioridade do título): derivar de sinal real,
pré-preencher como SUGESTÃO, sinalizar proveniência — nunca alucinar.

Bug original: LIA inventou "Carlos Mendes" do email paulo.moraes@... (sem sinal)
e não deduzia senioridade "Diretoria" de "Diretor Financeiro" (sinal óbvio).
"""
from app.domains.job_creation.nodes.intake import (
    _derive_name_from_email,
    _derive_intake_suggestions,
)


def test_derive_name_from_email_basic():
    assert _derive_name_from_email("paulo.moraes@democompany.com.br") == "Paulo Moraes"
    assert _derive_name_from_email("ana_paula.silva@x.com") == "Ana Paula Silva"
    assert _derive_name_from_email("joao@x.com") == "Joao"


def test_derive_name_from_email_rejects_generic_and_invalid():
    for generic in ("rh@x.com", "contato@x.com", "vagas@x.com", "no-reply@x.com",
                    "recrutamento@x.com", "talentos@x.com"):
        assert _derive_name_from_email(generic) is None
    assert _derive_name_from_email("") is None
    assert _derive_name_from_email(None) is None
    assert _derive_name_from_email("notanemail") is None
    assert _derive_name_from_email("123.456@x.com") is None


def test_seniority_inferred_from_title_when_missing():
    sen, inferred, _, _ = _derive_intake_suggestions(
        parsed_title="Diretor Financeiro", parsed_seniority=None,
        parsed_manager_name=None, parsed_manager_email=None,
    )
    assert inferred is True
    assert sen and "diret" in sen.lower(), f"esperava senioridade de diretoria, veio {sen!r}"


def test_explicit_seniority_is_not_overwritten():
    sen, inferred, _, _ = _derive_intake_suggestions(
        parsed_title="Diretor Financeiro", parsed_seniority="Pleno",
        parsed_manager_name=None, parsed_manager_email=None,
    )
    assert sen == "Pleno"
    assert inferred is False


def test_name_suggested_from_email_when_missing():
    _, _, name, suggested = _derive_intake_suggestions(
        parsed_title="Analista", parsed_seniority="Pleno",
        parsed_manager_name=None, parsed_manager_email="paulo.moraes@democompany.com.br",
    )
    assert name == "Paulo Moraes"
    assert suggested is True


def test_explicit_name_is_not_overwritten():
    _, _, name, suggested = _derive_intake_suggestions(
        parsed_title="Analista", parsed_seniority="Pleno",
        parsed_manager_name="Maria Souza", parsed_manager_email="paulo.moraes@x.com",
    )
    assert name == "Maria Souza"
    assert suggested is False


def test_no_signal_no_invention():
    # Sem título e sem email → nada é inventado (a LIA pergunta).
    sen, inf, name, sug = _derive_intake_suggestions(
        parsed_title=None, parsed_seniority=None,
        parsed_manager_name=None, parsed_manager_email=None,
    )
    assert sen is None and inf is False
    assert name is None and sug is False


# ── #8 departamento tenant-aware (auditoria 2026-06-03) ──────────────────────
from app.domains.job_creation.nodes.intake import _match_department


def test_match_department_finance():
    depts = ["Finanças", "Marketing", "Pesquisa e Desenvolvimento", "Tecnologia"]
    assert _match_department("Diretor Financeiro", depts) == "Finanças"


def test_match_department_research_clinic():
    depts = ["Finanças", "Pesquisa e Desenvolvimento", "Marketing"]
    assert _match_department("Diretor de Pesquisa Clínica", depts) == "Pesquisa e Desenvolvimento"


def test_match_department_does_not_match_seniority_to_diretoria():
    # "Diretor" é senioridade, não departamento — não pode casar com "Diretoria".
    depts = ["Diretoria", "Finanças"]
    assert _match_department("Diretor Financeiro", depts) == "Finanças"


def test_match_department_no_good_match_returns_none():
    # Cliente não tem depto correspondente → não inventa (LIA pergunta).
    depts = ["Finanças", "Marketing"]
    assert _match_department("Engenheiro de Dados", depts) is None


def test_match_department_empty_inputs():
    assert _match_department("", ["Finanças"]) is None
    assert _match_department("Diretor Financeiro", []) is None
    assert _match_department("Diretor Financeiro", None) is None
