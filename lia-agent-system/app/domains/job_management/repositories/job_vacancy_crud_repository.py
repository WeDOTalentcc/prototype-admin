from datetime import datetime
from typing import Any, Optional
from uuid import UUID

import uuid as uuid_lib
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_vacancy import JobVacancy


class JobVacancyCRUDRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Search ────────────────────────────────────────────────────────────────

    async def search_count(self, search_filter) -> int:
        count_stmt = select(func.count(JobVacancy.id)).where(search_filter)
        count_result = await self.db.execute(count_stmt)
        return count_result.scalar() or 0

    async def search_vacancies(self, search_filter, offset: int, page_size: int):
        stmt = (
            select(
                JobVacancy.id,
                JobVacancy.job_id,
                JobVacancy.title,
                JobVacancy.status,
                JobVacancy.created_at,
                JobVacancy.description
            )
            .where(search_filter)
            .order_by(JobVacancy.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        return result.all()

    # ── Archetypes ────────────────────────────────────────────────────────────

    async def get_completed_vacancies(self, company_id):
        result = await self.db.execute(
            select(JobVacancy)
            .where(JobVacancy.status == Concluída)
            .where(JobVacancy.company_id == company_id)
            .order_by(JobVacancy.closed_at.desc())
        )
        return result.scalars().all()

    # ── Get one ───────────────────────────────────────────────────────────────

    async def get_vacancy_by_id_and_company(self, job_vacancy_id: UUID, company_id):
        result = await self.db.execute(
            select(JobVacancy).where(
                JobVacancy.id == job_vacancy_id,
                JobVacancy.company_id == company_id
            )
        )
        return result.scalar_one_or_none()

    # ── List ──────────────────────────────────────────────────────────────────

    async def list_vacancies(
        self,
        company_id,
        status: Optional[str] = None,
        visibility: Optional[str] = None,
        skip: int = 0,
        limit: int = 500,
    ):
        query = select(JobVacancy).where(JobVacancy.company_id == company_id)
        if status:
            query = query.where(JobVacancy.status == status)
        if visibility:
            query = query.where(JobVacancy.visibility == visibility)
        query = query.offset(skip).limit(limit).order_by(JobVacancy.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all()

    # ── Create ────────────────────────────────────────────────────────────────

    async def create_vacancy(self, job_vacancy: JobVacancy) -> JobVacancy:
        self.db.add(job_vacancy)
        await self.db.flush()
        await self.db.refresh(job_vacancy)
        return job_vacancy

    # ── Update ────────────────────────────────────────────────────────────────

    async def flush_and_refresh(self, obj) -> Any:
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    # ── Session passthrough (for services that still take db) ────────────────

    def get_session(self) -> AsyncSession:
        return self.db

    async def search_by_query(self, company_id, query: str, offset: int, page_size: int):
        from sqlalchemy import func, select
        from app.models.job_vacancy import JobVacancy
        base_filter = JobVacancy.company_id == company_id
        if query and len(query) >= 2:
            search_term = f"%{query}%"
            search_filter = and_(
                base_filter,
                or_(
                    JobVacancy.title.ilike(search_term),
                    JobVacancy.job_id.ilike(search_term)
                )
            )
        else:
            search_filter = base_filter
        count_result = await self.db.execute(
            select(func.count()).select_from(JobVacancy).where(search_filter)
        )
        total = count_result.scalar() or 0
        rows_result = await self.db.execute(
            select(JobVacancy).where(search_filter)
            .order_by(JobVacancy.created_at.desc())
            .offset(offset).limit(page_size)
        )
        rows = list(rows_result.scalars().all())
        return total, rows


    async def search_for_summary_by_criteria(
        self,
        company_id,
        criteria: dict,
        limit: int = 10,
    ):
        """Search vacancies by sourcing-style criteria dict.

        Used by app/domains/sourcing/services/vacancy_search.py
        (Sprint Q2 ADR-001 cross-domain cleanup). Recognizes keys:
          cargo, gestor, area, senioridade, modelo_trabalho, localizacao, ano

        Returns ORM rows; caller is responsible for shaping VacancySummary.
        """
        from datetime import datetime
        from sqlalchemy import and_, or_, select
        from app.models.job_vacancy import JobVacancy

        valid_statuses = [
            "Concluída", "Fechada", "Filled", "Closed", "Cancelada", "Cancelled",
            "Ativa", "Active", "Open", "Em Andamento", "active", "ativa", "open",
        ]
        conditions = [
            JobVacancy.company_id == company_id,
            JobVacancy.status.in_(valid_statuses),
        ]

        if criteria.get("cargo"):
            conditions.append(JobVacancy.title.ilike(f"%{criteria['cargo']}%"))
        if criteria.get("gestor"):
            conditions.append(JobVacancy.manager.ilike(f"%{criteria['gestor']}%"))
        if criteria.get("area"):
            conditions.append(JobVacancy.department.ilike(f"%{criteria['area']}%"))
        if criteria.get("senioridade"):
            conditions.append(JobVacancy.seniority_level.ilike(f"%{criteria['senioridade']}%"))
        if criteria.get("modelo_trabalho"):
            conditions.append(JobVacancy.work_model.ilike(f"%{criteria['modelo_trabalho']}%"))
        if criteria.get("localizacao"):
            conditions.append(JobVacancy.location.ilike(f"%{criteria['localizacao']}%"))
        if criteria.get("ano"):
            year = int(criteria["ano"])
            year_start = datetime(year, 1, 1)
            year_end = datetime(year, 12, 31, 23, 59, 59)
            conditions.append(
                or_(
                    and_(JobVacancy.closed_at >= year_start, JobVacancy.closed_at <= year_end),
                    and_(JobVacancy.created_at >= year_start, JobVacancy.created_at <= year_end),
                )
            )

        result = await self.db.execute(
            select(JobVacancy)
            .where(and_(*conditions))
            .order_by(JobVacancy.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

