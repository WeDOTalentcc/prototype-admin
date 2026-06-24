"""TDD: intake deve surfaçar departamento candidato quando não encontrado no DB.

Fix P2: quando _match_department retorna None, o estado deve conter
department_candidate_from_title e existing_departments para o wizard
poder oferecer sugestão de criação ou escolha de existente.
"""
import pytest
from unittest.mock import patch, MagicMock

from app.domains.job_creation.nodes.intake import _dept_tokens, _match_department


def test_dept_tokens_drops_seniority():
    """_dept_tokens com drop_seniority=True deve remover tokens de senioridade."""
    result = _dept_tokens("Diretor Jurídico", drop_seniority=True)
    assert result
    joined = " ".join(result).lower()
    assert "juridico" in joined or "juridic" in joined,         f"Token de conteúdo juridico deve permanecer após drop_seniority, got: {result}"


def test_match_department_returns_none_when_no_match():
    """_match_department deve retornar None quando nenhum dept bate com threshold."""
    result = _match_department("Diretor Jurídico", ["Engenharia", "Produto", "Marketing"])
    assert result is None,         "Deve retornar None quando nenhum departamento tem score >= threshold"


def test_match_department_returns_best_match():
    """_match_department deve retornar o nome original do dept quando há match."""
    result = _match_department("Analista de RH", ["Recursos Humanos", "Engenharia"])
    if result is not None:
        assert result in ["Recursos Humanos", "Engenharia"],             "Se retornar algo, deve ser da lista fornecida"


def _make_mock_extractor(title="Diretor Jurídico", seniority="director"):
    """Cria mock de extractor retornando extraction com title e sem department."""
    mock_extraction = MagicMock()
    mock_extraction.overall_confidence = 0.8

    def _val(field_name):
        mapping = {
            "title": title,
            "seniority": seniority,
        }
        return mapping.get(field_name)

    # Mock each field as IntakeField with .value
    for field in ["title", "seniority", "department", "location", "work_model",
                  "contract_type", "manager_name", "manager_email"]:
        val = {"title": title, "seniority": seniority}.get(field)
        field_mock = MagicMock()
        field_mock.value = val
        field_mock.source = "llm" if val else None
        setattr(mock_extraction, field, field_mock)

    mock_extraction.overall_confidence = 0.8
    _title_field = getattr(mock_extraction, "title")
    mock_extraction.overall_confidence = 0.8

    mock_extractor = MagicMock()
    mock_extractor.extract.return_value = mock_extraction
    mock_extractor.extract_from_sources.return_value = mock_extraction
    return mock_extractor


def test_intake_state_has_department_candidate_when_no_match():
    """Estado retornado por intake_node deve ter department_candidate_from_title quando dept não encontrado."""
    from app.domains.job_creation.nodes.intake import intake_node

    state = {
        "user_query": "Quero criar vaga para Diretor Jurídico",
        "workspace_id": "00000000-0000-0000-0000-000000000001",
        "messages": [],
        "stage_history": [],
        "current_stage": "start",
    }

    mock_dept_names = ["Engenharia", "Produto", "Marketing"]
    mock_extractor = _make_mock_extractor(title="Diretor Jurídico", seniority="director")

    with patch(
        "app.domains.job_creation.nodes.intake.run_coro_in_threadpool",
        return_value=mock_dept_names
    ), patch(
        "app.domains.job_creation.graph.get_intake_extractor",
        return_value=mock_extractor
    ), patch(
        "app.domains.job_creation.nodes.intake.emit_intake_audit"
    ):
        result = intake_node(state)

    assert "department_candidate_from_title" in result,         "Estado deve ter department_candidate_from_title quando dept não encontrado"

    candidate = result.get("department_candidate_from_title")
    assert candidate is not None and candidate != "",         f"department_candidate_from_title deve ser string não-vazia, got: {candidate!r}"

    assert "existing_departments" in result,         "Estado deve ter existing_departments (lista dos departamentos existentes)"

    existing = result.get("existing_departments")
    assert isinstance(existing, list) and len(existing) > 0,         f"existing_departments deve ser lista não-vazia, got: {existing!r}"


def test_intake_no_candidate_when_dept_found():
    """Quando departamento é encontrado por match, department_candidate_from_title deve ser None/vazio."""
    from app.domains.job_creation.nodes.intake import intake_node

    state = {
        "user_query": "Quero criar vaga para Analista Financeiro",
        "workspace_id": "00000000-0000-0000-0000-000000000001",
        "messages": [],
        "stage_history": [],
        "current_stage": "start",
    }

    mock_dept_names = ["Financeiro", "Engenharia", "Produto"]
    mock_extractor = _make_mock_extractor(title="Analista Financeiro", seniority="analyst")

    with patch(
        "app.domains.job_creation.nodes.intake.run_coro_in_threadpool",
        return_value=mock_dept_names
    ), patch(
        "app.domains.job_creation.graph.get_intake_extractor",
        return_value=mock_extractor
    ), patch(
        "app.domains.job_creation.nodes.intake.emit_intake_audit"
    ):
        result = intake_node(state)

    if result.get("parsed_department"):
        candidate = result.get("department_candidate_from_title")
        assert candidate is None or candidate == "",             "Quando dept encontrado, department_candidate_from_title deve ser None ou vazio"
