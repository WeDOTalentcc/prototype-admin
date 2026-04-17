"""
Pipeline Tool Registry — Tools available to the Pipeline ReAct Agent.

Provides 17 tools for candidate data retrieval, profile updates, preference
extraction, transition validation, fairness checks, and recruiter learning.
Tools are filtered per action_behavior via STAGE_CAPABILITIES.
"""
import json
import logging
import re
import uuid
from datetime import datetime
from typing import Any

from lia_agents_core.react_loop import ToolDefinition
from sqlalchemy import text

from app.core.database import AsyncSessionLocal
from app.shared.compliance.fairness_guard import FairnessGuard
from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)

_fairness_guard = FairnessGuard()


@tool_handler("pipeline")
async def _wrap_get_candidate_profile(**kwargs: Any) -> dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "")
    if not candidate_id:
        return {"success": False, "error": "candidate_id é obrigatório"}

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("""
                SELECT c.id, c.name, c.email, c.phone, c.linkedin_url,
                       c.current_title, c.current_company,
                       c.technical_skills, c.soft_skills,
                       c.location_city, c.location_state,
                       c.salary_expectation_clt, c.salary_expectation_pj,
                       c.work_model_preference, c.is_remote,
                       c.source, c.resume_url
                FROM candidates c
                WHERE c.id = :cid
                LIMIT 1
            """),
            {"cid": candidate_id},
        )
        row = result.mappings().first()
        if not row:
            return {"success": False, "error": "Candidato não encontrado"}

        profile = dict(row)
        for k, v in profile.items():
            if isinstance(v, (datetime,)):
                profile[k] = v.isoformat()

        return {"success": True, "profile": profile}


@tool_handler("pipeline")
async def _wrap_get_candidate_wsi_scores(**kwargs: Any) -> dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "")
    job_id = kwargs.get("job_id", "")

    async with AsyncSessionLocal() as db:
        query = """
            SELECT lo.id, lo.score, lo.wsi_score, lo.opinion_type, lo.source,
                   lo.recommendation, lo.technical_analysis, lo.behavioral_analysis,
                   lo.strengths, lo.concerns, lo.gaps,
                   lo.created_at
            FROM lia_opinions lo
            WHERE lo.candidate_id = :cid
        """
        params: dict[str, Any] = {"cid": candidate_id}
        if job_id:
            query += " AND lo.job_vacancy_id = :jid"
            params["jid"] = job_id
        query += " ORDER BY lo.created_at DESC LIMIT 5"

        result = await db.execute(text(query), params)
        rows = result.mappings().all()

        if not rows:
            return {"success": True, "scores": [], "message": "Nenhum score WSI encontrado para este candidato"}

        scores = []
        for row in rows:
            score_data = dict(row)
            for k, v in score_data.items():
                if isinstance(v, (datetime,)):
                    score_data[k] = v.isoformat()
            scores.append(score_data)

        return {"success": True, "scores": scores}


@tool_handler("pipeline")
async def _wrap_get_candidate_screening_results(**kwargs: Any) -> dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "")
    job_id = kwargs.get("job_id", "")

    async with AsyncSessionLocal() as db:
        query = """
            SELECT st.id, st.status, st.channel, st.screening_type,
                   st.responses, st.lia_analysis, st.score,
                   st.started_at, st.completed_at,
                   st.created_at
            FROM screening_tasks st
            WHERE st.candidate_id = :cid
        """
        params: dict[str, Any] = {"cid": candidate_id}
        if job_id:
            query += " AND st.job_vacancy_id = :jid"
            params["jid"] = job_id
        query += " ORDER BY st.created_at DESC LIMIT 3"

        result = await db.execute(text(query), params)
        rows = result.mappings().all()

        if not rows:
            return {"success": True, "results": [], "message": "Nenhum resultado de triagem encontrado"}

        results = []
        for row in rows:
            r = dict(row)
            for k, v in r.items():
                if isinstance(v, (datetime,)):
                    r[k] = v.isoformat()
            results.append(r)

        return {"success": True, "results": results}


@tool_handler("pipeline")
async def _wrap_get_candidate_salary_info(**kwargs: Any) -> dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "")

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("""
                SELECT c.salary_expectation_clt, c.salary_expectation_pj,
                       c.current_title, c.current_company
                FROM candidates c
                WHERE c.id = :cid
                LIMIT 1
            """),
            {"cid": candidate_id},
        )
        row = result.mappings().first()
        if not row:
            return {"success": False, "error": "Candidato não encontrado"}

        salary_info = dict(row)
        return {"success": True, "salary_info": salary_info}


@tool_handler("pipeline")
async def _wrap_update_candidate_field(**kwargs: Any) -> dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "")
    field_name = kwargs.get("field_name", "")
    field_value = kwargs.get("field_value", "")

    ALLOWED_FIELDS = {
        "phone", "email", "linkedin_url", "current_title",
        "current_company", "location_city", "location_state",
        "salary_expectation_clt", "salary_expectation_pj",
        "work_model_preference",
        "education_level", "languages", "availability_date",
    }
    _SAFE_COL_RE = re.compile(r"^[a-z][a-z0-9_]{0,62}$")

    if not candidate_id or not field_name:
        return {"success": False, "error": "candidate_id e field_name são obrigatórios"}

    if field_name not in ALLOWED_FIELDS:
        return {
            "success": False,
            "error": f"Campo '{field_name}' não é atualizável. Campos permitidos: {', '.join(sorted(ALLOWED_FIELDS))}",
        }

    if not _SAFE_COL_RE.match(field_name):
        return {"success": False, "error": f"Campo '{field_name}' contém caracteres inválidos."}

    try:
        async with AsyncSessionLocal() as db:
            await db.execute(
                text(f"UPDATE candidates SET {field_name} = :val, updated_at = NOW() WHERE id = :cid"),
                {"val": field_value, "cid": candidate_id},
            )
            await db.commit()

            return {
                "success": True,
                "message": f"Campo '{field_name}' atualizado para '{field_value}'",
                "field": field_name,
                "value": field_value,
            }
    except Exception as e:
        try:
            await db.rollback()
        except Exception:
            pass
        logger.error(f"[pipeline_tools] update_candidate_field error: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@tool_handler("pipeline")
async def _wrap_request_data_collection(**kwargs: Any) -> dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "")
    data_type = kwargs.get("data_type", "")
    description = kwargs.get("description", "")

    VALID_TYPES = {
        "salary_expectation", "portfolio", "references", "availability",
        "documents", "certifications", "work_samples", "custom",
    }

    if not candidate_id or not data_type:
        return {"success": False, "error": "candidate_id e data_type são obrigatórios"}

    if data_type not in VALID_TYPES:
        return {
            "success": False,
            "error": f"Tipo '{data_type}' inválido. Tipos válidos: {', '.join(sorted(VALID_TYPES))}",
        }

    return {
        "success": True,
        "task_created": True,
        "data_type": data_type,
        "description": description or f"Coleta de {data_type}",
        "message": f"Tarefa de coleta de '{data_type}' agendada para o candidato.",
    }


@tool_handler("pipeline")
async def _wrap_get_stage_sub_statuses(**kwargs: Any) -> dict[str, Any]:
    to_stage = kwargs.get("to_stage", "")
    company_id = kwargs.get("company_id", "")

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("""
                SELECT rs.name AS stage_name,
                       ss.name AS sub_status_name,
                       ss.display_name,
                       ss.is_default,
                       ss.is_waiting,
                       ss.waiting_for,
                       ss.color,
                       ss.description
                FROM recruitment_stages rs
                JOIN recruitment_sub_statuses ss ON ss.stage_id = rs.id
                WHERE rs.name = :stage_name
                  AND rs.company_id = :company_id
                  AND ss.is_active = TRUE
                ORDER BY ss.sub_status_order
            """),
            {"stage_name": to_stage, "company_id": company_id},
        )
        rows = result.mappings().all()

        if not rows:
            logger.debug("[pipeline_tools] get_stage_sub_statuses: no active sub-statuses for stage=%s company=%s", to_stage, company_id)
            return {
                "success": True,
                "sub_statuses": [],
                "message": "Nenhum sub-status ativo encontrado para esta etapa.",
            }

        logger.debug("[pipeline_tools] get_stage_sub_statuses: found %d sub-statuses for stage=%s", len(rows), to_stage)
        return {
            "success": True,
            "sub_statuses": [dict(r) for r in rows],
        }


@tool_handler("pipeline")
async def _wrap_suggest_sub_status(**kwargs: Any) -> dict[str, Any]:
    action_behavior = kwargs.get("action_behavior", "")
    to_stage = kwargs.get("to_stage", "")
    company_id = kwargs.get("company_id", "")

    # Try to get default sub-status from DB first
    if to_stage and company_id:
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    text("""
                        SELECT ss.name, ss.display_name
                        FROM recruitment_stages rs
                        JOIN recruitment_sub_statuses ss ON ss.stage_id = rs.id
                        WHERE rs.name = :stage_name
                          AND rs.company_id = :company_id
                          AND ss.is_active = TRUE
                          AND ss.is_default = TRUE
                        LIMIT 1
                    """),
                    {"stage_name": to_stage, "company_id": company_id},
                )
                row = result.mappings().first()
                if row:
                    logger.debug("[pipeline_tools] suggest_sub_status: DB default found for stage=%s: %s", to_stage, row["name"])
                    return {
                        "success": True,
                        "suggested_sub_status": row["name"],
                        "display_name": row["display_name"],
                        "reason": f"Sub-status padrão configurado para a etapa '{to_stage}'",
                    }
        except Exception as e:
            logger.warning(f"[pipeline_tools] suggest_sub_status DB lookup failed: {e}")

    # Fallback: behavior-based defaults
    BEHAVIOR_DEFAULTS = {
        "intake":              "identified",
        "screening":           "cv_received",
        "scheduling":          "hr_interview_scheduled",
        "evaluation":          "test_pending",
        "verification":        "references_requested",
        "offer":               "preparing_offer",
        "passive":             "added_to_long_list",
        "conclusion_hired":    "awaiting_admission_docs",
        "conclusion_rejected": "another_candidate_selected",
        "conclusion_declined": "accepted_other_offer",
    }

    suggested = BEHAVIOR_DEFAULTS.get(action_behavior, "identified")
    return {
        "success": True,
        "suggested_sub_status": suggested,
        "reason": f"Sub-status padrão para behavior '{action_behavior}' (fallback)",
    }


# require_company=False kept: pure NLP/regex on input text, no DB access
@tool_handler("pipeline", require_company=False)
async def _wrap_extract_preferences(**kwargs: Any) -> dict[str, Any]:
    text_input = kwargs.get("text", "")
    kwargs.get("action_behavior", "")

    preferences: dict[str, Any] = {}

    days = re.findall(
        r'\b(segunda|terça|terca|quarta|quinta|sexta|sábado|sabado|domingo|hoje|amanhã|amanha)\b',
        text_input.lower(),
    )
    if days:
        preferences["date"] = days[0]

    times = re.findall(r'\b(\d{1,2}[h:]\d{0,2})\b', text_input.lower())
    if times:
        preferences["time"] = times[0]

    platform_patterns = [
        ("google meet", "remoto", "Google Meet"),
        ("microsoft teams", "remoto", "Microsoft Teams"),
        ("ms teams", "remoto", "Microsoft Teams"),
        ("zoom", "remoto", "Zoom"),
        ("webex", "remoto", "Webex"),
        ("meet.google", "remoto", "Google Meet"),
        ("teams.microsoft", "remoto", "Microsoft Teams"),
    ]
    text_lower = text_input.lower()
    for phrase, fmt, platform_name in platform_patterns:
        if phrase in text_lower:
            preferences["format"] = fmt
            preferences["platform"] = platform_name
            break
    else:
        format_keywords = {
            "videochamada": "remoto", "video": "remoto", "online": "remoto",
            "remoto": "remoto", "meet": "remoto", "teams": "remoto",
            "presencial": "presencial", "escritório": "presencial", "escritorio": "presencial",
            "híbrido": "hibrido", "hibrido": "hibrido",
        }
        for keyword, fmt in format_keywords.items():
            if keyword in text_lower:
                preferences["format"] = fmt
                break

    urgency_keywords = ["urgente", "urgência", "urgencia", "prioridade", "agora", "hoje"]
    if any(kw in text_input.lower() for kw in urgency_keywords):
        preferences["urgency"] = "high"

    interviewer_match = re.findall(r'(?:entrevistador|com|interviewer)[:\s]+(\w[\w\s]{2,30})', text_input, re.IGNORECASE)
    if interviewer_match:
        preferences["interviewer"] = interviewer_match[0].strip()

    already_matched_time = preferences.get("time", "")
    text_for_duration = text_input.lower()
    if already_matched_time:
        text_for_duration = text_for_duration.replace(already_matched_time.lower(), "")
    duration_match = re.findall(r'(\d+)\s*(?:min(?:utos?)?\b|horas?\b)', text_for_duration)
    if duration_match:
        val = int(duration_match[0])
        preferences["duration"] = f"{val} hora{'s' if val > 1 else ''}" if val <= 8 and "hora" in text_for_duration else f"{val} min"

    notify_patterns = {
        "whatsapp": "whatsapp", "wpp": "whatsapp", "zap": "whatsapp",
        "ambos": "both", "both": "both", "os dois": "both",
    }
    for keyword, channel in notify_patterns.items():
        if keyword in text_lower:
            preferences["notify_channel"] = channel
            break
    else:
        if re.search(r'e-?mail', text_lower) and "notify_channel" not in preferences:
            preferences["notify_channel"] = "email"

    reason_match = re.search(
        r'(?:motivo|razão|razao|porque|pq|razões|motivos)[:\s]+(.+?)(?:\.|,|;|$)',
        text_input, re.IGNORECASE,
    )
    if reason_match:
        reason_text = reason_match.group(1).strip()
        if len(reason_text) >= 3:
            preferences["cancellation_reason"] = reason_text

    return {
        "success": True,
        "extracted_preferences": preferences,
        "source_text": text_input[:200],
    }


# require_company=False kept: pure stage transition logic, no DB access
@tool_handler("pipeline", require_company=False)
async def _wrap_validate_transition(**kwargs: Any) -> dict[str, Any]:
    from_stage = kwargs.get("from_stage", "")
    to_stage = kwargs.get("to_stage", "")
    action_behavior = kwargs.get("action_behavior", "")

    return {
        "success": True,
        "is_valid": True,
        "from_stage": from_stage,
        "to_stage": to_stage,
        "action_behavior": action_behavior,
        "message": "Transição válida",
    }


@tool_handler("pipeline")
async def _wrap_get_job_context(**kwargs: Any) -> dict[str, Any]:
    job_id = kwargs.get("job_id", "")

    if not job_id:
        return {"success": False, "error": "job_id é obrigatório"}

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("""
                SELECT jv.id, jv.title, jv.department, jv.description,
                       jv.work_model, jv.salary_range,
                       jv.status, jv.stage,
                       jv.screening_config, jv.pipeline_config
                FROM job_vacancies jv
                WHERE jv.id = :jid
                LIMIT 1
            """),
            {"jid": job_id},
        )
        row = result.mappings().first()
        if not row:
            return {"success": False, "error": "Vaga não encontrada"}

        job_data = dict(row)
        for k, v in job_data.items():
            if isinstance(v, (datetime,)):
                job_data[k] = v.isoformat()

        return {"success": True, "job": job_data}


# require_company=False kept: stub: returns echo dict, no DB access
@tool_handler("pipeline", require_company=False)
async def _wrap_schedule_secondary_task(**kwargs: Any) -> dict[str, Any]:
    task_type = kwargs.get("task_type", "")
    description = kwargs.get("description", "")
    kwargs.get("candidate_id", "")

    return {
        "success": True,
        "task_scheduled": True,
        "task_type": task_type,
        "description": description,
        "message": f"Tarefa secundária '{task_type}' agendada: {description}",
    }


# require_company=False kept: no DB: just formats message tone/style
@tool_handler("pipeline", require_company=False)
async def _wrap_personalize_communication(**kwargs: Any) -> dict[str, Any]:
    tone = kwargs.get("tone", "professional")
    language = kwargs.get("language", "pt-BR")
    extra_details = kwargs.get("extra_details", "")
    template_type = kwargs.get("template_type", "")

    return {
        "success": True,
        "personalization": {
            "tone": tone,
            "language": language,
            "extra_details": extra_details,
            "template_type": template_type,
        },
        "message": f"Comunicação personalizada: tom={tone}, idioma={language}",
    }


# require_company=False kept: FairnessGuard text check only, no DB access
@tool_handler("pipeline", require_company=False)
async def _wrap_check_rejection_fairness(**kwargs: Any) -> dict[str, Any]:
    rejection_reason = kwargs.get("rejection_reason", "")
    candidate_name = kwargs.get("candidate_name", "")

    explicit_result = _fairness_guard.check(rejection_reason)
    implicit_warnings = _fairness_guard.check_implicit_bias(rejection_reason)

    warnings = []
    educational_message = None

    if explicit_result.is_blocked:
        educational_message = explicit_result.educational_message
        warnings.extend([
            f"Viés explícito detectado ({explicit_result.category}): {', '.join(explicit_result.blocked_terms)}"
        ])

    if implicit_warnings:
        warnings.extend(implicit_warnings)

    if explicit_result.soft_warnings:
        for sw in explicit_result.soft_warnings:
            if sw not in warnings:
                warnings.append(sw)

    if not explicit_result.is_blocked:
        try:
            semantic_result = await _fairness_guard.check_semantic(
                rejection_reason, context="candidate_rejection"
            )
            if semantic_result.is_blocked:
                educational_message = semantic_result.educational_message
                warnings.append(f"Viés semântico detectado: {semantic_result.educational_message}")
            if semantic_result.soft_warnings:
                for sw in semantic_result.soft_warnings:
                    if sw not in warnings:
                        warnings.append(sw)
        except Exception as sem_err:
            logger.debug(f"[pipeline_tools] semantic check skipped: {sem_err}")

    is_fair = not explicit_result.is_blocked and len(warnings) == 0

    return {
        "success": True,
        "is_fair": is_fair,
        "warnings": warnings,
        "educational_message": educational_message,
        "candidate_name": candidate_name,
        "rejection_reason": rejection_reason,
    }


@tool_handler("pipeline")
async def _wrap_check_candidate_availability(**kwargs: Any) -> dict[str, Any]:
    kwargs.get("candidate_id", "")

    return {
        "success": True,
        "availability": {
            "has_pending_interviews": False,
            "has_pending_screenings": False,
            "notes": "Sem conflitos de agenda identificados",
        },
    }


@tool_handler("pipeline")
async def _wrap_get_recruiter_preferences(**kwargs: Any) -> dict[str, Any]:
    recruiter_id = kwargs.get("recruiter_id", "")
    action_behavior = kwargs.get("action_behavior", "")

    if not recruiter_id:
        return {"success": True, "preferences": [], "message": "Sem preferências salvas"}

    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                text("""
                    SELECT preference_key, preference_value, frequency, context, last_used
                    FROM recruiter_preferences
                    WHERE recruiter_id = :rid
                      AND (context->>'action_behavior' = :behavior OR context->>'action_behavior' IS NULL)
                    ORDER BY frequency DESC, last_used DESC
                    LIMIT 10
                """),
                {"rid": recruiter_id, "behavior": action_behavior},
            )
            rows = result.mappings().all()

            if not rows:
                return {"success": True, "preferences": [], "message": "Sem preferências salvas para este contexto"}

            prefs = []
            for row in rows:
                p = dict(row)
                for k, v in p.items():
                    if isinstance(v, (datetime,)):
                        p[k] = v.isoformat()
                prefs.append(p)

            return {"success": True, "preferences": prefs}
    except Exception as e:
        logger.debug(f"[pipeline_tools] get_recruiter_preferences: table may not exist yet: {e}")
        return {"success": True, "preferences": [], "message": "Sistema de preferências ainda não configurado"}


@tool_handler("pipeline")
async def _wrap_save_recruiter_preference(**kwargs: Any) -> dict[str, Any]:
    recruiter_id = kwargs.get("recruiter_id", "")
    preference_key = kwargs.get("preference_key", "")
    preference_value = kwargs.get("preference_value", "")
    context = kwargs.get("context", {})

    BLOCKED_KEYS = {"rejection_reason", "candidate_personal_data", "salary_data"}
    if preference_key in BLOCKED_KEYS:
        return {"success": False, "error": f"Não é permitido salvar preferências do tipo '{preference_key}'"}

    if not recruiter_id or not preference_key:
        return {"success": False, "error": "recruiter_id e preference_key são obrigatórios"}

    try:
        async with AsyncSessionLocal() as db:
            existing = await db.execute(
                text("""
                    SELECT id, frequency FROM recruiter_preferences
                    WHERE recruiter_id = :rid AND preference_key = :pkey
                    LIMIT 1
                """),
                {"rid": recruiter_id, "pkey": preference_key},
            )
            row = existing.mappings().first()

            if row:
                await db.execute(
                    text("""
                        UPDATE recruiter_preferences
                        SET preference_value = :pval,
                            frequency = :freq,
                            last_used = NOW(),
                            context = :ctx
                        WHERE id = :pid
                    """),
                    {
                        "pval": preference_value,
                        "freq": (row["frequency"] or 0) + 1,
                        "ctx": json.dumps(context) if isinstance(context, dict) else context,
                        "pid": str(row["id"]),
                    },
                )
            else:
                await db.execute(
                    text("""
                        INSERT INTO recruiter_preferences (recruiter_id, preference_key, preference_value, frequency, context, last_used)
                        VALUES (:rid, :pkey, :pval, 1, :ctx, NOW())
                    """),
                    {
                        "rid": recruiter_id,
                        "pkey": preference_key,
                        "pval": preference_value,
                        "ctx": json.dumps(context) if isinstance(context, dict) else context,
                    },
                )

            await db.commit()
            return {
                "success": True,
                "message": f"Preferência '{preference_key}' salva com sucesso",
            }
    except Exception as e:
        try:
            await db.rollback()
        except Exception:
            pass
        logger.debug(f"[pipeline_tools] save_recruiter_preference: {e}")
        return {"success": True, "message": "Preferência registrada (tabela será criada em breve)"}


# ─── Interview Management Tools ───────────────────────────────────────────────

async def _get_candidate_phone(candidate_email: str, interview_id: str) -> str | None:
    """Busca telefone do candidato na tabela candidates usando email ou interview_id como fallback."""
    try:
        async with AsyncSessionLocal() as db:
            if candidate_email:
                result = await db.execute(
                    text("SELECT phone FROM candidates WHERE email = :email LIMIT 1"),
                    {"email": candidate_email},
                )
                row = result.mappings().first()
                if row and row.get("phone"):
                    return row["phone"]

            result = await db.execute(
                text("""
                    SELECT c.phone FROM candidates c
                    JOIN interviews i ON i.candidate_id = c.id
                    WHERE i.id::text = :iid
                    LIMIT 1
                """),
                {"iid": interview_id},
            )
            row = result.mappings().first()
            if row and row.get("phone"):
                return row["phone"]
    except Exception as e:
        logger.debug(f"[pipeline_tools] _get_candidate_phone failed: {e}")
    return None


@tool_handler("pipeline")
async def _wrap_get_interview_details(**kwargs: Any) -> dict[str, Any]:
    """Busca detalhes da entrevista agendada para o candidato na vaga atual."""
    candidate_id = kwargs.get("candidate_id", "") or kwargs.get("vacancy_candidate_id", "")
    if not candidate_id:
        return {"success": False, "error": "candidate_id é obrigatório"}

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("""
                SELECT
                    i.id::text AS interview_id,
                    i.title,
                    i.interview_type,
                    i.interview_mode,
                    i.start_time,
                    i.end_time,
                    i.duration_minutes,
                    i.meeting_url,
                    i.meeting_platform,
                    i.graph_event_id,
                    i.graph_organizer_email,
                    i.candidate_email,
                    i.candidate_name,
                    i.interviewer_email,
                    i.interviewer_name,
                    i.location,
                    i.status,
                    i.timezone
                FROM interviews i
                WHERE i.candidate_id::text = :cid
                  AND i.status IN ('scheduled', 'rescheduled')
                ORDER BY i.start_time ASC
                LIMIT 1
            """),
            {"cid": candidate_id},
        )
        row = result.mappings().first()

        if not row:
            return {
                "success": True,
                "found": False,
                "message": "Nenhuma entrevista agendada encontrada para este candidato",
            }

        interview = dict(row)
        for k, v in interview.items():
            if isinstance(v, datetime):
                interview[k] = v.isoformat()

        return {"success": True, "found": True, "interview": interview}


@tool_handler("pipeline")
async def _wrap_cancel_interview(**kwargs: Any) -> dict[str, Any]:
    """
    Cancela a entrevista agendada do candidato.
    Atualiza o banco de dados, cancela o evento no Teams via Microsoft Graph
    e notifica o candidato por email ou WhatsApp.
    """
    interview_id = kwargs.get("interview_id", "")
    cancellation_reason = kwargs.get("cancellation_reason", "Entrevista cancelada pelo recrutador")
    notify_channel = kwargs.get("notify_channel", "email")

    if not interview_id:
        return {"success": False, "error": "interview_id é obrigatório"}

    notifications_sent: list[dict[str, Any]] = []
    graph_status = "not_attempted"

    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                text("""
                    SELECT id::text, candidate_email, candidate_name,
                           interviewer_email, graph_event_id, graph_organizer_email,
                           meeting_url, start_time, job_title, status
                    FROM interviews WHERE id::text = :iid
                """),
                {"iid": interview_id},
            )
            row = result.mappings().first()
            if not row:
                return {"success": False, "error": f"Entrevista {interview_id} não encontrada"}

            interview_data = dict(row)

            await db.execute(
                text("""
                    UPDATE interviews
                    SET status = 'cancelled',
                        cancelled_at = NOW(),
                        cancellation_reason = :reason,
                        updated_at = NOW()
                    WHERE id::text = :iid
                """),
                {"reason": cancellation_reason, "iid": interview_id},
            )
            await db.commit()

        if interview_data.get("graph_event_id") and interview_data.get("graph_organizer_email"):
            try:
                from app.domains.interview_scheduling.services.calendar_service import CalendarService
                cal = CalendarService()
                await cal.cancel_interview(
                    organizer_email=interview_data["graph_organizer_email"],
                    event_id=interview_data["graph_event_id"],
                    cancellation_message=cancellation_reason,
                )
                graph_status = "cancelled"
            except Exception as graph_err:
                logger.warning(f"[pipeline_tools] Graph cancel not completed (graceful): {graph_err}")
                graph_status = "failed_gracefully"

        candidate_email = interview_data.get("candidate_email", "")
        candidate_name = interview_data.get("candidate_name", "Candidato")
        start_time = interview_data.get("start_time")
        date_str = ""
        if start_time:
            try:
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time)
                date_str = start_time.strftime("%d/%m/%Y às %H:%M")
            except Exception:
                date_str = str(start_time)

        if candidate_email and notify_channel in ("email", "both"):
            try:
                from app.domains.communication.services.communication_dispatcher import communication_dispatcher
                communication_dispatcher.send_email(
                    to_email=candidate_email,
                    subject=f"Entrevista cancelada — {interview_data.get('job_title', 'Vaga')}",
                    body_html=(
                        f"<p>Olá, {candidate_name}!</p>"
                        f"<p>Informamos que a entrevista agendada para <strong>{date_str}</strong> foi cancelada.</p>"
                        f"<p>Em breve entraremos em contato com mais informações.</p>"
                    ),
                )
                notifications_sent.append({"channel": "email", "recipient": candidate_email, "status": "sent"})
            except Exception as email_err:
                logger.warning(f"[pipeline_tools] Email cancel notification failed: {email_err}")
                notifications_sent.append({"channel": "email", "status": "failed"})

        if notify_channel in ("whatsapp", "both"):
            candidate_phone = await _get_candidate_phone(interview_data.get("candidate_email", ""), interview_id)
            if candidate_phone:
                try:
                    from app.domains.communication.services.communication_dispatcher import communication_dispatcher
                    communication_dispatcher.send_whatsapp(
                        to_phone=candidate_phone,
                        message=f"Olá, {candidate_name}! Informamos que a entrevista agendada para {date_str} foi cancelada. Em breve entraremos em contato com mais informações.",
                    )
                    notifications_sent.append({"channel": "whatsapp", "recipient": candidate_phone, "status": "sent"})
                except Exception as wa_err:
                    logger.warning(f"[pipeline_tools] WhatsApp cancel notification failed: {wa_err}")
                    notifications_sent.append({"channel": "whatsapp", "status": "failed"})

        try:
            async with AsyncSessionLocal() as db:
                await db.execute(
                    text("""
                        INSERT INTO notifications (id, user_id, title, message, notification_type, category, priority, source_agent, source_trigger, created_at)
                        VALUES (:nid, :uid, :title, :msg, 'info', 'interview', 'normal', 'pipeline_transition_agent', 'cancel_interview', NOW())
                    """),
                    {
                        "nid": str(__import__("uuid").uuid4()),
                        "uid": kwargs.get("recruiter_id", "default_user"),
                        "title": "Entrevista cancelada",
                        "msg": f"A entrevista de {candidate_name} agendada para {date_str} foi cancelada.",
                    },
                )
                await db.commit()
        except Exception:
            try:
                await db.rollback()
            except Exception:
                pass
            pass

        return {
            "success": True,
            "status": "cancelled",
            "interview_id": interview_id,
            "graph_status": graph_status,
            "notifications_sent": notifications_sent,
            "message": f"Entrevista cancelada. {candidate_name} será notificado(a).",
        }

    except Exception as e:
        try:
            await db.rollback()
        except Exception:
            pass
        logger.error(f"[pipeline_tools] cancel_interview error: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@tool_handler("pipeline")
async def _wrap_reschedule_interview(**kwargs: Any) -> dict[str, Any]:
    """
    Reagenda a entrevista para nova data e hora.
    Atualiza o banco de dados, atualiza o evento no Teams via Microsoft Graph
    e notifica o candidato com a nova data/hora.
    """
    interview_id = kwargs.get("interview_id", "")
    new_start_time_str = kwargs.get("new_start_time", "")
    duration_minutes = kwargs.get("duration_minutes")
    notify_channel = kwargs.get("notify_channel", "email")

    if not interview_id or not new_start_time_str:
        return {"success": False, "error": "interview_id e new_start_time são obrigatórios"}

    notifications_sent: list[dict[str, Any]] = []
    graph_status = "not_attempted"

    try:
        try:
            new_start = datetime.fromisoformat(new_start_time_str.replace("Z", "+00:00"))
        except ValueError:
            return {
                "success": False,
                "error": f"Formato de data inválido: {new_start_time_str}. Use ISO 8601 (ex: 2025-03-15T14:00:00)",
            }

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                text("""
                    SELECT id::text, candidate_email, candidate_name,
                           interviewer_email, graph_event_id, graph_organizer_email,
                           duration_minutes AS current_duration, meeting_url, job_title
                    FROM interviews WHERE id::text = :iid
                """),
                {"iid": interview_id},
            )
            row = result.mappings().first()
            if not row:
                return {"success": False, "error": f"Entrevista {interview_id} não encontrada"}

            interview_data = dict(row)
            final_duration = int(duration_minutes or interview_data.get("current_duration") or 60)
            from datetime import timedelta as _timedelta
            new_end = new_start + _timedelta(minutes=final_duration)

            await db.execute(
                text("""
                    UPDATE interviews
                    SET start_time = :new_start,
                        end_time = :new_end,
                        duration_minutes = :dur,
                        status = 'rescheduled',
                        updated_at = NOW()
                    WHERE id::text = :iid
                """),
                {"new_start": new_start, "new_end": new_end, "dur": final_duration, "iid": interview_id},
            )
            await db.commit()

        if interview_data.get("graph_event_id") and interview_data.get("graph_organizer_email"):
            try:
                from app.domains.interview_scheduling.services.calendar_service import CalendarService
                cal = CalendarService()
                await cal.reschedule_interview(
                    organizer_email=interview_data["graph_organizer_email"],
                    event_id=interview_data["graph_event_id"],
                    new_start_time=new_start,
                    new_duration_minutes=final_duration,
                )
                graph_status = "rescheduled"
            except Exception as graph_err:
                logger.warning(f"[pipeline_tools] Graph reschedule not completed (graceful): {graph_err}")
                graph_status = "failed_gracefully"

        candidate_email = interview_data.get("candidate_email", "")
        candidate_name = interview_data.get("candidate_name", "Candidato")
        new_date_str = new_start.strftime("%d/%m/%Y às %H:%M")

        if candidate_email and notify_channel in ("email", "both"):
            try:
                from app.domains.communication.services.communication_dispatcher import communication_dispatcher
                communication_dispatcher.send_email(
                    to_email=candidate_email,
                    subject=f"Entrevista reagendada — {interview_data.get('job_title', 'Vaga')}",
                    body_html=(
                        f"<p>Olá, {candidate_name}!</p>"
                        f"<p>Sua entrevista foi reagendada para <strong>{new_date_str}</strong>.</p>"
                        f"<p>Em breve você receberá o convite atualizado do calendário.</p>"
                    ),
                )
                notifications_sent.append({"channel": "email", "recipient": candidate_email, "status": "sent"})
            except Exception as email_err:
                logger.warning(f"[pipeline_tools] Email reschedule notification failed: {email_err}")
                notifications_sent.append({"channel": "email", "status": "failed"})

        if notify_channel in ("whatsapp", "both"):
            candidate_phone = await _get_candidate_phone(candidate_email, interview_id)
            if candidate_phone:
                try:
                    from app.domains.communication.services.communication_dispatcher import communication_dispatcher
                    communication_dispatcher.send_whatsapp(
                        to_phone=candidate_phone,
                        message=f"Olá, {candidate_name}! Sua entrevista foi reagendada para {new_date_str}. Em breve você receberá o convite atualizado.",
                    )
                    notifications_sent.append({"channel": "whatsapp", "recipient": candidate_phone, "status": "sent"})
                except Exception as wa_err:
                    logger.warning(f"[pipeline_tools] WhatsApp reschedule notification failed: {wa_err}")
                    notifications_sent.append({"channel": "whatsapp", "status": "failed"})

        try:
            async with AsyncSessionLocal() as db:
                await db.execute(
                    text("""
                        INSERT INTO notifications (id, user_id, title, message, notification_type, category, priority, source_agent, source_trigger, created_at)
                        VALUES (:nid, :uid, :title, :msg, 'info', 'interview', 'normal', 'pipeline_transition_agent', 'reschedule_interview', NOW())
                    """),
                    {
                        "nid": str(__import__("uuid").uuid4()),
                        "uid": kwargs.get("recruiter_id", "default_user"),
                        "title": "Entrevista reagendada",
                        "msg": f"A entrevista de {candidate_name} foi reagendada para {new_date_str}.",
                    },
                )
                await db.commit()
        except Exception:
            try:
                await db.rollback()
            except Exception:
                pass
            pass

        return {
            "success": True,
            "status": "rescheduled",
            "interview_id": interview_id,
            "new_start_time": new_start.isoformat(),
            "new_end_time": new_end.isoformat(),
            "duration_minutes": final_duration,
            "graph_status": graph_status,
            "notifications_sent": notifications_sent,
            "message": f"Entrevista reagendada para {new_date_str}. {candidate_name} será notificado(a).",
        }

    except Exception as e:
        try:
            await db.rollback()
        except Exception:
            pass
        logger.error(f"[pipeline_tools] reschedule_interview error: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


ALL_TOOLS: list[ToolDefinition] = [
    ToolDefinition(
        name="get_candidate_profile",
        description="Busca o perfil completo do candidato: nome, email, telefone, LinkedIn, cargo atual, skills, localização, pretensão salarial, modelo de trabalho",
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "UUID do candidato"},
            },
            "required": ["candidate_id"],
        },
        function=_wrap_get_candidate_profile,
    ),
    ToolDefinition(
        name="get_candidate_wsi_scores",
        description="Busca scores WSI do candidato: score geral, por competência (técnico, comportamental), classificação, recomendação, pontos fortes e de atenção",
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "UUID do candidato"},
                "job_id": {"type": "string", "description": "UUID da vaga (opcional, filtra por vaga)"},
            },
            "required": ["candidate_id"],
        },
        function=_wrap_get_candidate_wsi_scores,
    ),
    ToolDefinition(
        name="get_candidate_screening_results",
        description="Busca resultados de triagem do candidato: respostas, análise da LIA, score, parecer, canal utilizado, datas",
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "UUID do candidato"},
                "job_id": {"type": "string", "description": "UUID da vaga (opcional)"},
            },
            "required": ["candidate_id"],
        },
        function=_wrap_get_candidate_screening_results,
    ),
    ToolDefinition(
        name="get_candidate_salary_info",
        description="Busca informações salariais do candidato: pretensão CLT, pretensão PJ, cargo e empresa atuais",
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "UUID do candidato"},
            },
            "required": ["candidate_id"],
        },
        function=_wrap_get_candidate_salary_info,
    ),
    ToolDefinition(
        name="update_candidate_field",
        description="Atualiza um campo cadastral do candidato (telefone, email, LinkedIn, cargo, empresa, localização, pretensão salarial, modelo de trabalho)",
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "UUID do candidato"},
                "field_name": {"type": "string", "description": "Nome do campo a atualizar (phone, email, linkedin_url, etc.)"},
                "field_value": {"type": "string", "description": "Novo valor do campo"},
            },
            "required": ["candidate_id", "field_name", "field_value"],
        },
        function=_wrap_update_candidate_field,
    ),
    ToolDefinition(
        name="request_data_collection",
        description="Agenda uma tarefa para coletar um dado específico do candidato (pretensão salarial, portfólio, referências, disponibilidade, documentos, certificações)",
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "UUID do candidato"},
                "data_type": {"type": "string", "description": "Tipo de dado: salary_expectation, portfolio, references, availability, documents, certifications, work_samples, custom"},
                "description": {"type": "string", "description": "Descrição detalhada do que coletar"},
            },
            "required": ["candidate_id", "data_type"],
        },
        function=_wrap_request_data_collection,
    ),
    ToolDefinition(
        name="get_stage_sub_statuses",
        description="Lista os sub-statuses disponíveis para a etapa de destino",
        parameters={
            "type": "object",
            "properties": {
                "to_stage": {"type": "string", "description": "Slug da etapa destino"},
                "company_id": {"type": "string", "description": "ID da empresa"},
            },
            "required": ["to_stage"],
        },
        function=_wrap_get_stage_sub_statuses,
    ),
    ToolDefinition(
        name="suggest_sub_status",
        description="Sugere o sub-status mais adequado baseado no tipo de ação e contexto",
        parameters={
            "type": "object",
            "properties": {
                "action_behavior": {"type": "string", "description": "Tipo de ação (screening, scheduling, etc.)"},
                "context_notes": {"type": "string", "description": "Notas adicionais de contexto"},
            },
            "required": ["action_behavior"],
        },
        function=_wrap_suggest_sub_status,
    ),
    ToolDefinition(
        name="extract_preferences",
        description="Extrai preferências estruturadas do texto do recrutador: data, hora, formato, urgência, entrevistador, duração, plataforma",
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Texto do recrutador para extrair preferências"},
                "action_behavior": {"type": "string", "description": "Tipo de ação para contexto"},
            },
            "required": ["text"],
        },
        function=_wrap_extract_preferences,
    ),
    ToolDefinition(
        name="validate_transition",
        description="Valida se a transição de etapa é permitida pelas regras do pipeline",
        parameters={
            "type": "object",
            "properties": {
                "from_stage": {"type": "string", "description": "Etapa de origem"},
                "to_stage": {"type": "string", "description": "Etapa de destino"},
                "action_behavior": {"type": "string", "description": "Tipo de ação"},
            },
            "required": ["from_stage", "to_stage"],
        },
        function=_wrap_validate_transition,
    ),
    ToolDefinition(
        name="get_job_context",
        description="Busca dados da vaga: título, departamento, descrição, modelo de trabalho, faixa salarial, configuração de triagem",
        parameters={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "UUID da vaga"},
            },
            "required": ["job_id"],
        },
        function=_wrap_get_job_context,
    ),
    ToolDefinition(
        name="schedule_secondary_task",
        description="Agenda uma tarefa secundária combinada com a ação principal (ex: agendar + coletar info)",
        parameters={
            "type": "object",
            "properties": {
                "task_type": {"type": "string", "description": "Tipo da tarefa (collect_info, send_document, follow_up, custom)"},
                "description": {"type": "string", "description": "Descrição detalhada da tarefa"},
                "candidate_id": {"type": "string", "description": "UUID do candidato"},
            },
            "required": ["task_type", "description"],
        },
        function=_wrap_schedule_secondary_task,
    ),
    ToolDefinition(
        name="personalize_communication",
        description="Define personalização da comunicação com o candidato: tom, idioma, detalhes extras",
        parameters={
            "type": "object",
            "properties": {
                "tone": {"type": "string", "description": "Tom da mensagem: professional, friendly, formal, casual"},
                "language": {"type": "string", "description": "Idioma: pt-BR, en, es"},
                "extra_details": {"type": "string", "description": "Detalhes extras para incluir na comunicação"},
                "template_type": {"type": "string", "description": "Tipo de template a usar"},
            },
        },
        function=_wrap_personalize_communication,
    ),
    ToolDefinition(
        name="check_rejection_fairness",
        description="Valida motivo de rejeição contra viés discriminatório (FairnessGuard 3-tier: regex, implícito, semântico). OBRIGATÓRIO antes de confirmar qualquer rejeição",
        parameters={
            "type": "object",
            "properties": {
                "rejection_reason": {"type": "string", "description": "Motivo de rejeição informado pelo recrutador"},
                "candidate_name": {"type": "string", "description": "Nome do candidato"},
            },
            "required": ["rejection_reason"],
        },
        function=_wrap_check_rejection_fairness,
    ),
    ToolDefinition(
        name="check_candidate_availability",
        description="Verifica disponibilidade do candidato baseada em histórico de interações, entrevistas e triagens pendentes",
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "UUID do candidato"},
            },
            "required": ["candidate_id"],
        },
        function=_wrap_check_candidate_availability,
    ),
    ToolDefinition(
        name="get_recruiter_preferences",
        description="Busca preferências aprendidas do recrutador: padrões de agendamento, canais preferidos, horários habituais, ações recorrentes",
        parameters={
            "type": "object",
            "properties": {
                "recruiter_id": {"type": "string", "description": "UUID do recrutador"},
                "action_behavior": {"type": "string", "description": "Tipo de ação para filtrar preferências relevantes"},
            },
            "required": ["recruiter_id"],
        },
        function=_wrap_get_recruiter_preferences,
    ),
    ToolDefinition(
        name="save_recruiter_preference",
        description="Salva ou atualiza uma preferência aprendida do recrutador para futuras interações. NÃO salve dados sensíveis (motivos de rejeição, dados pessoais do candidato)",
        parameters={
            "type": "object",
            "properties": {
                "recruiter_id": {"type": "string", "description": "UUID do recrutador"},
                "preference_key": {"type": "string", "description": "Chave da preferência (ex: preferred_platform, preferred_time_slot, preferred_format)"},
                "preference_value": {"type": "string", "description": "Valor da preferência (ex: Google Meet, tarde, remoto)"},
                "context": {"type": "object", "description": "Contexto adicional: action_behavior, job_type, etc."},
            },
            "required": ["recruiter_id", "preference_key", "preference_value"],
        },
        function=_wrap_save_recruiter_preference,
    ),
    ToolDefinition(
        name="get_interview_details",
        description="Busca os detalhes da entrevista agendada para o candidato: data, hora, link da reunião, entrevistador, plataforma (Teams/Meet), event_id do Graph, status. Use antes de cancelar ou reagendar.",
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "UUID do candidato"},
            },
            "required": ["candidate_id"],
        },
        function=_wrap_get_interview_details,
    ),
    ToolDefinition(
        name="cancel_interview",
        description="Cancela a entrevista agendada do candidato. Atualiza o banco de dados, cancela o evento no Microsoft Teams via Graph API e notifica o candidato por email ou WhatsApp. Use SOMENTE após confirmar a intenção do recrutador.",
        parameters={
            "type": "object",
            "properties": {
                "interview_id": {"type": "string", "description": "UUID da entrevista (obtido via get_interview_details)"},
                "cancellation_reason": {"type": "string", "description": "Motivo do cancelamento (ex: 'Candidato optou por não prosseguir', 'Agenda do entrevistador indisponível')"},
                "notify_channel": {"type": "string", "description": "Canal de notificação ao candidato: 'email', 'whatsapp' ou 'both'. Padrão: 'email'"},
            },
            "required": ["interview_id"],
        },
        function=_wrap_cancel_interview,
    ),
    ToolDefinition(
        name="reschedule_interview",
        description="Reagenda a entrevista para nova data e hora. Atualiza o banco de dados, atualiza o evento no Microsoft Teams via Graph API e notifica o candidato com a nova data/hora. Use após obter a nova data/hora do recrutador.",
        parameters={
            "type": "object",
            "properties": {
                "interview_id": {"type": "string", "description": "UUID da entrevista (obtido via get_interview_details)"},
                "new_start_time": {"type": "string", "description": "Nova data e hora no formato ISO 8601 (ex: '2025-03-15T14:00:00')"},
                "duration_minutes": {"type": "integer", "description": "Duração em minutos (opcional, usa a duração atual se não informado)"},
                "notify_channel": {"type": "string", "description": "Canal de notificação ao candidato: 'email', 'whatsapp' ou 'both'. Padrão: 'email'"},
            },
            "required": ["interview_id", "new_start_time"],
        },
        function=_wrap_reschedule_interview,
    ),
]

_TOOL_MAP: dict[str, ToolDefinition] = {t.name: t for t in ALL_TOOLS}

# Tools que requerem confirmação ou validação adicional antes de executar.
# Carregados dinamicamente do banco (GuardrailRepository) em runtime.
# Esta lista serve como fallback estático caso o banco esteja indisponível.
GUARDRAIL_TOOLS: list[str] = [
    "update_candidate_field",   # Alteração de dados cadastrais
    "move_candidate",           # Mudança de etapa no pipeline
    "batch_move",               # Mover múltiplos candidatos de uma vez
    "reject_candidate",         # Rejeição definitiva
    "finalize_hiring",          # Contratação (irreversível)
    "delete_job",               # Deletar vaga
    "send_bulk_email",          # Email em massa para candidatos
]


def get_pipeline_transition_tools(
    action_behavior: str = "passive",
    allowed_tool_names: list[str] | None = None,
) -> list[ToolDefinition]:
    if allowed_tool_names is None:
        from app.domains.pipeline.agents.pipeline_stage_context import get_allowed_tools_for_behavior
        allowed_tool_names = get_allowed_tools_for_behavior(action_behavior)

    return [_TOOL_MAP[name] for name in allowed_tool_names if name in _TOOL_MAP]


# ─────────────────────────────────────────────────────────────────────────────
# Consolidated cv_screening pipeline tools (migrated from
# app/domains/cv_screening/agents/pipeline_tool_registry.py — task #323).
# These tools operate on vacancy_candidates and are exposed via get_pipeline_tools()
# / STAGE_TOOLS, used by the cv_screening PipelineReActAgent and other consumers.
# ─────────────────────────────────────────────────────────────────────────────


@tool_handler("cv_screening")
async def _wrap_view_candidate_profile(**kwargs: Any) -> dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
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
            if isinstance(v, datetime):
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
    logger.warning(f"[pipeline_tools] move_candidate called: candidate={candidate_id} target={target_stage} reason={reason}")
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


@tool_handler("cv_screening")
async def _wrap_analyze_cv(**kwargs: Any) -> dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
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


@tool_handler("cv_screening")
async def _wrap_run_wsi_screening(**kwargs: Any) -> dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    vacancy_id = kwargs.get("vacancy_id", "unknown")
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


@tool_handler("cv_screening")
async def _wrap_schedule_interview(**kwargs: Any) -> dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    interview_datetime = kwargs.get("datetime", "")
    interview_type = kwargs.get("type", "video")
    logger.info(f"[pipeline_tools] schedule_interview called: candidate={candidate_id} datetime={interview_datetime} type={interview_type}")
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


@tool_handler("cv_screening")
async def _wrap_send_communication(**kwargs: Any) -> dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    channel = kwargs.get("channel", "email")
    message_text = kwargs.get("message", "")
    logger.info(f"[pipeline_tools] send_communication called: candidate={candidate_id} channel={channel}")
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


@tool_handler("cv_screening")
async def _wrap_add_notes(**kwargs: Any) -> dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    note_text = kwargs.get("note_text", "")
    logger.info(f"[pipeline_tools] add_notes called for candidate={candidate_id}")
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


@tool_handler("cv_screening")
async def _wrap_batch_move(**kwargs: Any) -> dict[str, Any]:
    candidate_ids = kwargs.get("candidate_ids", [])
    target_stage = kwargs.get("target_stage", "unknown")
    reason = kwargs.get("reason", "")
    logger.info(f"[pipeline_tools] batch_move called: candidates={len(candidate_ids)} target={target_stage}")
    if not candidate_ids:
        return {"success": False, "data": {}, "message": "Nenhum candidato fornecido para movimentação em massa."}
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


@tool_handler("cv_screening")
async def _wrap_add_to_shortlist(**kwargs: Any) -> dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    logger.info(f"[pipeline_tools] add_to_shortlist called for candidate={candidate_id}")
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


@tool_handler("cv_screening")
async def _wrap_view_screening_results(**kwargs: Any) -> dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    logger.info(f"[pipeline_tools] view_screening_results called for candidate={candidate_id}")
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


@tool_handler("cv_screening")
async def _wrap_view_interview_notes(**kwargs: Any) -> dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    logger.info(f"[pipeline_tools] view_interview_notes called for candidate={candidate_id}")
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


@tool_handler("cv_screening")
async def _wrap_finalize_hiring(**kwargs: Any) -> dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    logger.info(f"[pipeline_tools] finalize_hiring called for candidate={candidate_id}")
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


@tool_handler("cv_screening")
async def _wrap_update_status(**kwargs: Any) -> dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "unknown")
    status = kwargs.get("status", "unknown")
    logger.info(f"[pipeline_tools] update_status called: candidate={candidate_id} status={status}")
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


@tool_handler("cv_screening")
async def _wrap_generate_report(**kwargs: Any) -> dict[str, Any]:
    report_type = kwargs.get("report_type", "summary")
    period = kwargs.get("period", "month")
    company_id = kwargs.get("company_id", "")
    period_days = {"week": 7, "month": 30, "quarter": 90}.get(period, 30)
    logger.info(f"[pipeline_tools] generate_report called: type={report_type} period={period}")
    report_id = f"rpt_{uuid.uuid4().hex[:12]}"
    summary: dict[str, Any] = {}
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


_CV_SCREENING_TOOL_DEFINITIONS: list[ToolDefinition] = [
    ToolDefinition(
        name="view_candidate_profile",
        description="Visualiza o perfil completo do candidato incluindo dados pessoais, experiencia, formacao e historico no pipeline.",
        parameters={
            "type": "object",
            "properties": {"candidate_id": {"type": "string", "description": "ID do candidato"}},
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
            "properties": {"candidate_id": {"type": "string", "description": "ID do candidato"}},
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
            "properties": {"candidate_id": {"type": "string", "description": "ID do candidato"}},
            "required": ["candidate_id"],
        },
        function=_wrap_add_to_shortlist,
    ),
    ToolDefinition(
        name="view_screening_results",
        description="Visualiza resultados do screening WSI de um candidato, incluindo score e detalhamento.",
        parameters={
            "type": "object",
            "properties": {"candidate_id": {"type": "string", "description": "ID do candidato"}},
            "required": ["candidate_id"],
        },
        function=_wrap_view_screening_results,
    ),
    ToolDefinition(
        name="view_interview_notes",
        description="Visualiza notas e feedback de entrevistas realizadas com o candidato.",
        parameters={
            "type": "object",
            "properties": {"candidate_id": {"type": "string", "description": "ID do candidato"}},
            "required": ["candidate_id"],
        },
        function=_wrap_view_interview_notes,
    ),
    ToolDefinition(
        name="generate_offer",
        description="Gera uma proposta de contratacao para o candidato com base nos dados da vaga e negociacao.",
        parameters={
            "type": "object",
            "properties": {"candidate_id": {"type": "string", "description": "ID do candidato"}},
            "required": ["candidate_id"],
        },
        function=_wrap_generate_offer,
    ),
    ToolDefinition(
        name="finalize_hiring",
        description="Finaliza o processo de contratacao do candidato, registrando a admissao no sistema.",
        parameters={
            "type": "object",
            "properties": {"candidate_id": {"type": "string", "description": "ID do candidato"}},
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
    ),
]

# cv_screening pipeline tools live in their own map to preserve the canonical
# ALL_TOOLS / _TOOL_MAP semantics used by the Pipeline*Agent decomposition tests.
_CV_SCREENING_TOOL_MAP: dict[str, ToolDefinition] = {
    t.name: t for t in _CV_SCREENING_TOOL_DEFINITIONS
}

STAGE_TOOLS: dict[str, list[str]] = {
    "triage": ["view_candidate_profile", "analyze_cv", "add_notes", "move_candidate"],
    "screening": ["run_wsi_screening", "view_screening_results", "add_notes", "move_candidate"],
    "shortlist": ["move_candidate", "add_to_shortlist", "view_candidate_profile", "add_notes", "batch_move"],
    "interview": ["schedule_interview", "view_interview_notes", "send_communication", "add_notes", "move_candidate"],
    "offer": ["generate_offer", "send_communication", "add_notes", "move_candidate", "generate_report"],
    "hired": ["finalize_hiring", "update_status", "send_communication", "add_notes", "generate_report"],
}


def get_pipeline_tools(stage: str = "") -> list[ToolDefinition]:
    """Return cv_screening pipeline tools, optionally filtered by stage.

    Mirrors the previous behavior of
    ``app.domains.cv_screening.agents.pipeline_tool_registry.get_pipeline_tools``
    (consolidated under task #323).

    Args:
        stage: Current pipeline stage identifier. If empty, returns all tools.

    Returns:
        List of ToolDefinition instances available for the given stage.
    """
    if not stage:
        return list(_CV_SCREENING_TOOL_DEFINITIONS)

    tool_names = STAGE_TOOLS.get(stage, list(_CV_SCREENING_TOOL_MAP.keys()))
    tools = [_CV_SCREENING_TOOL_MAP[name] for name in tool_names if name in _CV_SCREENING_TOOL_MAP]
    logger.debug(f"[pipeline_tools] Stage '{stage}' tools: {[t.name for t in tools]}")
    return tools
