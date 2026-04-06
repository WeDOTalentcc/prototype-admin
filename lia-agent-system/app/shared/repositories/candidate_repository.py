"""
Candidate Repository - Database access for Candidate model.
"""
import logging
from typing import Any
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.models.candidate import Candidate
from app.shared.repositories.sqlalchemy_base import SQLAlchemyRepository

logger = logging.getLogger(__name__)


class CandidateRepository(SQLAlchemyRepository[Candidate]):
    """Repository for Candidate model with domain-specific queries."""
    
    model_class = Candidate
    
    async def find_by_email(self, db, email: str) -> Candidate | None:
        """Find a candidate by email address."""
        query = select(self.model_class).where(self.model_class.email == email)
        if hasattr(db, 'execute'):
            result = await db.execute(query)
            return result.scalar_one_or_none()
        return db.query(self.model_class).filter(self.model_class.email == email).first()
    
    async def search(self, db, query: str, filters: dict[str, Any] | None = None,
                     limit: int = 50, offset: int = 0) -> list[Candidate]:
        """Search candidates by name, email, current_title, or skills."""
        search_pattern = f"%{query}%"
        stmt = select(self.model_class).where(
            or_(
                self.model_class.name.ilike(search_pattern),
                self.model_class.email.ilike(search_pattern),
                self.model_class.current_title.ilike(search_pattern),
                self.model_class.current_company.ilike(search_pattern),
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
            or_(
                self.model_class.name.ilike(search_pattern),
                self.model_class.email.ilike(search_pattern),
            )
        ).limit(limit).offset(offset).all()
    
    async def get_by_company(self, db, company_id: str,
                             limit: int = 50, offset: int = 0) -> list[Candidate]:
        """Get candidates filtered by source or additional_data company reference."""
        query = select(self.model_class).where(
            self.model_class.source == company_id
        ).order_by(self.model_class.created_at.desc()).limit(limit).offset(offset)
        if hasattr(db, 'execute'):
            result = await db.execute(query)
            return list(result.scalars().all())
        return db.query(self.model_class).filter(
            self.model_class.source == company_id
        ).limit(limit).offset(offset).all()
    
    async def get_with_experiences(self, db, id: UUID) -> Candidate | None:
        """Get candidate with eagerly loaded experiences and education."""
        query = (
            select(self.model_class)
            .options(
                selectinload(self.model_class.experiences),
                selectinload(self.model_class.education_records),
            )
            .where(self.model_class.id == id)
        )
        if hasattr(db, 'execute'):
            result = await db.execute(query)
            return result.scalar_one_or_none()
        return db.query(self.model_class).filter(
            self.model_class.id == id
        ).first()
