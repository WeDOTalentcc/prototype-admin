"""Task #768 — HITL gate and multi-input-mode regression tests for
``_wrap_import_workforce_plan``.

Guardrail: no input path may persist a workforce plan without explicit
``approved=True``. The three input modes (spreadsheet, paste, text) MUST
converge on the same HITL-approved write.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.domains.company_settings.agents.company_tool_registry import (
    _parse_workforce_paste,
    _wrap_import_workforce_plan,
)


@pytest.mark.asyncio
async def test_spreadsheet_mode_returns_preview_when_not_approved() -> None:
    plan = [{"department": "Eng", "role": "SWE", "quantity": 2, "deadline": "Q3"}]
    with patch(
        "app.domains.company_settings.agents.company_tool_registry.AsyncSessionLocal"
    ) as session_mock:
        result = await _wrap_import_workforce_plan(
            company_id="co_demo",
            plan_data=plan,
            input_mode="spreadsheet",
        )
        # Must NOT open a DB session when HITL preview is requested.
        session_mock.assert_not_called()

    assert result["success"] is True
    assert result["requires_human_approval"] is True
    assert result["data"]["proposed_plan_data"][0]["department"] == "Eng"
    assert result["data"]["total_hires"] == 2
    assert "expected_fields" in result["data"]


@pytest.mark.asyncio
async def test_paste_mode_parses_tsv_and_returns_preview() -> None:
    raw = (
        "Departamento\tCargo\tQuantidade\tPrazo\tSenioridade\n"
        "Engenharia\tBackend\t3\tQ2\tPleno\n"
        "Comercial\tAccount Executive\t2\tQ3\tSenior\n"
    )
    with patch(
        "app.domains.company_settings.agents.company_tool_registry.AsyncSessionLocal"
    ) as session_mock:
        result = await _wrap_import_workforce_plan(
            company_id="co_demo",
            raw_text=raw,
            input_mode="paste",
        )
        session_mock.assert_not_called()

    assert result["success"] is True
    assert result["requires_human_approval"] is True
    proposed = result["data"]["proposed_plan_data"]
    assert len(proposed) == 2
    assert proposed[0] == {
        "department": "Engenharia",
        "role": "Backend",
        "quantity": 3,
        "deadline": "Q2",
        "seniority": "Pleno",
    }
    assert result["data"]["total_hires"] == 5


@pytest.mark.asyncio
async def test_text_mode_calls_llm_and_returns_preview() -> None:
    """Free-text mode must (a) call the LLM extractor, (b) never write,
    and (c) return requires_human_approval=True."""
    fake_plan = [
        {
            "department": "Produto",
            "role": "Product Manager",
            "quantity": 1,
            "deadline": "2026-06",
            "seniority": "Senior",
        }
    ]
    with patch(
        "app.domains.company_settings.agents.company_tool_registry._extract_workforce_from_text",
        AsyncMock(return_value=fake_plan),
    ) as extractor, patch(
        "app.domains.company_settings.agents.company_tool_registry.AsyncSessionLocal"
    ) as session_mock:
        result = await _wrap_import_workforce_plan(
            company_id="co_demo",
            raw_text="Precisamos contratar 1 PM senior para o squad de produto em junho.",
            input_mode="text",
        )
        extractor.assert_awaited_once()
        session_mock.assert_not_called()

    assert result["success"] is True
    assert result["requires_human_approval"] is True
    assert result["data"]["proposed_plan_data"] == fake_plan


@pytest.mark.asyncio
async def test_empty_input_returns_clarification_error() -> None:
    """All three modes must refuse empty input gracefully — never crash,
    never write."""
    with patch(
        "app.domains.company_settings.agents.company_tool_registry.AsyncSessionLocal"
    ) as session_mock:
        result = await _wrap_import_workforce_plan(
            company_id="co_demo", input_mode="paste", raw_text=""
        )
        session_mock.assert_not_called()

    assert result["success"] is False
    assert result.get("requires_human_approval") is False
    assert "expected_fields" in result["data"]


def test_parse_workforce_paste_accepts_semicolon_and_aliases() -> None:
    raw = (
        "departamento;cargo;qtd;prazo;nivel\n"
        "RH;Recrutador;1;Q1;Pleno\n"
    )
    rows = _parse_workforce_paste(raw)
    assert rows == [
        {
            "department": "RH",
            "role": "Recrutador",
            "quantity": 1,
            "deadline": "Q1",
            "seniority": "Pleno",
        }
    ]


def test_parse_workforce_paste_rejects_unknown_header() -> None:
    raw = "foo;bar;baz\n1;2;3\n"
    assert _parse_workforce_paste(raw) == []


@pytest.mark.asyncio
@pytest.mark.parametrize("sneaky_value", ["false", "no", "0", "True", 1, "yes"])
async def test_approved_only_accepts_real_bool_true(sneaky_value) -> None:
    """Regression: ``approved`` must be the real Python True — any string
    or non-bool truthy value should keep the HITL gate closed. Task #768.
    """
    plan = [{"department": "Eng", "role": "SWE", "quantity": 1}]
    with patch(
        "app.domains.company_settings.agents.company_tool_registry.AsyncSessionLocal"
    ) as session_mock:
        result = await _wrap_import_workforce_plan(
            company_id="co_demo",
            plan_data=plan,
            input_mode="spreadsheet",
            approved=sneaky_value,
        )
        session_mock.assert_not_called()
    assert result["requires_human_approval"] is True
