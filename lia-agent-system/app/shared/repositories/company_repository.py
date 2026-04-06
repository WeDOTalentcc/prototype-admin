"""
Company Repository - Database access for CompanyProfile model.
"""
import logging

from sqlalchemy import select

from app.models.company import CompanyProfile
from app.shared.repositories.sqlalchemy_base import SQLAlchemyRepository

logger = logging.getLogger(__name__)


class CompanyRepository(SQLAlchemyRepository[CompanyProfile]):
    """Repository for CompanyProfile model with domain-specific queries."""
    
    model_class = CompanyProfile
    
    async def get_default(self, db) -> CompanyProfile | None:
        """Get the default company profile."""
        query = select(self.model_class).where(
            self.model_class.is_default
        )
        if hasattr(db, 'execute'):
            result = await db.execute(query)
            return result.scalar_one_or_none()
        return db.query(self.model_class).filter(
            self.model_class.is_default
        ).first()
    
    async def find_by_name(self, db, name: str) -> CompanyProfile | None:
        """Find a company profile by name."""
        query = select(self.model_class).where(
            self.model_class.name == name
        )
        if hasattr(db, 'execute'):
            result = await db.execute(query)
            return result.scalar_one_or_none()
        return db.query(self.model_class).filter(
            self.model_class.name == name
        ).first()
