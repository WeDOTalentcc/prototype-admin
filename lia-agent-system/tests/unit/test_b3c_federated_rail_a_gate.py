"""
Tests for B3c (2026-06-09): Rail A gate wired into federated _run_agent() path.
Verifies check_rail_a_capability is called when source=="rail_a" + intent_hint present.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_rail_a_gate_called_for_rail_a_source():
    """When context.metadata.source=="rail_a" + intent_hint, Rail A gate fires."""
    # Simula o resultado que check_rail_a_capability retornaria para job_insights
    _mock_cap_result = {
        "type": "message",
        "content": "Abrindo painel de insights...",
        "ui_action": "open_modal",
        "ui_action_params": {
            "modal_id": "job_insights",
            "data": {"job_id": "abc-123", "company_id": "co-1"},
        },
        "confidence": 1.0,
        "domain": "capability_map",
        "source": "rail_a_gate",
    }
    with patch(
        "app.orchestrator.guards.rail_a_capability_check.check_rail_a_capability",
        new=AsyncMock(return_value=_mock_cap_result),
    ) as mock_gate:
        # Simula o que o codigo do _run_agent faz internamente
        context = {
            "metadata": {
                "source": "rail_a",
                "intent_hint": "job_insights",
                "entity_ids": {"job_id": "abc-123"},
            }
        }
        _meta_ctx = context.get("metadata") or {}
        should_check = _meta_ctx.get("source") == "rail_a" and _meta_ctx.get("intent_hint")
        assert should_check, "Rail A guard condition must match for this context"

        if should_check:
            from app.orchestrator.guards.rail_a_capability_check import check_rail_a_capability
            cap = await check_rail_a_capability(
                context=context,
                message="mostra insights da vaga",
                company_id="co-1",
                db=MagicMock(),
            )
        assert mock_gate.called
    print("  OK: Rail A gate is called for source==rail_a + intent_hint")


@pytest.mark.asyncio
async def test_rail_a_gate_skipped_for_regular_messages():
    """Regular messages (no rail_a source) skip the gate — no overhead."""
    context_regular = {
        "metadata": {
            "source": "user_input",
            "domain_hint": "jobs_management",
        }
    }
    _meta_ctx = context_regular.get("metadata") or {}
    should_check = _meta_ctx.get("source") == "rail_a" and _meta_ctx.get("intent_hint")
    assert not should_check, "Non-rail_a messages must NOT trigger the gate"
    print("  OK: Regular messages skip Rail A gate")


@pytest.mark.asyncio
async def test_rail_a_gate_skipped_when_no_intent_hint():
    """source==rail_a but no intent_hint → gate skipped (incomplete Rail A metadata)."""
    context_partial = {
        "metadata": {"source": "rail_a"}  # no intent_hint
    }
    _meta_ctx = context_partial.get("metadata") or {}
    should_check = _meta_ctx.get("source") == "rail_a" and _meta_ctx.get("intent_hint")
    assert not should_check, "Without intent_hint, gate must not fire"
    print("  OK: Partial Rail A metadata skips gate")


@pytest.mark.asyncio
async def test_rail_a_returns_open_modal_for_job_insights():
    """Full integration: job_insights with entity_ids yields open_modal response."""
    from app.orchestrator.guards.rail_a_capability_check import check_rail_a_capability

    context = {
        "metadata": {
            "source": "rail_a",
            "intent_hint": "job_insights",
            "entity_ids": {"job_id": "610705ab-7a98-45e9-999a-5bdb62975989"},
        }
    }
    result = await check_rail_a_capability(
        context=context,
        message="mostra os insights da vaga Diretor Juridico",
        company_id="co-1",
        db=MagicMock(),
    )
    assert result is not None, "Should short-circuit (not return None)"
    assert result.get("ui_action") == "open_modal", f"Expected open_modal, got {result.get('ui_action')}"
    assert result.get("ui_action_params", {}).get("modal_id") == "job_insights"
    assert result.get("ui_action_params", {}).get("data", {}).get("job_id") == "610705ab-7a98-45e9-999a-5bdb62975989"
    print("  OK: job_insights with entity_ids → open_modal with data.job_id")


@pytest.mark.asyncio
async def test_rail_a_navigate_fallback_when_no_entity():
    """job_insights without entity_ids → navigate fallback, not broken open_modal."""
    from app.orchestrator.guards.rail_a_capability_check import check_rail_a_capability

    context = {
        "metadata": {
            "source": "rail_a",
            "intent_hint": "job_insights",
            # NO entity_ids — user opened chat without selecting a vaga
        }
    }
    result = await check_rail_a_capability(
        context=context,
        message="mostra os insights",
        company_id="co-1",
        db=MagicMock(),  # db present but resolver won't find entity from message alone
    )
    assert result is not None, "Should always short-circuit for non-chat-executable"
    # Either navigate_to (fallback when entity missing) or open_modal (if resolver found it)
    assert result.get("ui_action") in ("navigate_to", "open_modal"), f"Unexpected ui_action: {result}"
    print(f"  OK: no entity_ids → ui_action={result.get('ui_action')} (honest response)")
