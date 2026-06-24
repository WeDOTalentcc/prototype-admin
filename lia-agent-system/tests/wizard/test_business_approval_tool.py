from __future__ import annotations
import inspect
import pytest
from app.domains.job_management.agents.wizard_tool_registry import (
    TOOL_DEFINITIONS, STAGE_TOOLS, _TOOL_MAP,
)

BUSINESS_APPROVAL_TOOL = "request_business_approval"


def test_tool_registered_in_tool_definitions():
    names = {t.name for t in TOOL_DEFINITIONS}
    assert BUSINESS_APPROVAL_TOOL in names, (
        f"Tool {BUSINESS_APPROVAL_TOOL!r} nao encontrada em TOOL_DEFINITIONS. "
        "Adicionar ToolDefinition em wizard_tool_registry.py."
    )


def test_tool_in_tool_map():
    assert BUSINESS_APPROVAL_TOOL in _TOOL_MAP, (
        f"Tool {BUSINESS_APPROVAL_TOOL!r} ausente de _TOOL_MAP."
    )


def test_vacancy_id_required_no_company_id_in_schema():
    tool = _TOOL_MAP[BUSINESS_APPROVAL_TOOL]
    required = set(tool.parameters.get("required") or [])
    props = set((tool.parameters.get("properties") or {}).keys())
    assert "vacancy_id" in required, (
        f"Tool {BUSINESS_APPROVAL_TOOL!r} deve ter vacancy_id como required."
    )
    assert "company_id" not in props, (
        f"Tool {BUSINESS_APPROVAL_TOOL!r} NAO pode expor company_id no schema. "
        "Multi-tenancy canonical: company_id vem do JWT ContextVar via @tool_handler."
    )
    assert "company_id" not in required, (
        f"Tool {BUSINESS_APPROVAL_TOOL!r} NAO pode declarar company_id como required."
    )


def test_wrapper_reads_company_id_from_kwargs():
    tool = _TOOL_MAP[BUSINESS_APPROVAL_TOOL]
    fn = tool.function
    underlying = getattr(fn, "__wrapped__", fn)
    try:
        src = inspect.getsource(underlying)
    except (OSError, TypeError):
        src = ""
    assert 'kwargs.get("company_id")' in src or "kwargs['company_id']" in src, (
        f"Wrapper de {BUSINESS_APPROVAL_TOOL!r} nao extrai company_id de kwargs. "
        "Padrao canonical: @tool_handler injeta company_id do ContextVar JWT."
    )


def test_stage_tools_review_includes_business_approval():
    assert "review" in STAGE_TOOLS, "Stage review ausente de STAGE_TOOLS"
    assert BUSINESS_APPROVAL_TOOL in STAGE_TOOLS["review"], (
        f"{BUSINESS_APPROVAL_TOOL!r} deve estar em STAGE_TOOLS['review']. "
        "Wizard pergunta aprovacao quando vaga esta pronta pra publicar."
    )


def test_stage_tools_publish_includes_business_approval():
    assert "publish" in STAGE_TOOLS, "Stage publish ausente de STAGE_TOOLS"
    assert BUSINESS_APPROVAL_TOOL in STAGE_TOOLS["publish"], (
        f"{BUSINESS_APPROVAL_TOOL!r} deve estar em STAGE_TOOLS['publish']. "
        "Wizard pode solicitar aprovacao antes de publicar."
    )


def test_description_in_portuguese():
    tool = _TOOL_MAP[BUSINESS_APPROVAL_TOOL]
    desc = tool.description or ""
    pt_markers = ["aprovacao", "aprovacao de negocio", "vaga", "solicita", "publicar", "aprovadores"]
    assert any(m in desc.lower() for m in pt_markers), (
        f"Tool {BUSINESS_APPROVAL_TOOL!r} descricao deve ser em portugues. Atual: {desc!r}"
    )


def test_calls_trigger_approval_service():
    tool = _TOOL_MAP[BUSINESS_APPROVAL_TOOL]
    fn = tool.function
    underlying = getattr(fn, "__wrapped__", fn)
    try:
        src = inspect.getsource(underlying)
    except (OSError, TypeError):
        src = ""
    assert "approval_trigger_service" in src or "trigger_approval_if_required" in src, (
        f"Wrapper {BUSINESS_APPROVAL_TOOL!r} nao referencia approval_trigger_service. "
        "Produtor canonico unico: app/domains/job_creation/services/approval_trigger_service.py. "
        "Fix: importar e chamar trigger_approval_if_required()."
    )
