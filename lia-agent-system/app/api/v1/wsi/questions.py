"""
WSI package — question generation, suggestion, save, and version routes.

Routes:
  POST /generate-questions
  POST /suggest-question
  POST /questions/save
  GET  /question-sets/{job_id}/active
  GET  /question-sets/{job_id}/versions
  GET  /question-sets/{job_id}/version/{version}
  GET  /question-sets/{job_id}/consistency
"""
import json
import logging
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.cv_screening.services.screening_question_set_service import screening_question_set_service

from ._shared import (
    BLOOM_LEVELS,
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
    SaveQuestionsRequest,
    SuggestQuestionRequest,
    WSIQuestionOutput,
    _run_anthropic_sync,
    get_anthropic_client,
    parse_json_response,
)

logger = logging.getLogger(__name__)

router = APIRouter()

_FRAMEWORK_BLOOM_MAP = {
    "CBI": 4,
    "Bloom": 3,
    "Dreyfus": 2,
    "BigFive": 3,
}

_FRAMEWORK_CATEGORY_MAP = {
    "CBI": "technical",
    "Bloom": "technical",
    "Dreyfus": "technical",
    "BigFive": "behavioral",
}


@router.post("/generate-questions", response_model=GenerateQuestionsResponse)
async def generate_questions(
    request: GenerateQuestionsRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate WSI screening questions using the canonical F6 pipeline
    (CBI + Bloom + Dreyfus + BigFive via WSIService).
    """
    session_id = f"wsi_text_{uuid.uuid4().hex[:12]}"

    job_title = request.job_title or "Professional"
    all_skills = request.skills or request.technical_skills or ["Problem Solving", "Communication"]
    behavioral = request.behavioral_competencies or []
    seniority = request.seniority_level or request.seniority or "pleno"
    description = request.description or ""
    requirements = request.requirements or request.responsibilities or []
    job_desc_parts = [description] if description else []
    if requirements:
        job_desc_parts.append("Responsabilidades: " + ", ".join(requirements))
    job_description = "\n".join(job_desc_parts) if job_desc_parts else None

    from app.domains.cv_screening.services.wsi_service import WSIService
    wsi_svc = WSIService()
    requested_count = request.max_questions or request.num_questions
    mode = "full" if requested_count > 10 else "compact"
    wsi_questions = await wsi_svc.generate_from_simple_inputs(
        skills=all_skills,
        behavioral=behavioral,
        seniority=seniority,
        job_description=job_description,
        mode=mode,
        max_questions=requested_count,
    )

    questions = []
    for idx, wq in enumerate(wsi_questions):
        question_id = f"q_{session_id}_{idx+1}"
        bloom_level = _FRAMEWORK_BLOOM_MAP.get(wq.framework, 3)
        category = _FRAMEWORK_CATEGORY_MAP.get(wq.framework, "technical")
        questions.append(WSIQuestionOutput(
            id=question_id,
            text=wq.question_text,
            bloom_level=bloom_level,
            bloom_level_name=BLOOM_LEVELS.get(bloom_level, BLOOM_LEVELS[3])["name"],
            skill_targeted=wq.competency,
            question_type=wq.question_type,
            block_id=3 if category == "technical" else 4,
            category=category,
            is_eliminatory=False
        ))

    try:
        active_qs = await screening_question_set_service.get_active_version(db, request.job_vacancy_id or "")
        qs_version = active_qs.version if active_qs else None
        qs_id = str(active_qs.id) if active_qs else None

        await db.execute(text("""
            INSERT INTO wsi_sessions (id, candidate_id, job_vacancy_id, screening_type, mode, status, question_set_version, question_set_id)
            VALUES (:session_id, :candidate_id, :job_vacancy_id, :screening_type, :mode, :status, :question_set_version, :question_set_id)
            ON CONFLICT (id) DO NOTHING
        """), {
            "session_id": session_id,
            "candidate_id": "pending",
            "job_vacancy_id": request.job_vacancy_id or "",
            "screening_type": "text",
            "mode": "compact",
            "status": "in_progress",
            "question_set_version": qs_version,
            "question_set_id": qs_id,
        })

        for idx, q in enumerate(questions):
            await db.execute(text("""
                INSERT INTO wsi_questions (
                    id, session_id, competency, framework, question_type,
                    question_text, weight, expected_signals, scoring_criteria, sequence_order
                )
                VALUES (:id, :session_id, :competency, :framework, :question_type,
                        :question_text, :weight, :expected_signals::jsonb, :scoring_criteria::jsonb, :sequence_order)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": q.id,
                "session_id": session_id,
                "competency": q.skill_targeted,
                "framework": wsi_questions[idx].framework if idx < len(wsi_questions) else "CBI",
                "question_type": q.question_type,
                "question_text": q.text,
                "weight": wsi_questions[idx].weight if idx < len(wsi_questions) else 1.0 / max(len(questions), 1),
                "expected_signals": json.dumps(wsi_questions[idx].expected_signals if idx < len(wsi_questions) else []),
                "scoring_criteria": json.dumps(dict(wsi_questions[idx].scoring_criteria) if idx < len(wsi_questions) else {}),
                "sequence_order": idx + 1
            })
        await db.commit()
    except Exception as e:
        logger.warning(f"Failed to save to DB: {e}")

    return GenerateQuestionsResponse(
        session_id=session_id,
        questions=questions,
        job_title=job_title
    )


@router.post("/suggest-question")
async def suggest_question(request: SuggestQuestionRequest):
    """Generate a single screening question from a recruiter prompt using LLM."""
    client = await get_anthropic_client()

    block_context = {
        2: "Bloco 2 - Elegibilidade: perguntas eliminatórias sobre disponibilidade, requisitos mínimos",
        3: "Bloco 3 - Técnica: perguntas sobre conhecimento técnico, experiência prática",
        4: "Bloco 4 - Situacional/Comportamental: perguntas sobre soft skills, liderança, trabalho em equipe"
    }

    block_info = block_context.get(request.block_id, "Bloco genérico")

    prompt = f"""Você é um especialista em recrutamento usando a metodologia WSI.
O recrutador pediu para criar uma pergunta de triagem com base nesta instrução:

INSTRUÇÃO DO RECRUTADOR: "{request.prompt}"

CONTEXTO:
- Vaga: {request.job_title or 'Não especificada'}
- Senioridade: {request.seniority or 'Não especificada'}
- {block_info}
- Skills técnicas da vaga: {', '.join(request.technical_skills or []) or 'Não especificadas'}
- Competências comportamentais: {', '.join(request.behavioral_competencies or []) or 'Não especificadas'}

REGRAS:
1. Crie UMA pergunta profissional e bem formulada em português brasileiro
2. Se a instrução menciona "eliminatória", "disponibilidade" ou requisito obrigatório, marque como eliminatory
3. Se a instrução menciona skills técnicas, marque como technical
4. Senão, marque como classificatory/behavioral
5. A pergunta deve ser clara, direta e adequada para triagem de candidatos

Retorne APENAS JSON válido:
{{
  "question": "Texto completo da pergunta em português",
  "type": "eliminatory|classificatory",
  "category": "eligibility|technical|behavioral",
  "block_id": {request.block_id or 3},
  "skill_targeted": "competência que a pergunta avalia",
  "bloom_level": 3
}}"""

    if client:
        response = await _run_anthropic_sync(
            client,
            model="claude-sonnet-4-6",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
            timeout=30.0
        )
        try:
            if response is None:
                raise ValueError("Anthropic call timed out or failed")
            data = parse_json_response(response.content[0].text, {})
            if data.get("question"):
                return {
                    "success": True,
                    "question": data["question"],
                    "type": data.get("type", "classificatory"),
                    "category": data.get("category", "technical"),
                    "block_id": data.get("block_id", request.block_id or 3),
                    "skill_targeted": data.get("skill_targeted", ""),
                    "bloom_level": data.get("bloom_level", 3)
                }
        except Exception as e:
            logger.error(f"Suggest question failed: {e}")

    return {
        "success": False,
        "error": "Não foi possível gerar a sugestão. Tente novamente."
    }


@router.post("/questions/save")
async def save_questions(request: SaveQuestionsRequest, db: AsyncSession = Depends(get_db)):
    """Save screening questions for a job vacancy."""
    try:
        for q in request.questions:
            q_id = q.get("id", f"q_{uuid.uuid4().hex[:12]}")
            await db.execute(text("""
                INSERT INTO job_screening_questions (id, job_vacancy_id, question_text, category, question_type, weight, skill_targeted, block_id, source, is_active)
                VALUES (:id, :job_id, :text, :category, :type, :weight, :skill_targeted, :block_id, :source, true)
                ON CONFLICT (id) DO UPDATE SET
                    question_text = EXCLUDED.question_text,
                    category = EXCLUDED.category,
                    question_type = EXCLUDED.question_type,
                    weight = EXCLUDED.weight,
                    skill_targeted = EXCLUDED.skill_targeted,
                    block_id = EXCLUDED.block_id,
                    updated_at = NOW()
            """), {
                "id": q_id,
                "job_id": request.job_id,
                "text": q.get("text", q.get("question", "")),
                "category": q.get("category", "general"),
                "type": q.get("type", "open"),
                "weight": q.get("weight", 0.75),
                "skill_targeted": q.get("skill_targeted", ""),
                "block_id": q.get("block_id"),
                "source": request.source
            })
        await db.commit()
        try:
            await screening_question_set_service.save_question_set(
                db=db,
                job_vacancy_id=request.job_id,
                questions=request.questions,
                source=request.source or "manual",
                block_distribution=None,
                metadata=None,
            )
            logger.info(f"Saved question set version for job {request.job_id}")
        except Exception as version_err:
            logger.warning(f"Failed to save question set version: {version_err}")
        return {"success": True, "saved_count": len(request.questions)}
    except Exception as e:
        logger.error(f"Failed to save questions: {e}")
        try:
            await db.rollback()
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS job_screening_questions (
                    id VARCHAR(255) PRIMARY KEY,
                    job_vacancy_id VARCHAR(255) NOT NULL,
                    question_text TEXT NOT NULL,
                    category VARCHAR(100) DEFAULT 'general',
                    question_type VARCHAR(100) DEFAULT 'open',
                    weight FLOAT DEFAULT 0.75,
                    skill_targeted VARCHAR(255) DEFAULT '',
                    block_id INTEGER,
                    source VARCHAR(100) DEFAULT 'manual',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """))
            await db.commit()
            for q in request.questions:
                q_id = q.get("id", f"q_{uuid.uuid4().hex[:12]}")
                await db.execute(text("""
                    INSERT INTO job_screening_questions (id, job_vacancy_id, question_text, category, question_type, weight, skill_targeted, block_id, source, is_active)
                    VALUES (:id, :job_id, :text, :category, :type, :weight, :skill_targeted, :block_id, :source, true)
                    ON CONFLICT (id) DO UPDATE SET
                        question_text = EXCLUDED.question_text,
                        category = EXCLUDED.category,
                        question_type = EXCLUDED.question_type
                """), {
                    "id": q_id,
                    "job_id": request.job_id,
                    "text": q.get("text", q.get("question", "")),
                    "category": q.get("category", "general"),
                    "type": q.get("type", "open"),
                    "weight": q.get("weight", 0.75),
                    "skill_targeted": q.get("skill_targeted", ""),
                    "block_id": q.get("block_id"),
                    "source": request.source
                })
            await db.commit()
            try:
                await screening_question_set_service.save_question_set(
                    db=db,
                    job_vacancy_id=request.job_id,
                    questions=request.questions,
                    source=request.source or "manual",
                    block_distribution=None,
                    metadata=None,
                )
                logger.info(f"Saved question set version for job {request.job_id}")
            except Exception as version_err:
                logger.warning(f"Failed to save question set version: {version_err}")
            return {"success": True, "saved_count": len(request.questions)}
        except Exception as e2:
            logger.error(f"Failed even after table creation: {e2}")
            return {"success": False, "error": str(e2)}


@router.get("/question-sets/{job_id}/active")
async def get_active_question_set(job_id: str, db: AsyncSession = Depends(get_db)):
    try:
        qs = await screening_question_set_service.get_active_version(db, job_id)
        if not qs:
            return {"success": False, "error": "No active question set found", "version": None}
        return {
            "success": True,
            "version": qs.version,
            "questions_count": qs.questions_count,
            "questions": qs.questions_snapshot,
            "source": qs.source,
            "difficulty_coefficient": qs.difficulty_coefficient,
            "block_distribution": qs.block_distribution,
            "created_at": qs.created_at.isoformat() if qs.created_at else None,
        }
    except Exception as e:
        logger.error(f"Failed to get active question set: {e}")
        return {"success": False, "error": str(e)}


@router.get("/question-sets/{job_id}/versions")
async def list_question_set_versions(job_id: str, db: AsyncSession = Depends(get_db)):
    try:
        versions = await screening_question_set_service.list_versions(db, job_id)
        return {"success": True, "versions": versions, "total": len(versions)}
    except Exception as e:
        logger.error(f"Failed to list question set versions: {e}")
        return {"success": False, "error": str(e)}


@router.get("/question-sets/{job_id}/version/{version}")
async def get_question_set_by_version(job_id: str, version: int, db: AsyncSession = Depends(get_db)):
    try:
        qs = await screening_question_set_service.get_by_version(db, job_id, version)
        if not qs:
            return {"success": False, "error": f"Version {version} not found"}
        return {
            "success": True,
            "version": qs.version,
            "questions_count": qs.questions_count,
            "questions": qs.questions_snapshot,
            "source": qs.source,
            "is_active": qs.is_active,
            "difficulty_coefficient": qs.difficulty_coefficient,
            "block_distribution": qs.block_distribution,
            "created_at": qs.created_at.isoformat() if qs.created_at else None,
        }
    except Exception as e:
        logger.error(f"Failed to get question set version: {e}")
        return {"success": False, "error": str(e)}


@router.get("/question-sets/{job_id}/consistency")
async def check_question_set_consistency(job_id: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await screening_question_set_service.check_version_consistency(db, job_id)
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Failed to check consistency: {e}")
        return {"success": False, "error": str(e)}
