from __future__ import annotations
from datetime import date, datetime
from typing import Any
import logging

logger = logging.getLogger(__name__)


class ComplianceReporter:
    def __init__(self, db=None):
        self._db = db

    async def generate_report(
        self, company_id: str, from_date: date, to_date: date
    ) -> dict[str, Any]:
        logger.info(
            "[ComplianceReporter] Generating report company=%s %s->%s",
            company_id, from_date, to_date,
        )
        bias = await self._get_bias_summary(company_id, from_date, to_date)
        fairness = await self._get_fairness_summary(company_id, from_date, to_date)
        audit_count = await self._get_audit_log_count(company_id, from_date, to_date)
        consent = await self._get_consent_summary(company_id, from_date, to_date)
        retention = await self._get_retention_status(company_id)
        return {
            "company_id": company_id,
            "period": {"from": from_date.isoformat(), "to": to_date.isoformat()},
            "generated_at": datetime.utcnow().isoformat(),
            "bias_summary": bias,
            "fairness_summary": fairness,
            "audit_log_count": audit_count,
            "consent_summary": consent,
            "retention_status": retention,
        }

    async def _get_bias_summary(
        self, company_id: str, from_date: date, to_date: date
    ) -> dict:
        try:
            from app.domains.integrations_hub.services.rails_adapter import RailsAdapter
            adapter = RailsAdapter()
            snapshots = await adapter.get_bias_audit_snapshot_history(company_id)
            return {"snapshots": snapshots[:5], "source": "rails_adapter"}
        except Exception as exc:
            logger.warning("[ComplianceReporter] bias_summary unavailable: %s", exc)
            return {"snapshots": [], "source": "unavailable", "error": str(exc)}

    async def _get_fairness_summary(
        self, company_id: str, from_date: date, to_date: date
    ) -> dict:
        try:
            if self._db is None:
                return {"violations": 0, "source": "no_db"}
            from sqlalchemy import select, func
            from lia_models.audit_logs import SOXAuditLog
            result = await self._db.execute(
                select(func.count()).select_from(SOXAuditLog)
                .where(SOXAuditLog.client_id == company_id)
                .where(SOXAuditLog.action.ilike("%fairness%"))
            )
            count = result.scalar() or 0
            return {"fairness_events": count, "source": "sox_audit_log"}
        except Exception as exc:
            logger.warning("[ComplianceReporter] fairness_summary unavailable: %s", exc)
            return {"fairness_events": 0, "source": "unavailable"}

    async def _get_audit_log_count(
        self, company_id: str, from_date: date, to_date: date
    ) -> int:
        try:
            if self._db is None:
                return 0
            from sqlalchemy import select, func
            from lia_models.audit_logs import SOXAuditLog
            result = await self._db.execute(
                select(func.count()).select_from(SOXAuditLog)
                .where(SOXAuditLog.client_id == company_id)
            )
            return result.scalar() or 0
        except Exception as exc:
            logger.warning("[ComplianceReporter] audit_log_count unavailable: %s", exc)
            return -1

    async def _get_consent_summary(
        self, company_id: str, from_date: date, to_date: date
    ) -> dict:
        try:
            if self._db is None:
                return {"active": 0, "revoked": 0}
            from sqlalchemy import select, func
            from lia_models.observability import ConsentVersion
            result = await self._db.execute(
                select(func.count()).select_from(ConsentVersion)
            )
            total = result.scalar() or 0
            return {"consent_versions": total, "source": "consent_version_table"}
        except Exception as exc:
            logger.warning("[ComplianceReporter] consent_summary unavailable: %s", exc)
            return {"active": 0, "revoked": 0, "source": "unavailable"}

    async def _get_retention_status(self, company_id: str) -> dict:
        try:
            if self._db is None:
                return {"pending_deletion": 0}
            from sqlalchemy import select, func
            from lia_models.candidate import Candidate
            result = await self._db.execute(
                select(func.count()).select_from(Candidate)
                .where(Candidate.scheduled_deletion_at.isnot(None))
                .where(Candidate.scheduled_deletion_at <= datetime.utcnow())
            )
            overdue = result.scalar() or 0
            return {"pending_deletion": overdue, "source": "candidate_table"}
        except Exception as exc:
            logger.warning("[ComplianceReporter] retention_status unavailable: %s", exc)
            return {"pending_deletion": 0, "source": "unavailable"}
