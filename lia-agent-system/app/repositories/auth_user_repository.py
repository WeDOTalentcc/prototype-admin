"""UserRepository - manages User model CRUD for the auth domain."""
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.shared.encryption.encrypted_field_mixin import _sha256_hash

logger = logging.getLogger(__name__)


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """
        Look up a user by email using the SHA-256 hash index.

        Since the email column is nulled after encryption, lookups must use
        email_hash for all rows written after migration 060. Rows written
        before that migration still have plaintext email; the OR clause handles
        that transition period until pii.backfill_encrypt_existing completes.
        """
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

    async def get_by_workos_id(self, workos_id: str) -> User | None:
        result = await self.db.execute(select(User).where(User.workos_id == workos_id))
        return result.scalar_one_or_none()

    async def list_for_company(
        self,
        company_id: str,
        role: str | None = None,
        workos_only: bool = False,
        scim_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[User]:
        query = select(User).where(User.company_id == company_id)
        if role:
            query = query.where(User.role == role)
        if workos_only:
            query = query.where(User.workos_id.isnot(None))
        if scim_only:
            query = query.where(User.is_scim_managed == True)  # noqa: E712
        query = query.order_by(User.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_for_company(
        self,
        company_id: str,
        workos_only: bool = False,
        scim_only: bool = False,
    ) -> int:
        query = select(func.count(User.id)).where(User.company_id == company_id)
        if workos_only:
            query = query.where(User.workos_id.isnot(None))
        if scim_only:
            query = query.where(User.is_scim_managed == True)  # noqa: E712
        result = await self.db.execute(query)
        return result.scalar_one() or 0

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

    async def update_by_instance(self, user: User, data: dict) -> User:
        """Update an already-loaded User instance directly."""
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

    async def update_last_login(self, user_id: UUID) -> None:
        user = await self.get_by_id(user_id)
        if user:
            user.last_sso_login_at = datetime.utcnow()
            user.updated_at = datetime.utcnow()
            await self.db.commit()

    async def get_by_password_reset_token(self, token: str):
        result = await self.db.execute(
            select(User).where(User.password_reset_token == token)
        )
        return result.scalar_one_or_none()

    async def get_by_email_verification_token(self, token: str):
        result = await self.db.execute(
            select(User).where(User.email_verification_token == token)
        )
        return result.scalar_one_or_none()

    async def get_by_invitation_token(self, token: str):
        result = await self.db.execute(
            select(User).where(User.invitation_token == token)
        )
        return result.scalar_one_or_none()

    async def create_flush(self, data: dict):
        user = User(**data)
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user
