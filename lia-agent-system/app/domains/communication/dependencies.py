from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.communication.repositories.communication_repository import (
    CommunicationRepository,
)


def get_communication_repo(
    db: AsyncSession = Depends(get_db),
) -> CommunicationRepository:
    return CommunicationRepository(db)

from app.domains.communication.repositories.email_repository import EmailRepository


def get_email_repo(
    db: AsyncSession = Depends(get_db),
) -> EmailRepository:
    return EmailRepository(db)
