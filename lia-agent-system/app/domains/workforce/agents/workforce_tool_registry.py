"""
Workforce Tool Registry — exposes headcount-plan reads to the LIA chat.

Track B (wiring epic): PlannedHeadcount was a ghost feature — imported via the
"Workforce Planning" settings card and the chat import tool, but NO agent ever
read it back. This registry adds a single READ tool so recruiter_copilot can
answer "quantas vagas faltam abrir em <departamento>?" / "qual o plano de
headcount de <ano>?", consistent with the headcount table the recruiter sees.

Canonical source: PlannedHeadcount (via HiringPlan, per fiscal_year) — the same
store the settings table reads/saves (GET /workforce/plans + /headcounts).

Multi-tenancy: company_id is injected from the auth ContextVar by @tool_handler
(NEVER from LLM args). Provenance honesty (CLAUDE.md REGRA 4): if live open-
vacancy data cannot be read, the gap is returned as null + flagged — never
fabricated.

Sensors: tests/unit/test_workforce_plan_summary.py,
         tests/contract/test_workforce_tool_federation.py
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from lia_agents_core.tool_adapter import ToolDefinition, ToolOutput

from app.core.database import AsyncSessionLocal
from app.domains.company.repositories.department_repository import (
    DepartmentRepository,
)
from app.domains.job_management.repositories.job_vacancy_crud_repository import (
    JobVacancyCrudRepository,
)
from app.domains.workforce.repositories.workforce_repository import (
    WorkforceRepository,
)
from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)

UNASSIGNED_LABEL = "Não especificado"


def _norm(name: str | None) -> str:
    return (name or "").strip().lower()


def _build_message(data: dict[str, Any]) -> str:
    year = data["year"]
    if not data["has_plan"]:
        return f"Nenhum planejamento de headcount cadastrado para {year}."
    assigned = [
        d for d in data["departments"] if d["department"] != UNASSIGNED_LABEL
    ]
    base = (
        f"Plano {year}: {data['total_planned']} vaga(s) planejada(s) "
        f"em {len(assigned)} departamento(s)."
    )
    if not data["open_vacancies_available"]:
        return f"{base} Não consegui cruzar com as vagas abertas agora."
    gap = data["total_gap"]
    opened = data["total_open"]
    if gap > 0:
        return f"{base} {opened} já aberta(s) — faltam {gap} abrir."
    if gap == 0:
        return f"{base} Todas as {opened} já foram abertas."
    return f"{base} {opened} aberta(s) — {abs(gap)} acima do planejado."


def summarize_headcount_plan(
    *,
    headcounts: list[dict[str, Any]],
    dept_name_by_id: dict[str, str],
    open_by_dept_norm: dict[str, int] | None,
    year: int,
) -> dict[str, Any]:
    """Pure aggregation: planned headcount per department + gap vs open vacancies.

    `open_by_dept_norm` is None when live open-vacancy data is unavailable; in
    that case gaps are returned as null and flagged (no fabrication).
    """
    open_available = open_by_dept_norm is not None

    by_dept: dict[str, dict[str, int]] = {}
    unassigned_planned = 0
    unassigned_positions = 0
    for h in headcounts:
        cnt = int(h.get("headcount") or 0)
        dep_id = h.get("department_id")
        name = dept_name_by_id.get(dep_id) if dep_id else None
        if not name:
            unassigned_planned += cnt
            unassigned_positions += 1
            continue
        slot = by_dept.setdefault(name, {"planned": 0, "positions": 0})
        slot["planned"] += cnt
        slot["positions"] += 1

    departments: list[dict[str, Any]] = []
    total_planned = unassigned_planned
    total_open = 0
    total_gap = 0
    for name in sorted(by_dept):
        planned = by_dept[name]["planned"]
        positions = by_dept[name]["positions"]
        total_planned += planned
        entry: dict[str, Any] = {
            "department": name,
            "planned": planned,
            "positions": positions,
        }
        if open_available:
            opened = open_by_dept_norm.get(_norm(name), 0)
            gap = planned - opened
            entry["open_vacancies"] = opened
            entry["gap"] = gap
            total_open += opened
            total_gap += gap
        else:
            entry["open_vacancies"] = None
            entry["gap"] = None
        departments.append(entry)

    if unassigned_planned:
        departments.append(
            {
                "department": UNASSIGNED_LABEL,
                "planned": unassigned_planned,
                "positions": unassigned_positions,
                "open_vacancies": None,
                "gap": None,
            }
        )

    data = {
        "year": year,
        "has_plan": total_planned > 0,
        "total_planned": total_planned,
        "total_open": total_open if open_available else None,
        "total_gap": total_gap if open_available else None,
        "open_vacancies_available": open_available,
        "departments": departments,
    }
    return {"success": True, "data": data, "message": _build_message(data)}


@tool_handler("workforce")
async def _wrap_get_workforce_plan_summary(**kwargs: Any) -> dict[str, Any]:
    company_id = kwargs.get("company_id", "")
    year_arg = kwargs.get("year")
    try:
        year = int(year_arg) if year_arg else datetime.utcnow().year
    except (TypeError, ValueError):
        year = datetime.utcnow().year

    logger.info(
        "[workforce_tools] get_workforce_plan_summary: company=%s year=%s",
        company_id,
        year,
    )

    async with AsyncSessionLocal() as db:
        wf_repo = WorkforceRepository(db=db)
        active = await wf_repo.get_active_headcounts_filtered(company_id=company_id)
        headcounts = [
            {
                "department_id": str(h.department_id) if h.department_id else None,
                "headcount": int(h.headcount or 0),
                "title": h.title,
                "target_month": h.target_month,
                "status": h.status,
            }
            for h in active
            if h.target_year == year
        ]

        dept_repo = DepartmentRepository(db)
        depts = await dept_repo.list_active_for_company(company_id)
        dept_name_by_id = {str(d.id): d.name for d in depts}

        # Live open vacancies — degrade honestly (None, not fabricated) on error.
        open_by_dept_norm: dict[str, int] | None
        try:
            job_repo = JobVacancyCrudRepository(db)
            res = await job_repo.list_jobs_with_candidate_count(
                company_id=company_id,
                status="Ativa",
                department="all",
                limit=500,
            )
            open_by_dept_norm = {}
            for job in res.get("jobs", []):
                key = _norm(job.get("department"))
                if key:
                    open_by_dept_norm[key] = open_by_dept_norm.get(key, 0) + 1
        except Exception as exc:  # noqa: BLE001 — honest degrade, never fabricate
            logger.warning("[workforce_tools] open-vacancy read failed: %s", exc)
            open_by_dept_norm = None

    return summarize_headcount_plan(
        headcounts=headcounts,
        dept_name_by_id=dept_name_by_id,
        open_by_dept_norm=open_by_dept_norm,
        year=year,
    )


def get_workforce_tools() -> list[ToolDefinition]:
    return [
        ToolDefinition(
            name="get_workforce_plan_summary",
            description=(
                "Resumo do planejamento de headcount: vagas planejadas por "
                "departamento e, quando disponível, quantas já estão abertas e "
                "quantas faltam abrir. Use quando o recrutador perguntar sobre "
                "plano de contratações, headcount planejado, ou 'quantas vagas "
                "faltam abrir em <departamento>'."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "year": {
                        "type": "integer",
                        "description": "Ano fiscal do plano (padrão: ano atual).",
                    },
                },
                "required": [],
            },
            output_schema=ToolOutput,
            function=_wrap_get_workforce_plan_summary,
        ),
    ]
