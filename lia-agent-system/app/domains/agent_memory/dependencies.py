from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.agent_memory.repositories.agent_memory_repository import AgentMemoryRepository


def get_agent_memory_repo(db: AsyncSession = Depends(get_db)) -> AgentMemoryRepository:
    return AgentMemoryRepository(db)
