"""
Session lifecycle: validate_token, get_session_config, create_session, start_session,
get_history, complete_session.
"""
import logging
import random
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.candidate import Candidate
from lia_models.job_vacancy import JobVacancy
from lia_models.triagem import TriagemMessage, TriagemSession

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

logger = logging.getLogger(__name__)


async def validate_token(db: AsyncSession, token: str) -> dict[str, Any]:
    result = await db.execute(
        select(TriagemSession).where(TriagemSession.token == token)
    )
    session = result.scalar_one_or_none()

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
    session_result = await db.execute(
        select(TriagemSession).where(TriagemSession.token == token)
    )
    session_orm: TriagemSession | None = session_result.scalar_one_or_none()
    msg_result = await db.execute(
        select(TriagemMessage).where(
            TriagemMessage.session_id == uuid.UUID(session_data["id"])
        ).order_by(TriagemMessage.created_at)
    )
    messages = msg_result.scalars().all()

    job_info: dict[str, Any] = {}
    job_id = session_data.get("job_id")
    company_id = session_data.get("company_id")
    if job_id:
        try:
            query = select(JobVacancy).where(JobVacancy.job_id == job_id)
            if company_id and hasattr(JobVacancy, "company_id"):
                query = query.where(JobVacancy.company_id == company_id)
            job_result = await db.execute(query)
            job = job_result.scalar_one_or_none()
            if not job:
                query2 = select(JobVacancy).where(JobVacancy.id == uuid.UUID(job_id))
                if company_id and hasattr(JobVacancy, "company_id"):
                    query2 = query2.where(JobVacancy.company_id == company_id)
                job_result2 = await db.execute(query2)
                job = job_result2.scalar_one_or_none()
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
                channels = sc.get("channels") or {}
                # Task #425 — canonical 4-channel model with legacy fallback,
                # all gated by the master channel toggle (default ON for back-compat).
                chat_ch = channels.get("chat_web") or {}
                whatsapp_ch = channels.get("whatsapp") or {}
                phone_ch = channels.get("phone_pstn") or channels.get("phone") or {}
                voice_ch = channels.get("voice_web") or channels.get("voip_web") or {}
                master_enabled = sc.get("channels_master_enabled", True)
                job_info["chatWebEnabled"] = bool(master_enabled) and bool(chat_ch.get("enabled", True))
                job_info["whatsappEnabled"] = bool(master_enabled) and bool(whatsapp_ch.get("enabled", True))
                job_info["phoneEnabled"] = bool(master_enabled) and bool(phone_ch.get("enabled", False))
                job_info["voiceWebEnabled"] = bool(master_enabled) and bool(voice_ch.get("enabled", True))
        except Exception as e:
            logger.warning(f"[Triagem] Could not fetch job info for job_id={job_id}: {e}")

    # Task #425 — resolve candidate phone for PhoneConfirmModal pre-fill
    candidate_phone: str | None = session_data.get("candidate_phone")
    if not candidate_phone:
        cand_id = session_data.get("candidate_id")
        if cand_id:
            try:
                cand_uuid = uuid.UUID(cand_id) if isinstance(cand_id, str) else cand_id
                cand_result = await db.execute(
                    select(Candidate).where(Candidate.id == cand_uuid)
                )
                cand = cand_result.scalar_one_or_none()
                if cand:
                    candidate_phone = (
                        getattr(cand, "mobile_phone", None)
                        or getattr(cand, "phone", None)
                    )
            except Exception as e:
                logger.warning(f"[Triagem] Could not fetch candidate phone for candidate_id={cand_id}: {e}")

    config = {
        "companyName": session_data.get("company_name", ""),
        "companyLogoUrl": session_data.get("company_logo_url"),
        "jobTitle": session_data.get("job_title", ""),
        "candidateName": session_data.get("candidate_name", ""),
        "candidatePhone": candidate_phone,
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

    response: dict[str, Any] = {
        "valid": True,
        "completed": validation.get("completed", False),
        "session": session_data,
        "config": config,
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
    expires_days: int = 7,
    voice_mode: bool = False,
) -> TriagemSession:
    job = None
    screening_config: dict[str, Any] = {}
    try:
        q = select(JobVacancy).where(JobVacancy.job_id == job_id)
        if company_id and hasattr(JobVacancy, "company_id"):
            q = q.where(JobVacancy.company_id == company_id)
        job_result = await db.execute(q)
        job = job_result.scalar_one_or_none()
        if not job:
            try:
                q2 = select(JobVacancy).where(JobVacancy.id == uuid.UUID(job_id))
                if company_id and hasattr(JobVacancy, "company_id"):
                    q2 = q2.where(JobVacancy.company_id == company_id)
                job_result2 = await db.execute(q2)
                job = job_result2.scalar_one_or_none()
            except Exception:
                pass
        if job:
            screening_config = getattr(job, "screening_config", None) or {}
    except Exception as exc:
        logger.warning(f"[Triagem] Could not load job for session creation (job_id={job_id}): {exc}")

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
        expires_at=datetime.utcnow() + timedelta(days=expires_days),
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
    result = await db.execute(
        select(TriagemSession).where(TriagemSession.token == token)
    )
    session = result.scalar_one_or_none()
    if not session:
        return {"error": "not_found"}

    # Task #425 — session resumption: cap reopens to 2 (after the original
    # invited→started transition). reopen_count is persisted in
    # TriagemSession.metadata_json (JSON column, no migration required).
    REOPEN_LIMIT = 2
    if session.status == "invited":
        session.status = "started"
        session.started_at = datetime.utcnow()
    elif session.status in ("started", "in_progress"):
        meta = dict(session.metadata_json or {})
        current = int(meta.get("reopen_count", 0))
        if current >= REOPEN_LIMIT:
            return {
                "error": "reopen_limit_exceeded",
                "reopen_count": current,
                "limit": REOPEN_LIMIT,
                "message": (
                    f"Esta triagem já foi retomada {current}x e atingiu o limite "
                    f"de {REOPEN_LIMIT} reaberturas. Procure o recrutador para liberar uma nova tentativa."
                ),
            }
        meta["reopen_count"] = current + 1
        meta["last_reopened_at"] = datetime.utcnow().isoformat()
        session.metadata_json = meta
    elif session.status == "completed":
        return {
            "error": "session_completed",
            "message": "Esta triagem já foi finalizada e não pode ser reaberta.",
        }

    if voice_mode is not None:
        session.voice_mode = voice_mode
    await db.flush()

    use_voice = voice_mode if voice_mode is not None else session.voice_mode

    active_blocks = _get_session_blocks(session)
    first_block = active_blocks[0]
    first_question = first_block["questions"][0]
    transition = f"Vamos começar pela etapa de **{first_block['name']}**.\n\n{first_question}"

    audio_b64 = None
    if use_voice:
        audio_b64 = await _generate_tts_audio(transition)

    lia_msg = TriagemMessage(
        session_id=session.id,
        sender="lia",
        content=transition,
        message_type="question",
        wsi_block=0,
        wsi_question_id="block_0_q_0",
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
    result = await db.execute(
        select(TriagemSession).where(TriagemSession.token == token)
    )
    session = result.scalar_one_or_none()
    if not session:
        return {"error": "not_found"}

    msg_result = await db.execute(
        select(TriagemMessage).where(
            TriagemMessage.session_id == session.id
        ).order_by(TriagemMessage.created_at)
    )
    messages = msg_result.scalars().all()

    return {
        "session": session.to_dict(),
        "messages": [m.to_dict() for m in messages],
        "total": len(messages),
    }


async def complete_session(db: AsyncSession, token: str) -> dict[str, Any]:
    result = await db.execute(
        select(TriagemSession).where(TriagemSession.token == token)
    )
    session = result.scalar_one_or_none()
    if not session:
        return {"error": "not_found"}

    if session.status == "completed":
        return {"error": "already_completed", "session": session.to_dict()}

    session.status = "completed"
    session.completed_at = datetime.utcnow()

    scored_msgs_result = await db.execute(
        select(TriagemMessage).where(
            and_(
                TriagemMessage.session_id == session.id,
                TriagemMessage.sender == "candidate",
            )
        ).order_by(TriagemMessage.created_at)
    )
    candidate_msgs = scored_msgs_result.scalars().all()

    lia_msgs_result = await db.execute(
        select(TriagemMessage).where(
            and_(
                TriagemMessage.session_id == session.id,
                TriagemMessage.sender == "lia",
                TriagemMessage.message_type == "question",
            )
        ).order_by(TriagemMessage.created_at)
    )
    lia_question_msgs = lia_msgs_result.scalars().all()
    lia_by_block: dict[int, list[TriagemMessage]] = {}
    for lm in lia_question_msgs:
        bidx = lm.wsi_block if lm.wsi_block is not None else 0
        lia_by_block.setdefault(bidx, []).append(lm)

    active_blocks = _get_session_blocks(session)
    session_meta_for_scoring = session.metadata_json or {}
    eliminatory_keywords: list[str] = [
        str(k).lower() for k in (session_meta_for_scoring.get("eliminatory_keywords") or [])
    ]

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

    final_score, recommendation = _calculate_final_score(response_scores)
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


