"""T-11 B.1.2: CompanyTrainingConsentRepository canonical (ADR-RLHF-001).

Repository pattern (ADR-001) para CompanyTrainingConsent CRUD.
Fail-CLOSED: get_active_consent retorna None se record não-existe (default DENY).
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.company_training_consent import (
    CompanyTrainingConsent,
)


logger = logging.getLogger(__name__)


class CompanyTrainingConsentRepository:
    """Canonical repo CompanyTrainingConsent (T-11 ADR-RLHF-001)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _require_company_id(self, company_id) -> UUID:
        """ADR-001 multi-tenancy fail-closed canonical."""
        if not company_id:
            raise ValueError("company_id required (T-11 B.1.2 fail-closed)")
        if isinstance(company_id, str):
            return UUID(company_id)
        return company_id

    async def get_by_company(
        self, company_id
    ) -> Optional[CompanyTrainingConsent]:
        """Get consent record para company_id. Returns None se nunca opt-in."""
        company_id = self._require_company_id(company_id)
        stmt = select(CompanyTrainingConsent).where(
            CompanyTrainingConsent.company_id == company_id
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def is_active(self, company_id) -> bool:
        """T-11 B.1.3 canonical check — fail-CLOSED.

        Returns True ONLY se:
        - record existe
        - consent_given = True
        - revoked_at IS NULL

        Default = False (LGPD Art. 7: consent must be explicit).
        """
        try:
            company_id = self._require_company_id(company_id)
        except ValueError:
            return False  # fail-CLOSED
        stmt = select(CompanyTrainingConsent.id).where(
            and_(
                CompanyTrainingConsent.company_id == company_id,
                CompanyTrainingConsent.consent_given.is_(True),
                CompanyTrainingConsent.revoked_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar() is not None

    async def grant_consent(
        self,
        company_id,
        *,
        user_id: str,
        consent_text: str,
        consent_source: str = "admin_ui",
        ip_address: Optional[str] = None,
        version: str = "1.0",
    ) -> CompanyTrainingConsent:
        """Grant consent canonical (UPSERT pattern).

        Se record já existe + revoked: clear revoked_at + set granted_at NEW.
        Se record já existe + active: idempotent (no-op + return).
        Se record não existe: INSERT new com consent_given=True.
        """
        company_id = self._require_company_id(company_id)
        existing = await self.get_by_company(company_id)

        now = datetime.utcnow()
        if existing is None:
            # INSERT
            record = CompanyTrainingConsent(
                company_id=company_id,
                consent_given=True,
                granted_at=now,
                version=version,
                legal_basis="LGPD_ART_7_I",
                consent_source=consent_source,
                consent_text=consent_text,
                ip_address=ip_address,
                user_id_granted=user_id,
            )
            self.db.add(record)
            await self.db.flush()
            logger.info(
                "[CompanyTrainingConsent] GRANTED new company_id=%s by user=%s",
                company_id, user_id,
            )
            return record

        # UPDATE existing
        if existing.consent_given and not existing.revoked_at:
            # Idempotent
            logger.info(
                "[CompanyTrainingConsent] GRANT idempotent (already active) company_id=%s",
                company_id,
            )
            return existing

        # Re-grant após revoke: clear revoked_at + new granted_at
        existing.consent_given = True
        existing.granted_at = now
        existing.revoked_at = None
        existing.revoke_reason = None
        existing.user_id_granted = user_id
        existing.consent_source = consent_source
        existing.consent_text = consent_text
        existing.ip_address = ip_address
        existing.version = version
        await self.db.flush()
        logger.info(
            "[CompanyTrainingConsent] RE-GRANTED após revoke company_id=%s by user=%s",
            company_id, user_id,
        )
        return existing

    async def revoke_consent(
        self,
        company_id,
        *,
        user_id: str,
        reason: str,
    ) -> Optional[CompanyTrainingConsent]:
        """Revoke consent canonical (LGPD Art. 18 cascade).

        Sets revoked_at + revoke_reason. consent_given remains True (audit trail).
        Active check (`is_active`) uses revoked_at IS NULL pra determine state.
        """
        company_id = self._require_company_id(company_id)
        existing = await self.get_by_company(company_id)
        if existing is None:
            logger.warning(
                "[CompanyTrainingConsent] REVOKE skipped (no record) company_id=%s",
                company_id,
            )
            return None

        if existing.revoked_at is not None:
            logger.info(
                "[CompanyTrainingConsent] REVOKE idempotent company_id=%s",
                company_id,
            )
            return existing

        existing.revoked_at = datetime.utcnow()
        existing.revoke_reason = reason
        existing.user_id_revoked = user_id
        await self.db.flush()
        logger.info(
            "[CompanyTrainingConsent] REVOKED company_id=%s by user=%s reason=%s",
            company_id, user_id, reason[:100],
        )
        return existing
