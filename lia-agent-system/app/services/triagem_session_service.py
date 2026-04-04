import uuid
import logging
import random
import base64
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.triagem import TriagemSession, TriagemMessage
from lia_models.job_vacancy import JobVacancy

logger = logging.getLogger(__name__)


async def _generate_tts_audio(text: str) -> Optional[str]:
    try:
        from app.services.voice_service import voice_service
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
        return base64.b64encode(audio_bytes).decode("utf-8")
    except Exception as exc:
        logger.warning(f"[Triagem] TTS generation failed: {exc}")
        return None

WSI_BLOCKS = [
    {"index": 0, "name": "Técnico", "block_type": "technical", "competency": "technical_skills", "questions": [
        "Para começar, gostaria de confirmar algumas informações. Você tem disponibilidade para início imediato ou em qual prazo?",
        "Qual sua pretensão salarial para esta posição?",
        "Conte-me sobre sua experiência mais relevante para esta vaga. Quais tecnologias ou ferramentas você domina?",
        "Descreva um projeto técnico desafiador que você liderou ou participou. Qual foi seu papel e o resultado?",
    ]},
    {"index": 1, "name": "Comportamental", "block_type": "behavioral", "competency": "interpersonal_skills", "questions": [
        "Me conte sobre uma situação em que você precisou lidar com um conflito no ambiente de trabalho. Como você agiu?",
        "Descreva um momento em que você recebeu um feedback difícil. Como reagiu e o que mudou?",
    ]},
    {"index": 2, "name": "Situacional", "block_type": "situational", "competency": "problem_solving", "questions": [
        "Imagine que você recebe uma demanda urgente de dois gestores diferentes ao mesmo tempo. Como você priorizaria?",
        "Se você percebesse que um colega está cometendo um erro que pode impactar o projeto, como abordaria a situação?",
    ]},
    {"index": 3, "name": "Autodeclaração", "block_type": "behavioral", "competency": "self_assessment", "questions": [
        "Em uma escala de 1 a 5, como você avalia sua capacidade de trabalhar sob pressão?",
        "Quais são seus três principais pontos fortes profissionais?",
    ]},
    {"index": 4, "name": "Motivação", "block_type": "behavioral", "competency": "motivation", "questions": [
        "O que te motivou a se candidatar para esta vaga?",
        "Onde você se vê profissionalmente nos próximos 2-3 anos?",
    ]},
    {"index": 5, "name": "Encerramento", "block_type": "behavioral", "competency": "cultural_fit", "questions": [
        "Há algo mais que você gostaria de compartilhar sobre seu perfil ou experiência?",
    ]},
]

WELCOME_MESSAGE = (
    "Vou conduzir sua triagem para a vaga de {job_title} na {company_name}. "
    "A conversa tem {total_blocks} etapas e dura aproximadamente 15-20 minutos. "
    "Você pode responder por texto ou gravar áudio. Vamos começar?"
)

COMPLETION_MESSAGE = (
    "**Triagem concluída com sucesso.**\n\n"
    "Obrigada, {candidate_name}. Suas respostas foram registradas.\n\n"
    "**Próximos passos:**\n"
    "- Você receberá um e-mail de confirmação em instantes\n"
    "- A equipe da {company_name} avaliará seu perfil nos próximos dias\n"
    "- Fique atento ao seu e-mail para atualizações\n\n"
    "Agradecemos sua participação e desejamos sucesso."
)

COMPLETION_NEXT_STEPS = [
    "Você receberá um e-mail de confirmação em instantes",
    "A equipe da {company_name} avaliará seu perfil nos próximos dias",
    "Fique atento ao seu e-mail para atualizações",
]

BLOCK_TRANSITION_MESSAGES = [
    "Certo. Vamos para a próxima etapa: **{block_name}**.",
    "Entendido. Agora vamos falar sobre **{block_name}**.",
    "Obrigada. Seguindo para **{block_name}**.",
    "Anotado. Próxima etapa: **{block_name}**.",
]

PRE_COMPLETION_MESSAGE = (
    "Chegamos ao final da triagem.\n\n"
    "Foram **{total_questions} perguntas** respondidas em **{duration_minutes} minutos**.\n\n"
    "Deseja revisar alguma resposta antes de finalizar?"
)

TOTAL_QUESTIONS = sum(len(b["questions"]) for b in WSI_BLOCKS)


def _build_progress(current_block: int, questions_answered: int) -> Dict[str, Any]:
    block_name = "Concluído"
    if current_block < len(WSI_BLOCKS):
        block_name = WSI_BLOCKS[current_block]["name"]
    remaining = max(0, TOTAL_QUESTIONS - questions_answered)
    estimated_minutes = int(remaining * 1.5) if remaining > 0 else 0
    return {
        "current_block": current_block,
        "total_blocks": len(WSI_BLOCKS),
        "block_name": block_name,
        "questions_answered": questions_answered,
        "total_questions": TOTAL_QUESTIONS,
        "estimated_minutes_remaining": estimated_minutes,
    }


MAX_CONSECUTIVE_OFF_SCRIPT = 3

OFF_SCRIPT_SYSTEM_PROMPT = """Você é a LIA, assistente de recrutamento da empresa {company_name}.
Está conduzindo uma triagem para a vaga de {job_title}.

O candidato fez uma pergunta fora do roteiro em vez de responder à pergunta da triagem.
Responda a pergunta do candidato de forma breve e profissional, usando o contexto da vaga e empresa.
Depois, retome o roteiro naturalmente, reapresentando a pergunta original.

Pergunta original da triagem: {original_question}
Pergunta/comentário do candidato: {candidate_message}
Bloco atual: {block_name}

Responda em português brasileiro. Seja acolhedora e profissional.
Limite sua resposta a 3-4 frases, incluindo a retomada da pergunta original."""

FORCE_RESUME_MESSAGE = (
    "Entendo sua curiosidade. Essas informações adicionais podem ser discutidas com o recrutador "
    "nas próximas etapas do processo. Vamos prosseguir com a triagem para avaliar melhor o seu perfil."
    "\n\n{original_question}"
)

CONTEXTUAL_QUESTION_PROMPT = """Você é a LIA, assistente de recrutamento.
Está conduzindo uma triagem para a vaga de {job_title} na {company_name}.

O candidato acabou de responder à seguinte pergunta:
Pergunta: {previous_question}
Resposta do candidato: {candidate_response}

Agora você precisa fazer a próxima pergunta do bloco **{block_name}** ({block_type}).
A pergunta base é: {base_question}

Adapte a pergunta de forma natural considerando o que o candidato já compartilhou.
Faça uma transição suave entre a resposta anterior e a nova pergunta.
Mantenha o foco na competência sendo avaliada: {competency}.

Responda APENAS com a pergunta adaptada (sem explicações extras).
Limite: 2-3 frases no máximo. Português brasileiro."""

INTENT_CLASSIFICATION_PROMPT = """Classifique a intenção da seguinte mensagem de um candidato em uma triagem de emprego.

Mensagem: "{message}"

Contexto: O candidato deveria estar respondendo a uma pergunta de triagem no bloco "{block_name}".
Pergunta feita: "{current_question}"

Responda APENAS com uma das seguintes classificações:
- ANSWER: O candidato está respondendo à pergunta (mesmo que parcialmente)
- QUESTION: O candidato está fazendo uma pergunta sobre a vaga, empresa ou processo
- GREETING: O candidato está cumprimentando ou fazendo small talk
- UNCLEAR: A mensagem é confusa ou muito curta para classificar

Responda com apenas uma palavra: ANSWER, QUESTION, GREETING ou UNCLEAR"""


async def _call_llm(prompt: str) -> Optional[str]:
    try:
        from app.services.llm import llm_service
        result = await llm_service.generate(prompt, provider="gemini")
        return result.strip() if result else None
    except Exception as exc:
        logger.warning(f"[Triagem] LLM call failed: {exc}")
        return None


async def _classify_intent(message: str, block_name: str, current_question: str) -> str:
    prompt = INTENT_CLASSIFICATION_PROMPT.format(
        message=message[:500],
        block_name=block_name,
        current_question=current_question,
    )
    result = await _call_llm(prompt)
    if result and result.upper().strip() in ("ANSWER", "QUESTION", "GREETING", "UNCLEAR"):
        return result.upper().strip()
    return "ANSWER"


async def _generate_off_script_response(
    candidate_message: str,
    original_question: str,
    block_name: str,
    company_name: str,
    job_title: str,
) -> Optional[str]:
    prompt = OFF_SCRIPT_SYSTEM_PROMPT.format(
        company_name=company_name or "a empresa",
        job_title=job_title or "a vaga",
        original_question=original_question,
        candidate_message=candidate_message[:500],
        block_name=block_name,
    )
    return await _call_llm(prompt)


async def _generate_contextual_question(
    previous_question: str,
    candidate_response: str,
    base_question: str,
    block_name: str,
    block_type: str,
    competency: str,
    company_name: str,
    job_title: str,
) -> Optional[str]:
    prompt = CONTEXTUAL_QUESTION_PROMPT.format(
        job_title=job_title or "a vaga",
        company_name=company_name or "a empresa",
        previous_question=previous_question[:300],
        candidate_response=candidate_response[:500],
        base_question=base_question,
        block_name=block_name,
        block_type=block_type,
        competency=competency,
    )
    return await _call_llm(prompt)


def _score_response_deterministic(response_text: str, block_type: str, competency: str) -> Dict[str, Any]:
    try:
        from app.domains.cv_screening.services.wsi_deterministic_scorer import (
            calculate_wsi_deterministic,
        )
        result = calculate_wsi_deterministic(
            response_text=response_text,
            competency_name=competency,
        )
        return {
            "score": result.final_score,
            "block_type": block_type,
            "bloom_level": result.bloom_level,
            "dreyfus_level": result.dreyfus_level,
            "evidences": result.evidences,
            "red_flags": result.red_flags,
            "justification": result.justification,
        }
    except Exception as exc:
        logger.warning(f"[Triagem] Deterministic scoring failed: {exc}")
        return {
            "score": 3.0,
            "block_type": block_type,
            "bloom_level": 2,
            "dreyfus_level": 2,
            "evidences": [],
            "red_flags": [],
            "justification": "Scoring fallback applied",
        }


def _calculate_final_score(response_scores: List[Dict[str, Any]]) -> Tuple[float, str]:
    if not response_scores:
        return 3.0, "aguardando"

    technical_scores = []
    behavioral_scores = []

    for rs in response_scores:
        score = rs.get("score", 3.0)
        block_type = rs.get("block_type", "behavioral")
        # F9-1 — trait_weight do ranking F3; padrão 1.0 = pesos uniformes
        trait_weight = float(rs.get("trait_weight", 1.0))
        if block_type == "technical":
            technical_scores.append(("", score, 1.0))
        else:
            behavioral_scores.append(("", score, trait_weight))

    try:
        from app.domains.cv_screening.services.wsi_deterministic_scorer import (
            calculate_final_wsi_score,
        )
        result = calculate_final_wsi_score(
            technical_scores=technical_scores or [("", 3.0, 1.0)],
            behavioral_scores=behavioral_scores or [("", 3.0, 1.0)],
        )
        final = result["final_score"]
        scaled = round(final * 2.0, 1)

        if scaled >= 7.5:
            recommendation = "aprovado"
        elif scaled >= 5.5:
            recommendation = "aguardando"
        else:
            recommendation = "reprovado"

        return scaled, recommendation
    except Exception as exc:
        logger.warning(f"[Triagem] Final score calculation failed: {exc}")
        if response_scores:
            avg = sum(rs.get("score", 3.0) for rs in response_scores) / len(response_scores)
            scaled = round(avg * 2.0, 1)
        else:
            scaled = 6.0

        if scaled >= 7.5:
            recommendation = "aprovado"
        elif scaled >= 5.5:
            recommendation = "aguardando"
        else:
            recommendation = "reprovado"

        return scaled, recommendation


class TriagemSessionService:
    async def validate_token(self, db: AsyncSession, token: str) -> Dict[str, Any]:
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

    async def get_session_config(self, db: AsyncSession, token: str) -> Optional[Dict[str, Any]]:
        validation = await self.validate_token(db, token)
        if not validation["valid"]:
            return validation

        session_data = validation["session"]
        session_result = await db.execute(
            select(TriagemSession).where(TriagemSession.token == token)
        )
        session_orm: Optional[TriagemSession] = session_result.scalar_one_or_none()
        msg_result = await db.execute(
            select(TriagemMessage).where(
                TriagemMessage.session_id == uuid.UUID(session_data["id"])
            ).order_by(TriagemMessage.created_at)
        )
        messages = msg_result.scalars().all()

        job_info: Dict[str, Any] = {}
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
                total_blocks=len(WSI_BLOCKS),
            ),
            **job_info,
        }

        messages_data = [m.to_dict() for m in messages]

        response: Dict[str, Any] = {
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
        self,
        db: AsyncSession,
        candidate_id: str,
        job_id: str,
        company_id: str,
        candidate_name: Optional[str] = None,
        candidate_email: Optional[str] = None,
        job_title: Optional[str] = None,
        company_name: Optional[str] = None,
        company_logo_url: Optional[str] = None,
        invite_channel: str = "email",
        created_by: Optional[str] = None,
        expires_days: int = 7,
        voice_mode: bool = False,
    ) -> TriagemSession:
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
            total_blocks=len(WSI_BLOCKS),
            invite_channel=invite_channel,
            voice_mode=voice_mode,
            expires_at=datetime.utcnow() + timedelta(days=expires_days),
            created_by=created_by,
        )
        db.add(session)
        await db.flush()
        await db.refresh(session)

        welcome = WELCOME_MESSAGE.format(
            candidate_name=candidate_name or "candidato(a)",
            job_title=job_title or "a vaga",
            company_name=company_name or "a empresa",
            total_blocks=len(WSI_BLOCKS),
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

    async def start_session(self, db: AsyncSession, token: str, voice_mode: Optional[bool] = None) -> Dict[str, Any]:
        result = await db.execute(
            select(TriagemSession).where(TriagemSession.token == token)
        )
        session = result.scalar_one_or_none()
        if not session:
            return {"error": "not_found"}

        if session.status == "invited":
            session.status = "started"
            session.started_at = datetime.utcnow()

        if voice_mode is not None:
            session.voice_mode = voice_mode
        await db.flush()

        use_voice = voice_mode if voice_mode is not None else session.voice_mode

        first_block = WSI_BLOCKS[0]
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
            wsi_question_id=f"block_0_q_0",
            audio_base64=audio_b64,
        )
        db.add(lia_msg)
        await db.flush()

        return {
            "session": session.to_dict(),
            "lia_response": lia_msg.to_dict(),
            "progress": _build_progress(session.current_block, 0),
        }

    async def process_message(
        self,
        db: AsyncSession,
        token: str,
        content: str,
        message_type: str = "text",
        voice_mode: Optional[bool] = None,
    ) -> Dict[str, Any]:
        result = await db.execute(
            select(TriagemSession).where(TriagemSession.token == token)
        )
        session = result.scalar_one_or_none()
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

        candidate_msg = TriagemMessage(
            session_id=session.id,
            sender="candidate",
            content=content,
            message_type=message_type,
            wsi_block=session.current_block,
        )
        db.add(candidate_msg)
        await db.flush()

        lia_response = await self._generate_lia_response(db, session, content)

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

        all_cand_result = await db.execute(
            select(TriagemMessage).where(
                and_(
                    TriagemMessage.session_id == session.id,
                    TriagemMessage.sender == "candidate",
                )
            )
        )
        answered_count = len(all_cand_result.scalars().all())

        return {
            "candidate_message": candidate_msg.to_dict(),
            "lia_response": lia_msg.to_dict(),
            "progress": _build_progress(session.current_block, answered_count),
            "is_pre_completion": lia_response.get("is_pre_completion", False),
        }

    async def _generate_lia_response(
        self, db: AsyncSession, session: TriagemSession, candidate_content: str
    ) -> Dict[str, Any]:
        msg_result = await db.execute(
            select(TriagemMessage).where(
                and_(
                    TriagemMessage.session_id == session.id,
                    TriagemMessage.sender == "candidate",
                )
            ).order_by(TriagemMessage.created_at)
        )
        candidate_msgs = msg_result.scalars().all()
        candidate_count = len(candidate_msgs)

        current_block_idx = session.current_block
        if current_block_idx >= len(WSI_BLOCKS):
            return self._pre_completion_response(session, candidate_count)

        current_block = WSI_BLOCKS[current_block_idx]
        questions = current_block["questions"]
        block_name = current_block["name"]
        block_type = current_block.get("block_type", "behavioral")
        competency = current_block.get("competency", "general")

        last_lia_result = await db.execute(
            select(TriagemMessage).where(
                and_(
                    TriagemMessage.session_id == session.id,
                    TriagemMessage.sender == "lia",
                    TriagemMessage.message_type == "question",
                )
            ).order_by(TriagemMessage.created_at.desc())
        )
        last_lia_msg = last_lia_result.scalars().first()
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

        block_msg_result = await db.execute(
            select(TriagemMessage).where(
                and_(
                    TriagemMessage.session_id == session.id,
                    TriagemMessage.sender == "candidate",
                    TriagemMessage.wsi_block == current_block_idx,
                )
            )
        )
        block_candidate_msgs = block_msg_result.scalars().all()
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

        if next_block_idx >= len(WSI_BLOCKS):
            return self._pre_completion_response(session, candidate_count)

        next_block = WSI_BLOCKS[next_block_idx]
        transition = random.choice(BLOCK_TRANSITION_MESSAGES).format(block_name=next_block["name"])
        first_question = next_block["questions"][0]

        return {
            "content": f"{transition}\n\n{first_question}",
            "type": "question",
            "question_id": f"block_{next_block_idx}_q_0",
            "score": score_result["score"],
        }

    def _pre_completion_response(self, session: TriagemSession, total_questions: int) -> Dict[str, Any]:
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

    async def get_history(self, db: AsyncSession, token: str) -> Dict[str, Any]:
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

    async def complete_session(self, db: AsyncSession, token: str) -> Dict[str, Any]:
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

        response_scores = []
        for msg in candidate_msgs:
            block_idx = msg.wsi_block if msg.wsi_block is not None else 0
            if block_idx < len(WSI_BLOCKS):
                block = WSI_BLOCKS[block_idx]
                score_result = _score_response_deterministic(
                    msg.content,
                    block.get("block_type", "behavioral"),
                    block.get("competency", "general"),
                )
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

        post_actions = await self._trigger_post_completion(db, session)

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

    async def _trigger_post_completion(self, db: AsyncSession, session: TriagemSession) -> Dict[str, Any]:
        actions = {
            "email_confirmation": "queued",
            "recruiter_notification": "queued",
            "pipeline_update": "queued",
            "audit_log": "created",
        }

        logger.info(
            f"[Triagem] Post-completion triggered for session {session.token}: "
            f"candidate={session.candidate_name}, job={session.job_title}, "
            f"score={session.wsi_final_score}, recommendation={session.recommendation}"
        )

        try:
            from app.domains.communication.services.communication_dispatcher import CommunicationDispatcher
            comm_dispatcher = CommunicationDispatcher()

            confirmation_msg = (
                f"Sua triagem para a vaga de {session.job_title or 'a posição'} foi concluída com sucesso! "
                f"Nossa equipe avaliará seu perfil e você receberá uma resposta em até 5 dias úteis. "
                f"Agradecemos sua participação!"
            )
            dispatch_result = await comm_dispatcher.dispatch_message(
                company_id=session.company_id or "",
                recipient_email=session.candidate_email,
                recipient_phone=None,
                subject=f"Triagem Concluída - {session.job_title or 'Processo Seletivo'}",
                message=confirmation_msg,
                candidate_name=session.candidate_name,
                db=db,
            )
            actions["email_confirmation"] = "sent" if dispatch_result.get("success") else "failed"
            actions["confirmation_channels"] = dispatch_result.get("channels_sent", [])
            logger.info(
                f"[Triagem] Confirmation dispatched to {session.candidate_email} "
                f"(channels={dispatch_result.get('channels_sent', [])})"
            )
        except Exception as e:
            logger.warning(f"[Triagem] Failed to send confirmation: {e}")
            actions["email_confirmation"] = "failed"

        try:
            from app.domains.communication.services.teams_bot import teams_bot
            await teams_bot.notify_triagem_completed(
                candidate_name=session.candidate_name or "Candidato",
                job_title=session.job_title or "Vaga",
                score=session.wsi_final_score,
                classification=session.recommendation or "pendente",
            )
            actions["recruiter_notification"] = "sent"
            logger.info(
                f"[Triagem] Recruiter Teams notification sent: "
                f"'Candidato {session.candidate_name} concluiu triagem (score: {session.wsi_final_score})'"
            )
        except Exception as e:
            logger.warning(f"[Triagem] Failed to send Teams recruiter notification: {e}")
            actions["recruiter_notification"] = "failed"

        try:
            updated = await self._update_pipeline_stage(db, session)
            if not updated:
                actions["pipeline_update"] = "skipped_no_pipeline_row"
            elif session.wsi_final_score and session.wsi_final_score >= 7.5:
                actions["pipeline_update"] = "auto_moved_to_interview"
            elif session.wsi_final_score and session.wsi_final_score < 5.5:
                actions["pipeline_update"] = "marked_rejected"
            else:
                actions["pipeline_update"] = "marked_screened_pending"
        except Exception as e:
            logger.warning(f"[Triagem] Failed to update pipeline: {e}")
            actions["pipeline_update"] = "failed"

        return actions


    async def _update_pipeline_stage(
        self, db: AsyncSession, session: TriagemSession
    ) -> bool:
        from sqlalchemy import text as sql_text

        if not session.candidate_id or not session.job_id:
            logger.warning("[Triagem] Cannot update pipeline: missing candidate_id or job_id")
            return False

        score = session.wsi_final_score or 0.0

        if score >= 7.5:
            target_stage = "interview"
            target_status = "approved"
        elif score < 5.5:
            target_stage = "screened"
            target_status = "rejected"
        else:
            target_stage = "screened"
            target_status = "pending"

        result = await db.execute(
            sql_text(
                "UPDATE vacancy_candidates "
                "SET stage = :target_stage, status = :target_status, "
                "    lia_score = :score, stage_entered_at = NOW(), updated_at = NOW() "
                "WHERE candidate_id = CAST(:candidate_id AS UUID) "
                "  AND vacancy_id = CAST(:job_id AS UUID)"
            ),
            {
                "target_stage": target_stage,
                "target_status": target_status,
                "score": score,
                "candidate_id": session.candidate_id,
                "job_id": session.job_id,
            },
        )
        rows = result.rowcount
        await db.flush()
        if rows:
            logger.info(
                f"[Triagem] Pipeline updated: candidate={session.candidate_id} "
                f"→ stage={target_stage} status={target_status} score={score}"
            )
            return True
        else:
            logger.warning(
                f"[Triagem] No vacancy_candidates row found for "
                f"candidate={session.candidate_id} job={session.job_id} — "
                f"pipeline not updated (candidate may not be in pipeline yet)"
            )
            return False


    async def generate_tts_for_message(
        self, db: AsyncSession, token: str, message_id: str
    ) -> Dict[str, Any]:
        try:
            msg_uuid = uuid.UUID(message_id)
        except (ValueError, AttributeError):
            return {"error": "not_found"}

        result = await db.execute(
            select(TriagemSession).where(TriagemSession.token == token)
        )
        session = result.scalar_one_or_none()
        if not session:
            return {"error": "not_found"}

        msg_result = await db.execute(
            select(TriagemMessage).where(
                and_(
                    TriagemMessage.id == msg_uuid,
                    TriagemMessage.session_id == session.id,
                )
            )
        )
        message = msg_result.scalar_one_or_none()
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


triagem_service = TriagemSessionService()
