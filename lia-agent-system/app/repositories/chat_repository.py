"""
ChatRepository - session-in-constructor pattern.

Encapsulates all DB access for Conversation and Message models
previously scattered across app/api/v1/chat.py.
"""
import logging
import uuid
from typing import Any

from sqlalchemy import desc, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, Message

logger = logging.getLogger(__name__)


class ChatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Conversation helpers
    # ------------------------------------------------------------------

    async def create_conversation(self, user_id: str, company_id: str) -> Conversation:
        """Create new conversation for user under tenant company_id.

        company_id is REQUIRED — conversations table has RLS policy that
        rejects INSERT with NULL company_id (asyncpg.InsufficientPrivilegeError).
        Per CLAUDE.md REGRA 1 multi-tenancy + ADR-001 §3 fail-closed.
        """
        if not company_id:
            raise ValueError(
                "company_id is required (multi-tenancy fail-closed). "
                "conversations table has RLS policy — INSERT without "
                "company_id raises InsufficientPrivilegeError at runtime."
            )
        conversation = Conversation(
            user_id=user_id,
            company_id=company_id,
            user_role="recruiter",
            status="active",
        )
        self.db.add(conversation)
        await self.db.flush()
        return conversation

    async def get_conversation_by_id(
        self,
        conversation_id: str,
        company_id: str | None = None,
    ) -> Conversation | None:
        """Get conversation by id. Multi-tenancy defense-in-depth via
        company_id filter quando passado (REGRA ZERO + harness B.1)."""
        # TENANT-EXEMPT: dynamic builder — Conversation.company_id == company_id
        # é appended conditionally below quando company_id passado.
        query = select(Conversation).where(
            Conversation.id == uuid.UUID(conversation_id)
        )
        if company_id:
            query = query.where(Conversation.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_conversations(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        company_id: str | None = None,
    ) -> tuple[list[Conversation], int]:
        """List conversations for user. Multi-tenancy defense-in-depth via
        company_id filter quando passado (REGRA ZERO + harness B.1)."""
        offset = (page - 1) * page_size

        # TENANT-EXEMPT: dynamic builder — Conversation.company_id == company_id
        # é appended conditionally below quando company_id passado.
        list_query = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .where(not Conversation.is_archived)
        )
        # TENANT-EXEMPT: dynamic builder — Conversation.company_id == company_id
        # é appended conditionally below quando company_id passado.
        count_query = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .where(not Conversation.is_archived)
        )
        if company_id:
            list_query = list_query.where(Conversation.company_id == company_id)
            count_query = count_query.where(Conversation.company_id == company_id)

        list_query = (
            list_query.order_by(desc(Conversation.updated_at))
            .limit(page_size)
            .offset(offset)
        )
        result = await self.db.execute(list_query)
        conversations = list(result.scalars().all())

        count_result = await self.db.execute(count_query)
        total = len(count_result.scalars().all())

        return conversations, total

    async def update_conversation_intent(
        self, conversation: Conversation, intent: str, workflow_data: dict[str, Any]
    ) -> None:
        conversation.intent = intent
        conversation.workflow_data = workflow_data

    async def set_conversation_title(self, conversation: Conversation, title: str) -> None:
        if not conversation.title:
            conversation.title = title

    async def commit_and_refresh(self, *objects) -> None:
        await self.db.commit()
        for obj in objects:
            await self.db.refresh(obj)

    async def commit(self) -> None:
        await self.db.commit()

    # ------------------------------------------------------------------
    # Message helpers
    # ------------------------------------------------------------------

    async def add_user_message(
        self,
        conversation_id: Any,
        content: str,
        message_metadata: dict[str, Any] | None = None,
    ) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            role="user",
            content=content,
            message_metadata=message_metadata or {},
        )
        self.db.add(msg)
        await self.db.flush()
        return msg

    async def add_ai_message(
        self,
        conversation_id: Any,
        content: str,
        message_metadata: dict[str, Any] | None = None,
        prompt_version: str | None = None,
    ) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=content,
            message_metadata=message_metadata or {},
            prompt_version=prompt_version,
        )
        self.db.add(msg)
        return msg


    async def get_last_ai_message(self, conversation_id: Any) -> Message | None:
        """Get the most recent assistant message for a conversation."""
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .where(Message.role == "assistant")
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        return result.scalars().first()

    async def get_recent_messages(
        self, conversation_id: Any, limit: int = 20
    ) -> list[Message]:
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        return list(reversed(result.scalars().all()))

    # ------------------------------------------------------------------
    # Resolution helpers (raw SQL — kept as-is from original functions)
    # ------------------------------------------------------------------

    async def resolve_job_id_by_title(
        self, job_title: str, company_id: str | None = None
    ) -> dict[str, Any] | None:
        try:
            query = text("""
                SELECT id, title, status FROM job_vacancies
                WHERE LOWER(title) LIKE :pattern
                AND company_id = :company_id
                ORDER BY updated_at DESC LIMIT 1
            """)
            result = await self.db.execute(
                query,
                {"pattern": f"%{job_title.lower()}%", "company_id": company_id},
            )
            row = result.fetchone()
            if row:
                return {"id": str(row.id), "title": row.title, "status": row.status}
        except Exception as e:
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.warning(f"Failed to resolve job by title '{job_title}': {e}")
        return None

    async def resolve_candidate_by_name(
        self,
        candidate_name: str,
        company_id: str | None = None,
        job_id: str | None = None,
    ) -> dict[str, Any] | None:
        try:
            conditions = ["LOWER(c.name) LIKE :pattern"]
            bind: dict[str, Any] = {"pattern": f"%{candidate_name.lower()}%"}

            if company_id:
                conditions.append("vc.company_id = CAST(:company_id AS uuid)")
                bind["company_id"] = str(company_id)

            if job_id:
                conditions.append("vc.vacancy_id = CAST(:job_id AS uuid)")
                bind["job_id"] = str(job_id)

            where_clause = " AND ".join(conditions)
            query = text(f"""
                SELECT vc.id, vc.candidate_id, c.name, vc.stage, vc.status
                FROM vacancy_candidates vc
                JOIN candidates c ON c.id = vc.candidate_id
                WHERE {where_clause}
                ORDER BY vc.updated_at DESC LIMIT 1
            """)
            result = await self.db.execute(query, bind)
            row = result.fetchone()
            if row:
                return {
                    "id": str(row.id),
                    "candidate_id": str(row.candidate_id),
                    "name": row.name,
                    "stage": row.stage,
                    "status": row.status,
                }
        except Exception as e:
            # pii-logs ok: [REDACTED] substitui o nome; __name__ é tipo da exceção (não PII)
            logger.warning(f"Failed to resolve candidate by name [REDACTED]: {type(e).__name__}")
        return None

    async def lookup_candidate_id_by_name(self, candidate_name: str) -> str | None:
        """Simple lookup: returns candidate id string or None."""
        result = await self.db.execute(
            text("SELECT id FROM candidates WHERE LOWER(name) LIKE LOWER(:name) LIMIT 1"),
            {"name": f"%{candidate_name}%"},
        )
        row = result.fetchone()
        return str(row[0]) if row else None

    async def check_candidate_ownership(
        self, candidate_id: str, company_id: str
    ) -> bool:
        """Returns True if candidate belongs to company, False otherwise.

        F10 FU-2 fix (2026-05-24): `vacancy_candidates.company_id` is
        `character varying` (not uuid). The CAST(:co AS uuid) raised
        `operator does not exist: character varying = uuid`, falling
        into the broad except in chat.py:1093 which returned 403
        "Unable to verify candidate ownership" for ALL candidate-field
        updates via chat-action (every editable field except `name`,
        which uses the dedicated `/identity` endpoint). Pass `company_id`
        as string to match the actual column type.
        """
        result = await self.db.execute(
            text(
                "SELECT 1 FROM vacancy_candidates "
                "WHERE candidate_id = CAST(:cid AS uuid) "
                "AND company_id = :co LIMIT 1"
            ),
            {"cid": candidate_id, "co": str(company_id)},
        )
        return result.fetchone() is not None
