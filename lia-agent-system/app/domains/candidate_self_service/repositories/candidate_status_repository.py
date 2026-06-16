"""Repository: CandidateSelfServiceRepository — ADR-001 compliant, read-only."""
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class CandidateSelfServiceRepository:
    """Read-only repository for candidate self-service queries.

    All queries enforce candidate_id + vacancy_id + company_id scope.
    No write operations except audit logging.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_candidate_by_phone(
        self, phone: str, company_id: str
    ) -> dict[str, Any] | None:
        """Lookup candidate by phone for WhatsApp routing. ADR-006: no PII in logs."""
        result = await self._session.execute(
            text("""
                SELECT id, account_id
                FROM candidates
                WHERE (mobile_phone = :phone OR phone = :phone)
                  AND account_id = :company_id
                  AND is_deleted IS NOT TRUE
                LIMIT 1
            """),
            {"phone": phone, "company_id": company_id},
        )
        row = result.mappings().first()
        if row:
            logger.info("[CSS Repo] candidate found company_id=%s", company_id)
        return dict(row) if row else None

    async def log_portal_access(
        self,
        candidate_id: str,
        vacancy_id: str,
        company_id: str,
        channel: str,
        tools_called: list[str],
        fairness_triggered: bool,
    ) -> None:
        """Audit log for LGPD compliance — no PII stored, only IDs."""
        await self._session.execute(
            text("""
                INSERT INTO candidate_portal_audit_logs
                  (id, candidate_id, vacancy_id, company_id, channel,
                   tools_called, fairness_triggered, accessed_at)
                VALUES
                  (:id, :candidate_id, :vacancy_id, :company_id, :channel,
                   :tools_called, :fairness_triggered, :accessed_at)
            """),
            {
                "id": str(uuid.uuid4()),
                "candidate_id": candidate_id,
                "vacancy_id": vacancy_id,
                "company_id": company_id,
                "channel": channel,
                "tools_called": ",".join(tools_called),
                "fairness_triggered": fairness_triggered,
                "accessed_at": datetime.now(UTC),
            },
        )
        await self._session.commit()
