"""UserRepository - session-in-constructor pattern."""
import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from lia_models.job_vacancy import JobVacancy

logger = logging.getLogger(__name__)


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_company(self, company_id: str, role: str | None = None, is_active: bool | None = True) -> list[User]:
        query = select(User).where(User.company_id == company_id)
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        if role:
            query = query.where(User.role == role)
        query = query.order_by(User.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """
        Look up a user by email using the SHA-256 hash index.

        Uses email_hash for rows written after migration 060.
        Falls back to plaintext email for pre-migration rows (transition period).
        """
        from app.shared.encryption.encrypted_field_mixin import _sha256_hash
        from sqlalchemy import or_
        email_hash = _sha256_hash(email)
        result = await self.db.execute(
            select(User).where(
                or_(
                    User.email_hash == email_hash,
                    User._email_raw == email,  # transition: pre-migration rows with plaintext
                )
            )
        )
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> User:
        user = User(**data)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update(self, user_id: UUID, data: dict) -> User | None:
        user = await self.get_by_id(user_id)
        if not user:
            return None
        for key, value in data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete(self, user_id: UUID) -> bool:
        user = await self.get_by_id(user_id)
        if not user:
            return False
        await self.db.delete(user)
        await self.db.commit()
        return True

    async def count_active_jobs_by_email(self, emails: list[str]) -> dict[str, int]:
        """Return map of email -> active job count."""
        if not emails:
            return {}
        query = select(
            JobVacancy.recruiter_email,
            func.count(JobVacancy.id).label("count"),
        ).where(
            JobVacancy.recruiter_email.in_(emails),
            JobVacancy.status.in_(["Ativa", "Publicada", "Em Andamento"]),
        ).group_by(JobVacancy.recruiter_email)
        result = await self.db.execute(query)
        return {row.recruiter_email: row.count for row in result}
