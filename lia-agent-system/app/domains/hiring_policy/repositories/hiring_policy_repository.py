"""
HiringPolicy Repository — data access layer for company hiring policies.
Extracted from app/api/v1/hiring_policy.py as part of Phase 2 refactor.
"""
import logging
import uuid
from datetime import datetime

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company_hiring_policy import (
    AUTOMATION_RULES_DEFAULTS,
    COMMUNICATION_RULES_DEFAULTS,
    PIPELINE_RULES_DEFAULTS,
    SCHEDULING_RULES_DEFAULTS,
    SCREENING_RULES_DEFAULTS,
    CompanyHiringPolicy,
)

logger = logging.getLogger(__name__)


class HiringPolicyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_company(self, company_id: str) -> CompanyHiringPolicy | None:
        result = await self.db.execute(
            select(CompanyHiringPolicy).where(
                CompanyHiringPolicy.company_id == company_id
            )
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        company_id: str,
        update_data: dict,
        valid_blocks: list[str],
        user_id: str | None = None,
    ) -> CompanyHiringPolicy:
        """Create or merge-update a hiring policy."""
        policy = await self.get_by_company(company_id)
        if policy:
            for key, value in update_data.items():
                if key in valid_blocks:
                    existing = getattr(policy, key) or {}
                    if isinstance(existing, dict) and isinstance(value, dict):
                        # T-1169: criar NOVO dict — Column(JSON) puro não rastreia
                        # mutação in-place. setattr com mesma ref não vira UPDATE.
                        setattr(policy, key, {**existing, **value})
                    else:
                        setattr(policy, key, value)
            policy.updated_by = user_id
            policy.updated_at = datetime.utcnow()
        else:
            policy = CompanyHiringPolicy(
                id=uuid.uuid4(),
                company_id=company_id,
                pipeline_rules=update_data.get("pipeline_rules", PIPELINE_RULES_DEFAULTS.copy()),
                scheduling_rules=update_data.get("scheduling_rules", SCHEDULING_RULES_DEFAULTS.copy()),
                communication_rules=update_data.get("communication_rules", COMMUNICATION_RULES_DEFAULTS.copy()),
                screening_rules=update_data.get("screening_rules", SCREENING_RULES_DEFAULTS.copy()),
                automation_rules=update_data.get("automation_rules", AUTOMATION_RULES_DEFAULTS.copy()),
                pipeline_templates=update_data.get("pipeline_templates", []),
                created_by=user_id,
                updated_by=user_id,
            )
            self.db.add(policy)
        await self.db.flush()
        return policy

    async def create_if_missing(self, company_id: str, user_id: str | None) -> CompanyHiringPolicy:
        policy = await self.get_by_company(company_id)
        if not policy:
            policy = CompanyHiringPolicy(
                id=uuid.uuid4(),
                company_id=company_id,
                created_by=user_id,
            )
            self.db.add(policy)
        return policy

    async def flush(self) -> None:
        await self.db.flush()

    async def update_answered_questions(
        self, policy: CompanyHiringPolicy, answered_field: str
    ) -> CompanyHiringPolicy:
        existing = list(policy.answered_questions or [])
        if answered_field not in existing:
            existing.append(answered_field)
            policy.answered_questions = existing
        await self.db.flush()
        return policy


    async def update_offer_rules(
        self, company_id: str, rules: dict
    ) -> "CompanyHiringPolicy":
        """ADR-001: single-point update for offer_rules JSONB block."""
        policy = await self.get_by_company(company_id)
        if policy is None:
            raise ValueError(f"CompanyHiringPolicy nao encontrada para company_id={company_id}")
        policy.offer_rules = rules
        await self.db.flush()
        return policy

    # ── Conversation persistence (raw SQL to keep parity) ───────────

    async def fetch_conversation_history(
        self, company_id: str, session_id: str, limit: int = 10
    ) -> list[dict]:
        try:
            query = text("""
                SELECT m.role, m.content
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                WHERE c.context_type = 'policy'
                  AND c.context_id = :company_id
                  AND c.session_id = :session_id
                ORDER BY m.created_at DESC
                LIMIT :limit
            """)
            result = await self.db.execute(
                query, {"company_id": company_id, "session_id": session_id, "limit": limit}
            )
            return [{"role": r[0], "content": r[1]} for r in reversed(result.fetchall())]
        except Exception as e:
            logger.warning(f"[HiringPolicyRepo] Failed to fetch history: {e}")
            return []

    async def persist_chat_messages(
        self,
        company_id: str,
        session_id: str,
        user_message: str,
        assistant_reply: str,
        user_id: str | None = None,
    ) -> None:
        try:
            find_conv = text("""
                SELECT id FROM conversations
                WHERE context_type = 'policy'
                  AND context_id = :company_id
                  AND session_id = :session_id
                LIMIT 1
            """)
            row = (
                await self.db.execute(
                    find_conv, {"company_id": company_id, "session_id": session_id}
                )
            ).fetchone()
            if row:
                conv_id = row[0]
            else:
                conv_id = str(uuid.uuid4())
                await self.db.execute(
                    text("""
                        INSERT INTO conversations
                          (id, user_id, context_type, context_id, session_id, status, is_active, created_at, updated_at)
                        VALUES
                          (:id, :user_id, 'policy', :company_id, :session_id, 'active', true, NOW(), NOW())
                    """),
                    {
                        "id": conv_id,
                        "user_id": user_id or "default_user",
                        "company_id": company_id,
                        "session_id": session_id,
                    },
                )
            # RLS-EXEMPT: messages — transitive via conversation (migration 118)
            insert_msg = text("""
                INSERT INTO messages (id, conversation_id, role, content, created_at)
                VALUES (:id, :conv_id, :role, :content, NOW())
            """)
            for role, content in [("user", user_message), ("assistant", assistant_reply)]:
                await self.db.execute(
                    insert_msg,
                    {"id": str(uuid.uuid4()), "conv_id": conv_id, "role": role, "content": content},
                )
            await self.db.flush()
        except Exception as e:
            logger.warning(f"[HiringPolicyRepo] Failed to persist messages: {e}")
