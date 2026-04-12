"""
Passive Candidate Nurture — Automated engagement sequences for passive
candidates over time. Different from recruitment campaigns — nurture is
long-term relationship building with candidates not in an active process.
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)

SEQUENCE_TEMPLATES = {
    "tech_talent": {
        "name": "Tech Talent Nurture",
        "steps": [
            {"day": 0, "channel": "email", "type": "welcome", "subject": "Oportunidades em tecnologia na {company}"},
            {"day": 7, "channel": "email", "type": "content", "subject": "Tendências tech que estamos acompanhando"},
            {"day": 21, "channel": "email", "type": "culture", "subject": "Como é trabalhar na {company}"},
            {"day": 45, "channel": "email", "type": "opportunity", "subject": "Novas vagas que combinam com seu perfil"},
            {"day": 90, "channel": "email", "type": "check_in", "subject": "Novidades e oportunidades para você"},
        ],
        "cadence_days": 90,
    },
    "leadership": {
        "name": "Leadership Pipeline Nurture",
        "steps": [
            {"day": 0, "channel": "email", "type": "welcome", "subject": "Liderança e crescimento na {company}"},
            {"day": 14, "channel": "linkedin", "type": "connection", "subject": "Conexão profissional"},
            {"day": 30, "channel": "email", "type": "content", "subject": "Nossos desafios de liderança"},
            {"day": 60, "channel": "email", "type": "opportunity", "subject": "Posições de liderança abertas"},
        ],
        "cadence_days": 120,
    },
    "silver_medalist": {
        "name": "Silver Medalist Re-engagement",
        "steps": [
            {"day": 0, "channel": "email", "type": "appreciation", "subject": "Obrigado por participar do processo"},
            {"day": 30, "channel": "email", "type": "update", "subject": "Novidades da {company}"},
            {"day": 60, "channel": "email", "type": "opportunity", "subject": "Nova oportunidade que combina com você"},
        ],
        "cadence_days": 60,
    },
    "general": {
        "name": "General Talent Nurture",
        "steps": [
            {"day": 0, "channel": "email", "type": "welcome", "subject": "Bem-vindo(a) ao nosso banco de talentos"},
            {"day": 15, "channel": "email", "type": "culture", "subject": "Conheça nossa cultura"},
            {"day": 45, "channel": "email", "type": "opportunity", "subject": "Vagas que podem interessar você"},
            {"day": 90, "channel": "email", "type": "check_in", "subject": "Ainda interessado(a)? Temos novidades"},
        ],
        "cadence_days": 90,
    },
}


@tool_handler("talent_intelligence", module="candidate_nurture")
async def create_nurture_sequence(
    candidate_ids: list[str] | None = None,
    template: str = "general",
    custom_name: str | None = None,
    tags: list[str] | None = None,
    **kwargs,
) -> dict[str, Any]:
    """
    Create a nurture sequence for passive candidates.

    Args:
        candidate_ids: List of candidate UUIDs to enroll
        template: Sequence template (tech_talent, leadership, silver_medalist, general)
        custom_name: Custom name for this sequence
        tags: Tags for segmentation
    """
    company_id = kwargs.get("company_id", "")

    if not candidate_ids:
        return {
            "success": False,
            "data": {},
            "message": "Forneça candidate_ids para criar sequência de nurture.",
        }

    tmpl = SEQUENCE_TEMPLATES.get(template, SEQUENCE_TEMPLATES["general"])
    sequence_id = str(uuid.uuid4())
    now = datetime.utcnow()

    enrolled = []
    for cid in candidate_ids:
        enrolled.append({
            "candidate_id": cid,
            "enrolled_at": now.isoformat(),
            "current_step": 0,
            "status": "active",
            "next_touchpoint": now.isoformat(),
        })

    sequence = {
        "sequence_id": sequence_id,
        "name": custom_name or tmpl["name"],
        "template": template,
        "company_id": company_id,
        "created_at": now.isoformat(),
        "status": "active",
        "tags": tags or [],
        "steps": tmpl["steps"],
        "cadence_days": tmpl["cadence_days"],
        "total_enrolled": len(enrolled),
        "enrolled_candidates": enrolled,
    }

    try:
        import json

        from app.core.database import AsyncSessionLocal
        from sqlalchemy import text

        async with AsyncSessionLocal() as session:
            await session.execute(
                text("""
                    INSERT INTO nurture_sequences
                        (id, name, template, company_id, status, tags, steps,
                         cadence_days, total_enrolled, enrolled_candidates, created_at)
                    VALUES
                        (:id, :name, :template, :cid, :status, :tags, :steps,
                         :cadence, :total, :enrolled, :created)
                    ON CONFLICT (id) DO NOTHING
                """),
                {
                    "id": sequence_id,
                    "name": sequence["name"],
                    "template": template,
                    "cid": company_id,
                    "status": "active",
                    "tags": json.dumps(tags or []),
                    "steps": json.dumps(tmpl["steps"]),
                    "cadence": tmpl["cadence_days"],
                    "total": len(enrolled),
                    "enrolled": json.dumps(enrolled),
                    "created": now,
                },
            )
            await session.commit()
        logger.info(
            f"Persisted nurture sequence {sequence_id} with {len(enrolled)} candidates "
            f"(template={template}, company={company_id})"
        )
    except Exception as e:
        logger.warning(
            f"Could not persist nurture sequence to DB (sequence returned in-memory): {e}"
        )

    return {
        "success": True,
        "data": sequence,
        "message": (
            f"Sequência de nurture '{sequence['name']}' criada com {len(enrolled)} candidato(s). "
            f"Template: {template}, {len(tmpl['steps'])} etapas ao longo de {tmpl['cadence_days']} dias."
        ),
    }


@tool_handler("talent_intelligence", module="candidate_nurture")
async def get_engagement_metrics(
    sequence_id: str | None = None,
    period: str = "month",
    **kwargs,
) -> dict[str, Any]:
    """
    Get engagement metrics for nurture sequences, derived from real
    communication and candidate activity data in the database.

    Args:
        sequence_id: Specific sequence ID (optional — returns aggregate if not specified)
        period: Analysis period (week, month, quarter)
    """
    company_id = kwargs.get("company_id", "")

    period_days = {"week": 7, "month": 30, "quarter": 90}.get(period, 30)

    metrics_data: dict[str, Any] = {
        "total_candidates": 0,
        "active_candidates": 0,
        "contacted_candidates": 0,
        "responded_candidates": 0,
        "emails_sent": 0,
        "emails_opened": 0,
        "emails_clicked": 0,
        "moved_to_interview": 0,
        "hired": 0,
    }
    sequence_candidate_ids: list[str] = []
    try:
        import json

        from app.core.database import AsyncSessionLocal
        from sqlalchemy import text

        cutoff_date = (datetime.utcnow() - timedelta(days=period_days)).isoformat()

        async with AsyncSessionLocal() as session:
            if sequence_id:
                seq_row = await session.execute(
                    text("""
                        SELECT enrolled_candidates FROM nurture_sequences
                        WHERE id = :sid AND company_id = :cid
                    """),
                    {"sid": sequence_id, "cid": company_id},
                )
                seq_data = seq_row.mappings().first()
                if seq_data and seq_data.get("enrolled_candidates"):
                    enrolled_raw = seq_data["enrolled_candidates"]
                    if isinstance(enrolled_raw, str):
                        enrolled_raw = json.loads(enrolled_raw)
                    sequence_candidate_ids = [e["candidate_id"] for e in enrolled_raw if isinstance(e, dict)]

            candidate_filter = ""
            params: dict[str, Any] = {"cid": company_id, "cutoff": cutoff_date}
            if sequence_candidate_ids:
                candidate_filter = "AND id = ANY(:cand_ids)"
                params["cand_ids"] = sequence_candidate_ids

            row = await session.execute(
                text(f"""
                    SELECT
                        COUNT(*) AS total_candidates,
                        COALESCE(SUM(CASE WHEN status = 'Ativo' THEN 1 ELSE 0 END), 0) AS active,
                        COALESCE(SUM(CASE WHEN last_contacted_at IS NOT NULL
                                           AND last_contacted_at >= :cutoff THEN 1 ELSE 0 END), 0) AS contacted,
                        COALESCE(SUM(CASE WHEN last_activity_at IS NOT NULL
                                           AND last_activity_at >= :cutoff
                                           AND last_activity_at > COALESCE(last_contacted_at, '1970-01-01')
                                     THEN 1 ELSE 0 END), 0) AS responded
                    FROM candidates
                    WHERE company_id = :cid AND is_active = true {candidate_filter}
                """),
                params,
            )
            cand_data = row.mappings().first() or {}
            metrics_data["total_candidates"] = int(cand_data.get("total_candidates") or 0)
            metrics_data["active_candidates"] = int(cand_data.get("active") or 0)
            metrics_data["contacted_candidates"] = int(cand_data.get("contacted") or 0)
            metrics_data["responded_candidates"] = int(cand_data.get("responded") or 0)

            comm_row = await session.execute(
                text("""
                    SELECT
                        COUNT(*) AS total_sent,
                        COALESCE(SUM(CASE WHEN opened_at IS NOT NULL THEN 1 ELSE 0 END), 0) AS opened,
                        COALESCE(SUM(CASE WHEN clicked_at IS NOT NULL THEN 1 ELSE 0 END), 0) AS clicked
                    FROM communication_logs
                    WHERE company_id = :cid
                      AND channel = 'email'
                      AND created_at >= :cutoff
                """),
                {"cid": company_id, "cutoff": cutoff_date},
            )
            comm_data = comm_row.mappings().first() or {}
            metrics_data["emails_sent"] = int(comm_data.get("total_sent") or 0)
            metrics_data["emails_opened"] = int(comm_data.get("opened") or 0)
            metrics_data["emails_clicked"] = int(comm_data.get("clicked") or 0)

            pipeline_row = await session.execute(
                text("""
                    SELECT
                        COALESCE(SUM(CASE WHEN cs.stage_name ILIKE '%%entrevista%%'
                                          OR cs.action_behavior = 'INTERVIEW'
                                     THEN 1 ELSE 0 END), 0) AS in_interview,
                        COALESCE(SUM(CASE WHEN cs.stage_name ILIKE '%%contratad%%'
                                          OR cs.action_behavior = 'HIRE'
                                     THEN 1 ELSE 0 END), 0) AS hired
                    FROM candidate_stages cs
                    JOIN candidates c ON c.id = cs.candidate_id
                    WHERE c.company_id = :cid
                      AND cs.moved_at >= :cutoff
                """),
                {"cid": company_id, "cutoff": cutoff_date},
            )
            pipe_data = pipeline_row.mappings().first() or {}
            metrics_data["moved_to_interview"] = int(pipe_data.get("in_interview") or 0)
            metrics_data["hired"] = int(pipe_data.get("hired") or 0)

    except Exception as e:
        logger.warning(f"Could not fetch engagement data from DB: {e}")

    total = max(metrics_data["total_candidates"], 1)
    emails_sent = max(metrics_data["emails_sent"], 1)
    contacted = max(metrics_data["contacted_candidates"], 1)

    email_open_rate = round(metrics_data["emails_opened"] / emails_sent * 100, 1) if metrics_data["emails_sent"] > 0 else 0.0
    email_click_rate = round(metrics_data["emails_clicked"] / emails_sent * 100, 1) if metrics_data["emails_sent"] > 0 else 0.0
    response_rate = round(metrics_data["responded_candidates"] / contacted * 100, 1) if metrics_data["contacted_candidates"] > 0 else 0.0
    nurture_to_interview = round(metrics_data["moved_to_interview"] / total * 100, 1)
    nurture_to_hire = round(metrics_data["hired"] / total * 100, 1)

    overall_engagement = round(
        (metrics_data["responded_candidates"] + metrics_data["emails_clicked"]) / max(total, 1) * 100, 1
    )

    metrics = {
        "period": period,
        "period_days": period_days,
        "sequence_id": sequence_id,
        "data_source": "database",
        "overview": {
            "total_candidates_in_nurture": metrics_data["total_candidates"],
            "active_candidates": metrics_data["active_candidates"],
            "contacted_in_period": metrics_data["contacted_candidates"],
            "responded_in_period": metrics_data["responded_candidates"],
        },
        "engagement_rates": {
            "email_open_rate": email_open_rate,
            "email_click_rate": email_click_rate,
            "response_rate": response_rate,
            "overall_engagement_rate": overall_engagement,
        },
        "conversion": {
            "nurture_to_interview": nurture_to_interview,
            "nurture_to_hire": nurture_to_hire,
        },
        "channel_performance": {
            "email": {
                "sent": metrics_data["emails_sent"],
                "opened": metrics_data["emails_opened"],
                "clicked": metrics_data["emails_clicked"],
            },
        },
        "pipeline_movement": {
            "moved_to_interview": metrics_data["moved_to_interview"],
            "hired": metrics_data["hired"],
        },
    }

    return {
        "success": True,
        "data": metrics,
        "message": (
            f"Métricas de engajamento ({period}): {overall_engagement}% taxa geral de engajamento, "
            f"{email_open_rate}% abertura de emails, {nurture_to_hire}% conversão para contratação. "
            f"Base: {metrics_data['total_candidates']} candidatos."
        ),
    }


@tool_handler("talent_intelligence", module="candidate_nurture")
async def suggest_reengagement(
    days_inactive: int = 30,
    limit: int = 20,
    **kwargs,
) -> dict[str, Any]:
    """
    Suggest candidates for re-engagement based on inactivity period
    and past engagement signals.

    Args:
        days_inactive: Minimum days of inactivity to consider
        limit: Maximum candidates to suggest
    """
    company_id = kwargs.get("company_id", "")
    cutoff = datetime.utcnow() - timedelta(days=days_inactive)

    candidates_to_reengage = []
    try:
        from app.core.database import AsyncSessionLocal
        from sqlalchemy import text

        async with AsyncSessionLocal() as session:
            rows = await session.execute(
                text("""
                    SELECT id, name, email, current_title,
                           technical_skills, lia_score,
                           last_activity_at, last_contacted_at,
                           source, status
                    FROM candidates
                    WHERE company_id = :cid
                      AND is_active = true
                      AND (last_activity_at IS NULL OR last_activity_at < :cutoff)
                      AND (last_contacted_at IS NULL OR last_contacted_at < :cutoff)
                      AND lia_score IS NOT NULL
                      AND lia_score > 0
                    ORDER BY lia_score DESC NULLS LAST
                    LIMIT :lim
                """),
                {"cid": company_id, "cutoff": cutoff, "lim": limit},
            )

            for row in rows.mappings():
                last_activity = row.get("last_activity_at")
                days_since = (datetime.utcnow() - last_activity).days if last_activity else days_inactive + 30

                priority = "high" if (row.get("lia_score") or 0) >= 4.0 else (
                    "medium" if (row.get("lia_score") or 0) >= 3.0 else "low"
                )

                suggested_channel = "email"
                suggested_template = "general"
                if row.get("source") in ("linkedin", "LinkedIn"):
                    suggested_channel = "linkedin"
                    suggested_template = "tech_talent"
                elif (row.get("lia_score") or 0) >= 4.0:
                    suggested_template = "silver_medalist"

                candidates_to_reengage.append({
                    "candidate_id": str(row["id"]),
                    "name": row["name"],
                    "email": row["email"],
                    "current_title": row["current_title"],
                    "skills": (row.get("technical_skills") or [])[:5],
                    "lia_score": row.get("lia_score"),
                    "days_inactive": days_since,
                    "last_activity": last_activity.isoformat() if last_activity else None,
                    "priority": priority,
                    "suggested_channel": suggested_channel,
                    "suggested_template": suggested_template,
                    "suggested_action": (
                        "Recontactar com oportunidade relevante"
                        if priority == "high"
                        else "Enviar conteúdo de marca empregadora"
                    ),
                })

    except Exception as e:
        logger.error(f"Error fetching reengagement candidates: {e}", exc_info=True)
        return {
            "success": False,
            "data": {},
            "message": f"Erro ao buscar candidatos para reengajamento: {str(e)}",
        }

    high_priority = sum(1 for c in candidates_to_reengage if c["priority"] == "high")

    return {
        "success": True,
        "data": {
            "days_inactive_threshold": days_inactive,
            "total_suggestions": len(candidates_to_reengage),
            "high_priority": high_priority,
            "candidates": candidates_to_reengage,
        },
        "message": (
            f"Encontrados {len(candidates_to_reengage)} candidatos inativos há mais de {days_inactive} dias. "
            f"{high_priority} com alta prioridade para reengajamento."
        ),
    }
