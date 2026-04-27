"""
Teams Repository — data access layer for Microsoft Teams webhooks and conversations.
Extracted from app/api/v1/teams.py as part of Phase 2 refactor.
"""
import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.teams import TeamsActionAuditLog, TeamsConversation, TeamsMessage

logger = logging.getLogger(__name__)


class TeamsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── TeamsConversation ────────────────────────────────────────────────

    async def get_conversation_by_conversation_id(
        self, conversation_id: str
    ) -> TeamsConversation | None:
        result = await self.db.execute(
            select(TeamsConversation).where(
                TeamsConversation.conversation_id == conversation_id
            )
        )
        return result.scalar_one_or_none()

    async def get_conversation_by_teams_id(self, teams_conversation_id: str) -> TeamsConversation | None:
        """Legacy alias — uses teams_conversation_id field."""
        result = await self.db.execute(
            select(TeamsConversation).where(
                TeamsConversation.teams_conversation_id == teams_conversation_id
            )
        )
        return result.scalar_one_or_none()

    async def get_conversation_by_user_id(
        self, user_id: str
    ) -> TeamsConversation | None:
        result = await self.db.execute(
            select(TeamsConversation).where(
                TeamsConversation.user_id == user_id,
                TeamsConversation.is_active,
            )
        )
        return result.scalar_one_or_none()

    async def get_conversation_by_aad_object_id(
        self, aad_object_id: str
    ) -> TeamsConversation | None:
        result = await self.db.execute(
            select(TeamsConversation).where(
                TeamsConversation.user_aad_object_id == aad_object_id,
                TeamsConversation.is_active,
            ).limit(1)
        )
        return result.scalar_one_or_none()

    async def upsert_conversation(
        self,
        conversation_id: str,
        service_url: str,
        tenant_id: str | None,
        channel_id: str | None,
        user_id: str,
        user_name: str | None,
        user_aad_object_id: str | None,
        conversation_reference: dict,
        last_message_at: datetime | None,
        company_id: str | None = None,
    ) -> TeamsConversation:
        existing = await self.get_conversation_by_conversation_id(conversation_id)
        if existing:
            existing.last_message_at = last_message_at
            existing.conversation_reference = conversation_reference
            # Backfill company_id on update if it was missing (legacy rows)
            if company_id and not existing.company_id:
                existing.company_id = company_id
            return existing
        conv = TeamsConversation(
            conversation_id=conversation_id,
            service_url=service_url,
            tenant_id=tenant_id,
            channel_id=channel_id,
            user_id=user_id,
            user_name=user_name,
            user_aad_object_id=user_aad_object_id,
            conversation_reference=conversation_reference,
            last_message_at=last_message_at,
            company_id=company_id,
        )
        self.db.add(conv)
        logger.info(f"Stored new Teams conversation: {conversation_id} (company_id={company_id})")
        return conv

    async def create_conversation(self, data: dict) -> TeamsConversation:
        conv = TeamsConversation(**data)
        self.db.add(conv)
        await self.db.flush()
        await self.db.refresh(conv)
        return conv

    async def update_conversation(self, conv: TeamsConversation, data: dict) -> TeamsConversation:
        for key, value in data.items():
            setattr(conv, key, value)
        await self.db.flush()
        return conv

    # ── TeamsMessage ────────────────────────────────────────────────────

    async def get_conversation_for_message(
        self, conversation_id: str
    ) -> TeamsConversation | None:
        return await self.get_conversation_by_conversation_id(conversation_id)

    async def save_message(self, data: dict) -> TeamsMessage:
        msg = TeamsMessage(**data)
        self.db.add(msg)
        await self.db.flush()
        return msg

    async def log_message_from_activity(
        self, activity: dict, teams_conv: TeamsConversation
    ) -> None:
        message = TeamsMessage(
            teams_conversation_id=teams_conv.id,
            activity_id=activity.get("id"),
            message_type=activity.get("type", "message"),
            text=activity.get("text"),
            from_id=activity.get("from", {}).get("id", ""),
            from_name=activity.get("from", {}).get("name"),
            direction="incoming",
            activity_data=activity,
        )
        self.db.add(message)

    # ── TeamsActionAuditLog ─────────────────────────────────────────────

    async def log_action(self, data: dict) -> TeamsActionAuditLog:
        log = TeamsActionAuditLog(**data)
        self.db.add(log)
        await self.db.flush()
        return log

    async def create_audit_log(
        self,
        action: str,
        result: str,
        actor_id: str | None = None,
        actor_name: str | None = None,
        candidate_id: str | None = None,
        vacancy_id: str | None = None,
        company_id: str | None = None,
        details: dict | None = None,
    ) -> str:
        """Create an audit log entry, return its ID."""
        audit_id = str(uuid.uuid4())
        entry = TeamsActionAuditLog(
            id=audit_id,
            action=action,
            actor_id=actor_id,
            actor_name=actor_name,
            candidate_id=candidate_id,
            vacancy_id=vacancy_id,
            company_id=company_id,
            result=result,
            details=details or {},
        )
        self.db.add(entry)
        return audit_id

    async def list_audit_logs(
        self,
        *,
        action: str | None = None,
        candidate_id: str | None = None,
        company_id: str | None = None,
        limit: int = 50,
    ) -> list[TeamsActionAuditLog]:
        """List audit logs with optional filters.

        P0-3 fix (auditoria 2026-04-26): company_id filter is the multi-tenant
        boundary. Caller (endpoint) MUST pass current_user.company_id to avoid
        cross-tenant leak. None is allowed only for admin/diagnostic contexts
        where caller has explicitly opted in.
        """
        query = select(TeamsActionAuditLog)
        if action:
            query = query.where(TeamsActionAuditLog.action == action)
        if candidate_id:
            query = query.where(TeamsActionAuditLog.candidate_id == candidate_id)
        if company_id:
            query = query.where(TeamsActionAuditLog.company_id == company_id)
        query = query.order_by(TeamsActionAuditLog.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_audit_logs(
        self,
        *,
        action: str | None = None,
        candidate_id: str | None = None,
        company_id: str | None = None,
    ) -> int:
        """Count audit logs with optional filters. See list_audit_logs for tenant rules."""
        from sqlalchemy import func
        query = select(func.count(TeamsActionAuditLog.id))
        if action:
            query = query.where(TeamsActionAuditLog.action == action)
        if candidate_id:
            query = query.where(TeamsActionAuditLog.candidate_id == candidate_id)
        if company_id:
            query = query.where(TeamsActionAuditLog.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalar() or 0

    # ── Legacy compat ───────────────────────────────────────────────────

    async def get_conversation_by_candidate(
        self, candidate_id: str, vacancy_id: str | None = None
    ) -> TeamsConversation | None:
        q = select(TeamsConversation).where(
            TeamsConversation.candidate_id == candidate_id
        )
        if vacancy_id:
            q = q.where(TeamsConversation.vacancy_id == vacancy_id)
        result = await self.db.execute(q)
        return result.scalar_one_or_none()

    # ── SSO / Tab auth (teams.py Phase 2) ───────────────────────────────

    async def get_user_by_aad_object_id(self, aad_object_id: str):
        """Look up a User by azure_ad_object_id. Returns User or None."""
        from sqlalchemy import select as _select
        from app.auth.models import User
        result = await self.db.execute(
            _select(User).where(User.azure_ad_object_id == aad_object_id).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_user_by_email_hash_or_raw(self, email: str):
        """Look up a User by email (hash or raw). Returns User or None."""
        from sqlalchemy import or_, select as _select
        from app.auth.models import User
        try:
            from app.shared.encryption.encrypted_field_mixin import _sha256_hash
            result = await self.db.execute(
                _select(User).where(
                    or_(
                        User.email_hash == _sha256_hash(email),
                        User._email_raw == email,
                    )
                ).limit(1)
            )
        except ImportError:
            result = await self.db.execute(
                _select(User).where(User._email_raw == email).limit(1)
            )
        return result.scalar_one_or_none()

    async def backfill_aad_object_id(self, user, aad_object_id: str) -> None:
        """Set azure_ad_object_id on an existing User record."""
        user.azure_ad_object_id = aad_object_id
        self.db.add(user)

    async def get_user_by_platform_id(self, platform_user_id: str):
        """Look up a User by platform UUID (for tab events)."""
        from sqlalchemy import select as _select
        from app.auth.models import User
        result = await self.db.execute(
            _select(User).where(User.id == platform_user_id).limit(1)
        )
        return result.scalar_one_or_none()
