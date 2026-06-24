"""
Studio Summary API — single endpoint aggregating all 7 funnel service statuses.

Apply to: lia-agent-system/app/api/v1/studio_summary.py
Register: app.include_router(studio_summary_router)

Replaces the 3+ parallel fetches done by StudioJobStatusPanel in the frontend.
Each service status: "active" | "configured" | "attention" | "inactive"
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/studio-summary", tags=["Studio Summary"])


@router.get("")
async def get_studio_summary(
    job_id: str | None = Query(None, description="Filter by specific job vacancy"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Return aggregated funnel health for all 7 Studio services.

    Frontend uses this to render StudioJobStatusPanel and calibration row metrics
    without firing 3+ separate requests.
    """
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        return _empty_summary()

    results = await _aggregate(company_id, job_id, db)
    return results


# ── Aggregator ─────────────────────────────────────────────────────────────

async def _aggregate(company_id: str, job_id: str | None, db: AsyncSession) -> dict[str, Any]:
    services: dict[str, dict] = {
        s: {"status": "inactive", "metric": None}
        for s in ["intake", "alignment", "sourcing", "screening", "calibration", "offer", "nps"]
    }

    try:
        # ── intake: count open job vacancies ──────────────────────────────
        jv_result = await db.execute(
            text("""
                SELECT status, COUNT(*) as cnt
                FROM job_vacancies
                WHERE company_id = :cid
                  AND (:jid IS NULL OR id = :jid)
                  AND status NOT IN ('encerrada', 'cancelada', 'arquivada')
                GROUP BY status
            """),
            {"cid": company_id, "jid": job_id},
        )
        jv_rows = jv_result.fetchall()
        live_statuses = {"publicada", "ao_vivo"}
        draft_statuses = {"rascunho", "enriquecida", "ats_importada", "wsi_config"}
        live_count = sum(r.cnt for r in jv_rows if r.status in live_statuses)
        draft_count = sum(r.cnt for r in jv_rows if r.status in draft_statuses)
        total_jobs = sum(r.cnt for r in jv_rows)
        if live_count > 0:
            services["intake"] = {"status": "active", "metric": f"{total_jobs} vagas"}
        elif draft_count > 0:
            services["intake"] = {"status": "attention", "metric": f"{draft_count} em config"}
        elif total_jobs > 0:
            services["intake"] = {"status": "configured", "metric": f"{total_jobs} vagas"}

    except Exception as e:
        logger.warning("[StudioSummary] intake query failed: %s", e)

    try:
        # ── alignment: any approved alignment for company/job ─────────────
        al_result = await db.execute(
            text("""
                SELECT status, COUNT(*) as cnt
                FROM manager_alignments
                WHERE company_id = :cid
                  AND (:jid IS NULL OR job_vacancy_id = :jid)
                GROUP BY status
            """),
            {"cid": company_id, "jid": job_id},
        )
        al_rows = {r.status: r.cnt for r in al_result.fetchall()}
        if al_rows.get("approved", 0) > 0:
            services["alignment"] = {"status": "active", "metric": None}
        elif al_rows.get("pending", 0) > 0:
            services["alignment"] = {"status": "attention", "metric": "aguardando"}
        elif sum(al_rows.values()) > 0:
            services["alignment"] = {"status": "configured", "metric": None}
    except Exception as e:
        logger.warning("[StudioSummary] alignment query failed: %s", e)

    try:
        # ── sourcing: count active/paused sourcing agents ─────────────────
        sa_result = await db.execute(
            text("""
                SELECT status, COUNT(*) as cnt
                FROM sourcing_agents
                WHERE company_id = :cid
                  AND (:jid IS NULL OR job_id = :jid)
                  AND status != 'archived'
                GROUP BY status
            """),
            {"cid": company_id, "jid": job_id},
        )
        sa_rows = {r.status: r.cnt for r in sa_result.fetchall()}
        active_agents = sa_rows.get("active", 0)
        total_agents = sum(sa_rows.values())
        if active_agents > 0:
            services["sourcing"] = {"status": "active", "metric": f"{active_agents} ativos"}
        elif total_agents > 0:
            services["sourcing"] = {"status": "configured", "metric": f"{total_agents} agentes"}
    except Exception as e:
        logger.warning("[StudioSummary] sourcing query failed: %s", e)

    try:
        # ── screening: check WSI config on job vacancies ──────────────────
        ws_result = await db.execute(
            text("""
                SELECT COUNT(*) as cnt
                FROM job_vacancies
                WHERE company_id = :cid
                  AND (:jid IS NULL OR id = :jid)
                  AND wsi_questions IS NOT NULL
                  AND jsonb_array_length(wsi_questions::jsonb) > 0
            """),
            {"cid": company_id, "jid": job_id},
        )
        ws_count = ws_result.scalar() or 0
        if ws_count > 0:
            services["screening"] = {"status": "configured", "metric": f"{ws_count} vaga(s) com triagem"}
    except Exception as e:
        logger.warning("[StudioSummary] screening query failed: %s", e)

    try:
        # ── calibration: digital twins + accuracy ─────────────────────────
        tw_result = await db.execute(
            text("""
                SELECT COUNT(*) as cnt,
                       AVG(accuracy_pct) as avg_acc,
                       SUM(CASE WHEN accuracy_pct < 60 THEN 1 ELSE 0 END) as low_acc
                FROM digital_twins
                WHERE company_id = :cid
                  AND (:jid IS NULL OR job_vacancy_id = :jid)
                  AND status = 'active'
            """),
            {"cid": company_id, "jid": job_id},
        )
        tw_row = tw_result.fetchone()
        if tw_row and tw_row.cnt and tw_row.cnt > 0:
            avg_acc = round(tw_row.avg_acc) if tw_row.avg_acc else None
            has_low = (tw_row.low_acc or 0) > 0
            metric = f"{avg_acc}% acurácia" if avg_acc is not None else f"{tw_row.cnt} twin(s)"
            services["calibration"] = {
                "status": "attention" if has_low else "active",
                "metric": metric,
            }
    except Exception as e:
        logger.warning("[StudioSummary] calibration query failed: %s", e)

    # offer -- count draft+sent offers for this job (canonical OfferProposal)
    try:
        if job_id:
            from uuid import UUID as _UUID
            from app.domains.offer.repositories.offer_repository import OfferRepository
            offer_repo = OfferRepository(db)
            proposals = await offer_repo.list_by_job(company_id, _UUID(job_id), limit=50)
            accepted = sum(1 for p in proposals if p.status == "accepted")
            sent = sum(1 for p in proposals if p.status == "sent")
            drafts = sum(1 for p in proposals if p.status == "draft")
            total_offers = accepted + sent + drafts
            if accepted > 0:
                services["offer"] = {"status": "active", "metric": f"{accepted} aceita" + ("" if accepted == 1 else "s")}
            elif sent > 0:
                services["offer"] = {"status": "configured", "metric": f"{sent} enviada" + ("" if sent == 1 else "s")}
            elif total_offers > 0:
                services["offer"] = {"status": "configured", "metric": f"{total_offers} rascunho" + ("" if total_offers == 1 else "s")}
    except Exception as e:
        logger.warning("[StudioSummary] offer query failed: %s", e)

    # nps — avg score + response rate for this job
    try:
        from app.repositories.hiring_nps_repository import HiringNpsRepository
        nps_repo = HiringNpsRepository(db)
        nps_counts = await nps_repo.count_by_status(company_id, job_vacancy_id=job_id)
        total_nps = sum(nps_counts.values())
        responded = nps_counts.get("responded", 0)
        if responded > 0:
            avg = await nps_repo.avg_score_for_job(company_id, job_id or "")
            metric = f"{avg}/10" if avg is not None else f"{responded} resp."
            services["nps"] = {"status": "active", "metric": metric}
        elif total_nps > 0:
            services["nps"] = {"status": "configured", "metric": f"{total_nps} enviada{'' if total_nps == 1 else 's'}"}
    except Exception as e:
        logger.warning("[StudioSummary] nps query failed: %s", e)

    active_count = sum(1 for s in services.values() if s["status"] in ("active", "configured"))
    return {
        "company_id": company_id,
        "job_id": job_id,
        "services": services,
        "active_service_count": active_count,
    }


def _empty_summary() -> dict:
    return {
        "company_id": None,
        "job_id": None,
        "services": {s: {"status": "inactive", "metric": None} for s in
                     ["intake", "alignment", "sourcing", "screening", "calibration", "offer", "nps"]},
        "active_service_count": 0,
    }
