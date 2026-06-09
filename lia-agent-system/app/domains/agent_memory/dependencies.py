from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.agent_memory_repository import AgentMemoryRepository


def get_agent_memory_repo(db: AsyncSession = Depends(get_tenant_db)) -> AgentMemoryRepository:
    return AgentMemoryRepository(db)
