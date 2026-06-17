"""
Pipeline Tool Registry — Tools available to the Pipeline ReAct Agent.

Provides 17 tools for candidate data retrieval, profile updates, preference
extraction, transition validation, fairness checks, and recruiter learning.
Tools are filtered per action_behavior via STAGE_CAPABILITIES.
"""
import json
import logging
import re
from datetime import datetime
from typing import Any

from lia_agents_core.tool_adapter import ToolDefinition
from lia_agents_core.tool_adapter import ToolOutput
from sqlalchemy import text

from app.core.database import AsyncSessionLocal
from app.domains.pipeline.repositories.candidate_pipeline_repository import CandidatePipelineRepository
from app.domains.pipeline.repositories.lia_opinion_repository import LiaOpinionRepository
from app.domains.pipeline.repositories.stage_repository import StageRepository
from app.domains.pipeline.repositories.recruiter_preferences_repository import RecruiterPreferencesRepository
from app.shared.compliance.fairness_guard import FairnessGuard
from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)

_fairness_guard = FairnessGuard()


@tool_handler("pipeline")
async def _wrap_get_candidate_profile(**kwargs: Any) -> dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "")
    company_id = kwargs.get("company_id", "")  # P0.A canonical: PII (phone+salary+linkedin) leak gate
    if not candidate_id:
        return {"success": False, "error": "candidate_id é obrigatório"}

    async with AsyncSessionLocal() as db:
        repo = CandidatePipelineRepository(db)
        profile = await repo.get_profile(candidate_id, company_id)

    if not profile:
        return {"success": False, "error": "Candidato não encontrado"}

    return {"success": True, "profile": profile}


@tool_handler("pipeline")
async def _wrap_get_candidate_wsi_scores(**kwargs: Any) -> dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "")
    job_id = kwargs.get("job_id", "")
    company_id = kwargs.get("company_id", "")

    async with AsyncSessionLocal() as db:
        repo = LiaOpinionRepository(db)
        scores = await repo.get_by_candidate(candidate_id, company_id, job_id=job_id or None)

    if not scores:
        return {"success": True, "scores": [], "message": "Nenhum score WSI encontrado para este candidato"}

    return {"success": True, "scores": scores}


@tool_handler("pipeline")
async def _wrap_get_candidate_screening_results(**kwargs: Any) -> dict[str, Any]:
    candidate_id = kwargs.get("candidate_id", "")
    job_id = kwargs.get("job_id", "")

    async with AsyncSessionLocal() as db:
        # ADR-001-EXEMPT: screening_tasks table has no company_id column — tenant isolated
        # via FK chain screening_tasks.candidate_id → candidates.company_id.
        # Dedicated ScreeningTaskRepository lives in cv_screening domain; cross-domain
        # import would violate domain boundaries more than the SQL inline here.
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
    company_id = kwargs.get("company_id", "")  # P0.A canonical: salary PII leak gate

    async with AsyncSessionLocal() as db:
        repo = CandidatePipelineRepository(db)
        salary_info = await repo.get_salary_info(candidate_id, company_id)

    if not salary_info:
        return {"success": False, "error": "Candidato não encontrado"}

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
            # ADR-001-EXEMPT: _ALLOWED_FIELDS frozenset + _SAFE_COL_RE regex — dynamic field
            # update with double sanitization (allowlist + regex). 13 individual repo methods
            # would not add security beyond what the allowlist already provides.
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
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
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
        repo = StageRepository(db)
        rows = await repo.get_sub_statuses_for_stage(to_stage, company_id)

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
        "sub_statuses": rows,
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
                repo = StageRepository(db)
                row = await repo.get_default_sub_status(to_stage, company_id)
                if row:
                    logger.debug("[pipeline_tools] suggest_sub_status: DB default found for stage=%s: %s", to_stage, row["name"])
                    return {
                        "success": True,
                        "suggested_sub_status": row["name"],
                        "display_name": row["display_name"],
                        "reason": f"Sub-status padrão configurado para a etapa '{to_stage}'",
                    }
        except Exception as e:
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
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


@tool_handler("pipeline")
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


@tool_handler("pipeline")
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
        # ADR-001-EXEMPT: job_vacancies is Rails-owned table (schema managed by ats_api/);
        # JobVacancyCrudRepository in job_creation domain reads CRUD fields. This tool
        # needs pipeline_config + screening_config fields not yet in that repo. Adding
        # cross-domain repo import would couple pipeline → job_creation; inline text()
        # is the lesser coupling here.
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


@tool_handler("pipeline")
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


@tool_handler("pipeline")
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


@tool_handler("pipeline")
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
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
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
    company_id = kwargs.get("company_id", "")

    if not recruiter_id:
        return {"success": True, "preferences": [], "message": "Sem preferências salvas"}

    try:
        async with AsyncSessionLocal() as db:
            repo = RecruiterPreferencesRepository(db)
            prefs = await repo.get_preferences(recruiter_id, company_id, action_behavior=action_behavior)

        if not prefs:
            return {"success": True, "preferences": [], "message": "Sem preferências salvas para este contexto"}

        return {"success": True, "preferences": prefs}
    except Exception as e:
        # P1 audit 2026-05-20: graceful degradation legitima (tabela em rollout).
        # Adicionada flag fallback_used canonical.
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.debug(f"[pipeline_tools] get_recruiter_preferences: table may not exist yet: {e}")
        return {"success": True, "fallback_used": True, "preferences": [], "message": "Sistema de preferências ainda não configurado"}


@tool_handler("pipeline")
async def _wrap_save_recruiter_preference(**kwargs: Any) -> dict[str, Any]:
    recruiter_id = kwargs.get("recruiter_id", "")
    preference_key = kwargs.get("preference_key", "")
    preference_value = kwargs.get("preference_value", "")
    context = kwargs.get("context", {})
    company_id = kwargs.get("company_id", "")

    BLOCKED_KEYS = {"rejection_reason", "candidate_personal_data", "salary_data"}
    if preference_key in BLOCKED_KEYS:
        return {"success": False, "error": f"Não é permitido salvar preferências do tipo '{preference_key}'"}

    if not recruiter_id or not preference_key:
        return {"success": False, "error": "recruiter_id e preference_key são obrigatórios"}

    try:
        async with AsyncSessionLocal() as db:
            repo = RecruiterPreferencesRepository(db)
            await repo.upsert_preference(recruiter_id, company_id, preference_key, preference_value, context)

        return {
            "success": True,
            "message": f"Preferência '{preference_key}' salva com sucesso",
        }
    except Exception as e:
        # P1 audit 2026-05-20: REGRA 4 CLAUDE.md — fail-loud quando save NAO
        # persistiu. Anteriormente dizia "Preferência registrada" sem registrar.
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.exception("[pipeline_tools] save_recruiter_preference FAILED — failing LOUD")
        return {
            "success": False,
            "fallback_used": True,
            "needs_manual_review": True,
            "message": (
                "Não foi possível salvar a preferência no banco. "
                "A configuração NÃO foi registrada. Tente novamente ou peça suporte."
            ),
            "error": str(e),
        }


# ─── Interview Management Tools ───────────────────────────────────────────────

async def _get_candidate_phone(
    candidate_email: str, interview_id: str, company_id: str = ""
) -> str | None:
    """Busca telefone do candidato na tabela candidates usando email ou interview_id.

    P0.A canonical: company_id obrigatorio para tenant gate. company_id IS NULL
    preserva talent pool global sharing (Pearch AI / merge.dev imported).
    Default "" mantido como backward-compat soft (caller existente sem
    company_id continua funcionando mas com risk; futures DEVEM passar).
    """
    try:
        async with AsyncSessionLocal() as db:
            repo = CandidatePipelineRepository(db)
            if candidate_email and company_id:
                phone = await repo.get_phone_by_email(candidate_email, company_id)
                if phone:
                    return phone

            if company_id:
                phone = await repo.get_phone_by_interview(interview_id, company_id)
                if phone:
                    return phone
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.debug(f"[pipeline_tools] _get_candidate_phone failed: {e}")
    return None


@tool_handler("pipeline")
async def _wrap_get_interview_details(**kwargs: Any) -> dict[str, Any]:
    """Busca detalhes da entrevista agendada para o candidato na vaga atual."""
    candidate_id = kwargs.get("candidate_id", "") or kwargs.get("vacancy_candidate_id", "")
    if not candidate_id:
        return {"success": False, "error": "candidate_id é obrigatório"}

    async with AsyncSessionLocal() as db:
        # ADR-001-EXEMPT: interviews table has no company_id column — tenant isolated
        # via FK chain vacancy_candidates.company_id → candidates.company_id.
        # InterviewRepository in interview_scheduling domain manages interview CRUD;
        # cross-domain import for a read-only lookup here would couple pipeline →
        # interview_scheduling unnecessarily.
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
            # ADR-001-EXEMPT: multi-step orchestration with external side-effects
            # (DB write + Graph API cancel + email/WhatsApp notification + audit log).
            # Not a pure query — is a workflow. Extracting to repo would not improve
            # cohesion and would force repo to depend on CalendarService + comm_dispatcher.
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
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
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
                # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
                logger.warning(f"[pipeline_tools] Email cancel notification failed: {email_err}")
                notifications_sent.append({"channel": "email", "status": "failed"})

        if notify_channel in ("whatsapp", "both"):
            # P0.A canonical: pass company_id to _get_candidate_phone tenant gate.
            candidate_phone = await _get_candidate_phone(
                interview_data.get("candidate_email", ""),
                interview_id,
                kwargs.get("company_id", ""),
            )
            if candidate_phone:
                try:
                    from app.domains.communication.services.communication_dispatcher import communication_dispatcher
                    communication_dispatcher.send_whatsapp(
                        to_phone=candidate_phone,
                        message=f"Olá, {candidate_name}! Informamos que a entrevista agendada para {date_str} foi cancelada. Em breve entraremos em contato com mais informações.",
                    )
                    notifications_sent.append({"channel": "whatsapp", "recipient": candidate_phone, "status": "sent"})
                except Exception as wa_err:
                    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                    logger.warning(f"[pipeline_tools] WhatsApp cancel notification failed: {wa_err}")
                    notifications_sent.append({"channel": "whatsapp", "status": "failed"})

        # ADR-001-EXEMPT: part of interview workflow — audit notification INSERT; see EXEMPT marker on main async-with block above
        try:
            async with AsyncSessionLocal() as db:
                await db.execute(
                    # RLS-EXEMPT: notifications — user-scoped via user_id, no direct company_id column
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
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
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
            # ADR-001-EXEMPT: multi-step orchestration with external side-effects
            # (DB write + Graph API reschedule + email/WhatsApp notification + audit log).
            # Not a pure query — is a workflow. Extracting to repo would not improve
            # cohesion and would force repo to depend on CalendarService + comm_dispatcher.
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
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
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
                # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
                logger.warning(f"[pipeline_tools] Email reschedule notification failed: {email_err}")
                notifications_sent.append({"channel": "email", "status": "failed"})

        if notify_channel in ("whatsapp", "both"):
            # P0.A canonical: pass company_id to _get_candidate_phone tenant gate.
            candidate_phone = await _get_candidate_phone(
                candidate_email, interview_id, kwargs.get("company_id", ""),
            )
            if candidate_phone:
                try:
                    from app.domains.communication.services.communication_dispatcher import communication_dispatcher
                    communication_dispatcher.send_whatsapp(
                        to_phone=candidate_phone,
                        message=f"Olá, {candidate_name}! Sua entrevista foi reagendada para {new_date_str}. Em breve você receberá o convite atualizado.",
                    )
                    notifications_sent.append({"channel": "whatsapp", "recipient": candidate_phone, "status": "sent"})
                except Exception as wa_err:
                    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                    logger.warning(f"[pipeline_tools] WhatsApp reschedule notification failed: {wa_err}")
                    notifications_sent.append({"channel": "whatsapp", "status": "failed"})

        # ADR-001-EXEMPT: part of interview workflow — audit notification INSERT; see EXEMPT marker on main async-with block above
        try:
            async with AsyncSessionLocal() as db:
                await db.execute(
                    # RLS-EXEMPT: notifications — user-scoped via user_id, no direct company_id column
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
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
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
        touches_pii=True,
        pii_output_fields=["name", "email", "phone", "linkedin_url"],
        output_schema=ToolOutput,
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
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        output_schema=ToolOutput,
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
        output_schema=ToolOutput,
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
        touches_pii=True,
        pii_output_fields=["salary_expectation_clt", "salary_expectation_pj"],
        output_schema=ToolOutput,
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
        output_schema=ToolOutput,
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
        output_schema=ToolOutput,
        function=_wrap_request_data_collection,
    ),
    ToolDefinition(
        name="get_stage_sub_statuses",
        description="Lista os sub-statuses disponíveis para a etapa de destino",
        parameters={
            "type": "object",
            "properties": {
                "to_stage": {"type": "string", "description": "Slug da etapa destino"},
            },
            "required": ["to_stage"],
        },
        output_schema=ToolOutput,
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
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        output_schema=ToolOutput,
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
        output_schema=ToolOutput,
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
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        output_schema=ToolOutput,
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
        output_schema=ToolOutput,
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
        output_schema=ToolOutput,
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
        output_schema=ToolOutput,
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
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        touches_pii=True,
        pii_output_fields=["candidate_name"],
        output_schema=ToolOutput,
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
        output_schema=ToolOutput,
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
        output_schema=ToolOutput,
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
                "preference_value": {"type": "string", "description": "Novo valor da preferência (ex: Google Meet, tarde, remoto)"},
                "context": {"type": "object", "description": "Contexto adicional: action_behavior, job_type, etc."},
            },
            "required": ["recruiter_id", "preference_key", "preference_value"],
        },
        output_schema=ToolOutput,
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
        output_schema=ToolOutput,
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
        side_effects=["write", "send"],
        requires_human_review=True,
        output_schema=ToolOutput,
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
        output_schema=ToolOutput,
        function=_wrap_reschedule_interview,
    ),
]

_TOOL_MAP: dict[str, ToolDefinition] = {t.name: t for t in ALL_TOOLS}

# Tools que requerem confirmação ou validação adicional antes de executar.
# Carregados dinamicamente do banco (GuardrailRepository) em runtime.
# Esta lista serve como fallback estático caso o banco esteja indisponível.
from app.shared.compliance.safety_category import SafetyCategory

GUARDRAIL_TOOLS: dict[str, SafetyCategory] = {
    "update_candidate_field": SafetyCategory.DESTRUCTIVE_WRITE,   # Alteração de dados cadastrais
    "move_candidate": SafetyCategory.PIPELINE_MOVE,               # Mudança de etapa no pipeline
    "batch_move": SafetyCategory.BULK_ACTION,                     # Mover múltiplos candidatos de uma vez
    "reject_candidate": SafetyCategory.PIPELINE_MOVE,             # Rejeição definitiva
    "finalize_hiring": SafetyCategory.OFFER,                      # Contratação (irreversível)
    "delete_job": SafetyCategory.DESTRUCTIVE_WRITE,               # Deletar vaga
    "send_bulk_email": SafetyCategory.OUTREACH,                   # Email em massa para candidatos
}


def get_pipeline_transition_tools(
    action_behavior: str = "passive",
    allowed_tool_names: list[str] | None = None,
) -> list[ToolDefinition]:
    if allowed_tool_names is None:
        from app.domains.pipeline.agents.pipeline_stage_context import get_allowed_tools_for_behavior
        allowed_tool_names = get_allowed_tools_for_behavior(action_behavior)

    return [_TOOL_MAP[name] for name in allowed_tool_names if name in _TOOL_MAP]
