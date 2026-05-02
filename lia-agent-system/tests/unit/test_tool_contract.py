"""
TDD — ToolContract canônico.

RED: todos os testes falham antes da implementação.
GREEN: passam após o ToolContract estar implementado.

Harness Engineering:
  Guide: ToolContract declara explicitamente PII, decisão, side_effects.
  Sensor: este arquivo de testes — falha = contrato violado.
"""
from typing import Any, Callable
import pytest


# ── helpers ──────────────────────────────────────────────────────────────────

def _dummy_fn(**kwargs: Any) -> dict:
    return {"success": True, "data": {}, "message": "ok"}


# ── GRUPO 1: campos obrigatórios e defaults ───────────────────────────────────

def test_tool_contract_requires_name_description_function():
    from lia_agents_core.tool_adapter import ToolContract
    tc = ToolContract(name="my_tool", description="does X", function=_dummy_fn)
    assert tc.name == "my_tool"
    assert tc.description == "does X"
    assert tc.function is _dummy_fn


def test_tool_contract_defaults_safe():
    from lia_agents_core.tool_adapter import ToolContract
    tc = ToolContract(name="t", description="d", function=_dummy_fn)
    assert tc.version == "1.0.0"
    assert tc.owner_team == "backend"
    assert tc.parameters == {}
    assert tc.output_schema == {}
    assert tc.side_effects == ["read"]
    assert tc.requires_company_id is True
    assert tc.touches_pii is False
    assert tc.pii_output_fields == []
    assert tc.lgpd_legal_basis is None
    assert tc.affects_candidate_decision is False
    assert tc.requires_human_review is False
    assert tc.sla_ms == 5000


def test_tool_contract_rejects_unknown_side_effect():
    from lia_agents_core.tool_adapter import ToolContract
    import pydantic
    with pytest.raises((pydantic.ValidationError, ValueError)):
        ToolContract(
            name="t", description="d", function=_dummy_fn,
            side_effects=["invalid_effect"]
        )


# ── GRUPO 2: classificação de governança ─────────────────────────────────────

def test_pii_tool_declares_fields():
    from lia_agents_core.tool_adapter import ToolContract
    tc = ToolContract(
        name="get_candidate_profile",
        description="Retorna perfil do candidato",
        function=_dummy_fn,
        touches_pii=True,
        pii_output_fields=["name", "email", "phone"],
        lgpd_legal_basis="legitimate_interest",
    )
    assert tc.touches_pii is True
    assert "email" in tc.pii_output_fields
    assert tc.lgpd_legal_basis == "legitimate_interest"


def test_decision_tool_declares_fairness():
    from lia_agents_core.tool_adapter import ToolContract
    tc = ToolContract(
        name="move_candidate_stage",
        description="Move candidato de etapa",
        function=_dummy_fn,
        side_effects=["write"],
        affects_candidate_decision=True,
    )
    assert tc.affects_candidate_decision is True
    assert "write" in tc.side_effects


def test_send_tool_declares_send_effect():
    from lia_agents_core.tool_adapter import ToolContract
    tc = ToolContract(
        name="send_email",
        description="Envia e-mail para candidato",
        function=_dummy_fn,
        side_effects=["send"],
        touches_pii=True,
        pii_output_fields=["recipient_email"],
    )
    assert "send" in tc.side_effects


# ── GRUPO 3: output_schema ────────────────────────────────────────────────────

def test_output_schema_accepted():
    from lia_agents_core.tool_adapter import ToolContract
    schema = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "data": {"type": "object"},
            "message": {"type": "string"},
        },
        "required": ["success"],
    }
    tc = ToolContract(
        name="t", description="d", function=_dummy_fn,
        output_schema=schema,
    )
    assert tc.output_schema["required"] == ["success"]


# ── GRUPO 4: backward compatibility ─────────────────────────────────────────

def test_old_tool_definition_still_importable():
    """ToolDefinition permanece como alias para não quebrar os 223 registries."""
    from lia_agents_core.tool_adapter import ToolDefinition
    td = ToolDefinition(name="old", description="legacy", function=_dummy_fn)
    assert td.name == "old"


def test_tool_definition_is_tool_contract():
    """ToolDefinition == ToolContract — mesma classe."""
    from lia_agents_core.tool_adapter import ToolDefinition, ToolContract
    assert ToolDefinition is ToolContract


# ── GRUPO 5: conversão para LangChain ────────────────────────────────────────

def test_tool_contract_to_langchain_tool_sync():
    from lia_agents_core.tool_adapter import ToolContract, tool_definition_to_langchain_tool
    tc = ToolContract(name="sync_tool", description="sync", function=_dummy_fn)
    lc = tool_definition_to_langchain_tool(tc)
    assert lc.name == "sync_tool"


async def _async_fn(**kwargs: Any) -> dict:
    return {"success": True, "data": {}, "message": "async ok"}


def test_tool_contract_to_langchain_tool_async():
    from lia_agents_core.tool_adapter import ToolContract, tool_definition_to_langchain_tool
    tc = ToolContract(name="async_tool", description="async", function=_async_fn)
    lc = tool_definition_to_langchain_tool(tc)
    assert lc.name == "async_tool"
