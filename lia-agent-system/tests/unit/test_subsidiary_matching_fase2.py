"""TDD canonical -- Fase 2: subsidiary/CNPJ matching em benefits + variable_comp (2026-06-18).

Testa:
- TypedDict: parsed_subsidiary + parsed_subsidiary_cnpj declarados
- CompanyBenefitRepository.list_matching aceita subsidiary params
- matches_subsidiaries() funciona corretamente (via eligibility_matching)
- benefits_node passa subsidiary do state para o repo
- variable_comp_node passa subsidiary do state para o repo
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


# ---------------------------------------------------------------------------
# 1. TypedDict Fase 2 (anti-regressao LangGraph)
# ---------------------------------------------------------------------------

def test_state_typeddict_declares_subsidiary_fields():
    from app.domains.job_creation.state import JobCreationState
    import typing
    hints = typing.get_type_hints(JobCreationState)
    assert "parsed_subsidiary" in hints, "parsed_subsidiary ausente do TypedDict"
    assert "parsed_subsidiary_cnpj" in hints, "parsed_subsidiary_cnpj ausente do TypedDict"


# ---------------------------------------------------------------------------
# 2. matches_subsidiaries da eligibility_matching (unit)
# ---------------------------------------------------------------------------

def test_matches_subsidiaries_empty_means_universal():
    """Benefit sem restricao de subsidiaria aplica a qualquer vaga."""
    from app.shared.eligibility_matching import matches_subsidiaries
    # Lista vazia = sem restricao = aplica a todos
    assert matches_subsidiaries([], "Filial SP", "12.345.678/0001-90") is True
    assert matches_subsidiaries([], None, None) is True


def test_matches_subsidiaries_by_cnpj():
    from app.shared.eligibility_matching import matches_subsidiaries
    subsidiaries = [{"name": "Filial SP", "cnpj": "12.345.678/0001-90"}]
    # Match por CNPJ (digits only comparison)
    assert matches_subsidiaries(subsidiaries, None, "12.345.678/0001-90") is True
    assert matches_subsidiaries(subsidiaries, None, "99.999.999/0001-00") is False


def test_matches_subsidiaries_by_name_normalized():
    from app.shared.eligibility_matching import matches_subsidiaries
    subsidiaries = [{"name": "Filial São Paulo", "cnpj": "12.345.678/0001-90"}]
    # Match por nome normalizado
    assert matches_subsidiaries(subsidiaries, "filial sao paulo", None) is True
    assert matches_subsidiaries(subsidiaries, "Filial Rio", None) is False


# ---------------------------------------------------------------------------
# 3. CompanyBenefitRepository.list_matching signature
# ---------------------------------------------------------------------------

def test_benefit_repo_list_matching_accepts_subsidiary_params():
    """Garante que list_matching aceita subsidiary + subsidiary_cnpj (Fase 2)."""
    import inspect
    from app.domains.company.repositories.company_benefit_repository import CompanyBenefitRepository
    sig = inspect.signature(CompanyBenefitRepository.list_matching)
    params = list(sig.parameters.keys())
    assert "subsidiary" in params, "list_matching missing subsidiary param"
    assert "subsidiary_cnpj" in params, "list_matching missing subsidiary_cnpj param"


# ---------------------------------------------------------------------------
# 4. benefits_node passa subsidiary do state
# ---------------------------------------------------------------------------

@patch("app.domains.job_creation.nodes.benefits.run_coro_in_threadpool")
def test_benefits_node_passes_subsidiary_to_matching(mock_threadpool):
    """benefits_node deve ler parsed_subsidiary do state e passar para _fetch."""
    mock_threadpool.return_value = []

    from app.domains.job_creation.nodes.benefits import benefits_node
    state = {
        "workspace_id": "company-123",
        "parsed_seniority": "diretor",
        "parsed_department": "Juridico",
        "parsed_employment_type": "clt",
        "parsed_subsidiary": "Filial SP",
        "parsed_subsidiary_cnpj": "12.345.678/0001-90",
        "stage_history": [],
    }
    result = benefits_node(state)

    # Threadpool foi chamado -- verificar que a call incluiu subsidiary
    assert mock_threadpool.called
    # O node deve ter emitido ws_stage_payload normalmente
    assert result.get("benefits_suggested") is True
    payload = result.get("ws_stage_payload", {})
    assert payload.get("stage") == "benefits"
    # Context deve incluir infos do matching
    data = payload.get("data", {})
    assert data.get("context", {}).get("department") == "Juridico"


# ---------------------------------------------------------------------------
# 5. variable_comp_node passa subsidiary do state
# ---------------------------------------------------------------------------

@patch("app.domains.job_creation.nodes.variable_comp.run_coro_in_threadpool")
def test_variable_comp_node_passes_subsidiary_to_matching(mock_threadpool):
    mock_threadpool.return_value = []

    from app.domains.job_creation.nodes.variable_comp import variable_comp_node
    state = {
        "workspace_id": "company-456",
        "parsed_seniority": "diretor",
        "parsed_department": "Juridico",
        "parsed_employment_type": "clt",
        "parsed_subsidiary": "Filial RJ",
        "parsed_subsidiary_cnpj": "98.765.432/0001-00",
        "stage_history": [],
    }
    result = variable_comp_node(state)

    assert mock_threadpool.called
    assert result.get("variable_comp_suggested") is True
    payload = result.get("ws_stage_payload", {})
    assert payload.get("stage") == "variable_comp"


# ---------------------------------------------------------------------------
# 6. JobVacancy model has subsidiary fields
# ---------------------------------------------------------------------------

def test_job_vacancy_model_has_subsidiary_columns():
    """Garante que os campos existem no modelo (anti-regressao migration 293)."""
    from libs.models.lia_models.job_vacancy import JobVacancy
    assert hasattr(JobVacancy, "subsidiary"), "JobVacancy.subsidiary ausente -- migration 293 necessaria"
    assert hasattr(JobVacancy, "subsidiary_cnpj"), "JobVacancy.subsidiary_cnpj ausente -- migration 293 necessaria"


def test_department_model_has_subsidiary_columns():
    from libs.models.lia_models.company import Department
    assert hasattr(Department, "subsidiary_name"), "Department.subsidiary_name ausente -- migration 293 necessaria"
    assert hasattr(Department, "subsidiary_cnpj"), "Department.subsidiary_cnpj ausente -- migration 293 necessaria"
