"""
Teams Repository — data access layer for Microsoft Teams webhooks and conversations.
Extracted from app/api/v1/teams.py as part of Phase 2 refactor.
"""
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.teams import TeamsActionAuditLog, TeamsConversation, TeamsMessage

logger = logging.getLogger(__name__)


class TeamsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_conversation_by_teams_id(self, teams_conversation_id: str) -> TeamsConversation | None:
        result = await self.db.execute(
            select(TeamsConversation).where(
                TeamsConversation.teams_conversation_id == teams_conversation_id
            )
        )
        return result.scalar_one_or_none()

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

    async def save_message(self, data: dict) -> TeamsMessage:
        msg = TeamsMessage(**data)
        self.db.add(msg)
        await self.db.flush()
        return msg

    async def log_action(self, data: dict) -> TeamsActionAuditLog:
        log = TeamsActionAuditLog(**data)
        self.db.add(log)
        await self.db.flush()
        return log

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
