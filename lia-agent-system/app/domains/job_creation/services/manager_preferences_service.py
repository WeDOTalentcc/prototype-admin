"""
ManagerPreferencesService — learning loop for job creation per manager.

Stores and applies per-manager preferences derived from previous wizard sessions.
Key: (company_id, manager_email) — best-effort without FK (email may change).

Harness:
  GUIDE: apply_to_state() only fills fields NOT already set by the user.
  SENSOR: idempotency_key prevents double-counting in re-executed LangGraph nodes.
  FAIL-OPEN: apply_to_state() never raises — logs warning and returns empty dict.
  FAIL-CLOSED: record_job_completion() raises on DB failure (learning loop integrity).
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.job_creation.repositories.manager_preferences_repository import (
    ManagerPreferencesRepository,
)
from lia_models.manager_preferences import ManagerPreferences

logger = logging.getLogger(__name__)

QUALITY_FIELDS = ("preferred_seniorities", "preferred_departments", "preferred_work_models")


class ManagerPreferencesService:
    """Load, apply and record manager hiring preferences."""

    # ── Read ─────────────────────────────────────────────────────────────────

    @staticmethod
    async def get_or_create(
        db: AsyncSession,
        company_id: str,
        manager_email: str,
        manager_name: str | None = None,
    ) -> ManagerPreferences:
        """Return existing preferences or create an empty record."""
        repo = ManagerPreferencesRepository(db)
        prefs = await repo.get_by_company_and_email(company_id, manager_email)
        if prefs:
            return prefs

        prefs = ManagerPreferences(
            company_id=company_id,
            manager_email=manager_email,
            manager_name=manager_name,
        )
        db.add(prefs)
        await db.flush()  # get id without full commit
        return prefs

    # ── Apply (GUIDE) ─────────────────────────────────────────────────────────

    @staticmethod
    async def apply_to_state(
        db: AsyncSession,
        company_id: str,
        manager_email: str,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        """Return pre-fill dict with manager's learned preferences.

        FAIL-OPEN: returns {} on any error — wizard must not block on this.
        Only fills fields not already explicit in state.
        """
        try:
            repo = ManagerPreferencesRepository(db)
            prefs = await repo.get_by_company_and_email(company_id, manager_email)
            if not prefs or prefs.jobs_created_count < 1:
                return {}

            suggestions: dict[str, Any] = {}

            # Seniority: pick most-used from preferred_seniorities
            if prefs.preferred_seniorities and not state.get("seniority"):
                suggestions["seniority"] = prefs.preferred_seniorities[0]

            # Department
            if prefs.preferred_departments and not state.get("department"):
                suggestions["department"] = prefs.preferred_departments[0]

            # Work model
            if prefs.preferred_work_models and not state.get("work_model"):
                suggestions["work_model"] = prefs.preferred_work_models[0]

            # Salary percentile
            if prefs.salary_percentile_preference and not state.get("salary_percentile_preference"):
                suggestions["salary_percentile_preference"] = prefs.salary_percentile_preference

            # Screening style
            if prefs.screening_style != "standard" and not state.get("screening_style"):
                suggestions["screening_style"] = prefs.screening_style

            return suggestions

        except Exception as exc:
            logger.warning("apply_to_state failed — returning empty (fail-open): %s", exc)
            return {}

    # ── Record (Learning Loop) ────────────────────────────────────────────────

    @staticmethod
    async def record_job_completion(
        db: AsyncSession,
        company_id: str,
        manager_email: str,
        final_state: dict[str, Any],
        initial_state: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> None:
        """Update manager preferences after a job wizard completes.

        Idempotency: if idempotency_key already stored, skip (LangGraph re-execution guard).
        FAIL-CLOSED: raises on DB failure — caller must handle / rollback.
        """
        if not company_id:
            raise ValueError(
                "company_id obrigatório em record_job_completion — multi-tenancy enforcement"
            )
        prefs = await ManagerPreferencesService.get_or_create(
            db, company_id, manager_email,
            manager_name=final_state.get("manager_name"),
        )

        # Idempotency check — prevents double-counting on re-executed handoff_node
        if idempotency_key and prefs.last_idempotency_key == idempotency_key:
            logger.info("record_job_completion skipped (duplicate idempotency_key=%s)", idempotency_key)
            return

        # ── Update preferences ────────────────────────────────────────────────
        def _add_to_list(col: list | None, val: str | None) -> list:
            if not val:
                return col or []
            lst = list(col or [])
            if val in lst:
                lst.remove(val)
            lst.insert(0, val)  # most-recent first
            return lst[:10]  # cap at 10 entries

        if seniority := final_state.get("seniority"):
            prefs.preferred_seniorities = _add_to_list(prefs.preferred_seniorities, seniority)

        if dept := final_state.get("department"):
            prefs.preferred_departments = _add_to_list(prefs.preferred_departments, dept)

        if wm := final_state.get("work_model"):
            prefs.preferred_work_models = _add_to_list(prefs.preferred_work_models, wm)

        if pct := final_state.get("salary_percentile_preference"):
            prefs.salary_percentile_preference = int(pct)

        if ss := final_state.get("screening_style"):
            prefs.screening_style = ss

        # ── Track corrections (compare initial vs final state) ────────────────
        if initial_state:
            corrections = dict(prefs.corrections_log or {})
            for field in ("seniority", "department", "work_model", "screening_style"):
                init_val = initial_state.get(field)
                final_val = final_state.get(field)
                if init_val and final_val and init_val != final_val:
                    entry = corrections.setdefault(field, {"from": init_val, "to": final_val, "count": 0})
                    entry["to"] = final_val
                    entry["count"] += 1
            prefs.corrections_log = corrections

        prefs.jobs_created_count += 1
        prefs.last_job_created_at = datetime.utcnow()
        prefs.last_idempotency_key = idempotency_key
        prefs.updated_at = datetime.utcnow()

        await db.commit()
        logger.info(
            "manager_preferences updated company=%s email=%s jobs_count=%d",
            company_id, manager_email, prefs.jobs_created_count,
        )
