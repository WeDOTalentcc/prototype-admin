"""Sensor for the headcount-plan summary read tool (Track B — wiring epic).

PlannedHeadcount was a ghost feature: no agent read it. This tool lets the
recruiter chat (recruiter_copilot) answer "quantas vagas faltam abrir em
<departamento>?". These pure-function tests pin the aggregation AND the honest
handling when live open-vacancy data is unavailable (CLAUDE.md REGRA 4 /
provenance: never fabricate a gap we could not compute).
"""
from __future__ import annotations

from app.domains.workforce.agents.workforce_tool_registry import (
    UNASSIGNED_LABEL,
    summarize_headcount_plan,
)


def _hc(dep_id, headcount, title="Pos"):
    return {
        "department_id": dep_id,
        "headcount": headcount,
        "title": title,
        "target_month": 1,
        "status": "planned",
    }


def test_empty_plan_is_honest():
    out = summarize_headcount_plan(
        headcounts=[], dept_name_by_id={}, open_by_dept_norm={}, year=2024
    )
    assert out["success"] is True
    assert out["data"]["has_plan"] is False
    assert out["data"]["total_planned"] == 0
    assert "Nenhum" in out["message"] and "2024" in out["message"]


def test_groups_by_department_and_sums_headcount():
    hcs = [_hc("d1", 3), _hc("d1", 2), _hc("d2", 1)]
    names = {"d1": "Tecnologia", "d2": "Comercial"}
    out = summarize_headcount_plan(
        headcounts=hcs, dept_name_by_id=names, open_by_dept_norm={}, year=2024
    )
    data = out["data"]
    assert data["total_planned"] == 6
    tec = next(d for d in data["departments"] if d["department"] == "Tecnologia")
    assert tec["planned"] == 5
    assert tec["positions"] == 2


def test_gap_against_open_vacancies():
    hcs = [_hc("d1", 5)]
    names = {"d1": "Tecnologia"}
    out = summarize_headcount_plan(
        headcounts=hcs, dept_name_by_id=names,
        open_by_dept_norm={"tecnologia": 2}, year=2024,
    )
    data = out["data"]
    tec = data["departments"][0]
    assert tec["open_vacancies"] == 2
    assert tec["gap"] == 3
    assert data["total_gap"] == 3
    assert "faltam 3" in out["message"]


def test_open_unavailable_does_not_fabricate():
    hcs = [_hc("d1", 5)]
    names = {"d1": "Tecnologia"}
    out = summarize_headcount_plan(
        headcounts=hcs, dept_name_by_id=names, open_by_dept_norm=None, year=2024
    )
    data = out["data"]
    assert data["open_vacancies_available"] is False
    assert data["total_gap"] is None
    assert data["departments"][0]["gap"] is None
    assert "faltam" not in out["message"].lower()


def test_unassigned_department_has_no_gap():
    hcs = [_hc(None, 4)]
    out = summarize_headcount_plan(
        headcounts=hcs, dept_name_by_id={},
        open_by_dept_norm={"qualquer": 1}, year=2024,
    )
    data = out["data"]
    bucket = data["departments"][0]
    assert bucket["department"] == UNASSIGNED_LABEL
    assert bucket["planned"] == 4
    assert bucket["gap"] is None
    assert data["total_planned"] == 4


def test_department_name_normalization_matches_open_key():
    hcs = [_hc("d1", 3)]
    names = {"d1": "  Tecnologia  "}
    out = summarize_headcount_plan(
        headcounts=hcs, dept_name_by_id=names,
        open_by_dept_norm={"tecnologia": 1}, year=2024,
    )
    assert out["data"]["departments"][0]["gap"] == 2
