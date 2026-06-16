"""WorkforceRepository — multi-tenant safe.

Onda 4.2a-P0.3 (2026-05-23): get_hiring_plan/get_hiring_plan_with_details/
get_headcount aceitam company_id opcional pra cross-tenant guard
(audit Hub Minha Empresa LGPD).

ADR-001 T9 (2026-06-09): added 3 analytical query methods extracted from
workforce_planning_tools.py (talent_intelligence domain). Raw SQL for
aggregations (COUNT/SUM/AVG/EXTRACT epoch) lives here in the repository layer
— the canonical place per ADR-001 — using sqlalchemy.text() which is
permitted in repositories. The tools/ file previously carried ADR-001-EXEMPT
markers; those are now replaced by proper repo delegation.
"""
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import bindparam, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.workforce import HiringPlan, ImportJob, PlannedHeadcount, WorkforceEntry

# Default lookback for historical hire metrics (6 months)
_DEFAULT_LOOKBACK_DAYS = 180

# Default benchmark for avg time-to-fill when no data available
_DEFAULT_AVG_TIME_TO_FILL_DAYS = 45.0

# Source tags that identify internal employees / colaboradores
_INTERNAL_CANDIDATE_SOURCES = ("internal", "employee", "colaborador")


class WorkforceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Multi-tenancy guard (ADR-001 canonical)
    # ------------------------------------------------------------------

    @staticmethod
    def _require_company_id(company_id: str | None) -> None:
        """Fail-closed multi-tenancy invariant.

        Must be called as the first line of every public method that touches
        tenant data (ADR-001 + CLAUDE.md REGRA 1).
        """
        if not company_id:
            raise ValueError(
                "company_id is required for WorkforceRepository operations "
                "(multi-tenancy invariant, ADR-001 T9)"
            )

    # ------------------------------------------------------------------
    # Workforce forecasting analytics (ADR-001 T9 — extracted from tools/)
    # ------------------------------------------------------------------

    async def get_open_jobs_summary(
        self,
        company_id: str,
        department: str | None = None,
    ) -> dict[str, int]:
        """Return aggregate counts of open job vacancies for the tenant.

        Returns a dict:
            open_positions  — total non-cancelled/non-closed vacancies
            active_count    — vacancies with status = 'Ativa'
            pipeline_count  — vacancies with status in ('Pausada', 'Em Aprovação')

        Multi-tenancy: company_id is REQUIRED (fail-closed).
        """
        self._require_company_id(company_id)

        dept_filter = "AND department = :dept" if department else ""
        params: dict[str, Any] = {"cid": company_id}
        if department:
            params["dept"] = department

        sql = text(f"""
            SELECT
                COUNT(*) AS open_positions,
                COALESCE(SUM(CASE WHEN status = 'Ativa' THEN 1 ELSE 0 END), 0) AS active_count,
                COALESCE(SUM(CASE WHEN status IN ('Pausada', 'Em Aprovação') THEN 1 ELSE 0 END), 0) AS pipeline_count
            FROM job_vacancies
            WHERE company_id = :cid
              AND status NOT IN ('Cancelada', 'Fechada')
              {dept_filter}
        """)
        result = await self.db.execute(sql, params)
        row = result.mappings().first() or {}
        return {
            "open_positions": int(row.get("open_positions") or 0),
            "active_count": int(row.get("active_count") or 0),
            "pipeline_count": int(row.get("pipeline_count") or 0),
        }

    async def get_historical_hire_metrics(
        self,
        company_id: str,
        lookback_days: int = _DEFAULT_LOOKBACK_DAYS,
        department: str | None = None,
    ) -> dict[str, float]:
        """Return historical hiring metrics (closed vacancies) for the tenant.

        Returns a dict:
            total_hires       — count of vacancies closed within lookback window
            avg_time_to_fill  — average days from created_at to updated_at (closed);
                                defaults to 45.0 (industry benchmark) when no data.

        Multi-tenancy: company_id is REQUIRED (fail-closed).
        """
        self._require_company_id(company_id)

        dept_filter = "AND department = :dept" if department else ""
        lookback_dt = datetime.utcnow() - timedelta(days=lookback_days)
        params: dict[str, Any] = {"cid": company_id, "lookback": lookback_dt}
        if department:
            params["dept"] = department

        sql = text(f"""
            SELECT
                COUNT(*) AS total_hires,
                COALESCE(
                    AVG(EXTRACT(EPOCH FROM (updated_at - created_at)) / 86400),
                    :default_ttf
                ) AS avg_time_to_fill
            FROM job_vacancies
            WHERE company_id = :cid
              AND status = 'Fechada'
              AND updated_at >= :lookback
              {dept_filter}
        """)
        params["default_ttf"] = _DEFAULT_AVG_TIME_TO_FILL_DAYS
        result = await self.db.execute(sql, params)
        row = result.mappings().first() or {}
        return {
            "total_hires": int(row.get("total_hires") or 0),
            "avg_time_to_fill": float(row.get("avg_time_to_fill") or _DEFAULT_AVG_TIME_TO_FILL_DAYS),
        }

    async def get_internal_employee_count(
        self,
        company_id: str,
        department: str | None = None,
    ) -> int:
        """Return count of active internal employees / colaboradores for the tenant.

        Counts rows in the candidates table where source is one of the canonical
        internal tags: 'internal', 'employee', 'colaborador'.

        Multi-tenancy: company_id is REQUIRED (fail-closed).
        """
        self._require_company_id(company_id)

        dept_filter = "AND department = :dept" if department else ""
        params: dict[str, Any] = {"cid": company_id, "sources": list(_INTERNAL_CANDIDATE_SOURCES)}
        if department:
            params["dept"] = department

        sql = text(f"""
            SELECT COUNT(*) AS total_employees
            FROM candidates
            WHERE company_id = :cid
              AND is_active = true
              AND source IN :sources
              {dept_filter}
        """)
        result = await self.db.execute(
            sql.bindparams(bindparam("sources", expanding=True)), params
        )
        row = result.mappings().first() or {}
        return int(row.get("total_employees") or 0)

    # ------------------------------------------------------------------
    # Hiring Plans
    # ------------------------------------------------------------------

    async def list_hiring_plans(
        self,
        company_id=None,
        fiscal_year=None,
        status=None,
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> list[HiringPlan]:
        query = select(HiringPlan)
        if company_id:
            query = query.where(HiringPlan.company_id == company_id)
        if fiscal_year:
            query = query.where(HiringPlan.fiscal_year == fiscal_year)
        if status:
            query = query.where(HiringPlan.status == status)
        if not include_inactive:
            query = query.where(HiringPlan.is_active == True)
        query = query.order_by(HiringPlan.fiscal_year.desc(), HiringPlan.created_at.desc())
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_hiring_plan(self, data: dict) -> HiringPlan:
        plan = HiringPlan(**data)
        self.db.add(plan)
        await self.db.commit()
        await self.db.refresh(plan)
        return plan

    async def get_hiring_plan_with_details(
        self,
        plan_id,
        company_id=None,
    ) -> HiringPlan | None:
        """Onda 4.2a-P0.3 (2026-05-23): adicionado company_id pra cross-tenant
        guard. Quando passado, filtra por HiringPlan.company_id == company_id.
        """
        query = (
            select(HiringPlan)
            .options(
                selectinload(HiringPlan.planned_headcounts),
                selectinload(HiringPlan.import_jobs),
            )
            .where(HiringPlan.id == plan_id)
        )
        if company_id:
            query = query.where(HiringPlan.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_hiring_plan(
        self,
        plan_id,
        company_id=None,
    ) -> HiringPlan | None:
        """Onda 4.2a-P0.3 (2026-05-23): adicionado company_id pra cross-tenant
        guard. Quando passado, filtra por HiringPlan.company_id.
        """
        query = select(HiringPlan).where(HiringPlan.id == plan_id)
        if company_id:
            query = query.where(HiringPlan.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_hiring_plan(self, plan: HiringPlan, update_data: dict) -> HiringPlan:
        for field, value in update_data.items():
            setattr(plan, field, value)
        plan.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(plan)
        return plan

    async def soft_delete_hiring_plan(self, plan: HiringPlan) -> None:
        plan.is_active = False
        plan.updated_at = datetime.utcnow()
        await self.db.commit()

    # ------------------------------------------------------------------
    # Planned Headcounts
    # ------------------------------------------------------------------

    async def list_plan_headcounts(
        self,
        plan_id,
        status=None,
        priority=None,
        department_id=None,
        target_month=None,
        target_year=None,
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> list[PlannedHeadcount]:
        query = select(PlannedHeadcount).where(PlannedHeadcount.hiring_plan_id == plan_id)
        if status:
            query = query.where(PlannedHeadcount.status == status)
        if priority:
            query = query.where(PlannedHeadcount.priority == priority)
        if department_id:
            query = query.where(PlannedHeadcount.department_id == department_id)
        if target_month:
            query = query.where(PlannedHeadcount.target_month == target_month)
        if target_year:
            query = query.where(PlannedHeadcount.target_year == target_year)
        if not include_inactive:
            query = query.where(PlannedHeadcount.is_active == True)
        query = query.order_by(
            PlannedHeadcount.target_year,
            PlannedHeadcount.target_month,
            PlannedHeadcount.priority.desc(),
        )
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_headcount(self, headcount_data: dict, plan: HiringPlan) -> PlannedHeadcount:
        headcount = PlannedHeadcount(**headcount_data)
        self.db.add(headcount)
        plan.total_headcount = (plan.total_headcount or 0) + (headcount.headcount or 1)
        plan.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(headcount)
        return headcount

    async def create_headcounts_bulk(
        self, headcounts_data: list[dict], plan: HiringPlan
    ) -> list[PlannedHeadcount]:
        created = []
        total_new = 0
        for hc_data in headcounts_data:
            hc = PlannedHeadcount(**hc_data)
            self.db.add(hc)
            created.append(hc)
            total_new += hc.headcount or 1
        plan.total_headcount = (plan.total_headcount or 0) + total_new
        plan.updated_at = datetime.utcnow()
        await self.db.commit()
        for hc in created:
            await self.db.refresh(hc)
        return created

    async def get_headcount(
        self,
        headcount_id,
        company_id=None,
    ) -> PlannedHeadcount | None:
        """Onda 4.2a-P0.3 (2026-05-23): adicionado company_id pra cross-tenant
        guard. PlannedHeadcount não tem company_id direto — JOIN com HiringPlan
        e filtra por HiringPlan.company_id == company_id.
        """
        query = select(PlannedHeadcount).where(PlannedHeadcount.id == headcount_id)
        if company_id:
            query = query.join(HiringPlan, HiringPlan.id == PlannedHeadcount.hiring_plan_id).where(
                HiringPlan.company_id == company_id
            )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_headcount(
        self, headcount: PlannedHeadcount, update_data: dict
    ) -> PlannedHeadcount:
        old_value = headcount.headcount or 1
        for field, value in update_data.items():
            setattr(headcount, field, value)
        headcount.updated_at = datetime.utcnow()
        if headcount in update_data:
            new_value = update_data[headcount] or 1
            plan_result = await self.db.execute(
                select(HiringPlan).where(HiringPlan.id == headcount.hiring_plan_id)
            )
            plan = plan_result.scalar_one_or_none()
            if plan:
                plan.total_headcount = (plan.total_headcount or 0) - old_value + new_value
                plan.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(headcount)
        return headcount

    async def soft_delete_headcount(self, headcount: PlannedHeadcount) -> None:
        headcount.is_active = False
        headcount.updated_at = datetime.utcnow()
        plan_result = await self.db.execute(
            select(HiringPlan).where(HiringPlan.id == headcount.hiring_plan_id)
        )
        plan = plan_result.scalar_one_or_none()
        if plan:
            plan.total_headcount = max(0, (plan.total_headcount or 0) - (headcount.headcount or 1))
            plan.updated_at = datetime.utcnow()
        await self.db.commit()

    # ------------------------------------------------------------------
    # Import Jobs
    # ------------------------------------------------------------------

    async def create_import_job(self, data: dict) -> ImportJob:
        import_job = ImportJob(**data)
        self.db.add(import_job)
        await self.db.commit()
        await self.db.refresh(import_job)
        return import_job

    async def get_import_job(self, job_id, plan_id) -> ImportJob | None:
        result = await self.db.execute(
            select(ImportJob).where(
                ImportJob.id == job_id,
                ImportJob.hiring_plan_id == plan_id,
            )
        )
        return result.scalar_one_or_none()

    async def confirm_import_job(self, import_job: ImportJob, column_mapping: dict) -> ImportJob:
        import_job.column_mapping = column_mapping
        import_job.status = "completed"
        import_job.updated_at = datetime.utcnow()
        await self.db.commit()
        return import_job

    # ------------------------------------------------------------------
    # Stats helpers
    # ------------------------------------------------------------------

    async def get_plan_for_stats(self, company_id=None, fiscal_year=None, plan_id=None) -> HiringPlan | None:
        query = select(HiringPlan).where(HiringPlan.is_active == True)
        if company_id:
            query = query.where(HiringPlan.company_id == company_id)
        if fiscal_year:
            query = query.where(HiringPlan.fiscal_year == fiscal_year)
        if plan_id:
            query = query.where(HiringPlan.id == plan_id)
        result = await self.db.execute(query.limit(1))
        return result.scalar_one_or_none()

    async def get_active_headcounts_for_plan(self, plan_id) -> list[PlannedHeadcount]:
        result = await self.db.execute(
            select(PlannedHeadcount).where(
                PlannedHeadcount.hiring_plan_id == plan_id,
                PlannedHeadcount.is_active == True,
            )
        )
        return list(result.scalars().all())

    async def get_active_headcounts_filtered(self, company_id=None) -> list[PlannedHeadcount]:
        query = select(PlannedHeadcount).where(
            PlannedHeadcount.is_active == True,
            PlannedHeadcount.status.in_(["planned", "pending", "in_progress"]),
        )
        if company_id:
            query = query.join(HiringPlan).where(HiringPlan.company_id == company_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Workforce Entries
    # ------------------------------------------------------------------

    async def get_workforce_entries(
        self,
        year: int,
        company_id: str,
    ) -> list[WorkforceEntry]:
        self._require_company_id(company_id)
        result = await self.db.execute(
            select(WorkforceEntry)
            .where(
                WorkforceEntry.is_active == True,
                WorkforceEntry.year == year,
                WorkforceEntry.company_id == company_id,
            )
            .order_by(WorkforceEntry.month, WorkforceEntry.department)
        )
        return list(result.scalars().all())

    async def get_workforce_entries_for_year(
        self,
        year: int,
        company_id: str,
    ) -> list[WorkforceEntry]:
        self._require_company_id(company_id)
        result = await self.db.execute(
            select(WorkforceEntry).where(
                WorkforceEntry.year == year,
                WorkforceEntry.company_id == company_id,
            )
        )
        return list(result.scalars().all())

    async def upsert_workforce_entries(
        self,
        year: int,
        entries_data: list[dict],
        company_id: str,
    ) -> list[WorkforceEntry]:
        self._require_company_id(company_id)
        existing_result = await self.db.execute(
            select(WorkforceEntry).where(
                WorkforceEntry.year == year,
                WorkforceEntry.company_id == company_id,
            )
        )
        existing_map: dict[tuple, WorkforceEntry] = {
            (e.month, e.department): e
            for e in existing_result.scalars().all()
        }
        now = datetime.utcnow()
        for ed in entries_data:
            key = (ed["month"], ed["department"])
            existing = existing_map.get(key)
            if existing:
                existing.planned = ed["planned"]
                existing.actual = ed["actual"]
                existing.updated_at = now
            else:
                new_entry = WorkforceEntry(
                    company_id=company_id,
                    year=year,
                    month=ed["month"],
                    department=ed["department"],
                    planned=ed["planned"],
                    actual=ed["actual"],
                    is_active=True,
                )
                self.db.add(new_entry)
        await self.db.commit()
        return await self.get_workforce_entries(year, company_id)

    async def get_workforce_entry(
        self,
        year: int,
        month: str,
        department: str,
        company_id: str,
    ) -> WorkforceEntry | None:
        self._require_company_id(company_id)
        result = await self.db.execute(
            select(WorkforceEntry).where(
                WorkforceEntry.year == year,
                WorkforceEntry.month == month,
                WorkforceEntry.department == department,
                WorkforceEntry.company_id == company_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_workforce_entry(self, data: dict) -> WorkforceEntry:
        self._require_company_id(data.get("company_id"))
        entry = WorkforceEntry(**data)
        self.db.add(entry)
        await self.db.flush()
        return entry

    async def update_workforce_entry(self, entry: WorkforceEntry, planned: int, actual: int, notes: Any) -> None:
        entry.planned = planned
        entry.actual = actual
        entry.notes = notes
        entry.updated_at = datetime.utcnow()

    async def commit(self) -> None:
        await self.db.commit()

    async def rollback(self) -> None:
        await self.db.rollback()
