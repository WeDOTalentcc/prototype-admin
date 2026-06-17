"""ClientUserRepository - session-in-constructor pattern."""
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.client_account import ClientAccount
from app.models.client_user import ClientUser, ClientUserRole

logger = logging.getLogger(__name__)


class ClientUserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------------------------------------------------------------------------
    # ClientAccount helpers
    # ---------------------------------------------------------------------------

    async def get_client_by_id(self, client_id: UUID) -> ClientAccount | None:
        """Return the ClientAccount for the given UUID if not soft-deleted."""
        query = select(ClientAccount).where(
            and_(
                ClientAccount.id == client_id,
                ClientAccount.is_deleted.is_(False),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # ---------------------------------------------------------------------------
    # ClientUser queries
    # ---------------------------------------------------------------------------

    async def get_by_invitation_token(self, token: str) -> ClientUser | None:
        """Return the user that owns the given invitation token."""
        query = select(ClientUser).where(
            and_(
                ClientUser.invitation_token == token,
                ClientUser.is_deleted.is_(False),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_users(
        self,
        company_id: UUID,
        *,
        status: str | None = None,
        role: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ClientUser]:
        """Return a paginated list of users for a company."""
        conditions = [
            ClientUser.company_id == company_id,
            ClientUser.is_deleted.is_(False),
        ]
        if status:
            conditions.append(ClientUser.status == status)
        if role:
            conditions.append(ClientUser.role == role)
        if search:
            search_term = f"%{search}%"
            conditions.append(
                or_(
                    ClientUser.name.ilike(search_term),
                    ClientUser.email.ilike(search_term),
                )
            )
        query = (
            select(ClientUser)
            .where(and_(*conditions))
            .order_by(ClientUser.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_users(
        self,
        company_id: UUID,
        *,
        status: str | None = None,
        role: str | None = None,
        search: str | None = None,
    ) -> int:
        """Return the total number of users matching the filters."""
        conditions = [
            ClientUser.company_id == company_id,
            ClientUser.is_deleted.is_(False),
        ]
        if status:
            conditions.append(ClientUser.status == status)
        if role:
            conditions.append(ClientUser.role == role)
        if search:
            search_term = f"%{search}%"
            conditions.append(
                or_(
                    ClientUser.name.ilike(search_term),
                    ClientUser.email.ilike(search_term),
                )
            )
        query = select(func.count(ClientUser.id)).where(and_(*conditions))
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_by_id(self, user_id: UUID, company_id: UUID) -> ClientUser | None:
        """Return a user by ID scoped to a company."""
        query = select(ClientUser).where(
            and_(
                ClientUser.id == user_id,
                ClientUser.company_id == company_id,
                ClientUser.is_deleted.is_(False),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str, company_id: UUID) -> ClientUser | None:
        """
        Return an active user with the given email within a company.

        Uses email_hash index for rows written after migration 060.
        Falls back to plaintext email for pre-migration rows (transition period).
        """
        from app.shared.encryption.encrypted_field_mixin import _sha256_hash
        email_hash = _sha256_hash(email)
        query = select(ClientUser).where(
            and_(
                ClientUser.company_id == company_id,
                or_(
                    ClientUser.email_hash == email_hash,
                    ClientUser._email_raw == email,  # transition: pre-migration rows with plaintext
                ),
                ClientUser.is_deleted.is_(False),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def count_active_users(self, company_id: UUID) -> int:
        """Return the count of non-deleted users for a company (used for licence checks)."""
        query = select(func.count(ClientUser.id)).where(
            and_(
                ClientUser.company_id == company_id,
                ClientUser.is_deleted.is_(False),
            )
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    # ---------------------------------------------------------------------------
    # Mutations
    # ---------------------------------------------------------------------------

    def add(self, user: ClientUser) -> None:
        """Add a new ClientUser to the session (caller must flush/commit)."""
        self.db.add(user)

    async def flush(self) -> None:
        """Flush pending changes to obtain IDs without committing."""
        await self.db.flush()

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self.db.commit()

    async def rollback(self) -> None:
        """Roll back the current transaction."""
        await self.db.rollback()

    async def refresh(self, user: ClientUser) -> None:
        """Refresh the user instance from the database."""
        await self.db.refresh(user)

    # ---------------------------------------------------------------------------
    # Audit log
    # ---------------------------------------------------------------------------

    async def log_audit(
        self,
        company_id: str,
        action: str,
        user_email: str,
        performed_by: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Persist an audit log entry; swallows exceptions to avoid disrupting the caller."""
        try:
            audit_log = AuditLog(
                company_id=company_id,
                agent_name="user_management",
                decision_type="user_management",
                action=action,
                decision=action,
                reasoning=[
                    {
                        "action": action,
                        "target_user": user_email,
                        "performed_by": performed_by,
                        "details": details or {},
                    }
                ],
                criteria_used=["user_management_policy"],
                criteria_ignored=[],
            )
            self.db.add(audit_log)
            await self.db.flush()
            # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
            logger.info(f"Audit log: {action} for user {user_email} by {performed_by}")
        except Exception as exc:
            logger.warning(f"Failed to create audit log: {str(exc)}")
