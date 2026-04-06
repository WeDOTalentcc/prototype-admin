from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.triagem.repositories.triagem_repository import TriagemRepository


def get_triagem_repo(db: AsyncSession = Depends(get_db)) -> TriagemRepository:
    return TriagemRepository(db)
