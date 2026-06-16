"""
RED tests — GovernanceToolNode: pós-execução governance no ToolMessage.

Pipeline pós-execução (GovernanceToolNode sobre TimedToolNode):
  - PII masking em ToolMessage.content (se contract.touches_pii)
  - AuditService.log_action (background, sempre)
  - Fail-safe: governança nunca quebra o pipeline principal
"""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from lia_agents_core.timed_tool_node import GovernanceToolNode
from lia_agents_core.tool_adapter import ToolContract


def _contract(**kw) -> ToolContract:
    base = dict(
        name="test_tool",
        description="test",
        parameters={},
        output_schema={},
        function=lambda **k: None,
    )
    base.update(kw)
    return ToolContract(**base)


def _tool_message(name: str, content: str):
    from langchain_core.messages import ToolMessage
    return ToolMessage(content=content, tool_call_id="tc-1", name=name)


def _state(messages):
    return {"messages": messages}


@pytest.fixture
def gov_node():
    contracts = [
        _contract(name="pii_tool", touches_pii=True, pii_output_fields=["email"]),
        _contract(name="decision_tool", affects_candidate_decision=True, lgpd_legal_basis="LEGITIMATE_INTEREST"),
        _contract(name="plain_tool"),
    ]
    return GovernanceToolNode(tools=[], tool_contracts=contracts, domain="test")


@pytest.mark.asyncio
async def test_pii_masking_applied_on_output(gov_node):
    msg = _tool_message("pii_tool", json.dumps({"success": True, "data": {"email": "joao@test.com"}}))
    state = _state([msg])
    with patch("app.shared.pii_masking.mask_pii", side_effect=lambda x: "[REDACTED]") as mock_mask:
        result = await gov_node._apply_governance(state, config=None)
    mock_mask.assert_called()
    out = json.loads(result["messages"][-1].content)
    assert out["data"]["email"] == "[REDACTED]"


@pytest.mark.asyncio
async def test_non_pii_tool_content_unchanged(gov_node):
    msg = _tool_message("plain_tool", json.dumps({"success": True, "result": "ok"}))
    state = _state([msg])
    with patch("app.shared.pii_masking.mask_pii") as mock_mask:
        result = await gov_node._apply_governance(state, config=None)
    mock_mask.assert_not_called()
    assert "result" in result["messages"][-1].content


@pytest.mark.asyncio
async def test_audit_fired_for_known_tool(gov_node):
    msg = _tool_message("pii_tool", json.dumps({"success": True}))
    state = _state([msg])
    with patch.object(gov_node, "_audit", new_callable=AsyncMock) as mock_audit:
        result = await gov_node._apply_governance(state, config=None)
        await asyncio.sleep(0.05)
    mock_audit.assert_called_once()
    kw = mock_audit.call_args.kwargs
    assert kw["tool_name"] == "pii_tool"


@pytest.mark.asyncio
async def test_audit_extracts_company_id_from_config(gov_node):
    msg = _tool_message("plain_tool", '{"success": true}')
    state = _state([msg])
    config = {"configurable": {"company_id": "c-999", "user_id": "u-1"}}
    with patch.object(gov_node, "_audit", new_callable=AsyncMock) as mock_audit:
        await gov_node._apply_governance(state, config=config)
        await asyncio.sleep(0.05)
    kw = mock_audit.call_args.kwargs
    assert kw["company_id"] == "c-999"


@pytest.mark.asyncio
async def test_unknown_tool_passthrough(gov_node):
    msg = _tool_message("unknown_tool", '{"success": true}')
    state = _state([msg])
    result = await gov_node._apply_governance(state, config=None)
    assert result["messages"][-1].content == '{"success": true}'


@pytest.mark.asyncio
async def test_governance_failsafe_on_exception(gov_node):
    msg = _tool_message("pii_tool", "invalid-json-no-dict")
    state = _state([msg])
    # Should NOT raise — fail-safe
    result = await gov_node._apply_governance(state, config=None)
    assert result is not None
