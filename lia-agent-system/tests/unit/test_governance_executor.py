"""
RED tests for GovernanceExecutor — 8-step governance pipeline.

Pipeline:
  1. Validate input parameters
  2. Validate company_id isolation (fail-closed)
  3. Execute function with SLA timeout
  4. FairnessGuard if affects_candidate_decision
  5. PII masking on declared output fields if touches_pii
  6. Output schema validation
  7. Audit record (non-blocking background task)
  8. Metrics emission hook
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.tools.executor import GovernanceExecutor, ToolExecutionContext
from lia_agents_core.tool_adapter import ToolContract


def _simple_fn():
    async def fn(**kwargs):
        return {"success": True, "data": {"result": "ok"}, "message": "done"}
    return fn


def _make_tool(**overrides) -> ToolContract:
    defaults = dict(
        name="test_tool",
        description="A test tool",
        parameters={
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
        output_schema={},
        function=_simple_fn(),
    )
    defaults.update(overrides)
    return ToolContract(**defaults)


def _make_ctx(**overrides) -> ToolExecutionContext:
    defaults = dict(user_id="u-1", company_id="c-123")
    defaults.update(overrides)
    return ToolExecutionContext(**defaults)


@pytest.fixture
def executor():
    return GovernanceExecutor()


@pytest.mark.asyncio
async def test_step1_missing_required_param_returns_error(executor):
    result = await executor.execute(_make_tool(), parameters={}, context=_make_ctx())
    assert result.success is False
    assert "query" in result.error.lower()


@pytest.mark.asyncio
async def test_step1_valid_params_proceed(executor):
    result = await executor.execute(_make_tool(), parameters={"query": "hello"}, context=_make_ctx())
    assert result.success is True


@pytest.mark.asyncio
async def test_step2_missing_company_id_blocks_execution(executor):
    result = await executor.execute(
        _make_tool(requires_company_id=True),
        parameters={"query": "x"},
        context=_make_ctx(company_id=""),
    )
    assert result.success is False
    assert "company_id" in result.error.lower()


@pytest.mark.asyncio
async def test_step2_tool_without_requirement_passes_empty_company(executor):
    result = await executor.execute(
        _make_tool(requires_company_id=False),
        parameters={"query": "x"},
        context=_make_ctx(company_id=""),
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_step3_timeout_returns_error(executor):
    async def _slow(**kwargs):
        await asyncio.sleep(10)
    result = await executor.execute(
        _make_tool(function=_slow, sla_ms=50),
        parameters={"query": "x"},
        context=_make_ctx(),
    )
    assert result.success is False
    assert "timeout" in result.error.lower() or "timed out" in result.error.lower()


@pytest.mark.asyncio
async def test_step3_function_exception_returns_error(executor):
    async def _broken(**kwargs):
        raise ValueError("boom")
    result = await executor.execute(
        _make_tool(function=_broken),
        parameters={"query": "x"},
        context=_make_ctx(),
    )
    assert result.success is False
    assert "boom" in result.error


@pytest.mark.asyncio
async def test_step4_fairness_guard_blocks_biased_output(executor):
    async def _biased(**kwargs):
        return {"success": True, "data": {"score": "prefer young males"}, "message": "ok"}
    mock_fr = MagicMock()
    mock_fr.is_biased.return_value = True
    mock_fr.blocked_terms = ["young males"]
    tool = _make_tool(function=_biased, affects_candidate_decision=True)
    with patch.object(executor._fairness_guard, "check", return_value=mock_fr):
        result = await executor.execute(tool, parameters={"query": "x"}, context=_make_ctx())
    assert result.success is False
    assert "fairness" in result.error.lower() or "blocked" in result.error.lower()


@pytest.mark.asyncio
async def test_step4_fairness_guard_skipped_when_not_decision_tool(executor):
    tool = _make_tool(affects_candidate_decision=False)
    with patch.object(executor._fairness_guard, "check") as mock_check:
        result = await executor.execute(tool, parameters={"query": "x"}, context=_make_ctx())
    mock_check.assert_not_called()
    assert result.success is True


@pytest.mark.asyncio
async def test_step5_pii_fields_masked_in_output(executor):
    async def _pii(**kwargs):
        return {"success": True, "data": {"name": "João Silva", "cpf": "123.456.789-00"}, "message": "ok"}
    tool = _make_tool(function=_pii, touches_pii=True, pii_output_fields=["name", "cpf"])
    with patch("app.tools.executor.mask_pii", side_effect=lambda x: "[REDACTED]") as mock_mask:
        result = await executor.execute(tool, parameters={"query": "x"}, context=_make_ctx())
    assert result.success is True
    mock_mask.assert_called()


@pytest.mark.asyncio
async def test_step5_pii_masking_skipped_when_not_pii_tool(executor):
    with patch("app.tools.executor.mask_pii") as mock_mask:
        result = await executor.execute(_make_tool(touches_pii=False), parameters={"query": "x"}, context=_make_ctx())
    mock_mask.assert_not_called()
    assert result.success is True


@pytest.mark.asyncio
async def test_step6_output_missing_required_field_returns_error(executor):
    async def _incomplete(**kwargs):
        return {"success": True}
    result = await executor.execute(
        _make_tool(function=_incomplete, output_schema={"required": ["success", "data", "message"]}),
        parameters={"query": "x"},
        context=_make_ctx(),
    )
    assert result.success is False
    assert "output" in result.error.lower() or "schema" in result.error.lower()


@pytest.mark.asyncio
async def test_step6_valid_output_passes_schema(executor):
    result = await executor.execute(
        _make_tool(output_schema={"required": ["success", "data", "message"]}),
        parameters={"query": "x"},
        context=_make_ctx(),
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_step7_audit_log_called_on_success(executor):
    with patch.object(executor._audit_service, "log_action", new_callable=AsyncMock) as mock_log:
        result = await executor.execute(_make_tool(), parameters={"query": "x"}, context=_make_ctx())
        await asyncio.sleep(0.05)
    mock_log.assert_called_once()
    kw = mock_log.call_args.kwargs
    assert kw["company_id"] == "c-123"
    assert kw["action_type"] == "tool_call"
    assert kw["target_id"] == "test_tool"


@pytest.mark.asyncio
async def test_step8_metrics_emitted_on_success(executor):
    with patch.object(executor, "_emit_metrics") as mock_metrics:
        result = await executor.execute(_make_tool(), parameters={"query": "x"}, context=_make_ctx())
    mock_metrics.assert_called_once()
    assert mock_metrics.call_args[0][0] == "test_tool"
    assert mock_metrics.call_args[1]["success"] is True
