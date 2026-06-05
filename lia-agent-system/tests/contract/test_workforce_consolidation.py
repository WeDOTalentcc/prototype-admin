"""Workforce consolidation — chat import delegates to the canonical producer.

Track B / Fase 2 (2026-06-05): _import_workforce_plan_impl no longer writes
PlannedHeadcount inline. It delegates Sistema B to the canonical producer
import_planned_headcounts (which resolves department NAME->FK — covered by
tests/unit/test_headcount_import_service.py) and keeps Sistema C (JSON blob) as
the SOX before-state. A producer failure now surfaces HONESTLY (success=False),
replacing the previous silent-swallow behavior (CLAUDE.md REGRA 4).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

REG = "app.domains.company_settings.agents.company_tool_registry"


def _cp_mock():
    cp = MagicMock()
    cp.get_workforce_plan = AsyncMock(return_value=None)
    cp.upsert_workforce_plan = AsyncMock()
    return cp


@pytest.mark.asyncio
async def test_chat_import_delegates_to_canonical_producer():
    producer = AsyncMock(return_value={
        "created": 2, "resolved_departments": ["Engenharia"],
        "unresolved_departments": [], "plan_id": "p1", "fiscal_year": 2026,
    })
    cp = _cp_mock()
    plan_data = [
        {"department": "Engenharia", "role": "Dev Backend", "quantity": 2},
        {"department": "Produto", "role": "PM", "quantity": 1},
    ]
    with patch(f"{REG}.import_planned_headcounts", producer), patch(
        f"{REG}.CompanyProfileRepository", return_value=cp
    ):
        from app.domains.company_settings.agents.company_tool_registry import (
            _import_workforce_plan_impl,
        )
        result = await _import_workforce_plan_impl(
            session=AsyncMock(), company_id="c1", plan_data=plan_data
        )
    assert result["success"] is True
    producer.assert_awaited_once()
    assert producer.await_args.kwargs["items"] == plan_data
    assert producer.await_args.kwargs["source"] == "chat"
    assert not cp.upsert_workforce_plan.called  # Sistema C removido (Fase 3)
    assert result["data"]["headcounts_created"] == 2


@pytest.mark.asyncio
async def test_chat_import_surfaces_unresolved_departments():
    producer = AsyncMock(return_value={
        "created": 1, "resolved_departments": [],
        "unresolved_departments": ["Marte"], "plan_id": "p1", "fiscal_year": 2026,
    })
    cp = _cp_mock()
    with patch(f"{REG}.import_planned_headcounts", producer), patch(
        f"{REG}.CompanyProfileRepository", return_value=cp
    ):
        from app.domains.company_settings.agents.company_tool_registry import (
            _import_workforce_plan_impl,
        )
        result = await _import_workforce_plan_impl(
            session=AsyncMock(), company_id="c1",
            plan_data=[{"department": "Marte", "role": "X", "quantity": 1}],
        )
    assert result["success"] is True
    assert result["data"]["unresolved_departments"] == ["Marte"]
    assert "Marte" in result["message"]


@pytest.mark.asyncio
async def test_chat_import_empty_data_returns_error():
    producer = AsyncMock()
    cp = _cp_mock()
    with patch(f"{REG}.import_planned_headcounts", producer), patch(
        f"{REG}.CompanyProfileRepository", return_value=cp
    ):
        from app.domains.company_settings.agents.company_tool_registry import (
            _import_workforce_plan_impl,
        )
        result = await _import_workforce_plan_impl(
            session=AsyncMock(), company_id="c1", plan_data=[]
        )
    assert result["success"] is False
    producer.assert_not_awaited()


@pytest.mark.asyncio
async def test_chat_import_producer_failure_surfaces_honestly():
    """Producer failure -> success=False (was silently swallowed before Fase 2)."""
    producer = AsyncMock(side_effect=Exception("DB connection error"))
    cp = _cp_mock()
    with patch(f"{REG}.import_planned_headcounts", producer), patch(
        f"{REG}.CompanyProfileRepository", return_value=cp
    ):
        from app.domains.company_settings.agents.company_tool_registry import (
            _import_workforce_plan_impl,
        )
        result = await _import_workforce_plan_impl(
            session=AsyncMock(), company_id="c1",
            plan_data=[{"role": "Dev", "quantity": 1}],
        )
    assert result["success"] is False
    assert "Falha" in result["message"]
