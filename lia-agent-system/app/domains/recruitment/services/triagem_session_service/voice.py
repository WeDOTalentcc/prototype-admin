"""
Voice helpers: TTS generation and phone call initiation.
"""
import base64 as _b64
import logging
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.triagem import TriagemMessage, TriagemSession

from app.domains.recruitment.repositories.triagem_session_repository import (
    TriagemSessionRepository,
    find_job_vacancy_for_triagem,
)

logger = logging.getLogger(__name__)


async def _generate_tts_audio(text: str) -> str | None:
    try:
        from app.shared.services.voice_service import voice_service
        availability = voice_service.is_available()
        if not availability.get("any_synthesis"):
            logger.warning("[Triagem] TTS not available: no API key configured")
            return None
        clean_text = text.replace("**", "").replace("*", "").replace("#", "").replace("•", "-")
        if len(clean_text.strip()) < 2:
            return None
        audio_bytes = await voice_service.synthesize_speech(
            text=clean_text,
            voice="nova",
            speed=1.0,
            model="tts-1",
        )
        return _b64.b64encode(audio_bytes).decode("utf-8")
    except Exception as exc:
        logger.warning(f"[Triagem] TTS generation failed: {exc}")
        return None


async def generate_tts_for_message(
    db: AsyncSession, session: TriagemSession, message_id: str
) -> dict[str, Any]:
    import uuid as _uuid
    try:
        msg_uuid = _uuid.UUID(message_id)
    except (ValueError, AttributeError):
        return {"error": "not_found"}

    repo = TriagemSessionRepository(db)
    message = await repo.get_message_for_session(msg_uuid, session.id)
    if not message:
        return {"error": "not_found"}

    if message.sender != "lia":
        return {"error": "not_lia_message"}

    if message.audio_base64:
        return {"audio_base64": message.audio_base64, "message_id": str(message.id)}

    audio_b64 = await _generate_tts_audio(message.content)
    if not audio_b64:
        return {"error": "tts_failed"}

    message.audio_base64 = audio_b64
    await db.commit()

    return {"audio_base64": audio_b64, "message_id": str(message.id)}


async def request_phone_call(
    db: AsyncSession, session: TriagemSession, candidate_phone: str
) -> dict[str, Any]:
    job_id = session.job_id
    company_id = session.company_id
    job = None
    if job_id:
        job = await find_job_vacancy_for_triagem(db, job_id, company_id)

    sc = (getattr(job, "screening_config", None) or {}) if job else {}
    phone_ch = (sc.get("channels") or {}).get("phone") or {}
    if not phone_ch.get("enabled", False):
        return {"error": "phone_not_enabled"}

    existing_call = (session.metadata_json or {}).get("phone_call")
    if existing_call:
        requested_at = existing_call.get("requested_at")
        if requested_at:
            try:
                last_req = datetime.fromisoformat(requested_at)
                cooldown_seconds = 120
                if (datetime.utcnow() - last_req).total_seconds() < cooldown_seconds:
                    return {
                        "error": "call_already_requested",
                        "message": "Uma ligacao ja foi solicitada recentemente. Aguarde alguns minutos.",
                    }
            except (ValueError, TypeError):
                pass

    try:
        from app.domains.cv_screening.services.wsi_service import Competency
        from app.domains.cv_screening.services.wsi_voice_orchestrator import wsi_voice_orchestrator

        job_title = session.job_title or "a vaga"
        job_description = (job.description or "")[:1000] if job and job.description else ""

        competencies: list[Competency] = []
        if job and getattr(job, "screening_config", None):
            skills = job.screening_config.get("skills") or {}
            for skill_name, skill_data in list(skills.items())[:10]:
                if isinstance(skill_data, dict):
                    comp_type = skill_data.get("type", "technical")
                else:
                    comp_type = "technical"
                competencies.append(Competency(
                    name=skill_name,
                    type=comp_type if comp_type in ("technical", "behavioral", "cultural") else "technical",
                    weight=0.5,
                    seniority_level="pleno",
                ))
        if not competencies:
            competencies = [
                Competency(name="Experiencia Relevante", type="technical", weight=0.5, seniority_level="pleno"),
                Competency(name="Comunicacao", type="behavioral", weight=0.5, seniority_level="pleno"),
            ]

        voice_result = await wsi_voice_orchestrator.start_voice_screening(
            candidate_id=session.candidate_id,
            job_vacancy_id=session.job_id,
            competencies=competencies,
            candidate_phone=candidate_phone,
            candidate_name=session.candidate_name or "Candidato",
            job_title=job_title,
            job_description=job_description,
            mode="compact",
            db=db,
        )

        call_id = voice_result.call_id
        agent_id = voice_result.agent_id
        wsi_session_id = voice_result.session_id

        meta = session.metadata_json or {}
        meta["phone_call"] = {
            "call_id": call_id,
            "agent_id": agent_id,
            "wsi_session_id": wsi_session_id,
            "candidate_phone": candidate_phone,
            "requested_at": datetime.utcnow().isoformat(),
            "triagem_token": session.token,
        }
        session.metadata_json = meta
        session.status = "started" if session.status == "invited" else session.status
        session.started_at = session.started_at or datetime.utcnow()
        await db.commit()

        logger.info(
            f"[Triagem] Phone call requested: token={session.token}, call_id={call_id}, "
            f"wsi_session={wsi_session_id}, questions={voice_result.questions_generated}"
        )

        return {
            "status": "call_initiated",
            "call_id": call_id,
            "agent_id": agent_id,
            "wsi_session_id": wsi_session_id,
            "message": "Ligacao sendo realizada. Voce recebera uma chamada em instantes.",
        }

    except Exception as e:
        try:
            await db.rollback()
        except Exception:
            pass
        logger.error(f"[Triagem] Phone call request failed: {e}", exc_info=True)
        return {"error": "call_failed", "detail": str(e)}
