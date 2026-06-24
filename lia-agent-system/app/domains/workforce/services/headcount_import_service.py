"""Canonical producer for headcount import (Track B / Fase 2 — anti-fragmentação).

Both ingestion paths — the chat tool `import_workforce_plan` and the CSV import
endpoint `POST /workforce/entries/import` — funnel through
`import_planned_headcounts` so there is ONE place that:
  - maps loose import items (PT/EN keys, chat or spreadsheet) to canonical fields;
  - resolves department NAME → Department FK (normalized match);
  - gets/creates the fiscal-year HiringPlan;
  - writes PlannedHeadcount (Store B = canonical, the store the settings table
    and the chat tool get_workforce_plan_summary read).

Department names that don't match an existing Department are left UNLINKED
(department_id=None) and reported back in `unresolved_departments` — never
auto-created (product decision, Paulo 2026-06-05). This removes the previous
fragmentation where chat imports wrote department_id=None and CSV imports wrote
a parallel, never-rendered WorkforceEntry store.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app.domains.company.repositories.department_repository import (
    DepartmentRepository,
)
from app.repositories.workforce_repository import (
    WorkforceRepository,
)

logger = logging.getLogger(__name__)

_MONTHS = {
    "jan": 1, "janeiro": 1, "january": 1,
    "feb": 2, "fev": 2, "fevereiro": 2, "february": 2,
    "mar": 3, "marco": 3, "março": 3, "march": 3,
    "apr": 4, "abr": 4, "abril": 4, "april": 4,
    "may": 5, "mai": 5, "maio": 5,
    "jun": 6, "junho": 6, "june": 6,
    "jul": 7, "julho": 7, "july": 7,
    "aug": 8, "ago": 8, "agosto": 8, "august": 8,
    "sep": 9, "set": 9, "setembro": 9, "september": 9,
    "oct": 10, "out": 10, "outubro": 10, "october": 10,
    "nov": 11, "novembro": 11, "november": 11,
    "dec": 12, "dez": 12, "dezembro": 12, "december": 12,
}


def _norm(name: str | None) -> str:
    return (name or "").strip().lower()


def _parse_month(value: Any, default: int) -> int:
    if value is None or value == "":
        return default
    try:
        m = int(float(value))
        return m if 1 <= m <= 12 else default
    except (TypeError, ValueError):
        return _MONTHS.get(str(value).strip().lower(), default)


def _to_int(value: Any, default: int) -> int:
    try:
        return int(float(value)) if value not in (None, "") else default
    except (TypeError, ValueError):
        return default


def _to_float(value: Any) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def normalize_headcount_item(item: Any) -> dict[str, Any] | None:
    """Map a loose import item (chat plan_data or CSV row, PT/EN keys) to the
    canonical PlannedHeadcount field shape. Returns None for non-dict rows.
    """
    if not isinstance(item, dict):
        return None

    now = datetime.utcnow()
    title = (
        item.get("position") or item.get("cargo") or item.get("role")
        or item.get("title") or ""
    ).strip()
    department = (
        item.get("department") or item.get("departamento") or ""
    ).strip()
    headcount = _to_int(
        item.get("headcount") or item.get("quantity") or item.get("quantidade"), 1
    )

    target_month = item.get("target_month") or item.get("month") or item.get("mes")
    target_year = item.get("target_year") or item.get("year") or item.get("ano")
    if not (target_month and target_year):
        deadline = item.get("deadline") or item.get("prazo") or ""
        if deadline:
            try:
                d = datetime.fromisoformat(str(deadline)[:10])
                target_month = target_month or d.month
                target_year = target_year or d.year
            except (ValueError, TypeError):
                pass

    return {
        "title": title or "Posição a definir",
        "department": department,
        "headcount": headcount if headcount > 0 else 1,
        "level": item.get("seniority") or item.get("senioridade") or item.get("level"),
        "target_month": _parse_month(target_month, now.month),
        "target_year": _to_int(target_year, now.year),
        "salary_min": _to_float(item.get("salary_min") or item.get("salario_min")),
        "salary_max": _to_float(item.get("salary_max") or item.get("salario_max")),
        "notes": item.get("observations") or item.get("observacoes") or item.get("notes"),
    }


async def import_planned_headcounts(
    *,
    session: Any,
    company_id: str,
    items: list[Any],
    fiscal_year: int | None = None,
    source: str = "import",
) -> dict[str, Any]:
    """Canonical producer: write `items` as PlannedHeadcount (Store B), resolving
    department name→FK. Uses the injected session; relies on the repository's own
    commit semantics. Returns a summary (created + resolved/unresolved depts).
    """
    normalized = [n for n in (normalize_headcount_item(i) for i in items) if n]
    if not normalized:
        return {
            "created": 0,
            "resolved_departments": [],
            "unresolved_departments": [],
            "plan_id": None,
            "fiscal_year": fiscal_year or datetime.utcnow().year,
        }

    fiscal_year = fiscal_year or datetime.utcnow().year
    wf_repo = WorkforceRepository(db=session)
    plans = await wf_repo.list_hiring_plans(
        company_id=company_id, fiscal_year=fiscal_year
    )
    if plans:
        plan = plans[0]
    else:
        plan = await wf_repo.create_hiring_plan(
            {
                "company_id": company_id,
                "fiscal_year": fiscal_year,
                "name": f"Plano {fiscal_year} (LIA)",
                "status": "active",
                "created_by": source,
            }
        )

    dept_repo = DepartmentRepository(session)
    depts = await dept_repo.list_active_for_company(company_id)
    id_by_norm_name = {_norm(d.name): d.id for d in depts}

    resolved: set[str] = set()
    unresolved: set[str] = set()
    created = 0
    for n in normalized:
        dep_name = n["department"]
        dep_id = id_by_norm_name.get(_norm(dep_name)) if dep_name else None
        if dep_name:
            (resolved if dep_id else unresolved).add(dep_name)
        await wf_repo.create_headcount(
            headcount_data={
                "hiring_plan_id": plan.id,
                "department_id": dep_id,
                "title": n["title"],
                "level": n["level"],
                "headcount": n["headcount"],
                "target_month": n["target_month"],
                "target_year": n["target_year"],
                "salary_min": n["salary_min"],
                "salary_max": n["salary_max"],
                "notes": n["notes"],
                "ai_generated": source != "csv_import",
                "status": "planned",
            },
            plan=plan,
        )
        created += 1

    return {
        "created": created,
        "resolved_departments": sorted(resolved),
        "unresolved_departments": sorted(unresolved),
        "plan_id": str(plan.id),
        "fiscal_year": fiscal_year,
    }
