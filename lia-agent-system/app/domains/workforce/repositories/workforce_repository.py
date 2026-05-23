"""WorkforceRepository — multi-tenant safe.

Onda 4.2a-P0.3 (2026-05-23): get_hiring_plan/get_hiring_plan_with_details/
get_headcount aceitam company_id opcional pra cross-tenant guard
(audit Hub Minha Empresa LGPD).
"""
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.workforce import HiringPlan, ImportJob, PlannedHeadcount, WorkforceEntry


class WorkforceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

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
        # WT-2022 P0.WORK fix: required tenant scoping (cross-tenant prevention)
        if not company_id:
            raise ValueError("company_id required (WT-2022 P0.WORK)")
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
        # WT-2022 P0.WORK fix: required tenant scoping
        if not company_id:
            raise ValueError("company_id required (WT-2022 P0.WORK)")
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
        # WT-2022 P0.WORK fix: required tenant scoping (cross-tenant prevention)
        if not company_id:
            raise ValueError("company_id required (WT-2022 P0.WORK)")
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
        # WT-2022 P0.WORK fix: required tenant scoping
        if not company_id:
            raise ValueError("company_id required (WT-2022 P0.WORK)")
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
        # WT-2022 P0.WORK fix: caller MUST include company_id in data dict
        if not data.get("company_id"):
            raise ValueError("company_id required in data (WT-2022 P0.WORK)")
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
