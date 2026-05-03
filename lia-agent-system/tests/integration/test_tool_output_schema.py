"""R-004 — output_schema field em ToolDefinition + 1 caller exemplar.

Sprint 1 Quick Wins — REMEDIATION_BRIEF Wave 0.
Cobre criterio de aceite F-212 / R-004.

Os outros 31 tool registries seguem em debito Sprint 2 (mesmo pattern):
  - Cada ToolDefinition recebe output_schema=ToolOutput (ou subclasse).
  - ToolExecutor sera estendido para validar via .model_validate.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_tool_definition_has_output_schema_field() -> None:
    """R-004: ToolDefinition expoe campo opcional output_schema (Type[BaseModel])."""
    from lia_agents_core.tool_adapter import ToolDefinition

    fields = ToolDefinition.model_fields
    assert (
        "output_schema" in fields
    ), "R-004: ToolDefinition precisa ter campo 'output_schema' (Optional[Type[BaseModel]])."
    field = fields["output_schema"]
    # Default deve ser None (backward compat para tools legacy).
    assert field.default is None, "R-004: output_schema deve ter default=None para preservar backward compat."


def test_tool_output_class_exists_and_has_required_fields() -> None:
    """R-004: ToolOutput Pydantic class disponivel com success/message/data."""
    from lia_agents_core.tool_adapter import ToolOutput

    fields = ToolOutput.model_fields
    assert "success" in fields, "R-004: ToolOutput precisa ter campo 'success: bool'"
    assert "message" in fields, "R-004: ToolOutput precisa ter campo 'message: str'"
    assert "data" in fields, "R-004: ToolOutput precisa ter campo 'data: Optional[dict]'"


def test_tool_output_validates_canonical_payload() -> None:
    """R-004: ToolOutput.model_validate aceita payload {success, message, data}."""
    from lia_agents_core.tool_adapter import ToolOutput

    payload = {"success": True, "message": "Email sent", "data": {"message_id": "msg-1"}}
    instance = ToolOutput.model_validate(payload)
    assert instance.success is True
    assert instance.message == "Email sent"
    assert instance.data == {"message_id": "msg-1"}


def test_tool_output_rejects_missing_success() -> None:
    """R-004: ToolOutput rejeita payload sem campos obrigatorios."""
    from lia_agents_core.tool_adapter import ToolOutput

    with pytest.raises(Exception):
        ToolOutput.model_validate({"message": "no success field"})


def test_communication_send_email_tool_has_output_schema() -> None:
    """R-004: caller exemplar (communication_tool_registry) declara output_schema."""
    from lia_agents_core.tool_adapter import ToolOutput

    from app.domains.communication.agents.communication_tool_registry import (
        get_communication_tools,
    )

    tools = get_communication_tools()
    assert tools, "Pre-requisito: get_communication_tools() retorna lista nao vazia"

    send_email = next((t for t in tools if t.name == "send_email"), None)
    assert send_email is not None, "Pre-requisito: tool 'send_email' presente"
    assert send_email.output_schema is ToolOutput, (
        "R-004: tool 'send_email' deve declarar output_schema=ToolOutput "
        "como pattern canonical para Sprint 2 replicar nos demais 31 registries."
    )


def test_communication_other_tools_can_omit_output_schema_for_now() -> None:
    """R-004 backward compat: tools sem output_schema continuam validos (default None)."""
    from app.domains.communication.agents.communication_tool_registry import (
        get_communication_tools,
    )

    tools = get_communication_tools()
    other = [t for t in tools if t.name != "send_email"]
    # Pelo menos 1 tool ainda nao migrada (representando o debito Sprint 2)
    legacy = [t for t in other if t.output_schema is None]
    assert legacy, (
        "Setup do teste: deveria existir pelo menos 1 tool sem output_schema "
        "(sinal do debito Sprint 2 para replicar pattern)."
    )
