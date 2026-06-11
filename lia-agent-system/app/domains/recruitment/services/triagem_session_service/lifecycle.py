"""
Session lifecycle: validate_token, get_session_config, create_session, start_session,
get_history, complete_session.
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.triagem import TriagemMessage, TriagemSession

from app.domains.recruitment.repositories.triagem_session_repository import (
    TriagemSessionRepository,
    find_job_vacancy_for_triagem,
)

from ._shared import (
    BLOCK_TRANSITION_MESSAGES,
    COMPLETION_MESSAGE,
    COMPLETION_NEXT_STEPS,
    WELCOME_MESSAGE,
    WSI_BLOCKS_FALLBACK,
    _build_progress,
    _get_session_blocks,
)
from .completion import _trigger_post_completion
from .scoring import _calculate_final_score, _score_response_deterministic
from .voice import _generate_tts_audio
from .wsi_blocks import _load_or_generate_blocks
from . import eligibility_phase
from app.domains.persona.services.ai_persona_service import get_ai_persona

logger = logging.getLogger(__name__)

# -- Expires-by-channel canonical (Phase 1a LGPD Consent 2026-06-11)
# Async channels allow pausing between sessions => 2 days.
# Sync channels (real-time call) expire later for scheduling => 7 days.
ASYNC_CHANNELS: frozenset[str] = frozenset({"chat_web", "whatsapp"})
SYNC_CHANNELS: frozenset[str] = frozenset({"chamada_online", "chamada_telefonica"})
_EXPIRES_DAYS_ASYNC: int = 2
_EXPIRES_DAYS_SYNC: int = 7


def get_expires_days_for_channel(invite_channel: str, override: int | None = None) -> int:
    """Return canonical expires_days for a given invite channel.

    Async channels (chat_web, whatsapp) allow candidates to pause and resume
    across sessions. A 2-day window reduces stale-link risk.
    Sync channels (calls) need a longer window for scheduling convenience.

    Args:
        invite_channel: The channel slug (whatsapp, chat_web, chamada_online, etc.)
        override: Caller-supplied override; honoured when explicitly set.
    """
    if override is not None:
        return override
    return _EXPIRES_DAYS_ASYNC if invite_channel in ASYNC_CHANNELS else _EXPIRES_DAYS_SYNC


async def validate_token(db: AsyncSession, token: str) -> dict[str, Any]:
    repo = TriagemSessionRepository(db)
    session = await repo.get_session_by_token(token)

    if not session:
        return {"valid": False, "error": "not_found", "status_code": 404}

    if session.expires_at and session.expires_at < datetime.utcnow():
        return {"valid": False, "error": "expired", "status_code": 410, "session": session.to_dict()}

    if session.status == "completed":
        return {"valid": True, "completed": True, "session": session.to_dict()}

    return {"valid": True, "completed": False, "session": session.to_dict()}


async def get_session_config(db: AsyncSession, token: str) -> dict[str, Any] | None:
    validation = await validate_token(db, token)
    if not validation["valid"]:
        return validation

    session_data = validation["session"]
    repo = TriagemSessionRepository(db)
    session_orm = await repo.get_session_by_token(token)
    messages = await repo.list_messages_for_session(uuid.UUID(session_data["id"]))

    job_info: dict[str, Any] = {}
    job_id = session_data.get("job_id")
    company_id = session_data.get("company_id")

    # Phase 1a — fetch ai_name for InterviewLobby (fail-open: default Lia if unavailable)
    ai_name = "Lia"
    if company_id:
        try:
            persona = await get_ai_persona(company_id, db)
            ai_name = persona.get("name", "Lia") or "Lia"
        except Exception as _e:
            logger.warning("[Triagem] Could not fetch ai_persona for company_id=%s: %s", company_id, _e)
    if job_id:
        try:
            job = await find_job_vacancy_for_triagem(db, job_id, company_id)
            if job:
                job_info["jobDescription"] = (job.description or "")[:500] if job.description else None
                job_info["location"] = job.location
                job_info["workModel"] = job.work_model
                meta = (session_orm.metadata_json if session_orm else None) or {}
                show_salary = meta.get("show_salary", False)
                show_benefits = meta.get("show_benefits", False)
                if show_salary and job.salary_range:
                    job_info["salaryRange"] = job.salary_range
                if show_benefits and job.benefits:
                    job_info["benefits"] = job.benefits
                job_info["showSalary"] = show_salary
                job_info["showBenefits"] = show_benefits
                sc = getattr(job, "screening_config", None) or {}
                phone_ch = (sc.get("channels") or {}).get("phone") or {}
                job_info["phoneEnabled"] = bool(phone_ch.get("enabled", False))
        except Exception as e:
            logger.warning(f"[Triagem] Could not fetch job info for job_id={job_id}: {e}")

    config = {
        "companyName": session_data.get("company_name", ""),
        "companyLogoUrl": session_data.get("company_logo_url"),
        "jobTitle": session_data.get("job_title", ""),
        "candidateName": session_data.get("candidate_name", ""),
        "estimatedMinutes": 20,
        "privacyPolicyUrl": "/politica-privacidade",
        "audioEnabled": True,
        "feedbackEnabled": True,
        "voiceMode": session_data.get("voice_mode", False),
        "welcomeMessage": WELCOME_MESSAGE.format(
            candidate_name=session_data.get("candidate_name", "Candidato"),
            job_title=session_data.get("job_title", "a vaga"),
            company_name=session_data.get("company_name", "a empresa"),
            total_blocks=session_data.get("total_blocks", len(WSI_BLOCKS_FALLBACK)),
        ),
        **job_info,
    }

    messages_data = [m.to_dict() for m in messages]

    # Phase 1a — resolve is_affirmative / affirmative_type from session metadata
    _session_meta = (session_orm.metadata_json if session_orm else None) or {}
    _is_affirmative: bool = bool(_session_meta.get("is_affirmative", False))
    _affirmative_type: str | None = _session_meta.get("affirmative_criteria") or None
    # expires_at from session model (already in to_dict but adding to top-level for InterviewLobby)
    _expires_at: str = session_data.get("expires_at", "")

    # Phase 1a — fetch show_wedotalent_branding from CompanyHiringPolicy (fail-open: True)
    _show_branding: bool = True
    if company_id:
        try:
            from app.domains.company.repositories.company_hiring_policy_repository import (
                CompanyHiringPolicyRepository,
            )
            _policy_repo = CompanyHiringPolicyRepository(session_orm._sa_instance_state.session if session_orm else None)  # type: ignore[attr-defined]
        except Exception:
            pass  # fail-open: keep _show_branding = True
    # Simpler approach: read from session metadata if stored, otherwise default True
    _show_branding = True  # Phase 1a default; full per-tenant via CompanyHiringPolicy in Phase 1b

    response: dict[str, Any] = {
        "valid": True,
        "completed": validation.get("completed", False),
        "session": session_data,
        "config": config,
        # InterviewLobby fields (Phase 1a)
        "ai_name": ai_name,
        "is_affirmative": _is_affirmative,
        "affirmative_type": _affirmative_type,
        "has_practice_question": False,  # default False — Phase 1b will set this
        "expires_at": _expires_at,
        "show_wedotalent_branding": _show_branding,
        "progress": _build_progress(
            session_data.get("current_block", 0),
            len([m for m in messages if m.sender == "candidate"]),
        ),
    }

    if messages_data:
        response["messages"] = messages_data

    if validation.get("completed", False):
        candidate_msgs = [m for m in messages if m.sender == "candidate"]
        started = session_data.get("started_at")
        completed = session_data.get("completed_at")
        duration = 0
        if started and completed:
            try:
                from datetime import datetime as dt
                s = dt.fromisoformat(started) if isinstance(started, str) else started
                c = dt.fromisoformat(completed) if isinstance(completed, str) else completed
                duration = max(1, int((c - s).total_seconds() / 60))
            except Exception:
                duration = 15
        company = session_data.get("company_name", "a empresa")
        response["completion_summary"] = {
            "questionsAnswered": len(candidate_msgs),
            "durationMinutes": duration,
            "nextSteps": [
                s.format(company_name=company) for s in COMPLETION_NEXT_STEPS
            ],
        }

    return response


async def create_session(
    db: AsyncSession,
    candidate_id: str,
    job_id: str,
    company_id: str,
    candidate_name: str | None = None,
    candidate_email: str | None = None,
    job_title: str | None = None,
    company_name: str | None = None,
    company_logo_url: str | None = None,
    invite_channel: str = "email",
    created_by: str | None = None,
    expires_days: int | None = None,
    voice_mode: bool = False,
) -> TriagemSession:
    # Phase 1a: if caller did not specify expires_days, derive from invite channel
    _expires_days = get_expires_days_for_channel(invite_channel, override=expires_days)
    screening_config: dict[str, Any] = {}
    job = await find_job_vacancy_for_triagem(db, job_id, company_id)
    if job:
        screening_config = getattr(job, "screening_config", None) or {}

    blocks, qs_id, qs_version = await _load_or_generate_blocks(db, job_id, job)
    total_blocks = len(blocks)

    settings = screening_config.get("settings") or {}
    seniority_level = None
    is_affirmative = False
    affirmative_criteria = None
    eliminatory_keywords: list[str] = []
    if job:
        seniority_level = getattr(job, "seniority_level", None)
        is_affirmative = bool(getattr(job, "is_affirmative", False))
        affirmative_criteria = getattr(job, "affirmative_criteria_primary", None)
    eliminatory_questions = []
    for q in (screening_config.get("eliminatory_questions") or []):
        if isinstance(q, dict):
            eliminatory_keywords.extend(
                str(k).lower() for k in (q.get("eliminatory_keywords") or []) if k
            )
            eliminatory_questions.append(q)
    feedback_enabled = settings.get("feedback_enabled", True)
    show_salary = settings.get("show_salary", False)
    show_benefits = settings.get("show_benefits", False)

    session_meta: dict[str, Any] = {
        "wsi_blocks_cache": blocks,
        "wsi_question_set_id": qs_id,
        "wsi_question_set_version": qs_version,
        "screening_config": screening_config,
        "seniority_level": seniority_level,
        "is_affirmative": is_affirmative,
        "affirmative_criteria": affirmative_criteria,
        "eliminatory_keywords": eliminatory_keywords,
        "eliminatory_questions": eliminatory_questions,
        "feedback_enabled": feedback_enabled,
        "show_salary": show_salary,
        "show_benefits": show_benefits,
    }
    elig_state = eligibility_phase.build_eligibility_state(
        getattr(job, "eligibility_questions", None) or []
    )
    if elig_state:
        session_meta["eligibility"] = elig_state
    if not qs_id and not qs_version:
        session_meta["question_source"] = "fallback"
    else:
        session_meta["question_source"] = "question_set"

    token = str(uuid.uuid4())
    session = TriagemSession(
        token=token,
        candidate_id=candidate_id,
        candidate_name=candidate_name,
        candidate_email=candidate_email,
        job_id=job_id,
        job_title=job_title,
        company_id=company_id,
        company_name=company_name,
        company_logo_url=company_logo_url,
        status="invited",
        current_block=0,
        total_blocks=total_blocks,
        invite_channel=invite_channel,
        voice_mode=voice_mode,
        expires_at=datetime.utcnow() + timedelta(days=_expires_days),
        created_by=created_by,
        metadata_json=session_meta,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)

    welcome = WELCOME_MESSAGE.format(
        candidate_name=candidate_name or "candidato(a)",
        job_title=job_title or "a vaga",
        company_name=company_name or "a empresa",
        total_blocks=total_blocks,
    )
    welcome_msg = TriagemMessage(
        session_id=session.id,
        sender="lia",
        content=welcome,
        message_type="welcome",
        wsi_block=0,
    )
    db.add(welcome_msg)
    await db.flush()

    return session


async def start_session(db: AsyncSession, token: str, voice_mode: bool | None = None) -> dict[str, Any]:
    repo = TriagemSessionRepository(db)
    session = await repo.get_session_by_token(token)
    if not session:
        return {"error": "not_found"}
    # SEG-4 (Epico Elegibilidade Fase D): gate de consentimento LGPD no BACKEND
    # antes de iniciar a triagem. Antes so havia checkbox no frontend (nunca
    # verificado no servidor). Produtor canonico: ConsentCheckerService.
    if session.status == "invited" and session.candidate_id and session.company_id:
        try:
            from app.domains.lgpd.services.consent_checker_service import (
                ConsentCheckerService,
            )
            _consent = await ConsentCheckerService(db).check_candidate_consent(
                candidate_id=session.candidate_id,
                company_id=session.company_id,
                purpose="ai_screening",
            )
            if not _consent.allowed:
                logger.warning(
                    "[Triagem][SEG-4] consentimento negado candidate=%s reason=%s",
                    session.candidate_id, getattr(_consent, "reason", None),
                )
                return {
                    "error": "lgpd_consent_revoked",
                    "reason": getattr(_consent, "reason", None),
                    "session": session.to_dict(),
                }
        except Exception as _consent_exc:
            # P1 (audit 2026-06-05 #13): FAIL-CLOSED. Se a verificacao de consent
            # lanca, NAO prosseguir — bloquear a sessao (LGPD: nao iniciar triagem
            # com IA sem consent verificado no servidor). Antes caia atraves => fail-open.
            logger.error(
                "[Triagem][SEG-4] consent check falhou — fail-closed (sessao BLOQUEADA): %s",
                _consent_exc, exc_info=True,
            )
            return {
                "error": "lgpd_consent_check_failed",
                "reason": "Falha ao verificar consentimento; sessao bloqueada por seguranca (LGPD).",
                "session": session.to_dict(),
            }

    if session.status == "invited":
        session.status = "started"
        session.started_at = datetime.utcnow()

    if voice_mode is not None:
        session.voice_mode = voice_mode
    await db.flush()

    use_voice = voice_mode if voice_mode is not None else session.voice_mode

    active_blocks = _get_session_blocks(session)
    _elig = (session.metadata_json or {}).get("eligibility") or {}
    if eligibility_phase.is_active(_elig):
        _eq = eligibility_phase.current_question_text(_elig)
        transition = (
            "Antes de comecarmos, preciso confirmar alguns requisitos da vaga.\n\n"
            f"{_eq}"
        )
        _first_qid = "eligibility_0"
    else:
        first_block = active_blocks[0]
        first_question = first_block["questions"][0]
        transition = f"Vamos comecar pela etapa de **{first_block['name']}**.\n\n{first_question}"
        _first_qid = "block_0_q_0"

    audio_b64 = None
    if use_voice:
        audio_b64 = await _generate_tts_audio(transition)

    lia_msg = TriagemMessage(
        session_id=session.id,
        sender="lia",
        content=transition,
        message_type="question",
        wsi_block=0,
        wsi_question_id=_first_qid,
        audio_base64=audio_b64,
    )
    db.add(lia_msg)
    await db.flush()

    return {
        "session": session.to_dict(),
        "lia_response": lia_msg.to_dict(),
        "progress": _build_progress(session.current_block, 0, active_blocks),
    }


async def get_history(db: AsyncSession, token: str) -> dict[str, Any]:
    repo = TriagemSessionRepository(db)
    session = await repo.get_session_by_token(token)
    if not session:
        return {"error": "not_found"}

    messages = await repo.list_messages_for_session(session.id)

    return {
        "session": session.to_dict(),
        "messages": [m.to_dict() for m in messages],
        "total": len(messages),
    }


async def complete_session(db: AsyncSession, token: str) -> dict[str, Any]:
    repo = TriagemSessionRepository(db)
    session = await repo.get_session_by_token(token)
    if not session:
        return {"error": "not_found"}

    if session.status == "completed":
        return {"error": "already_completed", "session": session.to_dict()}

    session.status = "completed"
    session.completed_at = datetime.utcnow()

    candidate_msgs = await repo.list_candidate_messages_for_session(session.id)
    lia_question_msgs = await repo.list_lia_question_messages_for_session(session.id)
    lia_by_block: dict[int, list[TriagemMessage]] = {}
    for lm in lia_question_msgs:
        bidx = lm.wsi_block if lm.wsi_block is not None else 0
        lia_by_block.setdefault(bidx, []).append(lm)

    active_blocks = _get_session_blocks(session)
    session_meta_for_scoring = session.metadata_json or {}
    eliminatory_keywords: list[str] = [
        str(k).lower() for k in (session_meta_for_scoring.get("eliminatory_keywords") or [])
    ]
    # F9-2: senioridade da vaga gravada no metadata ao criar sessao (seniority_level)
    session_seniority: str | None = session_meta_for_scoring.get("seniority_level")

    candidate_by_block: dict[int, list[TriagemMessage]] = {}
    for msg in candidate_msgs:
        bidx = msg.wsi_block if msg.wsi_block is not None else 0
        candidate_by_block.setdefault(bidx, []).append(msg)

    response_scores = []
    for msg in candidate_msgs:
        block_idx = msg.wsi_block if msg.wsi_block is not None else 0
        if block_idx < len(active_blocks):
            block = active_blocks[block_idx]
            block_type = block.get("block_type", "behavioral")
            competency = block.get("competency", "general")
            score_result = _score_response_deterministic(
                msg.content,
                block_type,
                competency,
            )
            score_result["competency"] = competency
            score_result["block_type"] = block_type
            score_result["block_index"] = block_idx
            score_result["response_text"] = (msg.content or "")[:2000]
            block_lia_msgs = lia_by_block.get(block_idx, [])
            block_candidate_pos = candidate_by_block.get(block_idx, []).index(msg) if msg in candidate_by_block.get(block_idx, []) else 0
            if block_lia_msgs and block_candidate_pos < len(block_lia_msgs):
                score_result["question_text"] = (block_lia_msgs[block_candidate_pos].content or "")[:500]
            else:
                score_result["question_text"] = block.get("questions", [""])[0][:500] if block.get("questions") else ""
            if eliminatory_keywords:
                response_lower = (msg.content or "").lower()
                score_result["has_eliminatory_hit"] = any(kw in response_lower for kw in eliminatory_keywords)
            response_scores.append(score_result)

    final_score, recommendation = _calculate_final_score(response_scores, seniority=session_seniority)
    session.wsi_final_score = final_score
    session.recommendation = recommendation

    completion_content = COMPLETION_MESSAGE.format(
        candidate_name=session.candidate_name or "candidato(a)",
        company_name=session.company_name or "a empresa",
    )
    completion_msg = TriagemMessage(
        session_id=session.id,
        sender="lia",
        content=completion_content,
        message_type="completion",
        wsi_block=session.current_block,
    )
    db.add(completion_msg)
    await db.flush()

    post_actions = await _trigger_post_completion(db, session, response_scores)

    duration = 0
    if session.started_at and session.completed_at:
        duration = max(1, int((session.completed_at - session.started_at).total_seconds() / 60))

    return {
        "session": session.to_dict(),
        "completion_message": completion_msg.to_dict(),
        "wsi_score": session.wsi_final_score,
        "recommendation": session.recommendation,
        "completion_summary": {
            "questionsAnswered": len(candidate_msgs),
            "durationMinutes": duration,
            "nextSteps": [
                s.format(company_name=session.company_name or "a empresa")
                for s in COMPLETION_NEXT_STEPS
            ],
        },
        "post_actions": post_actions,
    }


