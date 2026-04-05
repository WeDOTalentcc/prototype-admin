import uuid
import json
import logging
import random
import base64
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, text

from app.models.triagem import TriagemSession, TriagemMessage
from lia_models.job_vacancy import JobVacancy

logger = logging.getLogger(__name__)


_event_dispatcher_cache = None


def _get_event_dispatcher():
    global _event_dispatcher_cache
    if _event_dispatcher_cache is None:
        from app.services.event_dispatcher import event_dispatcher
        _event_dispatcher_cache = event_dispatcher
    return _event_dispatcher_cache


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

WSI_BLOCKS_FALLBACK = [
    {"index": 0, "name": "Abordagem Inicial", "block_type": "technical", "competency": "technical_skills", "questions": [
        "Para começar, gostaria de confirmar algumas informações. Você tem disponibilidade para início imediato ou em qual prazo?",
        "Qual sua pretensão salarial para esta posição?",
    ]},
    {"index": 1, "name": "Apresentação da Oportunidade", "block_type": "behavioral", "competency": "motivation", "questions": [
        "O que te motivou a se candidatar para esta vaga?",
        "O que você sabe sobre a nossa empresa?",
    ]},
    {"index": 2, "name": "Perguntas Padrão da Empresa", "block_type": "behavioral", "competency": "cultural_fit", "questions": [
        "Descreva seu estilo de trabalho em equipe.",
    ]},
    {"index": 3, "name": "Competências Técnicas", "block_type": "technical", "competency": "technical_skills", "questions": [
        "Conte-me sobre sua experiência mais relevante para esta vaga. Quais tecnologias ou ferramentas você domina?",
        "Descreva um projeto técnico desafiador que você liderou ou participou. Qual foi seu papel e o resultado?",
    ]},
    {"index": 4, "name": "Competências Comportamentais e Fit", "block_type": "behavioral", "competency": "interpersonal_skills", "questions": [
        "Me conte sobre uma situação em que você precisou lidar com um conflito no ambiente de trabalho. Como você agiu?",
        "Descreva um momento em que você recebeu um feedback difícil. Como reagiu e o que mudou?",
        "Imagine que você recebe uma demanda urgente de dois gestores diferentes ao mesmo tempo. Como você priorizaria?",
    ]},
    {"index": 5, "name": "Resultado e Encerramento", "block_type": "behavioral", "competency": "self_assessment", "questions": [
        "Onde você se vê profissionalmente nos próximos 2-3 anos?",
        "Há algo mais que você gostaria de compartilhar sobre seu perfil ou experiência?",
    ]},
]

WSI_BLOCKS = WSI_BLOCKS_FALLBACK


def _build_wsi_blocks_from_question_set(questions_snapshot: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Build WSI blocks structure from a question set snapshot.
    Maps questions to canonical WSI blocks (0-5) based on block_id or category.
    Falls back to distributing by category if block_id is missing.
    """
    from app.domains.cv_screening.constants.wsi_constants import WSI_BLOCK_NAMES

    block_map: Dict[int, List[str]] = {i: [] for i in range(6)}
    block_meta: Dict[int, Dict[str, str]] = {
        0: {"block_type": "behavioral", "competency": "initial_approach"},
        1: {"block_type": "behavioral", "competency": "motivation"},
        2: {"block_type": "behavioral", "competency": "cultural_fit"},
        3: {"block_type": "technical", "competency": "technical_skills"},
        4: {"block_type": "behavioral", "competency": "interpersonal_skills"},
        5: {"block_type": "behavioral", "competency": "self_assessment"},
    }

    for q in questions_snapshot:
        text = q.get("text", q.get("question", q.get("question_text", "")))
        if not text:
            continue

        block_id = q.get("block_id")
        if block_id is not None:
            try:
                bid = int(block_id)
                if 0 <= bid <= 5:
                    block_map[bid].append(text)
                    continue
            except (ValueError, TypeError):
                pass

        category = q.get("category", "").lower()
        if category == "technical":
            block_map[3].append(text)
        elif category in ("behavioral", "situational", "contextual"):
            block_map[4].append(text)
        elif category == "company":
            block_map[2].append(text)
        else:
            block_map[4].append(text)

    blocks = []
    for idx in range(6):
        questions_for_block = block_map[idx]
        if not questions_for_block and idx not in (0, 5):
            continue
        if not questions_for_block:
            for fb in WSI_BLOCKS_FALLBACK:
                if fb["index"] == idx:
                    questions_for_block = fb["questions"]
                    break

        meta = block_meta[idx]
        blocks.append({
            "index": idx,
            "name": WSI_BLOCK_NAMES.get(idx, f"Bloco {idx}"),
            "block_type": meta["block_type"],
            "competency": meta["competency"],
            "questions": questions_for_block,
        })

    if not blocks:
        logger.warning("[Triagem] Question set mapping produced empty blocks, using fallback")
        return WSI_BLOCKS_FALLBACK

    return blocks

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


def _build_progress(
    current_block: int,
    questions_answered: int,
    blocks: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    active_blocks = blocks if blocks is not None else WSI_BLOCKS
    total_questions = sum(len(b["questions"]) for b in active_blocks)
    block_name = "Concluído"
    if current_block < len(active_blocks):
        block_name = active_blocks[current_block]["name"]
    remaining = max(0, total_questions - questions_answered)
    estimated_minutes = int(remaining * 1.5) if remaining > 0 else 0
    return {
        "current_block": current_block,
        "total_blocks": len(active_blocks),
        "block_name": block_name,
        "questions_answered": questions_answered,
        "total_questions": total_questions,
        "estimated_minutes_remaining": estimated_minutes,
    }


async def _load_or_generate_blocks(
    db: AsyncSession,
    job_id: str,
    job: Optional[Any] = None,
) -> Tuple[List[Dict[str, Any]], Optional[str], Optional[str]]:
    """
    Load WSI blocks for a job from:
    1. Active question set version (preferred)
    2. wsi_service.generate_screening_questions() (fallback)
    3. WSI_BLOCKS_FALLBACK hardcoded (emergency fallback)

    Returns:
        (blocks, wsi_question_set_id, wsi_question_set_version)
    """
    try:
        from app.domains.cv_screening.services.screening_question_set_service import (
            screening_question_set_service,
        )
        active_qs = await screening_question_set_service.get_active_version(db, job_id)
        if active_qs and active_qs.questions_snapshot:
            blocks = _build_wsi_blocks_from_question_set(active_qs.questions_snapshot)
            if blocks:
                logger.info(
                    f"[Triagem] Loaded question set v{active_qs.version} "
                    f"with {sum(len(b['questions']) for b in blocks)} questions for job {job_id}"
                )
                return blocks, str(active_qs.id), str(active_qs.version)
            logger.warning(f"[Triagem] Question set for job {job_id} produced empty blocks, trying wsi_service")
    except Exception as exc:
        logger.warning(f"[Triagem] Could not load question set for job {job_id}: {exc}")

    try:
        from app.domains.cv_screening.services.wsi_service import wsi_service, Competency
        competencies = []
        if job and getattr(job, "screening_config", None):
            skills = job.screening_config.get("skills") or {}
            for skill_name, skill_data in list(skills.items())[:10]:
                comp_type = skill_data.get("type", "technical") if isinstance(skill_data, dict) else "technical"
                competencies.append(Competency(
                    name=skill_name,
                    type=comp_type if comp_type in ("technical", "behavioral", "cultural") else "technical",
                    weight=0.5,
                    seniority_level=getattr(job, "seniority_level", "pleno") or "pleno",
                ))
        if not competencies:
            competencies = [
                Competency(name="Experiência Relevante", type="technical", weight=0.5, seniority_level="pleno"),
                Competency(name="Comunicação", type="behavioral", weight=0.5, seniority_level="pleno"),
            ]
        seniority = getattr(job, "seniority_level", "pleno") or "pleno" if job else "pleno"
        job_description = (job.description or "")[:1000] if job and job.description else ""
        sc = getattr(job, "screening_config", None) or {} if job else {}
        mode = sc.get("format", "compact")
        generated_qs = await wsi_service.generate_screening_questions(
            competencies=competencies,
            mode=mode,
            job_description=job_description,
            seniority=seniority,
        )
        if generated_qs:
            snapshot = [
                {"text": q.question_text, "category": _map_question_type_to_category(q.question_type), "block_id": None, "weight": q.weight}
                for q in generated_qs
            ]
            blocks = _build_wsi_blocks_from_question_set(snapshot)
            if blocks:
                logger.info(f"[Triagem] Generated {len(generated_qs)} questions via wsi_service for job {job_id}")
                return blocks, None, None
    except Exception as exc:
        logger.warning(f"[Triagem] wsi_service question generation failed for job {job_id}: {exc}")

    logger.warning(f"[Triagem] Using hardcoded fallback blocks for job {job_id}")
    return WSI_BLOCKS_FALLBACK, None, None


def _map_question_type_to_category(question_type: str) -> str:
    mapping = {
        "autodeclaration": "technical",
        "situational": "behavioral",
        "contextual": "behavioral",
        "open": "technical",
    }
    return mapping.get(question_type, "behavioral")


def _get_session_blocks(session: Any) -> List[Dict[str, Any]]:
    """
    Retrieve the WSI blocks for a session from its metadata_json cache.
    Falls back to global WSI_BLOCKS if not cached.
    """
    meta = session.metadata_json or {}
    cached_blocks = meta.get("wsi_blocks_cache")
    if cached_blocks and isinstance(cached_blocks, list) and len(cached_blocks) > 0:
        return cached_blocks
    return WSI_BLOCKS_FALLBACK


def _get_screening_config(session: Any) -> Dict[str, Any]:
    """Get the screening_config stored in session metadata, or empty dict."""
    meta = session.metadata_json or {}
    return meta.get("screening_config", {}) or {}


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
        job = None
        screening_config: Dict[str, Any] = {}
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
        eliminatory_keywords: List[str] = []
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

        session_meta: Dict[str, Any] = {
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
        active_blocks = _get_session_blocks(session)

        return {
            "candidate_message": candidate_msg.to_dict(),
            "lia_response": lia_msg.to_dict(),
            "progress": _build_progress(session.current_block, answered_count, active_blocks),
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

        active_blocks = _get_session_blocks(session)
        current_block_idx = session.current_block
        if current_block_idx >= len(active_blocks):
            return self._pre_completion_response(session, candidate_count)

        current_block = active_blocks[current_block_idx]
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

        if next_block_idx >= len(active_blocks):
            return self._pre_completion_response(session, candidate_count)

        next_block = active_blocks[next_block_idx]
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
        lia_by_block: Dict[int, List[TriagemMessage]] = {}
        for lm in lia_question_msgs:
            bidx = lm.wsi_block if lm.wsi_block is not None else 0
            lia_by_block.setdefault(bidx, []).append(lm)

        active_blocks = _get_session_blocks(session)
        session_meta_for_scoring = session.metadata_json or {}
        eliminatory_keywords: List[str] = [
            str(k).lower() for k in (session_meta_for_scoring.get("eliminatory_keywords") or [])
        ]

        candidate_by_block: Dict[int, List[TriagemMessage]] = {}
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

        post_actions = await self._trigger_post_completion(db, session, response_scores)

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

    async def _trigger_post_completion(self, db: AsyncSession, session: TriagemSession, response_scores: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        actions = {
            "email_confirmation": "queued",
            "recruiter_notification": "queued",
            "pipeline_update": "queued",
            "wsi_persistence": "queued",
            "audit_log": "created",
        }

        logger.info(
            f"[Triagem] Post-completion triggered for session {session.token}: "
            f"candidate={session.candidate_name}, job={session.job_title}, "
            f"score={session.wsi_final_score}, recommendation={session.recommendation}"
        )

        try:
            from app.domains.communication.services.communication_dispatcher import CommunicationDispatcher
            from app.domains.cv_screening.services.wsi_feedback_generator import get_feedback_generator
            from app.models.job_vacancy import JobVacancy
            from app.models.candidate import Candidate
            import json as _json
            import os as _os

            comm_dispatcher = CommunicationDispatcher()
            response_scores = response_scores or []

            # 1 — Resolve seniority from JobVacancy
            seniority_level = "junior"
            candidate_phone = None
            try:
                job_result = await db.execute(
                    select(JobVacancy).where(JobVacancy.id == session.job_id)
                )
                job = job_result.scalar_one_or_none()
                if job and getattr(job, "seniority_level", None):
                    seniority_level = job.seniority_level
            except Exception as _e:
                logger.warning(f"[Triagem] Could not resolve seniority: {_e}")

            # 2 — Resolve candidate phone for WhatsApp
            try:
                cand_result = await db.execute(
                    select(Candidate).where(Candidate.id == session.candidate_id)
                )
                cand = cand_result.scalar_one_or_none()
                if cand:
                    candidate_phone = getattr(cand, "mobile_phone", None) or getattr(cand, "phone", None)
            except Exception as _e:
                logger.warning(f"[Triagem] Could not resolve candidate phone: {_e}")

            # 3 — Generate structured feedback
            feedback_gen = get_feedback_generator()
            feedback_report = feedback_gen.generate(
                response_scores=response_scores,
                job_title=session.job_title or "a vaga",
                seniority_level=seniority_level,
                candidate_name=session.candidate_name or "Candidato(a)",
            )

            # 4 — Persist feedback_draft
            session.feedback_draft = _json.dumps(feedback_report, ensure_ascii=False)

            # 5 — Chat web: inject as final LIA message in the session
            try:
                feedback_chat_msg = TriagemMessage(
                    session_id=session.id,
                    sender="lia",
                    content=feedback_report["chat_text"],
                    message_type="feedback",
                    wsi_block=session.current_block,
                )
                db.add(feedback_chat_msg)
                await db.flush()
                actions["chat_feedback"] = "sent"
                logger.info(f"[Triagem] Chat feedback message added for session {session.token}")
            except Exception as _e:
                logger.warning(f"[Triagem] Could not add chat feedback message: {_e}")
                actions["chat_feedback"] = "failed"

            # 6 — Email: rich HTML feedback
            email_result = {"success": False}
            if session.candidate_email:
                try:
                    template_path = _os.path.join(
                        _os.path.dirname(__file__),
                        "..", "templates", "triagem_feedback_email.html"
                    )
                    with open(template_path) as _f:
                        html_template = _f.read()

                    # Simple template rendering (no Jinja2 dependency)
                    dim_html = ""
                    for d in feedback_report["dimensions"]:
                        dim_html += f"""
                        <div class="dimension-card">
                          <div class="dimension-header">
                            <span class="dim-icon">{d['icon']}</span>
                            <span class="dim-title">{d['title']}</span>
                          </div>
                          <div class="dimension-body">
                            <div class="feedback-row">
                              <span class="feedback-label label-strength">✅</span>
                              <div class="feedback-text">
                                <strong>Ponto Forte</strong>{d['strength']}
                              </div>
                            </div>
                            <div class="feedback-row">
                              <span class="feedback-label label-development">🌱</span>
                              <div class="feedback-text">
                                <strong>Área de Desenvolvimento</strong>{d['development']}
                              </div>
                            </div>
                            <div class="feedback-row">
                              <span class="feedback-label label-suggestion">💡</span>
                              <div class="feedback-text">
                                <strong>Sugestão Prática</strong>{d['suggestion']}
                              </div>
                            </div>
                          </div>
                        </div>"""

                    platform_email = _os.getenv("MAILGUN_FROM_EMAIL", "noreply@wedotalent.com")
                    html_body = (html_template
                        .replace("{{ candidate_name }}", feedback_report["first_name"])
                        .replace("{{ job_title }}", feedback_report["job_title"])
                        .replace("{{ intro_body }}", feedback_report["intro"].replace("\n", "<br>"))
                        .replace("{{ closing }}", feedback_report["closing"].replace("\n", "<br>"))
                        .replace("{{ company_name }}", session.company_name or "WeDOTalent")
                        .replace("{{ reply_email }}", platform_email)
                        .replace("{{ privacy_url }}", "https://wedotalent.com/privacidade")
                        .replace("{{ lgpd_url }}", "https://wedotalent.com/lgpd")
                        .replace("{% for dim in dimensions %}", "")
                        .replace("{% endfor %}", "")
                        .replace("""        <div class="dimension-card">
                          <div class="dimension-header">
                            <span class="dim-icon">{{ dim.icon }}</span>
                            <span class="dim-title">{{ dim.title }}</span>
                          </div>
                          <div class="dimension-body">
                            <div class="feedback-row">
                              <span class="feedback-label label-strength">✅</span>
                              <div class="feedback-text">
                                <strong>Ponto Forte</strong>
                                {{ dim.strength }}
                              </div>
                            </div>
                            <div class="feedback-row">
                              <span class="feedback-label label-development">🌱</span>
                              <div class="feedback-text">
                                <strong>Área de Desenvolvimento</strong>
                                {{ dim.development }}
                              </div>
                            </div>
                            <div class="feedback-row">
                              <span class="feedback-label label-suggestion">💡</span>
                              <div class="feedback-text">
                                <strong>Sugestão Prática</strong>
                                {{ dim.suggestion }}
                              </div>
                            </div>
                          </div>
                        </div>""", dim_html)
                    )

                    email_result = comm_dispatcher.send_email(
                        to_email=session.candidate_email,
                        subject=f"Feedback da sua triagem — {session.job_title or 'Processo Seletivo'}",
                        body_html=html_body,
                        body_text=feedback_report["plain_text"],
                    )
                    actions["email_confirmation"] = "sent" if email_result.get("success") else "failed"
                    logger.info(
                        f"[Triagem] Feedback email sent to {session.candidate_email} "
                        f"(mock={email_result.get('mock', False)})"
                    )
                except Exception as _e:
                    logger.warning(f"[Triagem] Could not send HTML feedback email: {_e}")
                    # Fallback: plain text email
                    email_result = comm_dispatcher.send_email(
                        to_email=session.candidate_email,
                        subject=f"Feedback da sua triagem — {session.job_title or 'Processo Seletivo'}",
                        body_html=f"<pre>{feedback_report['plain_text']}</pre>",
                        body_text=feedback_report["plain_text"],
                    )
                    actions["email_confirmation"] = "sent" if email_result.get("success") else "failed"

            # 7 — WhatsApp: condensed feedback
            whatsapp_result = {"success": False}
            should_send_whatsapp = (
                candidate_phone and (
                    session.invite_channel == "whatsapp"
                    or session.invite_channel is None  # default: try
                )
            )
            if should_send_whatsapp:
                try:
                    whatsapp_result = comm_dispatcher.send_whatsapp(
                        to_phone=candidate_phone,
                        message=feedback_report["whatsapp_text"],
                    )
                    logger.info(
                        f"[Triagem] WhatsApp feedback sent to {candidate_phone} "
                        f"(success={whatsapp_result.get('success')})"
                    )
                except Exception as _e:
                    logger.warning(f"[Triagem] Could not send WhatsApp feedback: {_e}")

            # 8 — Compile channel results
            channels_sent = []
            if actions.get("chat_feedback") == "sent":
                channels_sent.append("chat_web")
            if email_result.get("success"):
                channels_sent.append("email")
            if whatsapp_result.get("success"):
                channels_sent.append("whatsapp")

            actions["confirmation_channels"] = channels_sent
            logger.info(
                f"[Triagem] Feedback delivered via channels: {channels_sent} "
                f"for session {session.token}"
            )

        except Exception as e:
            logger.warning(f"[Triagem] Failed to generate/send feedback: {e}")
            actions["email_confirmation"] = "failed"

        try:
            from app.domains.communication.services.teams_bot import teams_bot
            await teams_bot.notify_triagem_completed(
                candidate_name=session.candidate_name or "Candidato",
                job_title=session.job_title or "Vaga",
                score=session.wsi_final_score,
                classification=session.recommendation or "pendente",
            )
            logger.info(
                f"[Triagem] Recruiter Teams notification sent: "
                f"'Candidato {session.candidate_name} concluiu triagem (score: {session.wsi_final_score})'"
            )
        except Exception as e:
            logger.warning(f"[Triagem] Failed to send Teams recruiter notification: {e}")

        try:
            from app.services.notification_service import (
                notification_service,
                NotificationType,
            )
            score_val = session.wsi_final_score or 0.0
            recommendation = session.recommendation or "pendente"
            notif_type = NotificationType.SUCCESS if score_val >= 7.5 else (
                NotificationType.WARNING if score_val < 5.5 else NotificationType.INFO
            )
            await notification_service.create_notification(
                user_id=session.created_by or "default_user",
                title=f"Triagem concluída: {session.candidate_name or 'Candidato'}",
                message=(
                    f"{session.candidate_name or 'Candidato'} concluiu a triagem para "
                    f"'{session.job_title or 'Vaga'}'. "
                    f"Score WSI: {score_val:.1f} — {recommendation.upper()}."
                ),
                notification_type=notif_type,
                category="screening_completed",
                source_agent="triagem_session_service",
                source_trigger="screening_completed",
                related_job_id=session.job_id,
                related_candidate_id=session.candidate_id,
                action_url=f"/candidates/{session.candidate_id}",
                action_label="Ver Candidato",
                metadata={
                    "wsi_score": score_val,
                    "recommendation": recommendation,
                    "screening_type": "web_chat",
                    "session_token": session.token,
                },
                db=db,
            )
            actions["recruiter_notification"] = "sent"
            logger.info(f"[Triagem] Recruiter notification sent via notification_service for session {session.token}")
        except Exception as e:
            logger.warning(f"[Triagem] Failed to send recruiter notification via notification_service: {e}")
            actions["recruiter_notification"] = "failed"

        wsi_session_id: Optional[str] = None
        try:
            wsi_session_id = await self._persist_wsi_results(db, session, response_scores)
            if wsi_session_id:
                actions["wsi_persistence"] = "done"
                meta = session.metadata_json or {}
                meta["wsi_session_id"] = wsi_session_id
                meta["wsi_channel"] = "web_chat"
                session.metadata_json = meta
                await db.flush()
            else:
                actions["wsi_persistence"] = "skipped"
        except Exception as e:
            logger.warning(f"[Triagem] Failed to persist WSI results: {e}")
            actions["wsi_persistence"] = "failed"

        if not wsi_session_id:
            logger.warning(
                f"[Triagem] Skipping screening-completed event dispatch — "
                f"wsi_session_id not available (persistence failed or was skipped)"
            )
            actions["pipeline_update"] = "skipped_no_wsi_session"
        else:
            try:
                score_val = session.wsi_final_score or 0.0
                recommendation = session.recommendation or "aguardando"
                passed = score_val >= 7.5
                classification_map = {
                    "aprovado": "recommended",
                    "reprovado": "not_recommended",
                    "aguardando": "pending_review",
                    "pendente": "pending_review",
                }
                classification = classification_map.get(recommendation, "pending_review")

                wsi_scores: Dict[str, Any] = {
                    "overall_wsi": score_val,
                }
                for rs in (response_scores or []):
                    bt = rs.get("block_type", "behavioral")
                    if bt == "technical":
                        wsi_scores.setdefault("technical_wsi", []).append(rs.get("score", 0.0))
                    else:
                        wsi_scores.setdefault("behavioral_wsi", []).append(rs.get("score", 0.0))
                if "technical_wsi" in wsi_scores and isinstance(wsi_scores["technical_wsi"], list):
                    lst = wsi_scores["technical_wsi"]
                    wsi_scores["technical_wsi"] = round(sum(lst) / len(lst) / 2.0, 2) if lst else 0.0
                if "behavioral_wsi" in wsi_scores and isinstance(wsi_scores["behavioral_wsi"], list):
                    lst = wsi_scores["behavioral_wsi"]
                    wsi_scores["behavioral_wsi"] = round(sum(lst) / len(lst) / 2.0, 2) if lst else 0.0

                dispatcher = _get_event_dispatcher()
                await dispatcher.on_screening_completed(
                    candidate_id=session.candidate_id,
                    vacancy_id=session.job_id,
                    company_id=session.company_id,
                    wsi_scores=wsi_scores,
                    screening_type="web_chat",
                    passed=passed,
                    classification=classification,
                    session_id=session.token,
                    wsi_session_id=wsi_session_id,
                )
                actions["pipeline_update"] = "dispatched_via_event_dispatcher"
                logger.info(
                    f"[Triagem] screening-completed event dispatched for "
                    f"candidate={session.candidate_id}, score={score_val}, passed={passed}"
                )
            except Exception as e:
                logger.warning(f"[Triagem] Failed to dispatch screening-completed event: {e}")
                actions["pipeline_update"] = "event_dispatch_failed"

        return actions

    async def _persist_wsi_results(
        self,
        db: AsyncSession,
        session: TriagemSession,
        response_scores: List[Dict[str, Any]],
    ) -> Optional[str]:
        """
        Persist screening results to WSI tables (wsi_sessions, wsi_questions,
        wsi_response_analyses, wsi_results) following the canonical WSI schema.

        Schema constraints respected:
        - wsi_sessions.screening_type IN ('voice', 'chat', 'hybrid')
        - wsi_sessions.mode IN ('compact', 'compact_plus')
        - wsi_response_analyses.question_id FK → wsi_questions(id)
        - scores in [1..5] range
        - wsi_results.classification IN ('excelente', 'alto', 'medio', 'regular', 'baixo')

        Returns the wsi_session_id string if the wsi_sessions row was successfully
        created; returns None on any critical failure so callers can skip the
        event-dispatcher dispatch.
        """
        if not session.candidate_id or not session.job_id:
            logger.warning("[Triagem] Cannot persist WSI results: missing candidate_id or job_id")
            return None

        wsi_session_id = f"system:{uuid.uuid4()}"
        meta = session.metadata_json or {}
        qs_version = meta.get("wsi_question_set_version")
        qs_id = meta.get("wsi_question_set_id")
        score_val = session.wsi_final_score or 0.0

        screening_config = _get_screening_config(session)
        raw_mode = screening_config.get("format") or "compact"
        _mode_map = {"compact": "compact", "compact_plus": "compact_plus", "full": "compact_plus"}
        mode = _mode_map.get(raw_mode, "compact")

        try:
            await db.execute(text(
                "INSERT INTO wsi_sessions "
                "    (id, candidate_id, job_vacancy_id, screening_type, mode, status, "
                "     question_set_version, question_set_id, completed_at) "
                "VALUES "
                "    (:id, :candidate_id, :job_vacancy_id, :screening_type, :mode, :status, "
                "     :question_set_version, :question_set_id, :completed_at)"
            ), {
                "id": wsi_session_id,
                "candidate_id": session.candidate_id,
                "job_vacancy_id": session.job_id,
                "screening_type": "chat",
                "mode": mode,
                "status": "completed",
                "question_set_version": int(qs_version) if qs_version else None,
                "question_set_id": qs_id,
                "completed_at": session.completed_at or datetime.utcnow(),
            })
        except Exception as exc:
            logger.error(f"[Triagem] wsi_sessions insert failed — aborting WSI persistence: {exc}")
            return None

        technical_scores: List[float] = []
        behavioral_scores: List[float] = []

        for seq, rs in enumerate(response_scores or [], start=1):
            block_type = rs.get("block_type", "behavioral")
            competency = rs.get("competency", "general")
            raw_score = float(rs.get("score", 6.0))
            score_1_5 = max(1.0, min(5.0, round(raw_score / 2.0, 2)))
            question_text = rs.get("question_text") or f"Questão {seq} — {competency}"
            response_text = rs.get("response_text") or ""

            question_id = str(uuid.uuid4())
            if block_type == "technical":
                framework = "CBI"
                q_type = "autodeclaration"
            else:
                framework = "CBI"
                q_type = "contextual"

            try:
                await db.execute(text(
                    "INSERT INTO wsi_questions "
                    "    (id, session_id, competency, framework, question_type, question_text, "
                    "     weight, sequence_order) "
                    "VALUES "
                    "    (:id, :session_id, :competency, :framework, :question_type, :question_text, "
                    "     :weight, :sequence_order)"
                ), {
                    "id": question_id,
                    "session_id": wsi_session_id,
                    "competency": competency,
                    "framework": framework,
                    "question_type": q_type,
                    "question_text": question_text[:2000],
                    "weight": 1.0,
                    "sequence_order": seq,
                })
            except Exception as exc:
                logger.warning(f"[Triagem] wsi_questions insert failed (seq={seq}): {exc}")
                if block_type == "technical":
                    technical_scores.append(score_1_5)
                else:
                    behavioral_scores.append(score_1_5)
                continue

            analysis_id = str(uuid.uuid4())
            try:
                await db.execute(text(
                    "INSERT INTO wsi_response_analyses "
                    "    (id, session_id, question_id, competency, response_text, "
                    "     autodeclaration_score, context_score, bloom_level, dreyfus_level, "
                    "     evidences, red_flags, consistency_penalty, final_score, justification) "
                    "VALUES "
                    "    (:id, :session_id, :question_id, :competency, :response_text, "
                    "     :autodeclaration_score, :context_score, :bloom_level, :dreyfus_level, "
                    "     :evidences::jsonb, :red_flags::jsonb, :consistency_penalty, :final_score, :justification)"
                ), {
                    "id": analysis_id,
                    "session_id": wsi_session_id,
                    "question_id": question_id,
                    "competency": competency,
                    "response_text": response_text,
                    "autodeclaration_score": score_1_5,
                    "context_score": score_1_5,
                    "bloom_level": max(1, min(5, rs.get("bloom_level", 2))),
                    "dreyfus_level": max(1, min(5, rs.get("dreyfus_level", 2))),
                    "evidences": json.dumps(rs.get("evidences", [])),
                    "red_flags": json.dumps(rs.get("red_flags", [])),
                    "consistency_penalty": 0.0,
                    "final_score": score_1_5,
                    "justification": rs.get("justification", "Score calculado a partir da resposta no chat web"),
                })
            except Exception as exc:
                logger.warning(f"[Triagem] wsi_response_analyses insert failed (seq={seq}): {exc}")

            if block_type == "technical":
                technical_scores.append(score_1_5)
            else:
                behavioral_scores.append(score_1_5)

        tech_wsi = max(1.0, min(5.0, round(sum(technical_scores) / len(technical_scores), 2))) if technical_scores else max(1.0, min(5.0, round(score_val / 2.0, 2)))
        beh_wsi = max(1.0, min(5.0, round(sum(behavioral_scores) / len(behavioral_scores), 2))) if behavioral_scores else max(1.0, min(5.0, round(score_val / 2.0, 2)))
        overall_wsi = max(1.0, min(5.0, round(score_val / 2.0, 2)))

        recommendation = session.recommendation or "aguardando"
        if overall_wsi >= 4.5:
            wsi_classification = "excelente"
        elif overall_wsi >= 3.75:
            wsi_classification = "alto"
        elif overall_wsi >= 2.75:
            wsi_classification = "medio"
        elif overall_wsi >= 2.0:
            wsi_classification = "regular"
        else:
            wsi_classification = "baixo"

        try:
            result_id = str(uuid.uuid4())
            await db.execute(text(
                "INSERT INTO wsi_results "
                "    (id, session_id, candidate_id, job_vacancy_id, "
                "     technical_wsi, behavioral_wsi, overall_wsi, classification, percentile) "
                "VALUES "
                "    (:id, :session_id, :candidate_id, :job_vacancy_id, "
                "     :technical_wsi, :behavioral_wsi, :overall_wsi, :classification, :percentile)"
            ), {
                "id": result_id,
                "session_id": wsi_session_id,
                "candidate_id": session.candidate_id,
                "job_vacancy_id": session.job_id,
                "technical_wsi": tech_wsi,
                "behavioral_wsi": beh_wsi,
                "overall_wsi": overall_wsi,
                "classification": wsi_classification,
                "percentile": None,
            })
        except Exception as exc:
            logger.error(f"[Triagem] wsi_results insert failed: {exc}")
            return None

        await db.flush()
        logger.info(
            f"[Triagem] WSI results persisted: wsi_session={wsi_session_id}, "
            f"tech={tech_wsi}, beh={beh_wsi}, overall={overall_wsi}, class={wsi_classification}"
        )
        return wsi_session_id


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


    async def request_phone_call(
        self, db: AsyncSession, token: str, candidate_phone: str
    ) -> Dict[str, Any]:
        result = await db.execute(
            select(TriagemSession).where(TriagemSession.token == token)
        )
        session = result.scalar_one_or_none()
        if not session:
            return {"error": "not_found"}

        if session.status == "completed":
            return {"error": "already_completed"}

        job_id = session.job_id
        company_id = session.company_id
        job = None
        if job_id:
            try:
                q = select(JobVacancy).where(JobVacancy.job_id == job_id)
                if company_id and hasattr(JobVacancy, "company_id"):
                    q = q.where(JobVacancy.company_id == company_id)
                r = await db.execute(q)
                job = r.scalar_one_or_none()
                if not job:
                    q2 = select(JobVacancy).where(JobVacancy.id == uuid.UUID(job_id))
                    if company_id and hasattr(JobVacancy, "company_id"):
                        q2 = q2.where(JobVacancy.company_id == company_id)
                    r2 = await db.execute(q2)
                    job = r2.scalar_one_or_none()
            except Exception as e:
                logger.warning(f"[Triagem] Could not fetch job for phone call: {e}")

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
                            "message": "Uma ligação já foi solicitada recentemente. Aguarde alguns minutos.",
                        }
                except (ValueError, TypeError):
                    pass

        try:
            from app.domains.cv_screening.services.wsi_voice_orchestrator import wsi_voice_orchestrator
            from app.domains.cv_screening.services.wsi_service import Competency

            job_title = session.job_title or "a vaga"
            job_description = (job.description or "")[:1000] if job and job.description else ""

            competencies: List[Competency] = []
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
                    Competency(name="Experiência Relevante", type="technical", weight=0.5, seniority_level="pleno"),
                    Competency(name="Comunicação", type="behavioral", weight=0.5, seniority_level="pleno"),
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
                "triagem_token": token,
            }
            session.metadata_json = meta
            session.status = "started" if session.status == "invited" else session.status
            session.started_at = session.started_at or datetime.utcnow()
            await db.commit()

            logger.info(
                f"[Triagem] Phone call requested: token={token}, call_id={call_id}, "
                f"wsi_session={wsi_session_id}, questions={voice_result.questions_generated}"
            )

            return {
                "status": "call_initiated",
                "call_id": call_id,
                "agent_id": agent_id,
                "wsi_session_id": wsi_session_id,
                "message": "Ligação sendo realizada. Você receberá uma chamada em instantes.",
            }

        except Exception as e:
            logger.error(f"[Triagem] Phone call request failed: {e}", exc_info=True)
            return {"error": "call_failed", "detail": str(e)}


triagem_service = TriagemSessionService()
