"""
AgentMemory repository — encapsulates all DB access for working memory.
"""
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from lia_agents_core.working_memory import AgentWorkingMemory


class AgentMemoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_memory(self, session_id: str, domain: str, company_id) -> AgentWorkingMemory | None:
        result = await self.db.execute(
            select(AgentWorkingMemory).where(
                AgentWorkingMemory.session_id == session_id,
                AgentWorkingMemory.domain == domain,
                AgentWorkingMemory.company_id == company_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_active_sessions(self, company_id, domain: str | None, limit: int) -> list[AgentWorkingMemory]:
        stmt = (
            select(AgentWorkingMemory)
            .where(AgentWorkingMemory.company_id == company_id)
            .order_by(desc(AgentWorkingMemory.updated_at))
        )
        if domain:
            stmt = stmt.where(AgentWorkingMemory.domain == domain)
        stmt = stmt.limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def commit(self) -> None:
        await self.db.commit()
