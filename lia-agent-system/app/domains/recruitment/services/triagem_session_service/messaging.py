"""
Message processing: process_message, _generate_lia_response, _pre_completion_response.
"""
import logging
import random
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.triagem import TriagemMessage, TriagemSession

from app.domains.recruitment.repositories.triagem_session_repository import (
    TriagemSessionRepository,
)

from ._shared import (
    BLOCK_TRANSITION_MESSAGES,
    FORCE_RESUME_MESSAGE,
    MAX_CONSECUTIVE_OFF_SCRIPT,
    PRE_COMPLETION_MESSAGE,
    _build_progress,
    _get_session_blocks,
)
from .conversation import (
    _classify_intent,
    _generate_contextual_question,
    _generate_off_script_response,
)
from .scoring import _score_response_deterministic
from .voice import _generate_tts_audio
from . import eligibility_phase
from sqlalchemy.orm.attributes import flag_modified

logger = logging.getLogger(__name__)


async def process_message(
    db: AsyncSession,
    token: str,
    content: str,
    message_type: str = "text",
    voice_mode: bool | None = None,
) -> dict[str, Any]:
    repo = TriagemSessionRepository(db)
    session = await repo.get_session_by_token(token)
    if not session:
        return {"error": "not_found"}

    if session.status == "completed":
        return {"error": "already_completed"}

    if session.status == "invited":
        session.status = "started"
        session.started_at = datetime.utcnow()

    if session.status not in ("started", "in_progress"):
        session.status = "in_progress"

    use_voice = voice_mode if voice_mode is not None else session.voice_mode

    _meta0 = session.metadata_json or {}
    _in_elig = eligibility_phase.is_active(_meta0.get("eligibility") or {})
    _msg_block = 999 if _in_elig else session.current_block
    candidate_msg = TriagemMessage(
        session_id=session.id,
        sender="candidate",
        content=content,
        message_type=message_type,
        wsi_block=_msg_block,
    )
    db.add(candidate_msg)
    await db.flush()

    lia_response = await _generate_lia_response(db, session, content)

    audio_b64 = None
    if use_voice:
        audio_b64 = await _generate_tts_audio(lia_response["content"])

    lia_msg = TriagemMessage(
        session_id=session.id,
        sender="lia",
        content=lia_response["content"],
        message_type=lia_response["type"],
        wsi_block=session.current_block,
        wsi_question_id=lia_response.get("question_id"),
        score=lia_response.get("score"),
        audio_base64=audio_b64,
    )
    db.add(lia_msg)
    await db.flush()

    answered_count = len(
        await repo.list_candidate_messages_for_session(session.id)
    )
    active_blocks = _get_session_blocks(session)

    return {
        "candidate_message": candidate_msg.to_dict(),
        "lia_response": lia_msg.to_dict(),
        "progress": _build_progress(session.current_block, answered_count, active_blocks),
        "is_pre_completion": lia_response.get("is_pre_completion", False),
    }


async def _generate_lia_response(
    db: AsyncSession, session: TriagemSession, candidate_content: str
) -> dict[str, Any]:
    repo = TriagemSessionRepository(db)
    _meta = session.metadata_json or {}
    _elig = _meta.get("eligibility") or {}
    if eligibility_phase.outcome(_elig) == "talent_pool":
        # candidato eliminado na elegibilidade — NAO inicia WSI; encerra com
        # mensagem de banco de talentos (sessao nao avanca para a entrevista).
        return {
            "content": (
                "Como conversamos, seu perfil foi adicionado ao nosso banco de "
                "talentos para oportunidades futuras compativeis. Obrigada pelo "
                "interesse!"
            ),
            "type": "eligibility_talent_pool",
            "question_id": None,
            "is_pre_completion": True,
        }
    if eligibility_phase.is_active(_elig):
        _new_elig, _resp = eligibility_phase.advance(_elig, candidate_content)
        _meta["eligibility"] = _new_elig
        if _resp.get("talent_pool"):
            _meta["eligibility_outcome"] = "talent_pool"
        session.metadata_json = _meta
        flag_modified(session, "metadata_json")
        await db.flush()
        if _resp.get("talent_pool"):
            return {
                "content": _resp.get("content", ""),
                "type": "eligibility_talent_pool",
                "question_id": None,
                "is_pre_completion": True,
            }
        if _resp.get("eligibility_done"):
            _blocks = _get_session_blocks(session)
            _fb = _blocks[0]
            _fq = _fb["questions"][0]
            return {
                "content": f"Perfeito! Agora vamos a entrevista. Vamos comecar pela etapa de {_fb['name']}: {_fq}",
                "type": "question",
                "question_id": "block_0_q_0",
            }
        return {
            "content": _resp.get("content", ""),
            "type": _resp.get("type", "question"),
            "question_id": f"eligibility_{_new_elig.get('index', 0)}",
        }
    candidate_msgs = await repo.list_candidate_messages_for_session(session.id)
    candidate_count = len(candidate_msgs)

    active_blocks = _get_session_blocks(session)
    current_block_idx = session.current_block
    if current_block_idx >= len(active_blocks):
        return _pre_completion_response(session, candidate_count)

    current_block = active_blocks[current_block_idx]
    questions = current_block["questions"]
    block_name = current_block["name"]
    block_type = current_block.get("block_type", "behavioral")
    competency = current_block.get("competency", "general")

    last_lia_msg = await repo.get_last_lia_question_message(session.id)
    current_question_text = last_lia_msg.content if last_lia_msg else questions[0]

    intent = await _classify_intent(candidate_content, block_name, current_question_text)

    meta = session.metadata_json or {}
    consecutive_off_script = meta.get("consecutive_off_script", 0)

    if intent in ("QUESTION", "GREETING"):
        consecutive_off_script += 1
        meta["consecutive_off_script"] = consecutive_off_script
        session.metadata_json = meta
        await db.flush()

        if consecutive_off_script >= MAX_CONSECUTIVE_OFF_SCRIPT:
            meta["consecutive_off_script"] = 0
            session.metadata_json = meta
            await db.flush()
            return {
                "content": FORCE_RESUME_MESSAGE.format(original_question=current_question_text),
                "type": "off_script_response",
                "question_id": None,
            }

        if intent == "QUESTION":
            off_script_response = await _generate_off_script_response(
                candidate_message=candidate_content,
                original_question=current_question_text,
                block_name=block_name,
                company_name=session.company_name or "",
                job_title=session.job_title or "",
            )
            if off_script_response:
                return {
                    "content": off_script_response,
                    "type": "off_script_response",
                    "question_id": None,
                }
            return {
                "content": f"Entendo sua dúvida, mas no momento não tenho essa informação. O recrutador poderá esclarecer após a triagem. Vamos prosseguir: {current_question_text}",
                "type": "off_script_response",
                "question_id": None,
            }

        return {
            "content": f"Olá! Vamos prosseguir com a triagem. {current_question_text}",
            "type": "off_script_response",
            "question_id": None,
        }

    if consecutive_off_script > 0:
        meta["consecutive_off_script"] = 0
        session.metadata_json = meta
        await db.flush()

    score_result = _score_response_deterministic(candidate_content, block_type, competency)

    block_candidate_msgs = await repo.list_candidate_messages_in_block(
        session.id, current_block_idx
    )
    q_index = len(block_candidate_msgs)

    if q_index < len(questions):
        base_question = questions[q_index]

        contextual_question = await _generate_contextual_question(
            previous_question=current_question_text,
            candidate_response=candidate_content,
            base_question=base_question,
            block_name=block_name,
            block_type=block_type,
            competency=competency,
            company_name=session.company_name or "",
            job_title=session.job_title or "",
        )

        final_question = contextual_question if contextual_question else base_question

        return {
            "content": final_question,
            "type": "question",
            "question_id": f"block_{current_block_idx}_q_{q_index}",
            "score": score_result["score"],
        }

    next_block_idx = current_block_idx + 1
    session.current_block = next_block_idx
    await db.flush()

    if next_block_idx >= len(active_blocks):
        return _pre_completion_response(session, candidate_count)

    next_block = active_blocks[next_block_idx]
    transition = random.choice(BLOCK_TRANSITION_MESSAGES).format(block_name=next_block["name"])
    first_question = next_block["questions"][0]

    return {
        "content": f"{transition}\n\n{first_question}",
        "type": "question",
        "question_id": f"block_{next_block_idx}_q_0",
        "score": score_result["score"],
    }


def _pre_completion_response(session: TriagemSession, total_questions: int) -> dict[str, Any]:
    duration = 0
    if session.started_at:
        duration = int((datetime.utcnow() - session.started_at).total_seconds() / 60)

    content = PRE_COMPLETION_MESSAGE.format(
        total_questions=total_questions,
        duration_minutes=max(duration, 1),
    )
    return {
        "content": content,
        "type": "confirmation",
        "is_pre_completion": True,
    }


