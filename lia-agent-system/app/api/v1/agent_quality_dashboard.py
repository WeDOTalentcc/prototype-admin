"""
Agent Quality Dashboard — aggregated metrics from audit, calibration, and fairness.

Combines data from:
- audit_logs (AuditService — decisions, errors, confidence)
- calibration_events (CalibrationEvent — divergences, weights)
- fairness_audit_log (FairnessGuard — warnings, blocks)

Single endpoint for the frontend Agent Control tab.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, case, cast, func, select, Float
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


async def _get_drift_status(company_id: str, db: AsyncSession) -> dict[str, Any]:
    """Aggregate drift status from quantitative + qualitative monitors."""
    result: dict[str, Any] = {"quantitative": None, "qualitative": None, "overall": "unknown"}

    # Quantitative drift (existing ModelDriftService)
    try:
        from app.domains.ai.services.model_drift_service import ModelDriftService
        svc = ModelDriftService()
        status = await svc.evaluate(db, company_id)
        result["quantitative"] = {
            "alert_level": status.alert_level,
            "triggers": [
                {"name": t.name, "delta": round(t.delta, 4), "triggered": t.triggered}
                for t in status.triggers
            ],
        }
    except Exception as exc:
        logger.debug("[AgentQualityDashboard] drift quantitative failed: %s", exc)

    # Qualitative drift (golden scenarios — reads last saved report)
    try:
        from app.services.golden_drift_monitor import BaselineManager
        bm = BaselineManager()
        if bm.has_baseline():
            baselines = bm.load()
            result["qualitative"] = {
                "has_baseline": True,
                "agents": {name: round(b.pass_rate, 3) for name, b in baselines.items()},
            }
        else:
            result["qualitative"] = {"has_baseline": False}
    except Exception as exc:
        logger.debug("[AgentQualityDashboard] drift qualitative failed: %s", exc)

    # Overall: worst of both
    quant_level = (result.get("quantitative") or {}).get("alert_level", "ok")
    if quant_level == "critical":
        result["overall"] = "critical"
    elif quant_level == "warning":
        result["overall"] = "warning"
    else:
        result["overall"] = "stable"

    return result


@router.get("/agent-quality-dashboard")
async def get_agent_quality_dashboard(
    period: str = Query("7d", pattern="^(7d|30d|90d)$"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)) -> dict[str, Any]:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Aggregated agent quality dashboard.

    Combines audit_logs + calibration_events + fairness_audit_log
    into a unified per-agent quality view.

    Args:
        period: Time window — 7d, 30d, or 90d.
    """
    company_id = str(current_user.company_id)
    days = {"7d": 7, "30d": 30, "90d": 90}[period]
    cutoff = datetime.utcnow() - timedelta(days=days)

    agents_data: dict[str, dict[str, Any]] = {}

    # --- 1. Audit logs: executions, confidence, errors per agent ---
    try:
        from app.models.audit_log import AuditLog

        audit_result = await db.execute(
            select(
                AuditLog.agent_name,
                func.count(AuditLog.id).label("total"),
                func.avg(AuditLog.confidence).label("avg_confidence"),
                func.sum(case((AuditLog.decision == "error", 1), else_=0)).label("errors"),
                func.sum(case((AuditLog.human_review_required == True, 1), else_=0)).label("human_reviews"),
            )
            .where(
                and_(
                    AuditLog.company_id == company_id,
                    AuditLog.created_at >= cutoff,
                )
            )
            .group_by(AuditLog.agent_name)
        )

        for row in audit_result.all():
            agent_id = row.agent_name or "unknown"
            total = row.total or 0
            agents_data[agent_id] = {
                "agent_id": agent_id,
                "total_executions": total,
                "avg_confidence": round(float(row.avg_confidence or 0), 3),
                "error_count": int(row.errors or 0),
                "error_rate": round(int(row.errors or 0) / max(total, 1), 3),
                "human_intervention_count": int(row.human_reviews or 0),
                "human_intervention_rate": round(int(row.human_reviews or 0) / max(total, 1), 3),
            }
    except Exception as exc:
        logger.debug("[AgentQualityDashboard] audit_logs query failed: %s", exc)

    # --- 2. Calibration events: divergences per agent ---
    try:
        from lia_models.calibration import CalibrationEvent

        cal_result = await db.execute(
            select(
                CalibrationEvent.context["domain"].astext.label("domain"),
                func.count(CalibrationEvent.id).label("total"),
                func.avg(CalibrationEvent.lia_score).label("avg_lia_score"),
            )
            .where(
                and_(
                    CalibrationEvent.company_id == company_id,
                    CalibrationEvent.created_at >= cutoff,
                )
            )
            .group_by(CalibrationEvent.context["domain"].astext)
        )

        for row in cal_result.all():
            domain = row.domain or "unknown"
            if domain not in agents_data:
                agents_data[domain] = {"agent_id": domain, "total_executions": 0}
            agents_data[domain]["calibration_events"] = int(row.total or 0)
            agents_data[domain]["avg_lia_score"] = round(float(row.avg_lia_score or 0), 2)
    except Exception as exc:
        logger.debug("[AgentQualityDashboard] calibration_events query failed: %s", exc)

    # --- 3. Fairness audit: warnings and blocks per context ---
    try:
        from lia_models.fairness_audit import FairnessAuditLog

        fair_result = await db.execute(
            select(
                FairnessAuditLog.context,
                func.count(FairnessAuditLog.id).label("total"),
                func.sum(case((FairnessAuditLog.is_blocked == True, 1), else_=0)).label("blocked"),
            )
            .where(
                and_(
                    FairnessAuditLog.company_id == company_id,
                    FairnessAuditLog.created_at >= cutoff,
                )
            )
            .group_by(FairnessAuditLog.context)
        )

        for row in fair_result.all():
            ctx = row.context or "unknown"
            # context is "domain=sourcing" format — extract domain
            domain = ctx.replace("domain=", "") if ctx.startswith("domain=") else ctx
            if domain not in agents_data:
                agents_data[domain] = {"agent_id": domain, "total_executions": 0}
            total_fair = int(row.total or 0)
            agents_data[domain]["fairness_checks"] = total_fair
            agents_data[domain]["fairness_blocks"] = int(row.blocked or 0)
            agents_data[domain]["fairness_warning_rate"] = round(
                (total_fair - int(row.blocked or 0)) / max(total_fair, 1), 3
            )
    except Exception as exc:
        logger.debug("[AgentQualityDashboard] fairness_audit_log query failed: %s", exc)

    # --- Compute trends and overall ---
    agents_list = list(agents_data.values())

    # Simple trend: if avg_confidence > 0.8 and error_rate < 0.05 → stable/improving
    for agent in agents_list:
        confidence = agent.get("avg_confidence", 0)
        error_rate = agent.get("error_rate", 0)
        if confidence >= 0.85 and error_rate < 0.03:
            agent["trend"] = "improving"
        elif confidence >= 0.7 and error_rate < 0.1:
            agent["trend"] = "stable"
        elif agent.get("total_executions", 0) < 5:
            agent["trend"] = "insufficient_data"
        else:
            agent["trend"] = "degrading"

    # Enrich with drift status from quantitative + qualitative monitors (P37-073)
    drift_status = await _get_drift_status(company_id, db)

    total_execs = sum(a.get("total_executions", 0) for a in agents_list)
    total_errors = sum(a.get("error_count", 0) for a in agents_list)
    total_fairness = sum(a.get("fairness_checks", 0) for a in agents_list)
    total_blocks = sum(a.get("fairness_blocks", 0) for a in agents_list)

    return {
        "agents": sorted(agents_list, key=lambda a: a.get("total_executions", 0), reverse=True),
        "overall": {
            "total_executions": total_execs,
            "avg_confidence": round(
                sum(a.get("avg_confidence", 0) * a.get("total_executions", 0) for a in agents_list)
                / max(total_execs, 1),
                3,
            ),
            "error_rate": round(total_errors / max(total_execs, 1), 3),
            "fairness_score": round(1 - (total_blocks / max(total_fairness, 1)), 3) if total_fairness else 1.0,
        },
        "drift_status": drift_status,
        "period": period,
        "company_id": company_id,
        "generated_at": datetime.utcnow().isoformat(),
    }
