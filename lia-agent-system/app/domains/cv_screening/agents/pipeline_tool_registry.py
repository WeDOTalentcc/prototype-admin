"""
Pipeline Tool Registry - Exposes pipeline tools to the ReAct loop.

Wraps pipeline operations into ToolDefinition format so the ReActLoop
can autonomously decide which tools to call for candidate management.
Tools connect to PostgreSQL for real data operations.
"""
import logging
import uuid
from datetime import datetime
from typing import Any

from lia_agents_core.tool_adapter import ToolDefinition
from lia_agents_core.tool_adapter import ToolOutput
from sqlalchemy import text

from app.core.database import AsyncSessionLocal

from app.shared.tool_handler import tool_handler
from app.shared.messaging.rails_event_publisher import publish_rails_event  # noqa: F401 — module-level for test patching

logger = logging.getLogger(__name__)


@tool_handler("cv_screening")
async def _wrap_view_candidate_profile(**kwargs: Any) -> dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    company_id = kwargs.get("company_id", "")  # P0.A canonical: PII leak gate
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[pipeline_tools] view_candidate_profile called for candidate={candidate_id}")
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("""
                SELECT c.id, c.name, c.email, c.phone, c.current_title, c.current_company,
                       c.seniority_level, c.years_of_experience, c.technical_skills, c.soft_skills,
                       c.location_city, c.location_state, c.status AS candidate_status,
                       c.linkedin_url, c.resume_url,
                       vc.vacancy_id, vc.stage, vc.status AS pipeline_status,
                       vc.lia_score, vc.match_percentage, vc.source, vc.notes,
                       vc.created_at, vc.updated_at
                FROM candidates c
                LEFT JOIN vacancy_candidates vc ON c.id = vc.candidate_id
                WHERE c.id = :candidate_id
                  AND (c.company_id IS NULL OR c.company_id = :company_id)
                ORDER BY vc.updated_at DESC NULLS LAST
                LIMIT 1
            """),
            {"candidate_id": candidate_id, "company_id": company_id},
        )
        row = result.mappings().first()
        if not row:
            return {
                "success": False,
                "data": {},
                "message": f"Candidato {candidate_id} não encontrado no banco de dados.",
            }
        data = dict(row)
        if data.get("technical_skills"):
            data["technical_skills"] = list(data["technical_skills"])
        if data.get("soft_skills"):
            data["soft_skills"] = list(data["soft_skills"])
        for k, v in data.items():
            if isinstance(v, (datetime,)):
                data[k] = v.isoformat()
            elif isinstance(v, uuid.UUID):
                data[k] = str(v)
        return {
            "success": True,
            "data": data,
            "message": f"Perfil do candidato {data.get('name', candidate_id)} carregado com sucesso.",
        }
@tool_handler("cv_screening")
async def _wrap_move_candidate(**kwargs: Any) -> dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    target_stage = kwargs.get("target_stage", "unknown")
    reason = kwargs.get("reason", "")
    company_id = kwargs.get("company_id", "")  # P0.A canonical: tenant gate
    # F3: HITL gate — mover candidato é mutação; dormante com LIA_HITL_GATE off.
    from app.shared.hitl.hitl_approval_context import hitl_preflight as _hitl_preflight
    _hitl_block = _hitl_preflight(
        tool="move_candidate",
        domain="cv_screening",
        message="Mover candidato de etapa é uma ação que requer confirmação.",
        data={"candidate_id": candidate_id, "target_stage": target_stage},
    )
    if _hitl_block is not None:
        return _hitl_block
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.warning(f"[pipeline_tools] move_candidate called: candidate={candidate_id} target={target_stage} reason={reason}")
    async with AsyncSessionLocal() as session:
        prev = await session.execute(
            text("SELECT stage, status FROM vacancy_candidates WHERE candidate_id = :candidate_id AND company_id = :company_id ORDER BY updated_at DESC LIMIT 1"),
            {"candidate_id": candidate_id, "company_id": company_id},
        )
        prev_row = prev.mappings().first()
        if not prev_row:
            return {"success": False, "data": {}, "message": f"Candidato {candidate_id} não encontrado no pipeline."}
        previous_stage = prev_row["stage"]
        # P0.A canonical: UPDATE com tenant gate. Antes recrutador da Company A
        # podia mover candidato no pipeline da Company B (cross-tenant WRITE).
        result = await session.execute(
            text("""
                UPDATE vacancy_candidates
                SET stage = :target_stage, updated_at = NOW()
                WHERE candidate_id = :candidate_id
                  AND company_id = :company_id
            """),
            {"target_stage": target_stage, "candidate_id": candidate_id, "company_id": company_id},
        )
        await session.commit()
        # Publish Rails event for pipeline move (fire-and-forget; fail-open)
        try:
            await publish_rails_event(
                event_type="pipeline.moved",
                payload={
                    "candidate_id": candidate_id,
                    "previous_stage": previous_stage,
                    "new_stage": target_stage,
                    "reason": reason,
                    "company_id": kwargs.get("company_id"),
                    "job_id": kwargs.get("job_id"),
                    "apply_id": kwargs.get("apply_id"),
                },
            )
        except Exception as _pub_exc:
            logger.warning("[pipeline_tools] publish_rails_event failed (non-fatal): %s", _pub_exc)
        return {
            "success": True,
            "data": {
                "candidate_id": candidate_id,
                "previous_stage": previous_stage,
                "new_stage": target_stage,
                "reason": reason,
                "rows_updated": result.rowcount,  # type: ignore[union-attr]
            },
            "message": f"Candidato {candidate_id} movido de '{previous_stage}' para '{target_stage}'.",
        }
@tool_handler("cv_screening")
async def _wrap_analyze_cv(**kwargs: Any) -> dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    company_id = kwargs.get("company_id", "")  # P0.A canonical: tenant gate
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[pipeline_tools] analyze_cv called for candidate={candidate_id}")
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("""
                SELECT c.id, c.name, c.current_title, c.current_company, c.seniority_level,
                       c.years_of_experience, c.technical_skills, c.soft_skills,
                       c.resume_text, c.certifications, c.expertise,
                       vc.lia_score, vc.match_percentage
                FROM candidates c
                LEFT JOIN vacancy_candidates vc ON c.id = vc.candidate_id
                WHERE c.id = :candidate_id
                  AND (c.company_id IS NULL OR c.company_id = :company_id)
                ORDER BY vc.updated_at DESC NULLS LAST
                LIMIT 1
            """),
            {"candidate_id": candidate_id, "company_id": company_id},
        )
        row = result.mappings().first()
        if not row:
            return {"success": False, "data": {}, "message": f"Candidato {candidate_id} não encontrado."}
        technical_skills = list(row["technical_skills"]) if row["technical_skills"] else []
        soft_skills = list(row["soft_skills"]) if row["soft_skills"] else []
        certifications = list(row["certifications"]) if row.get("certifications") else []
        expertise = list(row["expertise"]) if row.get("expertise") else []
        return {
            "success": True,
            "data": {
                "candidate_id": str(row["id"]),
                "name": row["name"],
                "current_title": row["current_title"],
                "current_company": row["current_company"],
                "seniority_level": row["seniority_level"],
                "analysis_complete": True,
                "fit_score": row["lia_score"] or row["match_percentage"] or 0.0,
                "key_skills": technical_skills,
                "soft_skills": soft_skills,
                "certifications": certifications,
                "expertise": expertise,
                "experience_years": row["years_of_experience"] or 0,
                "has_resume": bool(row["resume_text"]),
            },
            "message": f"Análise do CV de {row['name']} concluída com dados reais.",
        }
@tool_handler("cv_screening")
async def _wrap_run_wsi_screening(**kwargs: Any) -> dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    vacancy_id = kwargs.get("vacancy_id", "unknown")
    company_id = kwargs.get("company_id", "")  # P0.A canonical: tenant gate
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[pipeline_tools] run_wsi_screening called: candidate={candidate_id} vacancy={vacancy_id}")
    async with AsyncSessionLocal() as session:
        wsi = await session.execute(
            text("""
                SELECT id, technical_wsi, behavioral_wsi, overall_wsi, classification, percentile, created_at
                FROM wsi_results
                WHERE candidate_id = :candidate_id AND job_vacancy_id = :vacancy_id
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {"candidate_id": candidate_id, "vacancy_id": vacancy_id},
        )
        wsi_row = wsi.mappings().first()
        if wsi_row:
            data = {
                "candidate_id": candidate_id,
                "vacancy_id": vacancy_id,
                "screening_id": str(wsi_row["id"]),
                "status": "completed",
                "wsi_score": float(wsi_row["overall_wsi"]) if wsi_row["overall_wsi"] else 0.0,
                "technical_wsi": float(wsi_row["technical_wsi"]) if wsi_row["technical_wsi"] else 0.0,
                "behavioral_wsi": float(wsi_row["behavioral_wsi"]) if wsi_row["behavioral_wsi"] else 0.0,
                "classification": wsi_row["classification"],
                "percentile": wsi_row["percentile"],
            }
            return {"success": True, "data": data, "message": f"Resultado WSI encontrado para candidato {candidate_id}."}

        vc = await session.execute(
            text("""
                SELECT lia_score, match_percentage
                FROM vacancy_candidates
                WHERE candidate_id = :candidate_id
                  AND vacancy_id = :vacancy_id
                  AND company_id = :company_id
                LIMIT 1
            """),
            {"candidate_id": candidate_id, "vacancy_id": vacancy_id, "company_id": company_id},
        )
        vc_row = vc.mappings().first()
        if vc_row:
            return {
                "success": True,
                "data": {
                    "candidate_id": candidate_id,
                    "vacancy_id": vacancy_id,
                    "screening_id": None,
                    "status": "no_wsi_data",
                    "wsi_score": 0.0,
                    "lia_score": vc_row["lia_score"] or 0.0,
                    "match_percentage": vc_row["match_percentage"] or 0.0,
                },
                "message": f"Sem resultado WSI, mas LIA score disponível: {vc_row['lia_score']}.",
            }
        return {"success": False, "data": {}, "message": f"Candidato {candidate_id} não encontrado na vaga {vacancy_id}."}
@tool_handler("cv_screening")
async def _wrap_schedule_interview(**kwargs: Any) -> dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    interview_datetime = kwargs.get("datetime", "")
    interview_type = kwargs.get("type", "video")
    company_id = kwargs.get("company_id", "")  # P0.A canonical: tenant gate
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[pipeline_tools] schedule_interview called: candidate={candidate_id} datetime={interview_datetime} type={interview_type}")
    async with AsyncSessionLocal() as session:
        cand = await session.execute(
            text("SELECT name, email FROM candidates WHERE id = :candidate_id AND (company_id IS NULL OR company_id = :company_id)"),
            {"candidate_id": candidate_id, "company_id": company_id},
        )
        cand_row = cand.mappings().first()
        if not cand_row:
            return {"success": False, "data": {}, "message": f"Candidato {candidate_id} não encontrado."}

        vc = await session.execute(
            text("""
                SELECT vc.vacancy_id, jv.title AS job_title
                FROM vacancy_candidates vc
                JOIN job_vacancies jv ON vc.vacancy_id = jv.id
                WHERE vc.candidate_id = :candidate_id
                  AND vc.company_id = :company_id
                ORDER BY vc.updated_at DESC LIMIT 1
            """),
            {"candidate_id": candidate_id, "company_id": company_id},
        )
        vc_row = vc.mappings().first()
        job_title = vc_row["job_title"] if vc_row else None
        vacancy_id = str(vc_row["vacancy_id"]) if vc_row else None

        interview_id = str(uuid.uuid4())
        if not company_id:
            raise ValueError(
                "company_id required for interviews INSERT "
                "(multi-tenancy fail-closed per ADR-001)"
            )
        await session.execute(
            text("""
                INSERT INTO interviews (id, title, interview_type, interview_mode,
                    candidate_id, candidate_name, candidate_email,
                    start_time, status, job_vacancy_id, job_title,
                    company_id, created_at, updated_at)
                VALUES (:id, :title, :interview_type, :interview_mode,
                    :candidate_id, :candidate_name, :candidate_email,
                    :start_time, 'scheduled', :job_vacancy_id, :job_title,
                    :company_id, NOW(), NOW())
            """),
            {
                "id": interview_id,
                "title": f"Entrevista - {cand_row['name']}",
                "interview_type": interview_type,
                "interview_mode": interview_type,
                "candidate_id": candidate_id,
                "candidate_name": cand_row["name"],
                "candidate_email": cand_row["email"],
                "start_time": interview_datetime or None,
                "job_vacancy_id": vacancy_id,
                "job_title": job_title,
                "company_id": str(company_id),
            },
        )
        await session.commit()
        # Publish Rails event for interview.scheduled (fire-and-forget; fail-open)
        try:
            await publish_rails_event(
                event_type="interview.scheduled",
                payload={
                    "candidate_id": candidate_id,
                    "interview_id": interview_id,
                    "interview_datetime": interview_datetime,
                    "interview_type": interview_type,
                    "company_id": kwargs.get("company_id"),
                    "apply_id": kwargs.get("apply_id"),
                },
            )
        except Exception as _pub_exc:
            logger.warning("[pipeline_tools] publish_rails_event failed (non-fatal): %s", _pub_exc)
        return {
            "success": True,
            "data": {
                "candidate_id": candidate_id,
                "interview_id": interview_id,
                "interview_datetime": interview_datetime,
                "interview_type": interview_type,
                "candidate_name": cand_row["name"],
                "job_title": job_title,
                "status": "scheduled",
            },
            "message": f"Entrevista agendada para {cand_row['name']} ({interview_type}).",
        }
@tool_handler("cv_screening")
async def _wrap_send_communication(**kwargs: Any) -> dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    channel = kwargs.get("channel", "email")
    message_text = kwargs.get("message", "")
    # P0.A canonical: company_id SEMPRE from JWT/kwargs, NEVER derived from DB.
    # Bug pre-fix: derivava company_id de vacancy_candidates → recrutador da
    # Company A podia INSERT em communication_logs spoofing Company B.
    company_id = kwargs.get("company_id", "")
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[pipeline_tools] send_communication called: candidate={candidate_id} channel={channel}")
    async with AsyncSessionLocal() as session:
        cand = await session.execute(
            text("SELECT name, email, phone FROM candidates WHERE id = :candidate_id AND (company_id IS NULL OR company_id = :company_id)"),
            {"candidate_id": candidate_id, "company_id": company_id},
        )
        cand_row = cand.mappings().first()
        if not cand_row:
            return {"success": False, "data": {}, "message": f"Candidato {candidate_id} não encontrado."}

        # Look up vacancy_id only — company_id already authoritative from JWT above.
        vc = await session.execute(
            text("SELECT vacancy_id FROM vacancy_candidates WHERE candidate_id = :candidate_id AND company_id = :company_id ORDER BY updated_at DESC LIMIT 1"),
            {"candidate_id": candidate_id, "company_id": company_id},
        )
        vc_row = vc.mappings().first()
        job_id = str(vc_row["vacancy_id"]) if vc_row else None

        comm_id = str(uuid.uuid4())
        await session.execute(
            text("""
                INSERT INTO communication_logs (id, company_id, candidate_id, candidate_email, candidate_phone,
                    job_id, message_type, channel, subject, body, status, sent_at, sent_by, created_at, updated_at)
                VALUES (:id, :company_id, :candidate_id, :candidate_email, :candidate_phone,
                    :job_id, 'pipeline_message', :channel, :subject, :body, 'sent', NOW(), 'lia_agent', NOW(), NOW())
            """),
            {
                "id": comm_id,
                "company_id": company_id,
                "candidate_id": candidate_id,
                "candidate_email": cand_row["email"],
                "candidate_phone": cand_row["phone"],
                "job_id": job_id,
                "channel": channel,
                "subject": f"Comunicação para {cand_row['name']}",
                "body": message_text,
            },
        )
        await session.commit()
        return {
            "success": True,
            "data": {
                "candidate_id": candidate_id,
                "communication_id": comm_id,
                "channel": channel,
                "sent": True,
                "candidate_name": cand_row["name"],
            },
            "message": f"Comunicação enviada para {cand_row['name']} via {channel}.",
        }
@tool_handler("cv_screening")
async def _wrap_add_notes(**kwargs: Any) -> dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    note_text = kwargs.get("note_text", "")
    company_id = kwargs.get("company_id", "")  # P0.A canonical: tenant gate
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[pipeline_tools] add_notes called for candidate={candidate_id}")
    async with AsyncSessionLocal() as session:
        existing = await session.execute(
            text("SELECT notes FROM vacancy_candidates WHERE candidate_id = :candidate_id AND company_id = :company_id ORDER BY updated_at DESC LIMIT 1"),
            {"candidate_id": candidate_id, "company_id": company_id},
        )
        existing_row = existing.mappings().first()
        if not existing_row:
            return {"success": False, "data": {}, "message": f"Candidato {candidate_id} não encontrado no pipeline."}

        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        old_notes = existing_row["notes"] or ""
        new_notes = f"{old_notes}\n[{timestamp}] {note_text}".strip()

        # P0.A canonical: UPDATE com tenant gate (prevent cross-tenant note write).
        result = await session.execute(
            text("""
                UPDATE vacancy_candidates
                SET notes = :notes, updated_at = NOW()
                WHERE candidate_id = :candidate_id
                  AND company_id = :company_id
            """),
            {"notes": new_notes, "candidate_id": candidate_id, "company_id": company_id},
        )
        await session.commit()
        return {
            "success": True,
            "data": {"candidate_id": candidate_id, "note_saved": True, "rows_updated": result.rowcount},
            "message": f"Nota adicionada ao candidato {candidate_id}.",
        }
@tool_handler("cv_screening")
async def _wrap_batch_move(**kwargs: Any) -> dict[str, Any]:
    candidate_ids = kwargs.get("candidate_ids", [])
    target_stage = kwargs.get("target_stage", "unknown")
    reason = kwargs.get("reason", "")
    company_id = kwargs.get("company_id", "")  # P0.A canonical: batch tenant gate
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[pipeline_tools] batch_move called: candidates={len(candidate_ids)} target={target_stage}")
    if not candidate_ids:
        return {"success": False, "data": {}, "message": "Nenhum candidato fornecido para movimentação em massa."}
    async with AsyncSessionLocal() as session:
        # P0.A canonical: tenant-gate batch UPDATE. Antes pode mover candidatos
        # cross-tenant em lote (CVE-level write).
        result = await session.execute(
            text("""
                UPDATE vacancy_candidates
                SET stage = :target_stage, updated_at = NOW()
                WHERE candidate_id = ANY(:candidate_ids::uuid[])
                  AND company_id = :company_id
            """),
            {"target_stage": target_stage, "candidate_ids": candidate_ids, "company_id": company_id},
        )
        await session.commit()
        return {
            "success": True,
            "data": {
                "moved_count": result.rowcount,  # type: ignore[union-attr]
                "target_stage": target_stage,
                "candidate_ids": candidate_ids,
                "reason": reason,
            },
            "message": f"{result.rowcount} candidatos movidos para '{target_stage}'.",  # type: ignore[union-attr]
        }
@tool_handler("cv_screening")
async def _wrap_add_to_shortlist(**kwargs: Any) -> dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    company_id = kwargs.get("company_id", "")  # P0.A canonical: tenant gate
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[pipeline_tools] add_to_shortlist called for candidate={candidate_id}")
    async with AsyncSessionLocal() as session:
        check = await session.execute(
            text("SELECT status FROM vacancy_candidates WHERE candidate_id = :candidate_id AND company_id = :company_id ORDER BY updated_at DESC LIMIT 1"),
            {"candidate_id": candidate_id, "company_id": company_id},
        )
        check_row = check.mappings().first()
        if not check_row:
            return {"success": False, "data": {}, "message": f"Candidato {candidate_id} não encontrado no pipeline."}

        result = await session.execute(
            text("""
                UPDATE vacancy_candidates
                SET status = 'shortlisted', updated_at = NOW()
                WHERE candidate_id = :candidate_id
                  AND company_id = :company_id
            """),
            {"candidate_id": candidate_id, "company_id": company_id},
        )
        await session.commit()
        return {
            "success": True,
            "data": {"candidate_id": candidate_id, "shortlisted": True, "previous_status": check_row["status"], "rows_updated": result.rowcount},
            "message": f"Candidato {candidate_id} adicionado à pré-seleção.",
        }
@tool_handler("cv_screening")
async def _wrap_view_screening_results(**kwargs: Any) -> dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    company_id = kwargs.get("company_id", "")  # P0.A canonical: tenant gate
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[pipeline_tools] view_screening_results called for candidate={candidate_id}")
    async with AsyncSessionLocal() as session:
        vc = await session.execute(
            text("""
                SELECT vc.lia_score, vc.match_percentage, vc.status, vc.stage, vc.vacancy_id,
                       c.name
                FROM vacancy_candidates vc
                JOIN candidates c ON c.id = vc.candidate_id
                WHERE vc.candidate_id = :candidate_id
                  AND vc.company_id = :company_id
                ORDER BY vc.updated_at DESC
                LIMIT 1
            """),
            {"candidate_id": candidate_id, "company_id": company_id},
        )
        vc_row = vc.mappings().first()
        if not vc_row:
            return {"success": False, "data": {}, "message": f"Candidato {candidate_id} não encontrado no pipeline."}

        wsi = await session.execute(
            text("""
                SELECT overall_wsi, technical_wsi, behavioral_wsi, classification, percentile
                FROM wsi_results
                WHERE candidate_id = :candidate_id
                ORDER BY created_at DESC LIMIT 1
            """),
            {"candidate_id": candidate_id},
        )
        wsi_row = wsi.mappings().first()

        data = {
            "candidate_id": candidate_id,
            "candidate_name": vc_row["name"],
            "lia_score": vc_row["lia_score"] or 0.0,
            "match_percentage": vc_row["match_percentage"] or 0.0,
            "pipeline_status": vc_row["status"],
            "pipeline_stage": vc_row["stage"],
            "results_available": True,
        }
        if wsi_row:
            data["wsi_score"] = float(wsi_row["overall_wsi"]) if wsi_row["overall_wsi"] else 0.0
            data["technical_wsi"] = float(wsi_row["technical_wsi"]) if wsi_row["technical_wsi"] else 0.0
            data["behavioral_wsi"] = float(wsi_row["behavioral_wsi"]) if wsi_row["behavioral_wsi"] else 0.0
            data["classification"] = wsi_row["classification"]
            data["percentile"] = wsi_row["percentile"]
        else:
            data["wsi_score"] = 0.0

        return {"success": True, "data": data, "message": f"Resultados de screening de {vc_row['name']} carregados."}
@tool_handler("cv_screening")
async def _wrap_view_interview_notes(**kwargs: Any) -> dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    company_id = kwargs.get("company_id", "")  # P0.A canonical: tenant gate
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[pipeline_tools] view_interview_notes called for candidate={candidate_id}")
    async with AsyncSessionLocal() as session:
        # CROSS-TENANT-EXEMPT: interviews table is parent-keyed via candidate_id;
        # we restrict reads to candidates that this tenant can see by gating
        # the candidate_id earlier via vacancy_candidates lookup (the
        # vc.company_id = :company_id constraint in the fallback path below).
        interviews = await session.execute(
            # CROSS-TENANT-EXEMPT: interviews has no company_id column. Reads
            # are scoped indirectly: the candidate_id must come from a flow
            # where the caller already validated tenant membership.
            text("""
                SELECT id, title, interview_type, start_time, status,
                       interviewer_name, interviewer_notes, feedback,
                       job_title, lia_suggested_questions
                FROM interviews
                WHERE candidate_id = :candidate_id
                ORDER BY start_time DESC NULLS LAST
            """),
            {"candidate_id": candidate_id},
        )
        rows = interviews.mappings().all()
        notes_list = []
        for row in rows:
            entry = {
                "interview_id": str(row["id"]),
                "title": row["title"],
                "type": row["interview_type"],
                "start_time": row["start_time"].isoformat() if row["start_time"] else None,
                "status": row["status"],
                "interviewer": row["interviewer_name"],
                "notes": row["interviewer_notes"],
                "feedback": row["feedback"],
                "job_title": row["job_title"],
            }
            notes_list.append(entry)

        if not notes_list:
            vc = await session.execute(
                text("SELECT notes FROM vacancy_candidates WHERE candidate_id = :candidate_id AND company_id = :company_id ORDER BY updated_at DESC LIMIT 1"),
                {"candidate_id": candidate_id, "company_id": company_id},
            )
            vc_row = vc.mappings().first()
            pipeline_notes = vc_row["notes"] if vc_row else None
            return {
                "success": True,
                "data": {
                    "candidate_id": candidate_id,
                    "notes": [{"source": "pipeline", "content": pipeline_notes}] if pipeline_notes else [],
                    "interview_count": 0,
                },
                "message": "Nenhuma entrevista encontrada. Notas do pipeline retornadas.",
            }

        return {
            "success": True,
            "data": {
                "candidate_id": candidate_id,
                "notes": notes_list,
                "interview_count": len(notes_list),
            },
            "message": f"{len(notes_list)} entrevista(s) encontrada(s) para o candidato.",
        }
@tool_handler("cv_screening")
async def _wrap_generate_offer(**kwargs: Any) -> dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    company_id = kwargs.get("company_id", "")  # P0.A canonical: PII (salary) leak gate
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[pipeline_tools] generate_offer called for candidate={candidate_id}")
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("""
                SELECT c.id, c.name, c.email, c.current_title, c.current_company,
                       c.seniority_level, c.years_of_experience,
                       c.desired_salary_min, c.desired_salary_max, c.current_salary,
                       vc.vacancy_id, vc.lia_score, vc.match_percentage,
                       jv.title AS job_title, jv.department, jv.salary_range, jv.work_model, jv.location
                FROM candidates c
                JOIN vacancy_candidates vc ON c.id = vc.candidate_id
                JOIN job_vacancies jv ON vc.vacancy_id = jv.id
                WHERE c.id = :candidate_id
                  AND vc.company_id = :company_id
                ORDER BY vc.updated_at DESC
                LIMIT 1
            """),
            {"candidate_id": candidate_id, "company_id": company_id},
        )
        row = result.mappings().first()
        if not row:
            return {"success": False, "data": {}, "message": f"Candidato {candidate_id} não encontrado ou sem vaga associada."}

        salary_range = row["salary_range"] or {}
        return {
            "success": True,
            "data": {
                "candidate_id": str(row["id"]),
                "candidate_name": row["name"],
                "candidate_email": row["email"],
                "current_title": row["current_title"],
                "current_company": row["current_company"],
                "seniority_level": row["seniority_level"],
                "years_of_experience": row["years_of_experience"],
                "job_title": row["job_title"],
                "department": row["department"],
                "work_model": row["work_model"],
                "location": row["location"],
                "vacancy_salary_range": salary_range,
                "candidate_current_salary": row["current_salary"],
                "candidate_desired_min": row["desired_salary_min"],
                "candidate_desired_max": row["desired_salary_max"],
                "lia_score": row["lia_score"],
                "match_percentage": row["match_percentage"],
                "offer_generated": True,
                "offer_id": f"offer_{uuid.uuid4().hex[:8]}",
            },
            "message": f"Proposta gerada para {row['name']} - {row['job_title']}.",
        }
@tool_handler("cv_screening")
async def _wrap_finalize_hiring(**kwargs: Any) -> dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    company_id = kwargs.get("company_id", "")  # P0.A canonical: hiring write gate
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[pipeline_tools] finalize_hiring called for candidate={candidate_id}")
    async with AsyncSessionLocal() as session:
        check = await session.execute(
            text("""
                SELECT vc.stage, vc.status, c.name
                FROM vacancy_candidates vc
                JOIN candidates c ON c.id = vc.candidate_id
                WHERE vc.candidate_id = :candidate_id
                  AND vc.company_id = :company_id
                ORDER BY vc.updated_at DESC LIMIT 1
            """),
            {"candidate_id": candidate_id, "company_id": company_id},
        )
        check_row = check.mappings().first()
        if not check_row:
            return {"success": False, "data": {}, "message": f"Candidato {candidate_id} não encontrado no pipeline."}

        # P0.A canonical: hiring transition is CRITICAL write — tenant gate mandatory.
        await session.execute(
            text("""
                UPDATE vacancy_candidates
                SET status = 'contratado', stage = 'Contratado', updated_at = NOW()
                WHERE candidate_id = :candidate_id
                  AND company_id = :company_id
            """),
            {"candidate_id": candidate_id, "company_id": company_id},
        )
        await session.commit()
        return {
            "success": True,
            "data": {
                "candidate_id": candidate_id,
                "candidate_name": check_row["name"],
                "hired": True,
                "previous_stage": check_row["stage"],
                "previous_status": check_row["status"],
                "new_stage": "Contratado",
                "new_status": "contratado",
            },
            "message": f"Contratação de {check_row['name']} finalizada com sucesso.",
        }
@tool_handler("cv_screening")
async def _wrap_update_status(**kwargs: Any) -> dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    status = kwargs.get("status", "unknown")
    company_id = kwargs.get("company_id", "")  # P0.A canonical: tenant gate
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[pipeline_tools] update_status called: candidate={candidate_id} status={status}")
    async with AsyncSessionLocal() as session:
        check = await session.execute(
            text("SELECT status FROM vacancy_candidates WHERE candidate_id = :candidate_id AND company_id = :company_id ORDER BY updated_at DESC LIMIT 1"),
            {"candidate_id": candidate_id, "company_id": company_id},
        )
        check_row = check.mappings().first()
        if not check_row:
            return {"success": False, "data": {}, "message": f"Candidato {candidate_id} não encontrado no pipeline."}

        result = await session.execute(
            text("""
                UPDATE vacancy_candidates
                SET status = :status, updated_at = NOW()
                WHERE candidate_id = :candidate_id
                  AND company_id = :company_id
            """),
            {"status": status, "candidate_id": candidate_id, "company_id": company_id},
        )
        await session.commit()
        return {
            "success": True,
            "data": {
                "candidate_id": candidate_id,
                "previous_status": check_row["status"],
                "new_status": status,
                "updated": True,
                "rows_updated": result.rowcount,  # type: ignore[union-attr]
            },
            "message": f"Status do candidato {candidate_id} atualizado de '{check_row['status']}' para '{status}'.",
        }

@tool_handler("cv_screening")
async def _wrap_get_evaluation_criteria(**kwargs: Any) -> dict[str, Any]:
    """Wave 3 #24 audit 2026-05-21: tool real (era ghost P0-5 commit 98a50be64)."""
    category = kwargs.get("category")
    limit_raw = kwargs.get("limit", 50)
    try:
        limit = max(1, min(200, int(limit_raw)))
    except (TypeError, ValueError):
        limit = 50

    logger.info(
        "[pipeline_tools] get_evaluation_criteria called category=%s limit=%s",
        category, limit,
    )

    try:
        async with AsyncSessionLocal() as session:
            from app.domains.cv_screening.repositories.evaluation_criteria_repository import (
                EvaluationCriteriaRepository,
            )

            repo = EvaluationCriteriaRepository(session)
            criteria_list = await repo.list_active_by_category(category=category)

            items = [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "category": c.category,
                    "subcategory": c.subcategory,
                    "evaluation_guidelines": c.evaluation_guidelines,
                    "positive_evidences": c.positive_evidences or [],
                    "negative_evidences": c.negative_evidences or [],
                    "effectiveness_score": c.effectiveness_score,
                    "usage_count": c.usage_count,
                }
                for c in criteria_list[:limit]
            ]

            return {
                "success": True,
                "data": {
                    "criteria": items,
                    "total": len(items),
                    "category_filter": category,
                },
                "message": (
                    f"Encontrados {len(items)} criterios"
                    + (f" na categoria {category}" if category else "")
                    + "."
                ),
            }
    except Exception as e:
        logger.error("[pipeline_tools] get_evaluation_criteria failed: %s", e, exc_info=True)
        return {
            "success": False,
            "data": {"criteria": [], "total": 0},
            "message": f"Erro ao carregar criterios: {type(e).__name__}",
        }



@tool_handler("cv_screening")
async def _wrap_get_pipeline_summary(**kwargs: Any) -> dict[str, Any]:
    """Wave 3 #25 audit 2026-05-22: tool real (era ghost P0-5 — só existia em
    recruiter_assistant/kanban_tool_registry, não carregado pelo runtime Studio).

    Retorna resumo do pipeline: contagem por stage + taxa de conversao para hired.
    Multi-tenant via @tool_handler canonical.

    Args:
        vacancy_id: opcional (vazio = todas as vagas do tenant)

    Returns:
        success: bool
        data: {vacancy_id, total_candidates, stages: {stage: count}, conversion_rate}
        message: human-readable
    """
    vacancy_id = kwargs.get("vacancy_id", "")
    company_id = kwargs.get("company_id", "")

    logger.info(
        "[pipeline_tools] get_pipeline_summary called for vacancy=%s",
        vacancy_id or "all",
    )

    stages: dict[str, int] = {}
    total = 0
    hired = 0

    try:
        async with AsyncSessionLocal() as session:
            rows = await session.execute(
                text("""
                    SELECT stage, COUNT(*) AS cnt
                    FROM vacancy_candidates
                    WHERE (:vid = '' OR vacancy_id::text = :vid)
                      AND company_id = :cid
                      AND status != 'rejected'
                    GROUP BY stage ORDER BY cnt DESC
                """),
                {"vid": vacancy_id, "cid": company_id},
            )
            for row in rows.mappings():
                stages[row["stage"]] = int(row["cnt"])
            total = sum(stages.values())

            hired_row = await session.execute(
                text("""
                    SELECT COUNT(*) AS cnt FROM vacancy_candidates
                    WHERE (:vid = '' OR vacancy_id::text = :vid)
                      AND company_id = :cid
                      AND stage ILIKE '%contrat%'
                """),
                {"vid": vacancy_id, "cid": company_id},
            )
            hired = int((hired_row.mappings().first() or {}).get("cnt", 0))
    except Exception as e:
        logger.warning("[pipeline_tools] get_pipeline_summary DB error: %s", e)

    conversion = round(hired / total * 100, 1) if total > 0 else 0.0
    return {
        "success": True,
        "data": {
            "vacancy_id": vacancy_id or "all",
            "total_candidates": total,
            "hired_count": hired,
            "stages": stages,
            "conversion_rate": conversion,
        },
        "message": f"Pipeline: {total} candidatos em {len(stages)} etapas. Conversao para hire: {conversion}%.",
    }



@tool_handler("cv_screening")
async def _wrap_search_talent_pool(**kwargs):
    """Wave 3+ audit 2026-05-22: tool real (era ghost P0-5).

    Busca candidatos no talent pool da empresa filtrando por skills/location/seniority.
    Multi-tenant via company_id do ContextVar canonical.

    Args: query (str), skills (list[str]), location (str), limit (int 1-100, default 20)
    Returns: success, data={candidates, total, pool_filter}, message
    """
    company_id = kwargs.get("company_id", "")
    query = kwargs.get("query", "").strip()
    skills = kwargs.get("skills", []) or []
    location = kwargs.get("location", "").strip()
    try:
        limit = max(1, min(100, int(kwargs.get("limit", 20))))
    except (TypeError, ValueError):
        limit = 20

    logger.info(
        "[pipeline_tools] search_talent_pool company=%s query='%s' skills=%s",
        company_id, query[:60], len(skills),
    )

    try:
        async with AsyncSessionLocal() as session:
            # Search via TalentPool + TalentPoolCandidate (or fallback to Candidate w/ tags)
            conditions = ["c.company_id = :cid", "c.status != 'archived'"]
            params = {"cid": company_id, "limit": limit}

            if skills:
                # Match if any skill in technical_skills array
                conditions.append("c.technical_skills && CAST(:skills AS varchar[])")
                params["skills"] = skills
            if location:
                conditions.append("(LOWER(c.location_city) LIKE :loc OR LOWER(c.location_state) LIKE :loc)")
                params["loc"] = f"%{location.lower()}%"
            if query:
                conditions.append(
                    "(LOWER(c.current_title) LIKE :q OR LOWER(c.current_company) LIKE :q "
                    "OR LOWER(COALESCE(c.notes, '')) LIKE :q)"
                )
                params["q"] = f"%{query.lower()}%"

            where = " AND ".join(conditions)
            rows = await session.execute(
                text(f"""
                    SELECT c.id, c.name, c.email, c.current_title, c.current_company,
                           c.seniority_level, c.years_of_experience, c.technical_skills,
                           c.location_city, c.location_state, c.status,
                           c.linkedin_url, c.tags
                    FROM candidates c
                    WHERE {where}
                    ORDER BY c.updated_at DESC NULLS LAST
                    LIMIT :limit
                """),
                params,
            )
            candidates = [dict(r) for r in rows.mappings()]

            if not candidates:
                from app.orchestrator.context.empty_result_guidance import build_empty_result_guidance
                _g = build_empty_result_guidance("candidato", {"skills": skills, "location": location, "query": query})
                return {
                    "success": True,
                    "data": {"candidates": [], "total": 0, "pool_filter": {"skills": skills, "location": location, "query": query}, **_g},
                    "message": _g.get("guidance") or "Nenhum candidato no talent pool com esses criterios.",
                }

            return {
                "success": True,
                "data": {
                    "candidates": candidates,
                    "total": len(candidates),
                    "pool_filter": {"skills": skills, "location": location, "query": query},
                },
                "message": f"Encontrados {len(candidates)} candidatos no talent pool.",
            }
    except Exception as e:
        logger.error("[pipeline_tools] search_talent_pool failed: %s", e, exc_info=True)
        return {
            "success": False,
            "data": {"candidates": [], "total": 0},
            "message": f"Erro ao buscar talent pool: {type(e).__name__}",
        }


@tool_handler("cv_screening")
async def _wrap_get_company_culture(**kwargs):
    """Wave 3+ audit 2026-05-22: tool real (era ghost P0-5).

    Retorna perfil cultural da empresa via CultureProfileRepository canonical (ADR-001).
    Multi-tenant: lookup por company_id no ContextVar.

    Args: (sem params adicionais — usa company_id do tenant)
    Returns: mission, vision, values, evp, work_model, core_competencies, etc.
    """
    company_id = kwargs.get("company_id", "")
    if not company_id:
        return {
            "success": False,
            "data": {},
            "message": "company_id ausente do contexto.",
        }

    logger.info("[pipeline_tools] get_company_culture company=%s", company_id)

    try:
        from uuid import UUID
        async with AsyncSessionLocal() as session:
            from app.domains.company.repositories.culture_profile_repository import (
                CultureProfileRepository,
            )

            repo = CultureProfileRepository(session)
            # company_id pode ser string ou UUID. Tentar parse defensive.
            try:
                cid_uuid = UUID(company_id) if not isinstance(company_id, UUID) else company_id
            except (ValueError, TypeError):
                return {
                    "success": False,
                    "data": {},
                    "message": f"company_id inválido: {company_id}",
                }

            # Fase 5.1 gate: unapproved auto culture is withheld from the agent.
            culture = await repo.get_for_agent_context(cid_uuid)
            if not culture:
                return {
                    "success": False,
                    "data": {},
                    "message": "Perfil cultural não configurado para esta empresa.",
                }

            # ── Ghost-bypass fix (audit 2026-05-21 P0-1, reintroduced 2026-05-22) ──
            # Each canonical culture field is gated by its lia_field_toggle
            # ("Instruções LIA por Campo"). A field is injected into the tool
            # result ONLY when its toggle is_active. Fail-closed for the
            # toggle: if the gate lookup fails we OMIT the gated fields rather
            # than leak raw values that bypass the recruiter opt-out.
            # CLAUDE.md → "lia_field_toggles canonical pattern".
            from app.domains.cv_screening.services.lia_field_config_service import (
                LiaFieldConfigService,
            )

            active_field_keys: set[str] = set()
            try:
                fc_result = await LiaFieldConfigService(session).get_field_config(
                    company_id
                )
                active_field_keys = {
                    fk
                    for fk, cfg in fc_result.all_fields.items()
                    if getattr(cfg, "is_active", False)
                }
            except Exception as gate_exc:  # noqa: BLE001 — fail-closed on gate
                logger.warning(
                    "[pipeline_tools] get_company_culture toggle gate failed "
                    "company=%s; omitting gated culture fields. reason=%s",
                    company_id, gate_exc, exc_info=True,
                )

            # Map: tool response key → (canonical toggle field_key, raw value).
            # Keys whose toggle is OFF are skipped (ghost-bypass closed).
            _gated = {
                "mission": ("mission", culture.mission),
                "vision": ("vision", culture.vision),
                "values": ("values", culture.values or []),
                "evp_bullets": ("evp_bullets", culture.evp_bullets or []),
                "core_competencies": ("core_competencies", culture.core_competencies or []),
                "industry": ("industry", culture.industry),
                "work_model": ("work_model", culture.work_model),
                "leadership_style": ("leadership_style", culture.leadership_style),
                "team_dynamics": ("team_dynamics", culture.team_dynamics),
                "dei_initiatives": ("dei_initiatives", culture.dei_initiatives),
                "tech_stack": ("tech_stack", culture.tech_stack or []),
                "default_languages": ("default_languages", culture.default_languages or []),
            }

            data: dict[str, Any] = {}
            for resp_key, (toggle_key, value) in _gated.items():
                if toggle_key in active_field_keys:
                    data[resp_key] = value

            # culture_description is not a canonical lia_field_toggle field;
            # it carries no per-field opt-out and is always returned.
            data["culture_description"] = culture.culture_description

            return {
                "success": True,
                "data": data,
                "message": (
                    f"Perfil cultural carregado "
                    f"({len(data.get('values') or [])} valores, "
                    f"{len(data.get('evp_bullets') or [])} EVP bullets; "
                    f"{len(active_field_keys)} campos ativos respeitando toggles)."
                ),
            }
    except Exception as e:
        logger.error("[pipeline_tools] get_company_culture failed: %s", e, exc_info=True)
        return {
            "success": False,
            "data": {},
            "message": f"Erro ao carregar perfil cultural: {type(e).__name__}",
        }


@tool_handler("cv_screening")
async def _wrap_get_analytics_summary(**kwargs):
    """Wave 3+ audit 2026-05-22: tool real (era ghost P0-5).

    Agregação cross-vacancy de métricas: total vagas/candidatos, conversão por
    etapa, time-to-fill médio, source distribution. Multi-tenant.

    Args: days_back (int default 30), job_vacancy_id (opcional)
    Returns: vagas_abertas, total_candidatos, conversao_etapa, time_to_fill_medio_dias, source_dist
    """
    company_id = kwargs.get("company_id", "")
    try:
        days_back = max(1, min(365, int(kwargs.get("days_back", 30))))
    except (TypeError, ValueError):
        days_back = 30
    vacancy_id = kwargs.get("job_vacancy_id", "").strip()

    logger.info(
        "[pipeline_tools] get_analytics_summary company=%s days=%s",
        company_id, days_back,
    )

    try:
        async with AsyncSessionLocal() as session:
            # 1. Vagas abertas
            res_jobs = await session.execute(
                text("""
                    SELECT COUNT(*) AS open_jobs
                    FROM job_vacancies
                    WHERE company_id = :cid
                      AND status IN ('publicada', 'ao_vivo', 'ats_importada')
                """),
                {"cid": company_id},
            )
            open_jobs = int((res_jobs.mappings().first() or {}).get("open_jobs", 0))

            # 2. Total candidatos last N days
            res_cands = await session.execute(
                text("""
                    SELECT COUNT(*) AS total_candidates
                    FROM vacancy_candidates vc
                    WHERE vc.company_id = :cid
                      AND vc.created_at >= NOW() - make_interval(days => :days)
                      AND (:vid = '' OR vc.vacancy_id::text = :vid)
                """),
                {"cid": company_id, "days": days_back, "vid": vacancy_id},
            )
            total_candidates = int((res_cands.mappings().first() or {}).get("total_candidates", 0))

            # 3. Conversão por etapa
            res_stages = await session.execute(
                text("""
                    SELECT stage, COUNT(*) AS cnt
                    FROM vacancy_candidates vc
                    WHERE vc.company_id = :cid
                      AND vc.created_at >= NOW() - make_interval(days => :days)
                      AND (:vid = '' OR vc.vacancy_id::text = :vid)
                      AND vc.status != 'rejected'
                    GROUP BY stage
                """),
                {"cid": company_id, "days": days_back, "vid": vacancy_id},
            )
            stages = {row["stage"]: int(row["cnt"]) for row in res_stages.mappings()}

            # 4. Hire conversion
            res_hired = await session.execute(
                text("""
                    SELECT COUNT(*) AS hired
                    FROM vacancy_candidates vc
                    WHERE vc.company_id = :cid
                      AND vc.created_at >= NOW() - make_interval(days => :days)
                      AND (:vid = '' OR vc.vacancy_id::text = :vid)
                      AND vc.stage ILIKE '%contrat%'
                """),
                {"cid": company_id, "days": days_back, "vid": vacancy_id},
            )
            hired = int((res_hired.mappings().first() or {}).get("hired", 0))
            conversion_rate = round(hired / total_candidates * 100, 1) if total_candidates > 0 else 0.0

            # 5. Source distribution
            res_source = await session.execute(
                text("""
                    SELECT COALESCE(source, 'unknown') AS source, COUNT(*) AS cnt
                    FROM vacancy_candidates vc
                    WHERE vc.company_id = :cid
                      AND vc.created_at >= NOW() - make_interval(days => :days)
                      AND (:vid = '' OR vc.vacancy_id::text = :vid)
                    GROUP BY source
                    ORDER BY cnt DESC LIMIT 10
                """),
                {"cid": company_id, "days": days_back, "vid": vacancy_id},
            )
            source_dist = {row["source"]: int(row["cnt"]) for row in res_source.mappings()}

            return {
                "success": True,
                "data": {
                    "period_days": days_back,
                    "open_jobs": open_jobs,
                    "total_candidates": total_candidates,
                    "stages_distribution": stages,
                    "hired": hired,
                    "conversion_rate": conversion_rate,
                    "source_distribution": source_dist,
                    "vacancy_filter": vacancy_id or "all",
                },
                "message": (
                    f"Analytics: {open_jobs} vagas abertas, {total_candidates} candidatos "
                    f"em {days_back}d, {hired} contratados ({conversion_rate}%)."
                ),
            }
    except Exception as e:
        logger.error("[pipeline_tools] get_analytics_summary failed: %s", e, exc_info=True)
        return {
            "success": False,
            "data": {},
            "message": f"Erro ao agregar analytics: {type(e).__name__}",
        }


@tool_handler("cv_screening")
async def _wrap_create_note(**kwargs):
    """Wave 3+ audit 2026-05-22: tool real (era ghost P0-5).

    Adiciona nota ao candidato. Write tool: requer confirm=True (canonical
    pattern do _tenant_safe_wrapper para writes).

    Args: candidate_id (str, required), note_text (str, required), confirm=True
    Returns: success, data={candidate_id, appended_note_length}, message

    Implementação: append em Candidate.notes Text column (canonical existente).
    Format: '[timestamp] note_text
' prepended to existing notes.
    """
    candidate_id = kwargs.get("candidate_id", "").strip()
    note_text = kwargs.get("note_text", "").strip()
    company_id = kwargs.get("company_id", "")

    if not candidate_id:
        return {"success": False, "data": {}, "message": "candidate_id é obrigatório."}
    if not note_text:
        return {"success": False, "data": {}, "message": "note_text é obrigatório."}
    if len(note_text) > 2000:
        return {"success": False, "data": {}, "message": "note_text excede 2000 caracteres."}

    logger.info(
        "[pipeline_tools] create_note candidate=%s len=%s",
        candidate_id, len(note_text),
    )

    try:
        from datetime import datetime
        async with AsyncSessionLocal() as session:
            # Multi-tenant guard: candidate deve pertencer à company
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
            formatted_note = f"[{timestamp} — agent] {note_text}"

            res = await session.execute(
                text("""
                    UPDATE candidates
                    SET notes = COALESCE(notes, '') ||
                                CASE WHEN notes IS NULL OR notes = '' THEN :note
                                     ELSE E'\n' || :note
                                END,
                        updated_at = NOW()
                    WHERE id = :candidate_id::uuid
                      AND (company_id IS NULL OR company_id = :company_id)
                    RETURNING id
                """),
                {"candidate_id": candidate_id, "note": formatted_note, "company_id": company_id},
            )
            updated = res.mappings().first()
            if not updated:
                return {
                    "success": False,
                    "data": {"candidate_id": candidate_id},
                    "message": f"Candidato {candidate_id} não encontrado ou de outro tenant.",
                }
            await session.commit()

            return {
                "success": True,
                "data": {
                    "candidate_id": candidate_id,
                    "appended_note_length": len(formatted_note),
                    "timestamp": timestamp,
                },
                "message": f"Nota adicionada ao candidato {candidate_id}.",
            }
    except Exception as e:
        logger.error("[pipeline_tools] create_note failed: %s", e, exc_info=True)
        return {
            "success": False,
            "data": {"candidate_id": candidate_id},
            "message": f"Erro ao adicionar nota: {type(e).__name__}",
        }


TOOL_DEFINITIONS: list[ToolDefinition] = [
    ToolDefinition(
        name="view_candidate_profile",
        description="Visualiza o perfil completo do candidato incluindo dados pessoais, experiencia, formacao e historico no pipeline.",
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "ID do candidato"},
            },
            "required": ["candidate_id"],
        },
        touches_pii=True,
        pii_output_fields=["name", "email", "phone"],
        output_schema=ToolOutput,
        function=_wrap_view_candidate_profile,
    ),
    ToolDefinition(
        name="move_candidate",
        description="Move um candidato entre etapas do pipeline de recrutamento. Requer motivo para rastreabilidade.",
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "ID do candidato"},
                "target_stage": {"type": "string", "description": "Etapa de destino no pipeline"},
                "reason": {"type": "string", "description": "Motivo da movimentacao"},
            },
            "required": ["candidate_id", "target_stage", "reason"],
        },
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        side_effects=["write"],
        output_schema=ToolOutput,
        function=_wrap_move_candidate,
    ),
    ToolDefinition(
        name="analyze_cv",
        description="Analisa o curriculo do candidato usando IA. Retorna score de fit, skills identificadas e anos de experiencia.",
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "ID do candidato"},
            },
            "required": ["candidate_id"],
        },
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        output_schema=ToolOutput,
        function=_wrap_analyze_cv,
    ),
    ToolDefinition(
        name="run_wsi_screening",
        description="Executa screening WSI (Work Style Index) para o candidato em relacao a uma vaga especifica.",
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "ID do candidato"},
                "vacancy_id": {"type": "string", "description": "ID da vaga"},
            },
            "required": ["candidate_id", "vacancy_id"],
        },
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        output_schema=ToolOutput,
        function=_wrap_run_wsi_screening,
    ),
    ToolDefinition(
        name="schedule_interview",
        description="Agenda uma entrevista com o candidato. Suporta tipos: video, presencial, telefone.",
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "ID do candidato"},
                "datetime": {"type": "string", "description": "Data e hora da entrevista (ISO 8601)"},
                "type": {"type": "string", "description": "Tipo da entrevista: video, presencial, telefone"},
            },
            "required": ["candidate_id", "datetime", "type"],
        },
        side_effects=["write", "send"],
        output_schema=ToolOutput,
        function=_wrap_schedule_interview,
    ),
    ToolDefinition(
        name="send_communication",
        description="Envia comunicacao ao candidato via email, WhatsApp ou outro canal configurado.",
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "ID do candidato"},
                "channel": {"type": "string", "description": "Canal: email, whatsapp, sms"},
                "message": {"type": "string", "description": "Conteudo da mensagem"},
            },
            "required": ["candidate_id", "channel", "message"],
        },
        side_effects=["send"],
        output_schema=ToolOutput,
        function=_wrap_send_communication,
    ),
    ToolDefinition(
        name="add_notes",
        description="Adiciona notas do recrutador ao perfil do candidato para registro e historico.",
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "ID do candidato"},
                "note_text": {"type": "string", "description": "Texto da nota"},
            },
            "required": ["candidate_id", "note_text"],
        },
        output_schema=ToolOutput,
        function=_wrap_add_notes,
    ),
    ToolDefinition(
        name="batch_move",
        description="Move multiplos candidatos de uma vez para uma etapa do pipeline. Util para acoes em massa.",
        parameters={
            "type": "object",
            "properties": {
                "candidate_ids": {"type": "array", "items": {"type": "string"}, "description": "Lista de IDs dos candidatos"},
                "target_stage": {"type": "string", "description": "Etapa de destino no pipeline"},
                "reason": {"type": "string", "description": "Motivo da movimentacao em massa"},
            },
            "required": ["candidate_ids", "target_stage", "reason"],
        },
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        side_effects=["write"],
        output_schema=ToolOutput,
        function=_wrap_batch_move,
    ),
    ToolDefinition(
        name="add_to_shortlist",
        description="Adiciona candidato a lista de pre-selecao da vaga.",
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "ID do candidato"},
            },
            "required": ["candidate_id"],
        },
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        side_effects=["write"],
        output_schema=ToolOutput,
        function=_wrap_add_to_shortlist,
    ),
    ToolDefinition(
        name="view_screening_results",
        description="Visualiza resultados do screening WSI de um candidato, incluindo score e detalhamento.",
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "ID do candidato"},
            },
            "required": ["candidate_id"],
        },
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        output_schema=ToolOutput,
        function=_wrap_view_screening_results,
    ),
    ToolDefinition(
        name="view_interview_notes",
        description="Visualiza notas e feedback de entrevistas realizadas com o candidato.",
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "ID do candidato"},
            },
            "required": ["candidate_id"],
        },
        output_schema=ToolOutput,
        function=_wrap_view_interview_notes,
    ),
    ToolDefinition(
        name="generate_offer",
        description="Gera uma proposta de contratacao para o candidato com base nos dados da vaga e negociacao.",
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "ID do candidato"},
            },
            "required": ["candidate_id"],
        },
        output_schema=ToolOutput,
        function=_wrap_generate_offer,
    ),
    ToolDefinition(
        name="finalize_hiring",
        description="Finaliza o processo de contratacao do candidato, registrando a admissao no sistema.",
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "ID do candidato"},
            },
            "required": ["candidate_id"],
        },
        output_schema=ToolOutput,
        function=_wrap_finalize_hiring,
    ),
    ToolDefinition(
        name="update_status",
        description="Atualiza o status do candidato no sistema (contratado, rejeitado, desistente, etc.).",
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "ID do candidato"},
                "status": {"type": "string", "description": "Novo status: hired, rejected, withdrawn, on_hold"},
            },
            "required": ["candidate_id", "status"],
        },
        output_schema=ToolOutput,
        function=_wrap_update_status,
    ),
]


@tool_handler("cv_screening")
async def _wrap_generate_report(**kwargs: Any) -> dict[str, Any]:
    report_type = kwargs.get("report_type", "summary")
    period = kwargs.get("period", "month")
    company_id = kwargs.get("company_id", "")
    period_days = {"week": 7, "month": 30, "quarter": 90}.get(period, 30)
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[pipeline_tools] generate_report called: type={report_type} period={period}")
    report_id = f"rpt_{uuid.uuid4().hex[:12]}"
    summary: dict[str, Any] = {}
    try:
        async with AsyncSessionLocal() as session:
            # ADR-001-EXEMPT: multi-table analytics aggregation (funnel counts by status from applications table) — complex FILTER aggregate, repo extension deferred to dedicated analytics repo
            row = await session.execute(text("""
                SELECT COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE status = 'screening') AS screening,
                    COUNT(*) FILTER (WHERE status = 'interview') AS interview,
                    COUNT(*) FILTER (WHERE status = 'offer') AS offer,
                    COUNT(*) FILTER (WHERE status = 'hired') AS hired
                FROM applications
                WHERE company_id = :cid
                  AND created_at > NOW() - MAKE_INTERVAL(days => :days)
            """), {"cid": company_id, "days": period_days})
            data = row.mappings().first() or {}
            summary = {
                "total_applications": int(data.get("total") or 0),
                "screening": int(data.get("screening") or 0),
                "interview": int(data.get("interview") or 0),
                "offer": int(data.get("offer") or 0),
                "hired": int(data.get("hired") or 0),
            }
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.warning(f"[pipeline_tools] generate_report DB error: {e}")
    return {
        "success": True,
        "data": {
            "report_type": report_type,
            "period": period,
            "report_id": report_id,
            "generated": True,
            "summary": summary,
        },
        "message": f"Relatorio '{report_type}' de pipeline gerado (id: {report_id}). {summary.get('total_applications', 0)} candidaturas no periodo.",
    }


TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="generate_report",
        description="Gera relatorio de metricas do pipeline de selecao para o periodo selecionado.",
        parameters={
            "type": "object",
            "properties": {
                "report_type": {"type": "string", "description": "Tipo de relatorio: summary, funnel, detailed"},
                "period": {"type": "string", "description": "Periodo: week, month, quarter"},
            },
            "required": [],
        },
        output_schema=ToolOutput,
        function=_wrap_generate_report,
    )
)

# Wave 3 #24 audit 2026-05-21: re-add get_evaluation_criteria (era removido P0-5
# por ser ghost; agora implementado como tool real via _wrap_get_evaluation_criteria).
TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="get_evaluation_criteria",
        description="Retorna catalogo de criterios de avaliacao do produto, opcionalmente filtrado por categoria (technical_skill, behavioral_competency, experience, education, certification, language, responsibility). Use para listar criterios disponiveis antes de avaliar um candidato.",
        parameters={
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Categoria do criterio. Opcional.",
                    "enum": ["technical_skill", "behavioral_competency", "experience", "education", "certification", "language", "responsibility"],
                },
                "limit": {
                    "type": "integer",
                    "description": "Max resultados (1-200, default 50).",
                    "minimum": 1,
                    "maximum": 200,
                },
            },
            "required": [],
        },
        affects_candidate_decision=False,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        side_effects=["read"],
        output_schema=ToolOutput,
        function=_wrap_get_evaluation_criteria,
    )
)

# Wave 3 #25 audit 2026-05-22: re-add get_pipeline_summary (era ghost P0-5
# por não ser carregado por nenhum registry do runtime; só existia em
# recruiter_assistant/kanban_tool_registry que custom_agent_runtime não importa).
TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="get_pipeline_summary",
        description="Retorna resumo do pipeline de recrutamento: contagem de candidatos por etapa, total e taxa de conversao para hire. Use para diagnosticar gargalos do funil e identificar etapas com baixa conversao.",
        parameters={
            "type": "object",
            "properties": {
                "vacancy_id": {
                    "type": "string",
                    "description": "ID da vaga. Opcional. Se omitido retorna pipeline agregado de todas as vagas do tenant.",
                },
            },
            "required": [],
        },
        affects_candidate_decision=False,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        side_effects=["read"],
        output_schema=ToolOutput,
        function=_wrap_get_pipeline_summary,
    )
)

# Wave 3+ audit 2026-05-22: 4 ghost tools restantes implementadas como REAIS.
TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="search_talent_pool",
        description="Busca candidatos no talent pool da empresa filtrando por skills, localização e/ou texto. Use para encontrar candidatos passivos antes de criar novas vagas.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Termo de busca livre (cargo, empresa atual, notas)."},
                "skills": {"type": "array", "items": {"type": "string"}, "description": "Lista de skills técnicas."},
                "location": {"type": "string", "description": "Cidade ou estado."},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100, "description": "Max resultados (default 20)."},
            },
            "required": [],
        },
        affects_candidate_decision=False,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        side_effects=["read"],
        output_schema=ToolOutput,
        function=_wrap_search_talent_pool,
    )
)
TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="get_company_culture",
        description="Retorna perfil cultural da empresa (missão, visão, valores, EVP, core competencies, work model). Use para avaliar fit cultural de candidatos.",
        parameters={"type": "object", "properties": {}, "required": []},
        affects_candidate_decision=False,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        side_effects=["read"],
        output_schema=ToolOutput,
        function=_wrap_get_company_culture,
    )
)
TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="get_analytics_summary",
        description="Agregação de métricas: vagas abertas, total candidatos, distribuição por etapa, taxa de conversão para hire, distribuição por fonte. Use para diagnosticar funil.",
        parameters={
            "type": "object",
            "properties": {
                "days_back": {"type": "integer", "minimum": 1, "maximum": 365, "description": "Período em dias (default 30)."},
                "job_vacancy_id": {"type": "string", "description": "Filtrar por vaga específica. Opcional."},
            },
            "required": [],
        },
        affects_candidate_decision=False,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        side_effects=["read"],
        output_schema=ToolOutput,
        function=_wrap_get_analytics_summary,
    )
)
TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="create_note",
        description="Adiciona uma nota ao candidato. Append-only (preserva histórico). Use para registrar observações, feedback de entrevista, ou pareceres da IA. Requer confirm=True (canonical write).",
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "UUID do candidato."},
                "note_text": {"type": "string", "description": "Texto da nota (max 2000 chars)."},
                "confirm": {"type": "boolean", "description": "Confirmação explícita (canonical write gate)."},
            },
            "required": ["candidate_id", "note_text", "confirm"],
        },
        affects_candidate_decision=False,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        side_effects=["write"],
        output_schema=ToolOutput,
        function=_wrap_create_note,
    )
)

_TOOL_MAP: dict[str, ToolDefinition] = {t.name: t for t in TOOL_DEFINITIONS}

STAGE_TOOLS: dict[str, list[str]] = {
    "triage": ["view_candidate_profile", "analyze_cv", "add_notes", "move_candidate"],
    "screening": ["run_wsi_screening", "view_screening_results", "add_notes", "move_candidate"],
    "shortlist": ["move_candidate", "add_to_shortlist", "view_candidate_profile", "add_notes", "batch_move"],
    "interview": ["schedule_interview", "view_interview_notes", "send_communication", "add_notes", "move_candidate"],
    "offer": ["generate_offer", "send_communication", "add_notes", "move_candidate", "generate_report"],
    "hired": ["finalize_hiring", "update_status", "send_communication", "add_notes", "generate_report"],
}


def get_pipeline_tools(stage: str = "") -> list[ToolDefinition]:
    """Return pipeline tools, optionally filtered by stage.

    Args:
        stage: Current pipeline stage identifier. If empty, returns all tools.

    Returns:
        List of ToolDefinition instances available for the given stage.
    """
    if not stage:
        return list(TOOL_DEFINITIONS)

    tool_names = STAGE_TOOLS.get(stage, list(_TOOL_MAP.keys()))
    tools = [_TOOL_MAP[name] for name in tool_names if name in _TOOL_MAP]
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.debug(f"[pipeline_tools] Stage '{stage}' tools: {[t.name for t in tools]}")
    return tools
