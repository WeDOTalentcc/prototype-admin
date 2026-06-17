"""
Job Repository - Database access for JobVacancy model.
"""
import logging
from typing import Any
from uuid import UUID

from sqlalchemy import or_, select

from app.models.job_vacancy import JobVacancy
from app.shared.repositories.sqlalchemy_base import SQLAlchemyRepository

logger = logging.getLogger(__name__)


class JobRepository(SQLAlchemyRepository[JobVacancy]):
    """Repository for JobVacancy model with domain-specific queries."""
    
    model_class = JobVacancy
    
    async def find_by_company(self, db, company_id: str,
                              status: str | None = None,
                              limit: int = 50, offset: int = 0) -> list[JobVacancy]:
        """Find job vacancies by company, optionally filtered by status."""
        query = select(self.model_class).where(
            self.model_class.company_id == company_id
        )
        if status:
            query = query.where(self.model_class.status == status)
        query = query.order_by(self.model_class.created_at.desc())
        query = query.limit(limit).offset(offset)
        if hasattr(db, 'execute'):
            result = await db.execute(query)
            return list(result.scalars().all())
        return db.query(self.model_class).filter(
            self.model_class.company_id == company_id
        ).limit(limit).offset(offset).all()
    
    async def get_active_jobs(self, db, company_id: str) -> list[JobVacancy]:
        """Get all active job vacancies for a company."""
        query = select(self.model_class).where(
            self.model_class.company_id == company_id,
            self.model_class.status == "Ativa",
        ).order_by(self.model_class.created_at.desc())
        if hasattr(db, 'execute'):
            result = await db.execute(query)
            return list(result.scalars().all())
        return db.query(self.model_class).filter(
            self.model_class.company_id == company_id,
            self.model_class.status == "Ativa",
        ).all()
    
    async def search(self, db, query: str, filters: dict[str, Any] | None = None,
                     limit: int = 50, offset: int = 0) -> list[JobVacancy]:
        """Search job vacancies by title, department, or description."""
        search_pattern = f"%{query}%"
        stmt = select(self.model_class).where(
            or_(
                self.model_class.title.ilike(search_pattern),
                self.model_class.department.ilike(search_pattern),
                self.model_class.description.ilike(search_pattern),
            )
        )
        if filters:
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    stmt = stmt.where(getattr(self.model_class, key) == value)
        stmt = stmt.order_by(self.model_class.created_at.desc())
        stmt = stmt.limit(limit).offset(offset)
        if hasattr(db, 'execute'):
            result = await db.execute(stmt)
            return list(result.scalars().all())
        return db.query(self.model_class).filter(
            self.model_class.title.ilike(search_pattern)
        ).limit(limit).offset(offset).all()
    
    async def update_status(self, db, id: UUID, status: str) -> JobVacancy | None:
        """Update the status of a job vacancy."""
        return await self.update(db, id, {"status": status})
