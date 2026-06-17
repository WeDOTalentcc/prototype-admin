"""Sensor for the canonical headcount import producer (Track B / Fase 2).

Pins: (1) loose PT/EN import items normalize to canonical PlannedHeadcount
fields (month names, deadline→month/year, position/role/cargo fallback); and
(2) import_planned_headcounts resolves department NAME → FK and reports
unmatched names as unresolved (never auto-creating). This is the single
producer both the chat tool and the CSV endpoint now share.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.workforce.services.headcount_import_service import (
    import_planned_headcounts,
    normalize_headcount_item,
)

MOD = "app.domains.workforce.services.headcount_import_service"


def test_normalize_maps_pt_keys_and_month_name():
    n = normalize_headcount_item(
        {"departamento": "Tecnologia", "cargo": "Dev", "quantidade": "3",
         "mes": "Fev", "ano": "2024"}
    )
    assert n["department"] == "Tecnologia"
    assert n["title"] == "Dev"
    assert n["headcount"] == 3
    assert n["target_month"] == 2
    assert n["target_year"] == 2024


def test_normalize_deadline_to_month_year():
    n = normalize_headcount_item({"role": "PM", "deadline": "2025-08-15"})
    assert n["target_month"] == 8
    assert n["target_year"] == 2025


def test_normalize_defaults_and_non_dict():
    assert normalize_headcount_item("x") is None
    n = normalize_headcount_item({"department": "RH"})
    assert n["title"] == "Posição a definir"
    assert n["headcount"] == 1


def test_normalize_numeric_month_and_salary():
    n = normalize_headcount_item(
        {"position": "Eng", "month": "3", "year": "2024",
         "salary_min": "5000", "salary_max": "8000.5"}
    )
    assert n["target_month"] == 3
    assert n["salary_min"] == 5000.0
    assert n["salary_max"] == 8000.5


def _mock_repos(plan_id, dept_pairs):
    plan = MagicMock()
    plan.id = plan_id
    wf = MagicMock()
    wf.list_hiring_plans = AsyncMock(return_value=[plan])
    wf.create_hiring_plan = AsyncMock(return_value=plan)
    wf.create_headcount = AsyncMock()
    depts = []
    for did, name in dept_pairs:
        d = MagicMock()
        d.id = did
        d.name = name
        depts.append(d)
    dept = MagicMock()
    dept.list_active_for_company = AsyncMock(return_value=depts)
    return wf, dept


@pytest.mark.asyncio
async def test_import_resolves_department_fk_and_reports_unresolved():
    tec_id = uuid.uuid4()
    wf, dept = _mock_repos(uuid.uuid4(), [(tec_id, "Tecnologia")])
    with patch(f"{MOD}.WorkforceRepository", return_value=wf), patch(
        f"{MOD}.DepartmentRepository", return_value=dept
    ):
        out = await import_planned_headcounts(
            session=MagicMock(),
            company_id="c1",
            items=[
                {"department": "Tecnologia", "position": "Dev",
                 "headcount": 3, "month": 2, "year": 2024},
                {"department": "Inexistente", "position": "X",
                 "headcount": 1, "month": 1, "year": 2024},
            ],
            fiscal_year=2024,
            source="csv_import",
        )
    assert out["created"] == 2
    assert out["resolved_departments"] == ["Tecnologia"]
    assert out["unresolved_departments"] == ["Inexistente"]
    dept_ids = {
        c.kwargs["headcount_data"]["department_id"]
        for c in wf.create_headcount.await_args_list
    }
    assert tec_id in dept_ids
    assert None in dept_ids


@pytest.mark.asyncio
async def test_import_empty_items_creates_nothing():
    wf, dept = _mock_repos(uuid.uuid4(), [])
    with patch(f"{MOD}.WorkforceRepository", return_value=wf), patch(
        f"{MOD}.DepartmentRepository", return_value=dept
    ):
        out = await import_planned_headcounts(
            session=MagicMock(), company_id="c1", items=[], fiscal_year=2024
        )
    assert out["created"] == 0
    wf.create_headcount.assert_not_awaited()
