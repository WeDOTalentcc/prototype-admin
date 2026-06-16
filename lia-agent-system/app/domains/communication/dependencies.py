from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.domains.communication.repositories.communication_repository import (
    CommunicationRepository,
)


def get_communication_repo(
    db: AsyncSession = Depends(get_tenant_db),
) -> CommunicationRepository:
    return CommunicationRepository(db)

from app.domains.communication.repositories.email_repository import EmailRepository


def get_email_repo(
    db: AsyncSession = Depends(get_tenant_db),
) -> EmailRepository:
    return EmailRepository(db)


from app.domains.communication.services.communication_service import CommunicationService, communication_service as _comm_singleton

def get_communication_service() -> CommunicationService:
    return _comm_singleton

from app.domains.communication.services.email_service import (
    EmailService as _EmailService,
    MailgunEmailService as _MailgunEmailService,
    get_email_service,
    get_mailgun_email_service,
)
