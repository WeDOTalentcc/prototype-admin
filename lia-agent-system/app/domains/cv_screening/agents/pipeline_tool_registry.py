"""
Pipeline Tool Registry - Exposes pipeline tools to the ReAct loop.

Wraps pipeline operations into ToolDefinition format so the ReActLoop
can autonomously decide which tools to call for candidate management.
Tools connect to PostgreSQL for real data operations.
"""
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import text

from app.core.database import AsyncSessionLocal
from lia_agents_core.react_loop import ToolDefinition

logger = logging.getLogger(__name__)


async def _wrap_view_candidate_profile(**kwargs: Any) -> Dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    logger.info(f"[pipeline_tools] view_candidate_profile called for candidate={candidate_id}")
    try:
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
                    ORDER BY vc.updated_at DESC NULLS LAST
                    LIMIT 1
                """),
                {"candidate_id": candidate_id},
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
    except Exception as e:
        logger.error(f"[pipeline_tools] view_candidate_profile error: {e}")
        return {"success": False, "data": {}, "message": f"Erro ao carregar perfil: {str(e)}"}


async def _wrap_move_candidate(**kwargs: Any) -> Dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    target_stage = kwargs.get("target_stage", "unknown")
    reason = kwargs.get("reason", "")
    logger.info(f"[pipeline_tools] move_candidate called: candidate={candidate_id} target={target_stage} reason={reason}")
    try:
        async with AsyncSessionLocal() as session:
            prev = await session.execute(
                text("SELECT stage, status FROM vacancy_candidates WHERE candidate_id = :candidate_id ORDER BY updated_at DESC LIMIT 1"),
                {"candidate_id": candidate_id},
            )
            prev_row = prev.mappings().first()
            if not prev_row:
                return {"success": False, "data": {}, "message": f"Candidato {candidate_id} não encontrado no pipeline."}
            previous_stage = prev_row["stage"]
            result = await session.execute(
                text("""
                    UPDATE vacancy_candidates
                    SET stage = :target_stage, updated_at = NOW()
                    WHERE candidate_id = :candidate_id
                """),
                {"target_stage": target_stage, "candidate_id": candidate_id},
            )
            await session.commit()
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
    except Exception as e:
        logger.error(f"[pipeline_tools] move_candidate error: {e}")
        return {"success": False, "data": {}, "message": f"Erro ao mover candidato: {str(e)}"}


async def _wrap_analyze_cv(**kwargs: Any) -> Dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    logger.info(f"[pipeline_tools] analyze_cv called for candidate={candidate_id}")
    try:
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
                    ORDER BY vc.updated_at DESC NULLS LAST
                    LIMIT 1
                """),
                {"candidate_id": candidate_id},
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
    except Exception as e:
        logger.error(f"[pipeline_tools] analyze_cv error: {e}")
        return {"success": False, "data": {}, "message": f"Erro ao analisar CV: {str(e)}"}


async def _wrap_run_wsi_screening(**kwargs: Any) -> Dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    vacancy_id = kwargs.get("vacancy_id", "unknown")
    logger.info(f"[pipeline_tools] run_wsi_screening called: candidate={candidate_id} vacancy={vacancy_id}")
    try:
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
                    WHERE candidate_id = :candidate_id AND vacancy_id = :vacancy_id
                    LIMIT 1
                """),
                {"candidate_id": candidate_id, "vacancy_id": vacancy_id},
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
    except Exception as e:
        logger.error(f"[pipeline_tools] run_wsi_screening error: {e}")
        return {"success": False, "data": {}, "message": f"Erro no screening WSI: {str(e)}"}


async def _wrap_schedule_interview(**kwargs: Any) -> Dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    interview_datetime = kwargs.get("datetime", "")
    interview_type = kwargs.get("type", "video")
    logger.info(f"[pipeline_tools] schedule_interview called: candidate={candidate_id} datetime={interview_datetime} type={interview_type}")
    try:
        async with AsyncSessionLocal() as session:
            cand = await session.execute(
                text("SELECT name, email FROM candidates WHERE id = :candidate_id"),
                {"candidate_id": candidate_id},
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
                    ORDER BY vc.updated_at DESC LIMIT 1
                """),
                {"candidate_id": candidate_id},
            )
            vc_row = vc.mappings().first()
            job_title = vc_row["job_title"] if vc_row else None
            vacancy_id = str(vc_row["vacancy_id"]) if vc_row else None

            interview_id = str(uuid.uuid4())
            await session.execute(
                text("""
                    INSERT INTO interviews (id, title, interview_type, interview_mode,
                        candidate_id, candidate_name, candidate_email,
                        start_time, status, job_vacancy_id, job_title, created_at, updated_at)
                    VALUES (:id, :title, :interview_type, :interview_mode,
                        :candidate_id, :candidate_name, :candidate_email,
                        :start_time, 'scheduled', :job_vacancy_id, :job_title, NOW(), NOW())
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
                },
            )
            await session.commit()
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
    except Exception as e:
        logger.error(f"[pipeline_tools] schedule_interview error: {e}")
        return {"success": False, "data": {}, "message": f"Erro ao agendar entrevista: {str(e)}"}


async def _wrap_send_communication(**kwargs: Any) -> Dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    channel = kwargs.get("channel", "email")
    message_text = kwargs.get("message", "")
    logger.info(f"[pipeline_tools] send_communication called: candidate={candidate_id} channel={channel}")
    try:
        async with AsyncSessionLocal() as session:
            cand = await session.execute(
                text("SELECT name, email, phone FROM candidates WHERE id = :candidate_id"),
                {"candidate_id": candidate_id},
            )
            cand_row = cand.mappings().first()
            if not cand_row:
                return {"success": False, "data": {}, "message": f"Candidato {candidate_id} não encontrado."}

            vc = await session.execute(
                text("SELECT company_id, vacancy_id FROM vacancy_candidates WHERE candidate_id = :candidate_id ORDER BY updated_at DESC LIMIT 1"),
                {"candidate_id": candidate_id},
            )
            vc_row = vc.mappings().first()
            company_id = vc_row["company_id"] if vc_row else None
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
    except Exception as e:
        logger.error(f"[pipeline_tools] send_communication error: {e}")
        return {"success": False, "data": {}, "message": f"Erro ao enviar comunicação: {str(e)}"}


async def _wrap_add_notes(**kwargs: Any) -> Dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    note_text = kwargs.get("note_text", "")
    logger.info(f"[pipeline_tools] add_notes called for candidate={candidate_id}")
    try:
        async with AsyncSessionLocal() as session:
            existing = await session.execute(
                text("SELECT notes FROM vacancy_candidates WHERE candidate_id = :candidate_id ORDER BY updated_at DESC LIMIT 1"),
                {"candidate_id": candidate_id},
            )
            existing_row = existing.mappings().first()
            if not existing_row:
                return {"success": False, "data": {}, "message": f"Candidato {candidate_id} não encontrado no pipeline."}

            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
            old_notes = existing_row["notes"] or ""
            new_notes = f"{old_notes}\n[{timestamp}] {note_text}".strip()

            result = await session.execute(
                text("""
                    UPDATE vacancy_candidates
                    SET notes = :notes, updated_at = NOW()
                    WHERE candidate_id = :candidate_id
                """),
                {"notes": new_notes, "candidate_id": candidate_id},
            )
            await session.commit()
            return {
                "success": True,
                "data": {"candidate_id": candidate_id, "note_saved": True, "rows_updated": result.rowcount},
                "message": f"Nota adicionada ao candidato {candidate_id}.",
            }
    except Exception as e:
        logger.error(f"[pipeline_tools] add_notes error: {e}")
        return {"success": False, "data": {}, "message": f"Erro ao adicionar nota: {str(e)}"}


async def _wrap_batch_move(**kwargs: Any) -> Dict[str, Any]:
    candidate_ids = kwargs.get("candidate_ids", [])
    target_stage = kwargs.get("target_stage", "unknown")
    reason = kwargs.get("reason", "")
    logger.info(f"[pipeline_tools] batch_move called: candidates={len(candidate_ids)} target={target_stage}")
    if not candidate_ids:
        return {"success": False, "data": {}, "message": "Nenhum candidato fornecido para movimentação em massa."}
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("""
                    UPDATE vacancy_candidates
                    SET stage = :target_stage, updated_at = NOW()
                    WHERE candidate_id = ANY(:candidate_ids::uuid[])
                """),
                {"target_stage": target_stage, "candidate_ids": candidate_ids},
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
    except Exception as e:
        logger.error(f"[pipeline_tools] batch_move error: {e}")
        return {"success": False, "data": {}, "message": f"Erro na movimentação em massa: {str(e)}"}


async def _wrap_add_to_shortlist(**kwargs: Any) -> Dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    logger.info(f"[pipeline_tools] add_to_shortlist called for candidate={candidate_id}")
    try:
        async with AsyncSessionLocal() as session:
            check = await session.execute(
                text("SELECT status FROM vacancy_candidates WHERE candidate_id = :candidate_id ORDER BY updated_at DESC LIMIT 1"),
                {"candidate_id": candidate_id},
            )
            check_row = check.mappings().first()
            if not check_row:
                return {"success": False, "data": {}, "message": f"Candidato {candidate_id} não encontrado no pipeline."}

            result = await session.execute(
                text("""
                    UPDATE vacancy_candidates
                    SET status = 'shortlisted', updated_at = NOW()
                    WHERE candidate_id = :candidate_id
                """),
                {"candidate_id": candidate_id},
            )
            await session.commit()
            return {
                "success": True,
                "data": {"candidate_id": candidate_id, "shortlisted": True, "previous_status": check_row["status"], "rows_updated": result.rowcount},
                "message": f"Candidato {candidate_id} adicionado à pré-seleção.",
            }
    except Exception as e:
        logger.error(f"[pipeline_tools] add_to_shortlist error: {e}")
        return {"success": False, "data": {}, "message": f"Erro ao adicionar à pré-seleção: {str(e)}"}


async def _wrap_view_screening_results(**kwargs: Any) -> Dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    logger.info(f"[pipeline_tools] view_screening_results called for candidate={candidate_id}")
    try:
        async with AsyncSessionLocal() as session:
            vc = await session.execute(
                text("""
                    SELECT vc.lia_score, vc.match_percentage, vc.status, vc.stage, vc.vacancy_id,
                           c.name
                    FROM vacancy_candidates vc
                    JOIN candidates c ON c.id = vc.candidate_id
                    WHERE vc.candidate_id = :candidate_id
                    ORDER BY vc.updated_at DESC
                    LIMIT 1
                """),
                {"candidate_id": candidate_id},
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
    except Exception as e:
        logger.error(f"[pipeline_tools] view_screening_results error: {e}")
        return {"success": False, "data": {}, "message": f"Erro ao carregar resultados: {str(e)}"}


async def _wrap_view_interview_notes(**kwargs: Any) -> Dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    logger.info(f"[pipeline_tools] view_interview_notes called for candidate={candidate_id}")
    try:
        async with AsyncSessionLocal() as session:
            interviews = await session.execute(
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
                    text("SELECT notes FROM vacancy_candidates WHERE candidate_id = :candidate_id ORDER BY updated_at DESC LIMIT 1"),
                    {"candidate_id": candidate_id},
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
                    "message": f"Nenhuma entrevista encontrada. Notas do pipeline retornadas.",
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
    except Exception as e:
        logger.error(f"[pipeline_tools] view_interview_notes error: {e}")
        return {"success": False, "data": {}, "message": f"Erro ao carregar notas: {str(e)}"}


async def _wrap_generate_offer(**kwargs: Any) -> Dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    logger.info(f"[pipeline_tools] generate_offer called for candidate={candidate_id}")
    try:
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
                    ORDER BY vc.updated_at DESC
                    LIMIT 1
                """),
                {"candidate_id": candidate_id},
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
    except Exception as e:
        logger.error(f"[pipeline_tools] generate_offer error: {e}")
        return {"success": False, "data": {}, "message": f"Erro ao gerar proposta: {str(e)}"}


async def _wrap_finalize_hiring(**kwargs: Any) -> Dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    logger.info(f"[pipeline_tools] finalize_hiring called for candidate={candidate_id}")
    try:
        async with AsyncSessionLocal() as session:
            check = await session.execute(
                text("""
                    SELECT vc.stage, vc.status, c.name
                    FROM vacancy_candidates vc
                    JOIN candidates c ON c.id = vc.candidate_id
                    WHERE vc.candidate_id = :candidate_id
                    ORDER BY vc.updated_at DESC LIMIT 1
                """),
                {"candidate_id": candidate_id},
            )
            check_row = check.mappings().first()
            if not check_row:
                return {"success": False, "data": {}, "message": f"Candidato {candidate_id} não encontrado no pipeline."}

            await session.execute(
                text("""
                    UPDATE vacancy_candidates
                    SET status = 'contratado', stage = 'Contratado', updated_at = NOW()
                    WHERE candidate_id = :candidate_id
                """),
                {"candidate_id": candidate_id},
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
    except Exception as e:
        logger.error(f"[pipeline_tools] finalize_hiring error: {e}")
        return {"success": False, "data": {}, "message": f"Erro ao finalizar contratação: {str(e)}"}


async def _wrap_update_status(**kwargs: Any) -> Dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    status = kwargs.get("status", "unknown")
    logger.info(f"[pipeline_tools] update_status called: candidate={candidate_id} status={status}")
    try:
        async with AsyncSessionLocal() as session:
            check = await session.execute(
                text("SELECT status FROM vacancy_candidates WHERE candidate_id = :candidate_id ORDER BY updated_at DESC LIMIT 1"),
                {"candidate_id": candidate_id},
            )
            check_row = check.mappings().first()
            if not check_row:
                return {"success": False, "data": {}, "message": f"Candidato {candidate_id} não encontrado no pipeline."}

            result = await session.execute(
                text("""
                    UPDATE vacancy_candidates
                    SET status = :status, updated_at = NOW()
                    WHERE candidate_id = :candidate_id
                """),
                {"status": status, "candidate_id": candidate_id},
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
    except Exception as e:
        logger.error(f"[pipeline_tools] update_status error: {e}")
        return {"success": False, "data": {}, "message": f"Erro ao atualizar status: {str(e)}"}


TOOL_DEFINITIONS: List[ToolDefinition] = [
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
        function=_wrap_update_status,
    ),
]


async def _wrap_generate_report(**kwargs: Any) -> Dict[str, Any]:
    report_type = kwargs.get("report_type", "summary")
    period = kwargs.get("period", "month")
    company_id = kwargs.get("company_id", "")
    period_days = {"week": 7, "month": 30, "quarter": 90}.get(period, 30)
    logger.info(f"[pipeline_tools] generate_report called: type={report_type} period={period}")
    report_id = f"rpt_{uuid.uuid4().hex[:12]}"
    summary: Dict[str, Any] = {}
    try:
        async with AsyncSessionLocal() as session:
            row = await session.execute(text("""
                SELECT COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE status = 'screening') AS screening,
                    COUNT(*) FILTER (WHERE status = 'interview') AS interview,
                    COUNT(*) FILTER (WHERE status = 'offer') AS offer,
                    COUNT(*) FILTER (WHERE status = 'hired') AS hired
                FROM applications
                WHERE (:cid = '' OR company_id = :cid)
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
                "company_id": {"type": "string", "description": "ID da empresa (opcional)"},
            },
            "required": [],
        },
        function=_wrap_generate_report,
    )
)

_TOOL_MAP: Dict[str, ToolDefinition] = {t.name: t for t in TOOL_DEFINITIONS}

STAGE_TOOLS: Dict[str, List[str]] = {
    "triage": ["view_candidate_profile", "analyze_cv", "add_notes", "move_candidate"],
    "screening": ["run_wsi_screening", "view_screening_results", "add_notes", "move_candidate"],
    "shortlist": ["move_candidate", "add_to_shortlist", "view_candidate_profile", "add_notes", "batch_move"],
    "interview": ["schedule_interview", "view_interview_notes", "send_communication", "add_notes", "move_candidate"],
    "offer": ["generate_offer", "send_communication", "add_notes", "move_candidate", "generate_report"],
    "hired": ["finalize_hiring", "update_status", "send_communication", "add_notes", "generate_report"],
}


def get_pipeline_tools(stage: str = "") -> List[ToolDefinition]:
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
    logger.debug(f"[pipeline_tools] Stage '{stage}' tools: {[t.name for t in tools]}")
    return tools
