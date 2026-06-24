"""TDD canonical -- benefits_node e variable_comp_node (2026-06-18).

Testa:
- Pass-through quando ja confirmado
- Skip quando company_id ausente
- Emissao correta de ws_stage_payload
- Separacao de suggested vs catalog por confidence
- TypedDict: campos declarados no state (anti-regressao LangGraph silent drop)
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


# ---------------------------------------------------------------------------
# 1. TypedDict declarations (anti-regressao)
# ---------------------------------------------------------------------------

def test_state_typeddict_declares_benefits_fields():
    """Garante que confirmed_benefits e benefits_suggested estao no TypedDict."""
    from app.domains.job_creation.state import JobCreationState
    import typing
    hints = typing.get_type_hints(JobCreationState)
    assert "confirmed_benefits" in hints, "confirmed_benefits ausente do TypedDict -- LangGraph vai descartar"
    assert "benefits_suggested" in hints, "benefits_suggested ausente do TypedDict"
    assert "confirmed_variable_compensation" in hints, "confirmed_variable_compensation ausente do TypedDict"
    assert "variable_comp_suggested" in hints, "variable_comp_suggested ausente do TypedDict"


# ---------------------------------------------------------------------------
# 2. benefits_node
# ---------------------------------------------------------------------------

def _make_benefits_state(**overrides):
    base = {
        "workspace_id": "company-123",
        "parsed_seniority": "senior",
        "parsed_department": "RH",
        "parsed_employment_type": "clt",
        "stage_history": [],
    }
    base.update(overrides)
    return base


def test_benefits_node_pass_through_when_already_confirmed():
    from app.domains.job_creation.nodes.benefits import benefits_node
    state = _make_benefits_state(
        benefits_suggested=True,
        confirmed_benefits=[{"name": "Vale Refeicao"}],
    )
    result = benefits_node(state)
    # Nao deve chamar o repositorio; retorna o mesmo estado
    assert result.get("benefits_suggested") is True
    assert result.get("confirmed_benefits") == [{"name": "Vale Refeicao"}]
    assert "ws_stage_payload" not in result or result.get("current_stage") != "benefits"


def test_benefits_node_skip_when_no_company_id():
    from app.domains.job_creation.nodes.benefits import benefits_node
    state = _make_benefits_state(workspace_id="", company_id="")
    result = benefits_node(state)
    assert result.get("benefits_suggested") is True
    assert result.get("confirmed_benefits") == []


@patch("app.domains.job_creation.nodes.benefits.run_coro_in_threadpool")
def test_benefits_node_emits_ws_stage_payload(mock_threadpool):
    """Verifica que o node emite ws_stage_payload com stage=benefits."""
    mock_benefit = MagicMock()
    mock_benefit.id = "benefit-1"
    mock_benefit.name = "Vale Refeicao"
    mock_benefit.category = "alimentacao"
    mock_benefit.description = "R$800/mes"
    mock_benefit.value = 800.0
    mock_benefit.value_type = "fixed"
    mock_benefit.currency = "BRL"
    mock_benefit.frequency = "monthly"
    mock_benefit.provider = ""
    mock_benefit.notes = ""
    mock_benefit.seniority_levels = ["senior"]
    mock_benefit.departments = {"RH": True}
    mock_benefit.contract_types = ["clt"]
    # matches all 3 dims -> confidence 0.95

    mock_benefit2 = MagicMock()
    mock_benefit2.id = "benefit-2"
    mock_benefit2.name = "Gympass"
    mock_benefit2.category = "bem_estar"
    mock_benefit2.description = ""
    mock_benefit2.value = None
    mock_benefit2.value_type = "fixed"
    mock_benefit2.currency = "BRL"
    mock_benefit2.frequency = "monthly"
    mock_benefit2.provider = ""
    mock_benefit2.notes = ""
    mock_benefit2.seniority_levels = []
    mock_benefit2.departments = {}
    mock_benefit2.contract_types = []
    # zero restrictions -> confidence 0.50

    # matches=True para ambos (o mock ja filtra dentro do node pelo _fetch_benefits_matching)
    mock_threadpool.return_value = [
        {
            "id": "benefit-1",
            "name": "Vale Refeicao",
            "category": "alimentacao",
            "description": "R$800/mes",
            "value": 800.0,
            "value_type": "fixed",
            "currency": "BRL",
            "frequency": "monthly",
            "provider": "",
            "notes": "",
            "confidence": 0.95,
            "source": "catalog",
            "benefit_id": "benefit-1",
        },
        {
            "id": "benefit-2",
            "name": "Gympass",
            "category": "bem_estar",
            "description": "",
            "value": None,
            "value_type": "fixed",
            "currency": "BRL",
            "frequency": "monthly",
            "provider": "",
            "notes": "",
            "confidence": 0.50,
            "source": "catalog",
            "benefit_id": "benefit-2",
        },
    ]

    from app.domains.job_creation.nodes.benefits import benefits_node
    state = _make_benefits_state()
    result = benefits_node(state)

    assert result.get("current_stage") == "benefits"
    assert result.get("benefits_suggested") is True
    payload = result.get("ws_stage_payload", {})
    assert payload.get("stage") == "benefits"
    data = payload.get("data", {})
    # Vale Refeicao tem confidence 0.95 -> suggested
    assert any(b["name"] == "Vale Refeicao" for b in data.get("suggested", []))
    # Gympass tem confidence 0.50 -> catalog
    assert any(b["name"] == "Gympass" for b in data.get("catalog", []))


@patch("app.domains.job_creation.nodes.benefits.run_coro_in_threadpool")
def test_benefits_node_empty_catalog(mock_threadpool):
    """Quando catalogo vazio, ainda emite o panel (nao pula o stage)."""
    mock_threadpool.return_value = []

    from app.domains.job_creation.nodes.benefits import benefits_node
    state = _make_benefits_state()
    result = benefits_node(state)

    assert result.get("benefits_suggested") is True
    payload = result.get("ws_stage_payload", {})
    assert payload.get("stage") == "benefits"


# ---------------------------------------------------------------------------
# 3. variable_comp_node
# ---------------------------------------------------------------------------

def _make_vc_state(**overrides):
    base = {
        "workspace_id": "company-456",
        "parsed_seniority": "diretor",
        "parsed_department": "Juridico",
        "parsed_employment_type": "clt",
        "stage_history": [],
    }
    base.update(overrides)
    return base


def test_variable_comp_node_pass_through_when_confirmed():
    from app.domains.job_creation.nodes.variable_comp import variable_comp_node
    state = _make_vc_state(
        variable_comp_suggested=True,
        confirmed_variable_compensation=[{"kind": "plr", "target_pct": 15.0}],
    )
    result = variable_comp_node(state)
    assert result.get("variable_comp_suggested") is True
    assert result.get("confirmed_variable_compensation") == [{"kind": "plr", "target_pct": 15.0}]


def test_variable_comp_node_skip_when_no_company_id():
    from app.domains.job_creation.nodes.variable_comp import variable_comp_node
    state = _make_vc_state(workspace_id="", company_id="")
    result = variable_comp_node(state)
    assert result.get("variable_comp_suggested") is True
    assert result.get("confirmed_variable_compensation") == []


@patch("app.domains.job_creation.nodes.variable_comp.run_coro_in_threadpool")
def test_variable_comp_node_emits_ws_stage_payload(mock_threadpool):
    mock_threadpool.return_value = [
        {
            "id": "comp-1",
            "name": "PLR Anual",
            "kind": "plr",
            "description": "Participacao nos lucros",
            "target_pct": 15.0,
            "frequency": "annual",
            "currency": "BRL",
            "notes": "",
            "confidence": 0.95,
            "source": "catalog",
            "component_id": "comp-1",
        },
        {
            "id": "comp-2",
            "name": "Bonus Trimestral",
            "kind": "bonus",
            "description": "",
            "target_pct": 10.0,
            "frequency": "quarterly",
            "currency": "BRL",
            "notes": "",
            "confidence": 0.65,
            "source": "catalog",
            "component_id": "comp-2",
        },
    ]

    from app.domains.job_creation.nodes.variable_comp import variable_comp_node
    state = _make_vc_state()
    result = variable_comp_node(state)

    assert result.get("current_stage") == "variable_comp"
    assert result.get("variable_comp_suggested") is True
    payload = result.get("ws_stage_payload", {})
    assert payload.get("stage") == "variable_comp"
    data = payload.get("data", {})
    assert any(c["name"] == "PLR Anual" for c in data.get("suggested", []))
    assert any(c["name"] == "Bonus Trimestral" for c in data.get("catalog", []))


@patch("app.domains.job_creation.nodes.variable_comp.run_coro_in_threadpool")
def test_variable_comp_node_elevates_jd_extracted_confidence(mock_threadpool):
    """Componente que veio do JD deve ter confidence 0.90 mesmo se catalogo tinha 0.65."""
    mock_threadpool.return_value = [
        {
            "id": "comp-jd",
            "name": "Comissao",
            "kind": "commission",
            "description": "",
            "target_pct": 5.0,
            "frequency": "monthly",
            "currency": "BRL",
            "notes": "",
            "confidence": 0.65,
            "source": "catalog",
            "component_id": "comp-jd",
        },
    ]

    from app.domains.job_creation.nodes.variable_comp import variable_comp_node
    state = _make_vc_state(
        variable_comp_extracted=[{"component_id": "comp-jd", "kind": "commission", "target_pct": 5.0}],
    )
    result = variable_comp_node(state)

    payload = result.get("ws_stage_payload", {})
    data = payload.get("data", {})
    # Comissao foi extraida do JD -> confidence elevado para 0.90 -> sugerida
    comissao = next((c for c in data.get("suggested", []) if c["name"] == "Comissao"), None)
    assert comissao is not None, "Comissao extraida do JD deve aparecer em suggested"
    assert comissao["confidence"] == 0.90
    assert comissao["source"] == "jd_extracted"


# ---------------------------------------------------------------------------
# 4. Graph wiring (anti-regressao)
# ---------------------------------------------------------------------------

def test_graph_contains_benefits_and_variable_comp_nodes():
    from app.domains.job_creation.graph import create_job_creation_graph
    g = create_job_creation_graph()
    assert "benefits" in g.nodes, "benefits nao esta no grafo"
    assert "variable_comp" in g.nodes, "variable_comp nao esta no grafo"
