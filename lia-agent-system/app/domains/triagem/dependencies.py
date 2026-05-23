"""P2 D (2026-05-23): get_triagem_repo retorna canonical TriagemSessionRepository.

Antes: retornava stub vazio TriagemRepository com apenas self.db.
Agora: retorna canonical com 7 métodos reais. Endpoint usage de `repo.db`
continua funcional (mesma interface).
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.domains.recruitment.repositories.triagem_session_repository import (
    TriagemSessionRepository,
)


def get_triagem_repo(
    db: AsyncSession = Depends(get_tenant_db),
) -> TriagemSessionRepository:
    return TriagemSessionRepository(db)
