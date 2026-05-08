"""
OptoutRepository — data access layer for communication opt-out (unsubscribe) flows.
Extracted from app/api/v1/communication_optout.py as part of Phase 2 refactor.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession


class OptoutRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_existing_optout(
        self,
        company_id: uuid.UUID,
        email: str,
    ):
        """Return existing ConsentEvent revocation for email+company, or None."""
        from app.domains.analytics.models.observability import ConsentEvent

        result = await self.db.execute(
            select(ConsentEvent).where(
                and_(
                    ConsentEvent.company_id == company_id,
                    ConsentEvent.subject_email == email,
                    ConsentEvent.event_type == "revoked",
                    ConsentEvent.channel == "communication_email",
                )
            ).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_active_consent_version_id(
        self,
        company_id: uuid.UUID,
    ):
        """Return the current ConsentVersion id for communication_email, or None."""
        from lia_models.observability import ConsentVersion

        result = await self.db.execute(
            select(ConsentVersion.id).where(
                and_(
                    ConsentVersion.company_id == company_id,
                    ConsentVersion.consent_type == "communication_email",
                    ConsentVersion.is_current,
                )
            ).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_lgpd_consent(
        self,
        *,
        candidate_id: str,
        company_id: str,
        consent_type: str,
    ):
        """Return the LGPDConsent row for (candidate, company, consent_type) or None."""
        from lia_models.communication_settings import LGPDConsent

        result = await self.db.execute(
            select(LGPDConsent).where(
                and_(
                    LGPDConsent.candidate_id == candidate_id,
                    LGPDConsent.company_id == company_id,
                    LGPDConsent.consent_type == consent_type,
                )
            )
        )
        return result.scalar_one_or_none()

    async def create_optout_event(
        self,
        company_id: uuid.UUID,
        consent_version_id,
        email: str,
        ip_address: str | None,
        user_agent: str,
    ):
        """Persist a ConsentEvent with event_type=revoked and return it."""
        from app.domains.analytics.models.observability import ConsentEvent

        now = datetime.utcnow()
        proof_data = f"{email}|{company_id}|revoked|communication_email|{now.isoformat()}"
        proof_hash = hashlib.sha256(proof_data.encode()).hexdigest()

        event = ConsentEvent(
            id=uuid.uuid4(),
            company_id=company_id,
            consent_version_id=consent_version_id,
            subject_email=email,
            subject_identifier=email,
            event_type="revoked",
            consent_given=False,
            ip_address=ip_address,
            user_agent=user_agent[:500],
            device_info={},
            channel="communication_email",
            proof_hash=proof_hash,
            expires_at=None,
        )
        self.db.add(event)
        return event
