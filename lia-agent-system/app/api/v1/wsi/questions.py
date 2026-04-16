"""
WSI package — question generation, suggestion, save, version, regenerate,
templates, adjust, and per-job retrieval routes.

Routes:
  POST /generate-questions
  POST /regenerate-questions
  GET  /question-templates
  POST /suggest-question
  POST /questions/save
  POST /questions/adjust
  GET  /questions/{job_id}
  GET  /question-sets/{job_id}/active
  GET  /question-sets/{job_id}/versions
  GET  /question-sets/{job_id}/version/{version}
  GET  /question-sets/{job_id}/consistency

Canonical contract: this is the single owner of the `/api/v1/wsi/*` namespace
for question CRUD. The historical `app/api/v1/wsi_questions.py` and
`app/api/v1/wsi_question_adjust.py` standalone files were merged here in
Task #244 and removed.
"""
import json
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, validator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.voice.repositories.wsi_repository import WsiRepository
from app.domains.cv_screening.dependencies import WSIService, get_wsi_service
from app.domains.cv_screening.services.screening_question_set_service import (
    ScreeningQuestionSetService,
    get_screening_question_set_service,
)
from app.domains.cv_screening.services.wsi_question_adjuster import (
    wsi_question_adjuster_service,
)
# NOTE: AuditService + check_fairness intentionally not imported here yet.
# Task #247 (follow-up) will reintroduce FairnessGuard + audit logging on
# `/wsi/generate-questions` — they were dead-code in the deleted
# `wsi_questions.py` (shadowed by the canonical handler below).

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

# ---------------------------------------------------------------------------
# Models for legacy `/regenerate-questions`, `/question-templates`, `/questions/adjust`
# (merged from wsi_questions.py and wsi_question_adjust.py in Task #244)
# ---------------------------------------------------------------------------

MIN_TECHNICAL_QUESTIONS = 4
MIN_BEHAVIORAL_QUESTIONS = 2
MIN_ELIGIBILITY_QUESTIONS = 2
DEFAULT_MAX_QUESTIONS = 12


class WSIQuestion(BaseModel):
    """Legacy WSI question shape used by /regenerate-questions and /question-templates."""
    id: str
    question: str
    type: str = "open"
    required: bool = True
    options: list[str] | None = None
    expected_answer: str | None = None
    competency_validated: str | None = None
    skill_type: str | None = None
    block_id: int | None = None


class RegenerateQuestionsRequest(BaseModel):
    company_id: str
    job_title: str
    current_questions: list[WSIQuestion] = Field(default_factory=list)
    technical_skills: list[str] = Field(default_factory=list)
    behavioral_competencies: list[str] = Field(default_factory=list)
    seniority: str | None = None
    max_questions: int = DEFAULT_MAX_QUESTIONS

    @validator('technical_skills', 'behavioral_competencies', pre=True, always=True)
    def filter_empty_strings(cls, v):
        if v is None:
            return []
        return [s.strip() for s in v if s and s.strip()]


class QuestionsResponse(BaseModel):
    success: bool
    questions: list[WSIQuestion]
    changes_summary: str | None = None
    questions_added: int = 0
    questions_removed: int = 0
    quality_warnings: list[str] = Field(default_factory=list)
    block_distribution: dict | None = None


class QuestionItem(BaseModel):
    """Per-job question item used by /questions/adjust and GET /questions/{job_id}."""
    id: str | None = None
    text: str
    category: str | None = None
    type: str | None = "open"
    weight: float | None = 0.75
    skill_targeted: str | None = None


class AdjustQuestionsRequest(BaseModel):
    job_id: str
    block_id: str
    adjustment_prompt: str
    current_questions: list[QuestionItem]
    job_context: dict[str, Any] | None = None


class GetQuestionsResponse(BaseModel):
    success: bool
    job_id: str
    questions: list[QuestionItem]
    questions_count: int
    source: str | None = None
    saved_at: str | None = None


QUESTION_TEMPLATES = {
    "technical": {
        "Python": "Descreva um projeto onde você utilizou Python para resolver um problema complexo. Quais bibliotecas você usou?",
        "JavaScript": "Como você organiza o código JavaScript em projetos grandes? Cite padrões que utiliza.",
        "React": "Explique como você gerencia estado em aplicações React. Já usou Redux, Context API ou outras soluções?",
        "Node.js": "Descreva sua experiência com Node.js em aplicações de produção. Como lida com escalabilidade?",
        "SQL": "Dê um exemplo de uma query SQL complexa que você escreveu. Como otimizou a performance?",
        "Docker": "Como você utiliza Docker no seu fluxo de trabalho? Tem experiência com orquestração?",
        "AWS": "Quais serviços AWS você já utilizou? Descreva um projeto onde aplicou arquitetura cloud.",
        "TypeScript": "Quais benefícios você vê no uso de TypeScript? Como aplica tipagem avançada?",
        "Kubernetes": "Descreva sua experiência com Kubernetes. Já configurou clusters em produção?",
        "Git": "Como você organiza branches e commits? Qual estratégia de git flow prefere?",
        "Java": "Descreva sua experiência com Java. Quais frameworks já utilizou em produção?",
        "C#": "Como você estrutura projetos em C#? Tem experiência com .NET Core?",
        "Go": "Quais são os benefícios que você vê no uso de Go? Em quais projetos aplicou?",
        "Ruby": "Descreva sua experiência com Ruby on Rails. Como lida com performance?",
        "PHP": "Como você organiza código em PHP? Quais frameworks conhece?",
    },
    "behavioral": {
        "Comunicação": "Conte sobre uma situação onde precisou explicar algo técnico para uma pessoa não-técnica.",
        "Liderança": "Descreva um momento onde liderou uma equipe ou projeto. Quais desafios enfrentou?",
        "Resolução de Problemas": "Fale sobre um problema complexo que resolveu. Qual foi sua abordagem?",
        "Trabalho em Equipe": "Como você lida com conflitos em equipe? Dê um exemplo concreto.",
        "Adaptabilidade": "Conte sobre uma mudança significativa no trabalho. Como se adaptou?",
        "Proatividade": "Descreva uma iniciativa que você tomou sem ser solicitado. Qual foi o resultado?",
        "Organização": "Como você gerencia múltiplas tarefas com prazos conflitantes?",
        "Empatia": "Conte sobre uma situação onde precisou entender o ponto de vista do outro.",
        "Resiliência": "Fale sobre um fracasso ou obstáculo significativo. Como superou?",
        "Pensamento Analítico": "Descreva uma decisão importante que tomou baseada em dados.",
        "Criatividade": "Conte sobre uma solução criativa que você propôs para um problema.",
        "Foco no Cliente": "Descreva uma situação onde foi além para atender às necessidades de um cliente.",
    }
}


def _normalize_competency(comp: str) -> str:
    return comp.strip().lower()


def _validate_question_coverage(
    questions: list[WSIQuestion],
    technical_skills: list[str],
    behavioral_competencies: list[str]
) -> list[str]:
    warnings = []
    tech_questions = [q for q in questions if q.skill_type == "technical"]
    behav_questions = [q for q in questions if q.skill_type == "behavioral"]
    elig_questions = [q for q in questions if q.block_id == 2 or q.skill_type == "eligibility"]

    if len(elig_questions) < MIN_ELIGIBILITY_QUESTIONS:
        warnings.append(f"Apenas {len(elig_questions)} perguntas de elegibilidade. Recomendado: {MIN_ELIGIBILITY_QUESTIONS}+")
    if len(tech_questions) < MIN_TECHNICAL_QUESTIONS and len(technical_skills) >= MIN_TECHNICAL_QUESTIONS:
        warnings.append(f"Apenas {len(tech_questions)} perguntas técnicas geradas. Recomendado: {MIN_TECHNICAL_QUESTIONS}+")
    if len(behav_questions) < MIN_BEHAVIORAL_QUESTIONS and len(behavioral_competencies) >= MIN_BEHAVIORAL_QUESTIONS:
        warnings.append(f"Apenas {len(behav_questions)} perguntas comportamentais geradas. Recomendado: {MIN_BEHAVIORAL_QUESTIONS}+")
    return warnings

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
# TODO(phase2): extract to repository — WSI question management
async def generate_questions(
    request: GenerateQuestionsRequest,
    db: AsyncSession = Depends(get_db),
    sqs_svc: ScreeningQuestionSetService = Depends(get_screening_question_set_service),
    wsi_svc: WSIService = Depends(get_wsi_service),
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
        active_qs = await sqs_svc.get_active_version(db, request.job_vacancy_id or "")
        qs_version = active_qs.version if active_qs else None
        qs_id = str(active_qs.id) if active_qs else None

        _repo = WsiRepository(db)
        await _repo.upsert_session(
            session_id=session_id,
            candidate_id="pending",
            job_vacancy_id=request.job_vacancy_id or "",
            screening_type="text",
            mode="compact",
            status="in_progress",
            question_set_version=qs_version,
            question_set_id=qs_id,
        )

        for idx, q in enumerate(questions):
            await _repo.upsert_question(
                question_id=q.id,
                session_id=session_id,
                competency=q.skill_targeted,
                framework=wsi_questions[idx].framework if idx < len(wsi_questions) else "CBI",
                question_type=q.question_type,
                question_text=q.text,
                weight=wsi_questions[idx].weight if idx < len(wsi_questions) else 1.0 / max(len(questions), 1),
                expected_signals=wsi_questions[idx].expected_signals if idx < len(wsi_questions) else [],
                scoring_criteria=dict(wsi_questions[idx].scoring_criteria) if idx < len(wsi_questions) else {},
                sequence_order=idx + 1,
            )
    except Exception as e:
        logger.warning(f"Failed to save to DB: {e}")

    return GenerateQuestionsResponse(
        session_id=session_id,
        questions=questions,
        job_title=job_title
    )


@router.post("/suggest-question", response_model=None)
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


@router.post("/questions/save", response_model=None)
async def save_questions(
    request: SaveQuestionsRequest,
    db: AsyncSession = Depends(get_db),
    sqs_svc: ScreeningQuestionSetService = Depends(get_screening_question_set_service),
):
    """Save screening questions for a job vacancy."""
    try:
        for q in request.questions:
            q_id = q.get("id", f"q_{uuid.uuid4().hex[:12]}")
            _repo = WsiRepository(db)
            await _repo.upsert_job_screening_question(
                question_id=q_id,
                job_id=request.job_id,
                question_text=q.get("text", q.get("question", "")),
                category=q.get("category", "general"),
                question_type=q.get("type", "open"),
                weight=q.get("weight", 0.75),
                skill_targeted=q.get("skill_targeted", ""),
                block_id=q.get("block_id"),
                source=request.source,
            )
        try:
            await sqs_svc.save_question_set(
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
            try:
                await sqs_svc.save_question_set(
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


@router.get("/question-sets/{job_id}/active", response_model=None)
async def get_active_question_set(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    sqs_svc: ScreeningQuestionSetService = Depends(get_screening_question_set_service),
):
    try:
        qs = await sqs_svc.get_active_version(db, job_id)
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


@router.get("/question-sets/{job_id}/versions", response_model=None)
async def list_question_set_versions(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    sqs_svc: ScreeningQuestionSetService = Depends(get_screening_question_set_service),
):
    try:
        versions = await sqs_svc.list_versions(db, job_id)
        return {"success": True, "versions": versions, "total": len(versions)}
    except Exception as e:
        logger.error(f"Failed to list question set versions: {e}")
        return {"success": False, "error": str(e)}


@router.get("/question-sets/{job_id}/version/{version}", response_model=None)
async def get_question_set_by_version(
    job_id: str,
    version: int,
    db: AsyncSession = Depends(get_db),
    sqs_svc: ScreeningQuestionSetService = Depends(get_screening_question_set_service),
):
    try:
        qs = await sqs_svc.get_by_version(db, job_id, version)
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


@router.get("/question-sets/{job_id}/consistency", response_model=None)
async def check_question_set_consistency(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    sqs_svc: ScreeningQuestionSetService = Depends(get_screening_question_set_service),
):
    try:
        result = await sqs_svc.check_version_consistency(db, job_id)
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Failed to check consistency: {e}")
        return {"success": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Merged from app/api/v1/wsi_questions.py (Task #244):
#   POST /regenerate-questions
#   GET  /question-templates
# ---------------------------------------------------------------------------

@router.post("/regenerate-questions", response_model=QuestionsResponse)
async def regenerate_wsi_questions(
    request: RegenerateQuestionsRequest,
    wsi_svc: WSIService = Depends(get_wsi_service),
):
    """
    Regenerate WSI questions when competencies change.

    Accepts full competency lists and computes diffs server-side:
    - Keeps questions for competencies still in the list
    - Removes questions for competencies no longer in the list
    - Generates new questions for new competencies via LLM
    - Ensures minimum WSI quality thresholds
    """
    try:
        current_questions = request.current_questions

        current_tech_set: set[str] = {_normalize_competency(c) for c in request.technical_skills}
        current_behav_set: set[str] = {_normalize_competency(c) for c in request.behavioral_competencies}
        all_current_competencies = current_tech_set | current_behav_set

        retained_questions: list[WSIQuestion] = []
        covered_competencies: set[str] = set()
        removed_count = 0

        for q in current_questions:
            if q.competency_validated:
                comp_normalized = _normalize_competency(q.competency_validated)
                if comp_normalized in all_current_competencies:
                    retained_questions.append(q)
                    covered_competencies.add(comp_normalized)
                else:
                    removed_count += 1
            else:
                retained_questions.append(q)

        new_tech = [s for s in request.technical_skills if _normalize_competency(s) not in covered_competencies]
        new_behav = [s for s in request.behavioral_competencies if _normalize_competency(s) not in covered_competencies]

        added_count = 0
        tech_count = sum(1 for q in retained_questions if q.skill_type == "technical")
        behav_count = sum(1 for q in retained_questions if q.skill_type == "behavioral")

        tech_needed = max(0, MIN_TECHNICAL_QUESTIONS - tech_count)
        tech_to_generate = new_tech[:max(tech_needed, 2)]
        behav_needed = max(0, MIN_BEHAVIORAL_QUESTIONS - behav_count)
        behav_to_generate = new_behav[:max(behav_needed, 1)]

        if tech_to_generate or behav_to_generate:
            _raw = await wsi_svc.generate_from_simple_inputs(
                skills=tech_to_generate,
                behavioral=behav_to_generate,
                seniority=request.seniority or "pleno",
                job_description=request.job_title,
                mode="compact",
            )
            for wq in _raw:
                if len(retained_questions) >= request.max_questions:
                    break
                skill_type = "behavioral" if wq.framework == "BigFive" or wq.question_type == "situational" else "technical"
                block_id = 4 if skill_type == "behavioral" else 3
                new_q = WSIQuestion(
                    id=wq.id,
                    question=wq.question_text,
                    type="open",
                    required=True,
                    competency_validated=wq.competency,
                    skill_type=skill_type,
                    block_id=block_id,
                )
                retained_questions.append(new_q)
                covered_competencies.add(_normalize_competency(wq.competency))
                added_count += 1

        changes = []
        if added_count > 0:
            changes.append(f"Adicionadas {added_count} novas perguntas")
        if removed_count > 0:
            changes.append(f"Removidas {removed_count} perguntas de competências não mais selecionadas")

        warnings = _validate_question_coverage(
            retained_questions,
            request.technical_skills,
            request.behavioral_competencies,
        )

        return QuestionsResponse(
            success=True,
            questions=retained_questions,
            changes_summary=". ".join(changes) if changes else "Nenhuma alteração necessária",
            questions_added=added_count,
            questions_removed=removed_count,
            quality_warnings=warnings,
        )
    except Exception as e:
        logger.error(f"Error regenerating WSI questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/question-templates", response_model=None)
async def get_question_templates():
    """Get available question templates for reference."""
    return {
        "success": True,
        "templates": QUESTION_TEMPLATES,
        "supported_technical": list(QUESTION_TEMPLATES.get("technical", {}).keys()),
        "supported_behavioral": list(QUESTION_TEMPLATES.get("behavioral", {}).keys()),
        "minimums": {
            "technical": MIN_TECHNICAL_QUESTIONS,
            "behavioral": MIN_BEHAVIORAL_QUESTIONS,
        },
    }


# ---------------------------------------------------------------------------
# Merged from app/api/v1/wsi_question_adjust.py (Task #244):
#   POST /questions/adjust
#   GET  /questions/{job_id}
# ---------------------------------------------------------------------------

@router.post("/questions/adjust", response_model=None)
async def adjust_questions(request: AdjustQuestionsRequest):
    """Adjust WSI questions based on recruiter's natural language prompt."""
    try:
        result = await wsi_question_adjuster_service.adjust_questions(
            job_id=request.job_id,
            block_id=request.block_id,
            adjustment_prompt=request.adjustment_prompt,
            current_questions=[q.dict() for q in request.current_questions],
            job_context=request.job_context,
        )
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Adjustment failed"))
        return result
    except ValueError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adjusting WSI questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/questions/{job_id}", response_model=GetQuestionsResponse)
async def get_questions_for_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    sqs_svc: ScreeningQuestionSetService = Depends(get_screening_question_set_service),
):
    """
    Retrieve saved screening questions for a job vacancy.

    Primary source: the active screening_question_sets version written by
    ``POST /wsi/questions/save`` via ScreeningQuestionSetService.

    Fallback: if no active question-set version exists (e.g. the version
    write failed during save but row-level writes to job_screening_questions
    succeeded), queries job_screening_questions directly via WsiRepository.
    """
    try:
        qs = await sqs_svc.get_active_version(db, job_id)
    except Exception as e:
        logger.error(f"Failed to load active question set for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    if qs and qs.questions_snapshot:
        questions: list[QuestionItem] = []
        for q in qs.questions_snapshot:
            if not isinstance(q, dict):
                continue
            questions.append(QuestionItem(
                id=q.get("id"),
                text=q.get("text") or q.get("question") or "",
                category=q.get("category"),
                type=q.get("type", "open"),
                weight=q.get("weight", 0.75),
                skill_targeted=q.get("skill_targeted"),
            ))
        return GetQuestionsResponse(
            success=True,
            job_id=job_id,
            questions=questions,
            questions_count=len(questions),
            source=qs.source,
            saved_at=qs.created_at.isoformat() if qs.created_at else None,
        )

    # Fallback: read directly from job_screening_questions table.
    try:
        repo = WsiRepository(db)
        raw_rows = await repo.get_job_screening_questions(job_id)
    except Exception as e:
        logger.error(f"Fallback read from job_screening_questions failed for job {job_id}: {e}")
        raw_rows = []

    fallback_questions: list[QuestionItem] = [
        QuestionItem(
            id=r.get("id"),
            text=r.get("text") or "",
            category=r.get("category"),
            type=r.get("type", "open"),
            weight=r.get("weight", 0.75),
            skill_targeted=r.get("skill_targeted"),
        )
        for r in raw_rows
    ]
    if fallback_questions:
        logger.info(
            f"get_questions_for_job: no active question set for job {job_id}; "
            f"returning {len(fallback_questions)} rows from job_screening_questions fallback"
        )
    return GetQuestionsResponse(
        success=True,
        job_id=job_id,
        questions=fallback_questions,
        questions_count=len(fallback_questions),
        source="job_screening_questions" if fallback_questions else None,
        saved_at=None,
    )
