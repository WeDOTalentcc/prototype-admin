"""
Dependency injection functions for the chat domain repository.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.chat_repository import ChatRepository


def get_chat_repo(db: AsyncSession = Depends(get_tenant_db)) -> ChatRepository:
    return ChatRepository(db)
