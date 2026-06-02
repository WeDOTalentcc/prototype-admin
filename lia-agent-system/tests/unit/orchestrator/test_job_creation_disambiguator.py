"""Unit tests for the job-creation disambiguator (Task #1204).

Pure, deterministic coverage of:
  • is_job_creation_message detection
  • path scoring + confident routing vs. clarify gating
  • quick-create param extraction (and the no-title → guided fallback)
  • create_and_search precedence (compound owned by Plan&Execute, not wizard)
  • classify_path_choice PT-BR (negatives win, explicit keyword > bare confirm)
"""

import pytest

from app.orchestrator.routing.job_creation_disambiguator import (
    JobCreationPath,
    classify_path_choice,
    decide_job_creation,
    extract_quick_create_params,
    is_job_creation_message,
    score_job_creation_paths,
)


# ── detection ──────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "msg",
    [
        "criar vaga",
        "quero criar uma vaga de designer",
        "abrir uma nova posição",
        "preciso contratar um dev backend",
        "cadastrar vaga",
    ],
)
def test_is_job_creation_message_positive(msg):
    assert is_job_creation_message(msg) is True


@pytest.mark.parametrize(
    "msg",
    [
        "",
        "qual o status das minhas vagas?",
        "me mostra os candidatos do funil",
        "bom dia, tudo bem?",
    ],
)
def test_is_job_creation_message_negative(msg):
    assert is_job_creation_message(msg) is False


# ── routing vs clarify ─────────────────────────────────────────────────


def test_bare_create_is_ambiguous_and_clarifies():
    decision = decide_job_creation("criar vaga", plan_service_enabled=False)
    assert decision.action == "clarify"
    assert len(decision.clarification_options) >= 2
    assert JobCreationPath.QUICK_CREATE in decision.option_paths
    assert JobCreationPath.GUIDED_WIZARD in decision.option_paths


def test_explicit_quick_marker_routes_quick():
    decision = decide_job_creation(
        "cria rápido uma vaga de Designer Pleno", plan_service_enabled=False
    )
    assert decision.action == "route"
    assert decision.path == JobCreationPath.QUICK_CREATE


def test_explicit_guided_marker_routes_guided():
    decision = decide_job_creation(
        "me ajuda a criar uma vaga passo a passo", plan_service_enabled=False
    )
    assert decision.action == "route"
    assert decision.path == JobCreationPath.GUIDED_WIZARD


def test_rich_detail_routes_quick():
    decision = decide_job_creation(
        "criar vaga de Engenheiro de Dados sênior, remoto, faixa R$ 15 mil",
        plan_service_enabled=False,
    )
    assert decision.action == "route"
    assert decision.path == JobCreationPath.QUICK_CREATE


def test_quick_without_title_falls_back_to_guided():
    # "rápido" pushes quick, but there is no extractable title → guided.
    decision = decide_job_creation(
        "cria uma vaga rápido aí", plan_service_enabled=False
    )
    assert decision.action == "route"
    assert decision.path == JobCreationPath.GUIDED_WIZARD
    assert "job_title" in decision.missing_required


def test_create_and_search_routes_compound():
    decision = decide_job_creation(
        "criar vaga de QA e já buscar candidatos", plan_service_enabled=True
    )
    assert decision.action == "route"
    assert decision.path == JobCreationPath.CREATE_AND_SEARCH


def test_create_and_search_precedence_over_quick_detail():
    # Even with rich detail, the compound search intent wins (owned by P&E).
    decision = decide_job_creation(
        "abrir vaga de Designer sênior remoto e buscar candidatos",
        plan_service_enabled=True,
    )
    assert decision.path == JobCreationPath.CREATE_AND_SEARCH


@pytest.mark.parametrize(
    "msg",
    [
        "criar vaga de QA e iniciar sourcing",
        "abrir vaga de Designer sênior remoto e fazer sourcing",
        "criar vaga de backend e prospectar",
        "criar vaga de dados e já lançar busca",
        "abrir vaga e começar a buscar",
        "criar vaga de produto e iniciar a busca ativa",
    ],
)
def test_standalone_sourcing_forces_compound_precedence(msg):
    # Compound phrasings whose search intent has no explicit candidate noun
    # ("iniciar sourcing", "prospectar", "busca ativa") must STILL be owned by
    # Plan & Execute — the wizard never executes the compound (precedence hard).
    decision = decide_job_creation(msg, plan_service_enabled=True)
    assert decision.path == JobCreationPath.CREATE_AND_SEARCH


def test_non_job_creation_returns_none_action():
    decision = decide_job_creation("qual o status do funil?")
    assert decision.action == "none"


def test_thresholds_override_force_clarify():
    # Impossible confidence threshold → always clarify, even with strong signal.
    decision = decide_job_creation(
        "cria rápido uma vaga de Designer Pleno remoto",
        confidence_threshold=1.1,
        gap_threshold=0.0,
    )
    assert decision.action == "clarify"


# ── scoring floors ─────────────────────────────────────────────────────


def test_scoring_floors_quick_and_guided():
    scores = score_job_creation_paths("criar vaga")
    assert scores[JobCreationPath.QUICK_CREATE] >= 1.0
    assert scores[JobCreationPath.GUIDED_WIZARD] >= 1.0
    assert scores[JobCreationPath.CREATE_AND_SEARCH] == 0.0


# ── param extraction ───────────────────────────────────────────────────


def test_extract_params_title_seniority_workmodel():
    params = extract_quick_create_params(
        "criar vaga de Desenvolvedor Backend sênior remoto"
    )
    assert "job_title" in params
    assert "backend" in params["job_title"].lower()
    assert params.get("seniority") == "sênior"
    assert params.get("work_model") == "remoto"


def test_extract_params_salary():
    params = extract_quick_create_params("vaga de Analista com salário R$ 8 mil")
    assert "salary" in params


def test_extract_params_empty_when_no_title():
    params = extract_quick_create_params("cria rápido aí")
    assert "job_title" not in params


# ── follow-up classification ───────────────────────────────────────────


@pytest.mark.parametrize(
    "reply,expected",
    [
        ("criação rápida", JobCreationPath.QUICK_CREATE.value),
        ("a primeira", JobCreationPath.QUICK_CREATE.value),
        ("passo a passo", JobCreationPath.GUIDED_WIZARD.value),
        ("a segunda opção", JobCreationPath.GUIDED_WIZARD.value),
        ("quero criar e buscar candidatos", JobCreationPath.CREATE_AND_SEARCH.value),
        ("a terceira", JobCreationPath.CREATE_AND_SEARCH.value),
    ],
)
def test_classify_path_choice_explicit(reply, expected):
    assert classify_path_choice(reply) == expected


@pytest.mark.parametrize(
    "reply",
    ["não", "deixa pra lá", "cancela", "agora não", "depois"],
)
def test_classify_path_choice_negatives_cancel(reply):
    assert classify_path_choice(reply) == "cancel"


def test_classify_bare_confirmation_defaults_guided():
    assert classify_path_choice("sim, vamos") == JobCreationPath.GUIDED_WIZARD.value


def test_classify_ambiguous_returns_none():
    assert classify_path_choice("sei lá, tanto faz pra mim") is None


def test_classify_empty_returns_none():
    assert classify_path_choice("") is None
