"""CredentialsAccessLogRepository — ADR-001 canonical repository.

Wave 3 Camada 3 Item 1 — registered 2026-05-22
==============================================

LGPD Art. 37 audit trail. APPEND-ONLY by contract: this repository
only exposes ``log_access`` (insert) and read methods. UPDATE/DELETE
of audit log entries is forbidden in normal app flow (would break the
audit guarantee).

Pattern: session-in-constructor (idem `IntegrationsHubRepository`).
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.credentials_access_log import CredentialsAccessLog

logger = logging.getLogger(__name__)


class CredentialsAccessLogRepository:
    """Repository canonical para credentials_access_logs (LGPD Art. 37).

    Multi-tenancy: cada metodo publico exige ``company_id``. Cross-tenant
    reads ficam barrados pelo gate ``_require_company_id``.
    """

    # Canonical accessor_type values — keep in sync with model docstring.
    VALID_ACCESSOR_TYPES = frozenset(
        {"human_user", "system", "agent", "celery_task"}
    )

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _require_company_id(company_id: str | None) -> str:
        if not company_id:
            raise ValueError(
                "CredentialsAccessLogRepository requires non-empty company_id "
                "(multi-tenancy invariant)"
            )
        return str(company_id)

    async def log_access(
        self,
        *,
        company_id: str,
        integration_connection_id: str | None,
        accessor_user_id: str | None,
        accessor_type: str,
        access_purpose: str,
        client_ip: str | None = None,
        request_id: str | None = None,
    ) -> CredentialsAccessLog:
        """Append one audit entry. Must be called BEFORE the decrypt op.

        Raises
        ------
        ValueError
            If ``company_id`` empty, ``accessor_type`` not canonical,
            or ``access_purpose`` empty.
        """
        company_id = self._require_company_id(company_id)

        if accessor_type not in self.VALID_ACCESSOR_TYPES:
            raise ValueError(
                f"accessor_type must be one of {sorted(self.VALID_ACCESSOR_TYPES)}, "
                f"got {accessor_type!r}"
            )

        if not access_purpose or not access_purpose.strip():
            raise ValueError(
                "access_purpose is REQUIRED — caller must document why "
                "credentials are being decrypted (LGPD Art. 37)."
            )

        entry = CredentialsAccessLog(
            company_id=company_id,
            integration_connection_id=integration_connection_id,
            accessor_user_id=accessor_user_id,
            accessor_type=accessor_type,
            access_purpose=access_purpose.strip()[:200],
            client_ip=(client_ip or None),
            request_id=(request_id or None),
        )
        self.db.add(entry)
        await self.db.flush()  # get PK without committing the surrounding txn

        logger.info(
            "credentials_access_log.created",
            extra={
                "audit_log_id": str(entry.id),
                "company_id": company_id,
                "integration_connection_id": str(integration_connection_id)
                if integration_connection_id
                else None,
                "accessor_type": accessor_type,
                "access_purpose": entry.access_purpose,
                "request_id": request_id,
            },
        )
        return entry

    async def list_for_company(
        self,
        company_id: str,
        *,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CredentialsAccessLog]:
        """Forensic query: all decryption events for tenant in window."""
        company_id = self._require_company_id(company_id)

        filters = [CredentialsAccessLog.company_id == company_id]
        if since is not None:
            filters.append(CredentialsAccessLog.accessed_at >= since)
        if until is not None:
            filters.append(CredentialsAccessLog.accessed_at <= until)

        # TENANT-EXEMPT: dynamic builder — filters[0] is CredentialsAccessLog.company_id == company_id (above); _require_company_id gate aplicado em L122
        query = (
            select(CredentialsAccessLog)
            .where(and_(*filters))
            .order_by(desc(CredentialsAccessLog.accessed_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_for_connection(
        self,
        connection_id: str,
        company_id: str,
        *,
        limit: int = 100,
    ) -> list[CredentialsAccessLog]:
        """Trace: all accesses to a single connection (response-to-leak query)."""
        company_id = self._require_company_id(company_id)
        query = (
            select(CredentialsAccessLog)
            .where(
                and_(
                    CredentialsAccessLog.integration_connection_id == connection_id,
                    CredentialsAccessLog.company_id == company_id,
                )
            )
            .order_by(desc(CredentialsAccessLog.accessed_at))
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
