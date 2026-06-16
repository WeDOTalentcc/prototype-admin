"""
Sensor: Rail A capability gate handles navigate_page (not just modal_id/navigate_fallback).

Root cause: rail_a_capability_check.py only handled cap.modal_id and cap.navigate_fallback
for chat_executable=false capabilities. Capabilities with navigate_page (e.g., ir_para_vagas,
ir_para_visao_global) fell through to None, causing the LLM to be called instead of
short-circuiting with the correct navigation action.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from types import SimpleNamespace


def _make_cap(
    *,
    chat_executable=False,
    modal_id=None,
    navigate_page=None,
    navigate_fallback=None,
    navigate_query=None,
    entity_required=None,
):
    return SimpleNamespace(
        chat_executable=chat_executable,
        modal_id=modal_id,
        navigate_page=navigate_page,
        navigate_fallback=navigate_fallback,
        navigate_query=navigate_query,
        entity_required=entity_required or [],
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "intent,cap,expected_page,expected_query",
    [
        (
            "ir_para_vagas",
            _make_cap(navigate_page="vagas", navigate_fallback="/jobs"),
            "vagas",
            None,
        ),
        (
            "ir_para_visao_global",
            _make_cap(navigate_page="pipeline_kanban", navigate_fallback="/recrutar"),
            "pipeline_kanban",
            None,
        ),
        (
            "ir_para_visao_global_candidatos",
            _make_cap(
                navigate_page="pipeline_kanban",
                navigate_query={"view": "candidatos"},
            ),
            "pipeline_kanban",
            {"view": "candidatos"},
        ),
        (
            "ir_para_dashboard",
            _make_cap(navigate_page="dashboard"),
            "dashboard",
            None,
        ),
    ],
    ids=["vagas", "visao_global", "visao_global_candidatos", "dashboard"],
)
async def test_rail_a_handles_navigate_page(intent, cap, expected_page, expected_query):
    with patch(
        "app.shared.services.capability_map_service.CapabilityMapService.get",
        return_value=cap,
    ):
        from app.orchestrator.guards.rail_a_capability_check import (
            check_rail_a_capability,
        )

        result = await check_rail_a_capability(
            context={"metadata": {"intent_hint": intent, "source": "rail_a"}},
            message="ir para vagas",
            company_id="test-company",
            db=AsyncMock(),
        )

    assert result is not None, f"Rail A returned None for {intent} — navigate_page not handled"
    assert result["ui_action"] == "navigate_to"
    assert result["ui_action_params"]["page"] == expected_page
    assert result["confidence"] == 1.0
    assert result["source"] == "rail_a_gate"

    if expected_query:
        assert result["ui_action_params"]["query"] == expected_query
    else:
        assert "query" not in result["ui_action_params"]


@pytest.mark.asyncio
async def test_rail_a_navigate_page_includes_fallback():
    """navigate_fallback is included as 'fallback' param for FE resilience."""
    cap = _make_cap(navigate_page="vagas", navigate_fallback="/jobs")
    with patch(
        "app.shared.services.capability_map_service.CapabilityMapService.get",
        return_value=cap,
    ):
        from app.orchestrator.guards.rail_a_capability_check import (
            check_rail_a_capability,
        )

        result = await check_rail_a_capability(
            context={"metadata": {"intent_hint": "ir_para_vagas", "source": "rail_a"}},
            message="ir para vagas",
            company_id="test-company",
            db=AsyncMock(),
        )

    assert result["ui_action_params"]["fallback"] == "/jobs"


@pytest.mark.asyncio
async def test_rail_a_chat_executable_falls_through():
    """chat_executable=true capabilities should NOT be short-circuited."""
    cap = _make_cap(chat_executable=True, navigate_page="vagas")
    with patch(
        "app.shared.services.capability_map_service.CapabilityMapService.get",
        return_value=cap,
    ):
        from app.orchestrator.guards.rail_a_capability_check import (
            check_rail_a_capability,
        )

        result = await check_rail_a_capability(
            context={"metadata": {"intent_hint": "buscar_vagas", "source": "rail_a"}},
            message="buscar vagas",
            company_id="test-company",
            db=AsyncMock(),
        )

    # chat_executable=true → should fall through (return None or non-navigate)
    # The function should return None since there's no entity_required
    assert result is None


@pytest.mark.asyncio
async def test_rail_a_no_intent_hint_falls_through():
    """No intent_hint → normal processing."""
    from app.orchestrator.guards.rail_a_capability_check import (
        check_rail_a_capability,
    )

    result = await check_rail_a_capability(
        context={"metadata": {}},
        message="hello",
        company_id="test-company",
        db=AsyncMock(),
    )
    assert result is None
