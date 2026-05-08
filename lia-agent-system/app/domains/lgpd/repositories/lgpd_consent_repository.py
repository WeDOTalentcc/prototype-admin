"""LGPDConsent repository — ORM ops for consent_checker_service +
granular_consent_service.

Per ADR-001: services do not run select(Model) inline.
Multi-tenant invariant: company_id required on all reads.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.communication_settings import LGPDConsent


class LGPDConsentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _require_company_id(company_id: str) -> str:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        return str(company_id)

    async def get_for_candidate_purpose(
        self,
        candidate_id: str,
        company_id: str,
        consent_type: str,
    ) -> Optional[LGPDConsent]:
        company_id = self._require_company_id(company_id)
        stmt = select(LGPDConsent).where(
            and_(
                LGPDConsent.candidate_id == candidate_id,
                LGPDConsent.company_id == company_id,
                LGPDConsent.consent_type == consent_type,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_candidate(
        self,
        candidate_id: str,
        company_id: str,
    ) -> list[LGPDConsent]:
        company_id = self._require_company_id(company_id)
        stmt = select(LGPDConsent).where(
            and_(
                LGPDConsent.candidate_id == candidate_id,
                LGPDConsent.company_id == company_id,
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def add(self, consent: LGPDConsent) -> LGPDConsent:
        self.db.add(consent)
        await self.db.flush()
        return consent

    async def list_active_for_candidate(
        self,
        candidate_id: str,
        company_id: str,
    ) -> list[LGPDConsent]:
        """Return consents with consent_given=True for the candidate.

        Used by candidate_channel_selector to map active consents to channels.
        """
        company_id = self._require_company_id(company_id)
        stmt = select(LGPDConsent).where(
            and_(
                LGPDConsent.candidate_id == candidate_id,
                LGPDConsent.company_id == company_id,
                LGPDConsent.consent_given,
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
