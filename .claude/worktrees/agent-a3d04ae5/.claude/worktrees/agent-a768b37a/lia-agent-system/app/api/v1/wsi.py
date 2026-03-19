"""
WSI (Work Sample Interview) API v1 Endpoints.

Provides RESTful API for WSI text screening workflow based on:
- Bloom's Taxonomy (Cognitive Levels)
- Dreyfus Model (Proficiency Levels)
- Big Five Personality Indicators
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import uuid
import json
import logging
import os

from app.core.database import get_db
from app.services.screening_question_set_service import screening_question_set_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/wsi", tags=["WSI Text Screening"])

AI_INTEGRATIONS_ANTHROPIC_API_KEY = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY")
AI_INTEGRATIONS_ANTHROPIC_BASE_URL = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL")


BLOOM_LEVELS = {
    1: {"name": "Remember", "name_pt": "Lembrar", "description": "Recall facts and basic concepts"},
    2: {"name": "Understand", "name_pt": "Compreender", "description": "Explain ideas and concepts"},
    3: {"name": "Apply", "name_pt": "Aplicar", "description": "Use information in new situations"},
    4: {"name": "Analyze", "name_pt": "Analisar", "description": "Draw connections among ideas"},
    5: {"name": "Evaluate", "name_pt": "Avaliar", "description": "Justify decisions or positions"},
    6: {"name": "Create", "name_pt": "Criar", "description": "Produce new or original work"}
}

DREYFUS_LEVELS = {
    1: {"name": "Novice", "name_pt": "Novato", "description": "Follows rigid rules"},
    2: {"name": "Advanced Beginner", "name_pt": "Iniciante Avançado", "description": "Recognizes situational aspects"},
    3: {"name": "Competent", "name_pt": "Competente", "description": "Conscious planning, prioritization"},
    4: {"name": "Proficient", "name_pt": "Proficiente", "description": "Holistic view, fluid adaptation"},
    5: {"name": "Expert", "name_pt": "Expert", "description": "Deep intuition, transcends rules"}
}

BIG_FIVE_TRAITS = {
    "openness": {"name": "Openness", "name_pt": "Abertura", "high": "Curious, creative", "low": "Conventional, routine-oriented"},
    "conscientiousness": {"name": "Conscientiousness", "name_pt": "Conscienciosidade", "high": "Organized, disciplined", "low": "Flexible, spontaneous"},
    "extraversion": {"name": "Extraversion", "name_pt": "Extroversão", "high": "Outgoing, assertive", "low": "Reserved, reflective"},
    "agreeableness": {"name": "Agreeableness", "name_pt": "Amabilidade", "high": "Cooperative, empathetic", "low": "Competitive, independent"},
    "neuroticism": {"name": "Neuroticism", "name_pt": "Estabilidade Emocional", "high": "Sensitive, anxious", "low": "Calm, resilient"}
}


class WSIQuestionOutput(BaseModel):
    id: str
    text: str
    bloom_level: int
    bloom_level_name: str
    skill_targeted: str
    question_type: str
    block_id: Optional[int] = None
    category: Optional[str] = None
    is_eliminatory: Optional[bool] = False


class GenerateQuestionsRequest(BaseModel):
    job_vacancy_id: Optional[str] = None
    company_id: Optional[str] = None
    job_title: Optional[str] = None
    requirements: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    technical_skills: Optional[List[str]] = None
    behavioral_competencies: Optional[List[str]] = None
    responsibilities: Optional[List[str]] = None
    seniority_level: Optional[str] = "pleno"
    seniority: Optional[str] = None
    department: Optional[str] = None
    description: Optional[str] = None
    num_questions: int = Field(default=5, ge=3, le=12)
    max_questions: Optional[int] = None


class GenerateQuestionsResponse(BaseModel):
    session_id: str
    questions: List[WSIQuestionOutput]
    job_title: Optional[str]
    methodology: str = "WSI (Bloom + Dreyfus + Big Five)"


class BigFiveIndicators(BaseModel):
    openness: int = Field(ge=0, le=100, description="Curiosity, creativity, openness to new experiences")
    conscientiousness: int = Field(ge=0, le=100, description="Organization, discipline, goal-orientation")
    extraversion: int = Field(ge=0, le=100, description="Sociability, assertiveness, energy")
    agreeableness: int = Field(ge=0, le=100, description="Cooperation, empathy, teamwork")
    neuroticism: int = Field(ge=0, le=100, description="Emotional stability (inverse: low = stable)")


class AnalyzeResponseRequest(BaseModel):
    session_id: str
    question_id: str
    response_text: str
    candidate_id: str


class AnalyzeResponseOutput(BaseModel):
    question_id: str
    bloom_score: int = Field(ge=1, le=6)
    bloom_level_name: str
    dreyfus_level: int = Field(ge=1, le=5)
    dreyfus_level_name: str
    big_five_indicators: BigFiveIndicators
    score: float = Field(ge=0, le=5)
    feedback: str
    evidences: List[str]
    red_flags: List[str]


class ResponseInput(BaseModel):
    question_id: str
    response_text: str


class CompleteScreeningRequest(BaseModel):
    session_id: str
    candidate_id: str
    job_vacancy_id: Optional[str] = None
    responses: List[ResponseInput]


class ArchetypeIndicator(BaseModel):
    archetype: str
    match_score: int = Field(ge=0, le=100)
    description: str


class CompleteScreeningResponse(BaseModel):
    result_id: str
    candidate_id: str
    job_vacancy_id: Optional[str]
    overall_score: float = Field(ge=0, le=5)
    classification: str
    cognitive_level: Dict[str, Any]
    proficiency_level: Dict[str, Any]
    big_five_profile: BigFiveIndicators
    archetype_indicators: List[ArchetypeIndicator]
    summary: str
    recommendations: List[str]
    response_analyses: List[AnalyzeResponseOutput]


async def get_anthropic_client():
    """Get Anthropic client for AI analysis."""
    try:
        from anthropic import Anthropic
        if not AI_INTEGRATIONS_ANTHROPIC_API_KEY or not AI_INTEGRATIONS_ANTHROPIC_BASE_URL:
            logger.warning("Anthropic API not configured, using fallback responses")
            return None
        return Anthropic(
            api_key=AI_INTEGRATIONS_ANTHROPIC_API_KEY,
            base_url=AI_INTEGRATIONS_ANTHROPIC_BASE_URL
        )
    except Exception as e:
        logger.error(f"Failed to create Anthropic client: {e}")
        return None


def parse_json_response(content: str, fallback: Dict) -> Dict:
    """Safely parse JSON from LLM response."""
    try:
        if isinstance(content, dict):
            return content
        content_str = content if isinstance(content, str) else str(content)
        if "```json" in content_str:
            start = content_str.find("```json") + 7
            end = content_str.find("```", start)
            content_str = content_str[start:end].strip()
        elif "```" in content_str:
            start = content_str.find("```") + 3
            end = content_str.find("```", start)
            content_str = content_str[start:end].strip()
        return json.loads(content_str)
    except (json.JSONDecodeError, ValueError):
        logger.warning("Failed to parse JSON, using fallback")
        return fallback


@router.post("/generate-questions", response_model=GenerateQuestionsResponse)
async def generate_questions(
    request: GenerateQuestionsRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate WSI screening questions based on job requirements.
    
    Questions target different Bloom taxonomy levels (Remember → Create)
    to assess cognitive abilities across the spectrum.
    """
    session_id = f"wsi_text_{uuid.uuid4().hex[:12]}"
    
    job_title = request.job_title or "Professional"
    all_requirements = request.requirements or request.responsibilities or []
    all_skills = request.skills or request.technical_skills or ["Problem Solving", "Communication"]
    behavioral = request.behavioral_competencies or []
    seniority = request.seniority_level or request.seniority or "pleno"
    num_q = request.max_questions or request.num_questions
    department = request.department or ""
    description = request.description or ""
    
    client = await get_anthropic_client()
    
    if client:
        prompt = f"""Você é um especialista em recrutamento usando a metodologia WSI (WeDoTalent Skill Index).
Gere {num_q} perguntas de triagem para a vaga de {job_title}.

CONTEXTO DA VAGA:
- Cargo: {job_title}
- Senioridade: {seniority}
- Departamento: {department or 'Não especificado'}
- Descrição: {description or 'Não fornecida'}
- Responsabilidades: {', '.join(all_requirements) if all_requirements else 'Não especificadas'}
- Competências Técnicas: {', '.join(all_skills) if all_skills else 'Não especificadas'}
- Competências Comportamentais: {', '.join(behavioral) if behavioral else 'Não especificadas'}

METODOLOGIA WSI - BLOCOS:
- Bloco 2 (Elegibilidade): Perguntas eliminatórias sobre disponibilidade, requisitos mínimos, localização
- Bloco 3 (Técnica): Perguntas sobre conhecimento técnico, experiência prática, profundidade nas skills requeridas
- Bloco 4 (Situacional/Comportamental): Perguntas situacionais sobre competências comportamentais, liderança, trabalho em equipe

REGRAS:
1. Gere pelo menos 1 pergunta eliminatória (Bloco 2) sobre elegibilidade
2. Distribua as perguntas técnicas (Bloco 3) entre as skills requeridas
3. Inclua perguntas situacionais (Bloco 4) baseadas nas competências comportamentais
4. Calibre a complexidade pela senioridade: junior=perguntas mais diretas, senior=perguntas mais profundas
5. Cada pergunta deve ser em português brasileiro
6. Use Taxonomia de Bloom para variar níveis cognitivos

Retorne APENAS JSON válido:
{{
  "questions": [
    {{
      "text": "Texto da pergunta em português",
      "bloom_level": 4,
      "skill_targeted": "Nome da competência avaliada",
      "question_type": "eliminatory|technical|situational|behavioral",
      "block_id": 2,
      "category": "eligibility|technical|behavioral",
      "is_eliminatory": false
    }}
  ]
}}"""
        
        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )
            data = parse_json_response(response.content[0].text, {"questions": []})
            questions_data = data.get("questions", [])
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            questions_data = []
    else:
        questions_data = []
    
    if not questions_data:
        questions_data = [
            {
                "text": f"Qual sua experiência com {all_skills[0] if all_skills else 'a área'}? Cite um exemplo prático.",
                "bloom_level": 2,
                "skill_targeted": all_skills[0] if all_skills else "General",
                "question_type": "contextual"
            },
            {
                "text": "Descreva uma situação desafiadora que você enfrentou no trabalho. Como você a resolveu?",
                "bloom_level": 4,
                "skill_targeted": "Problem Solving",
                "question_type": "situational"
            },
            {
                "text": "Como você organiza suas tarefas e prioridades no dia a dia?",
                "bloom_level": 3,
                "skill_targeted": "Organization",
                "question_type": "behavioral"
            },
            {
                "text": "Conte sobre um projeto onde você precisou trabalhar em equipe. Qual foi seu papel?",
                "bloom_level": 3,
                "skill_targeted": "Teamwork",
                "question_type": "contextual"
            },
            {
                "text": "Se você pudesse melhorar um processo na sua área de atuação, o que seria e como faria?",
                "bloom_level": 6,
                "skill_targeted": "Innovation",
                "question_type": "creative"
            }
        ][:num_q]
    
    questions = []
    for idx, q in enumerate(questions_data):
        question_id = f"q_{session_id}_{idx+1}"
        bloom_level = q.get("bloom_level", 3)
        questions.append(WSIQuestionOutput(
            id=question_id,
            text=q.get("text", ""),
            bloom_level=bloom_level,
            bloom_level_name=BLOOM_LEVELS.get(bloom_level, BLOOM_LEVELS[3])["name"],
            skill_targeted=q.get("skill_targeted", "General"),
            question_type=q.get("question_type", "contextual"),
            block_id=q.get("block_id"),
            category=q.get("category"),
            is_eliminatory=q.get("is_eliminatory", False)
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
        
        for q in questions:
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
                "framework": "Bloom",
                "question_type": q.question_type,
                "question_text": q.text,
                "weight": 1.0 / len(questions),
                "expected_signals": json.dumps(["Context", "Action", "Result"]),
                "scoring_criteria": json.dumps({"bloom_level": q.bloom_level}),
                "sequence_order": questions.index(q) + 1
            })
        await db.commit()
    except Exception as e:
        logger.warning(f"Failed to save to DB: {e}")
    
    return GenerateQuestionsResponse(
        session_id=session_id,
        questions=questions,
        job_title=job_title
    )


class JDEvaluateRequest(BaseModel):
    job_title: str
    responsibilities: Optional[List[str]] = None
    technical_skills: Optional[List[str]] = None
    behavioral_competencies: Optional[List[str]] = None
    seniority: Optional[str] = None
    department: Optional[str] = None
    description: Optional[str] = None

class JDEvaluateResponse(BaseModel):
    success: bool = True
    score: int
    max_score: int = 100
    indicators: List[Dict[str, Any]]
    lia_suggestion: str
    can_generate: bool
    details: Dict[str, Any]

@router.post("/jd-evaluate")
async def evaluate_jd(request: JDEvaluateRequest):
    """Evaluate job description quality for WSI question generation."""
    resp_count = len(request.responsibilities or [])
    tech_count = len(request.technical_skills or [])
    behav_count = len(request.behavioral_competencies or [])
    has_seniority = bool(request.seniority)
    has_description = bool(request.description and len(request.description) > 20)
    
    score = 0
    indicators = []
    
    if resp_count >= 3:
        score += 30
        indicators.append({"label": "Responsabilidades", "count": resp_count, "status": "sufficient", "minimum": 3})
    elif resp_count >= 1:
        score += 15
        indicators.append({"label": "Responsabilidades", "count": resp_count, "status": "partial", "minimum": 3})
    else:
        indicators.append({"label": "Responsabilidades", "count": 0, "status": "insufficient", "minimum": 3})
    
    if tech_count >= 3:
        score += 30
        indicators.append({"label": "Comp. Técnicas", "count": tech_count, "status": "sufficient", "minimum": 3})
    elif tech_count >= 1:
        score += 15
        indicators.append({"label": "Comp. Técnicas", "count": tech_count, "status": "partial", "minimum": 3})
    else:
        indicators.append({"label": "Comp. Técnicas", "count": 0, "status": "insufficient", "minimum": 3})
    
    if behav_count >= 3:
        score += 25
        indicators.append({"label": "Comp. Comportamentais", "count": behav_count, "status": "sufficient", "minimum": 3})
    elif behav_count >= 1:
        score += 12
        indicators.append({"label": "Comp. Comportamentais", "count": behav_count, "status": "partial", "minimum": 3})
    else:
        indicators.append({"label": "Comp. Comportamentais", "count": 0, "status": "insufficient", "minimum": 3})
    
    if has_seniority:
        score += 10
        indicators.append({"label": "Senioridade", "count": 1, "status": "sufficient", "minimum": 1})
    else:
        indicators.append({"label": "Senioridade", "count": 0, "status": "insufficient", "minimum": 1})
    
    if has_description:
        score += 5
    
    if score >= 70:
        suggestion = f"JD bem estruturado para {request.job_title}. As perguntas WSI serão calibradas com base nas {tech_count} competências técnicas e {behav_count} comportamentais identificadas."
    elif score >= 50:
        missing = []
        if resp_count < 3: missing.append("responsabilidades")
        if tech_count < 3: missing.append("competências técnicas")
        if behav_count < 3: missing.append("competências comportamentais")
        suggestion = f"JD parcialmente completo. Para melhorar a qualidade das perguntas, adicione mais: {', '.join(missing)}."
    else:
        suggestion = "JD precisa de mais informações para gerar perguntas de qualidade. Adicione responsabilidades, competências técnicas e comportamentais."
    
    return JDEvaluateResponse(
        success=True,
        score=score,
        indicators=indicators,
        lia_suggestion=suggestion,
        can_generate=score >= 40,
        details={
            "responsibilities_count": resp_count,
            "technical_skills_count": tech_count,
            "behavioral_competencies_count": behav_count,
            "seniority_defined": has_seniority,
            "has_description": has_description
        }
    )


class SaveQuestionsRequest(BaseModel):
    job_id: str
    questions: List[Dict[str, Any]]
    source: Optional[str] = "manual"

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


class SuggestQuestionRequest(BaseModel):
    prompt: str
    job_title: Optional[str] = None
    block_id: Optional[int] = None
    technical_skills: Optional[List[str]] = None
    behavioral_competencies: Optional[List[str]] = None
    seniority: Optional[str] = None
    description: Optional[str] = None

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
        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}]
            )
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


@router.post("/analyze-response", response_model=AnalyzeResponseOutput)
async def analyze_response(
    request: AnalyzeResponseRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze a single candidate response using Claude AI.
    
    Evaluates:
    - Bloom's Taxonomy level demonstrated (cognitive level)
    - Dreyfus Model proficiency level
    - Big Five personality indicators
    """
    client = await get_anthropic_client()
    
    question_text = ""
    try:
        result = await db.execute(text("""
            SELECT question_text, competency FROM wsi_questions WHERE id = :question_id
        """), {"question_id": request.question_id})
        row = result.fetchone()
        if row:
            question_text = row[0]
    except Exception:
        pass
    
    if client:
        prompt = f"""Analyze this candidate response using WSI methodology (Bloom + Dreyfus + Big Five).

QUESTION: {question_text or "Not available"}

CANDIDATE RESPONSE:
{request.response_text}

Analyze and provide:
1. **Bloom Level (1-6)**: What cognitive level does the response demonstrate?
   1=Remember (recalls facts), 2=Understand (explains), 3=Apply (uses in practice), 
   4=Analyze (connects ideas), 5=Evaluate (justifies decisions), 6=Create (produces new ideas)

2. **Dreyfus Level (1-5)**: What proficiency level?
   1=Novice, 2=Advanced Beginner, 3=Competent, 4=Proficient, 5=Expert

3. **Big Five Indicators (0-100 each)**:
   - Openness: Creativity, curiosity for new ideas
   - Conscientiousness: Organization, discipline, goal focus
   - Extraversion: Sociability, assertiveness, energy
   - Agreeableness: Cooperation, empathy, teamwork
   - Neuroticism: Emotional sensitivity (low = stable/calm)

4. **Score (0-5)**: Overall quality of response
5. **Feedback**: Brief constructive feedback in Portuguese
6. **Evidences**: Key points that support the evaluation
7. **Red Flags**: Any concerns or inconsistencies

Return ONLY valid JSON:
{{
  "bloom_score": 4,
  "dreyfus_level": 3,
  "big_five": {{
    "openness": 65,
    "conscientiousness": 70,
    "extraversion": 55,
    "agreeableness": 60,
    "neuroticism": 35
  }},
  "score": 3.5,
  "feedback": "Resposta demonstra boa capacidade analítica...",
  "evidences": ["Exemplo concreto citado", "Métricas mencionadas"],
  "red_flags": []
}}"""

        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            data = parse_json_response(response.content[0].text, {})
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            data = {}
    else:
        data = {}
    
    bloom_score = data.get("bloom_score", 3)
    dreyfus_level = data.get("dreyfus_level", 3)
    big_five = data.get("big_five", {
        "openness": 50, "conscientiousness": 50, "extraversion": 50,
        "agreeableness": 50, "neuroticism": 50
    })
    
    analysis_id = str(uuid.uuid4())
    try:
        await db.execute(text("""
            INSERT INTO wsi_response_analyses (
                id, session_id, question_id, candidate_id, job_vacancy_id,
                competency, response_text, bloom_level, dreyfus_level,
                evidences, red_flags, final_score, justification
            )
            VALUES (:id, :session_id, :question_id, :candidate_id, :job_vacancy_id,
                    :competency, :response_text, :bloom_level, :dreyfus_level,
                    :evidences::jsonb, :red_flags::jsonb, :final_score, :justification)
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": analysis_id,
            "session_id": request.session_id,
            "question_id": request.question_id,
            "candidate_id": request.candidate_id,
            "job_vacancy_id": "",
            "competency": "General",
            "response_text": request.response_text,
            "bloom_level": bloom_score,
            "dreyfus_level": dreyfus_level,
            "evidences": json.dumps(data.get("evidences", [])),
            "red_flags": json.dumps(data.get("red_flags", [])),
            "final_score": data.get("score", 3.0),
            "justification": data.get("feedback", "")
        })
        await db.commit()
    except Exception as e:
        logger.warning(f"Failed to save analysis: {e}")
    
    return AnalyzeResponseOutput(
        question_id=request.question_id,
        bloom_score=bloom_score,
        bloom_level_name=BLOOM_LEVELS.get(bloom_score, BLOOM_LEVELS[3])["name"],
        dreyfus_level=dreyfus_level,
        dreyfus_level_name=DREYFUS_LEVELS.get(dreyfus_level, DREYFUS_LEVELS[3])["name"],
        big_five_indicators=BigFiveIndicators(
            openness=big_five.get("openness", 50),
            conscientiousness=big_five.get("conscientiousness", 50),
            extraversion=big_five.get("extraversion", 50),
            agreeableness=big_five.get("agreeableness", 50),
            neuroticism=big_five.get("neuroticism", 50)
        ),
        score=data.get("score", 3.0),
        feedback=data.get("feedback", "Análise em processamento"),
        evidences=data.get("evidences", []),
        red_flags=data.get("red_flags", [])
    )


@router.post("/complete-screening", response_model=CompleteScreeningResponse)
async def complete_screening(
    request: CompleteScreeningRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Complete WSI screening by analyzing all responses and generating final report.
    
    Returns comprehensive assessment including:
    - Overall score (0-5)
    - Cognitive level (Bloom average)
    - Proficiency level (Dreyfus average)
    - Big Five personality profile
    - Archetype indicators
    - Summary and recommendations
    """
    response_analyses = []
    
    for resp in request.responses:
        analysis = await analyze_response(
            AnalyzeResponseRequest(
                session_id=request.session_id,
                question_id=resp.question_id,
                response_text=resp.response_text,
                candidate_id=request.candidate_id
            ),
            db
        )
        response_analyses.append(analysis)
    
    avg_bloom = sum(a.bloom_score for a in response_analyses) / len(response_analyses) if response_analyses else 3
    avg_dreyfus = sum(a.dreyfus_level for a in response_analyses) / len(response_analyses) if response_analyses else 3
    avg_score = sum(a.score for a in response_analyses) / len(response_analyses) if response_analyses else 3.0
    
    avg_big_five = BigFiveIndicators(
        openness=int(sum(a.big_five_indicators.openness for a in response_analyses) / len(response_analyses)) if response_analyses else 50,
        conscientiousness=int(sum(a.big_five_indicators.conscientiousness for a in response_analyses) / len(response_analyses)) if response_analyses else 50,
        extraversion=int(sum(a.big_five_indicators.extraversion for a in response_analyses) / len(response_analyses)) if response_analyses else 50,
        agreeableness=int(sum(a.big_five_indicators.agreeableness for a in response_analyses) / len(response_analyses)) if response_analyses else 50,
        neuroticism=int(sum(a.big_five_indicators.neuroticism for a in response_analyses) / len(response_analyses)) if response_analyses else 50
    )
    
    if avg_score >= 4.5:
        classification = "excelente"
    elif avg_score >= 4.0:
        classification = "alto"
    elif avg_score >= 3.0:
        classification = "medio"
    elif avg_score >= 2.0:
        classification = "regular"
    else:
        classification = "baixo"
    
    archetypes = []
    o, c, e, a, n = (
        avg_big_five.openness, avg_big_five.conscientiousness,
        avg_big_five.extraversion, avg_big_five.agreeableness, 100 - avg_big_five.neuroticism
    )
    
    if o >= 70 and e >= 60:
        archetypes.append(ArchetypeIndicator(
            archetype="Catalisador Visionário",
            match_score=min(100, (o + e) // 2),
            description="Inovador, inspirador, busca mudanças"
        ))
    if c >= 70 and a >= 60:
        archetypes.append(ArchetypeIndicator(
            archetype="Executor Confiável",
            match_score=min(100, (c + a) // 2),
            description="Metódico, colaborativo, entrega consistente"
        ))
    if a >= 70 and e >= 60:
        archetypes.append(ArchetypeIndicator(
            archetype="Guardião de Clientes",
            match_score=min(100, (a + e) // 2),
            description="Empático, comunicativo, orientado ao cliente"
        ))
    if o >= 70 and c >= 60:
        archetypes.append(ArchetypeIndicator(
            archetype="Estrategista Analítico",
            match_score=min(100, (o + c) // 2),
            description="Pensador profundo, orientado a dados"
        ))
    if not archetypes:
        archetypes.append(ArchetypeIndicator(
            archetype="Perfil Equilibrado",
            match_score=60,
            description="Perfil versátil com características balanceadas"
        ))
    
    bloom_level_name = BLOOM_LEVELS.get(round(avg_bloom), BLOOM_LEVELS[3])
    dreyfus_level_name = DREYFUS_LEVELS.get(round(avg_dreyfus), DREYFUS_LEVELS[3])
    
    recommendations = []
    if avg_bloom < 4:
        recommendations.append("Desenvolver habilidades de análise crítica e avaliação")
    if avg_dreyfus < 3:
        recommendations.append("Ganhar mais experiência prática em projetos reais")
    if avg_big_five.conscientiousness < 50:
        recommendations.append("Trabalhar organização e planejamento")
    if avg_big_five.extraversion < 40:
        recommendations.append("Desenvolver habilidades de comunicação interpessoal")
    if not recommendations:
        recommendations.append("Candidato demonstra perfil sólido para a posição")
    
    summary = (
        f"Candidato avaliado como {classification.upper()} (Score: {avg_score:.1f}/5.0). "
        f"Demonstra nível cognitivo {bloom_level_name['name_pt']} (Bloom {round(avg_bloom)}) "
        f"e proficiência {dreyfus_level_name['name_pt']} (Dreyfus {round(avg_dreyfus)}). "
        f"Arquétipo predominante: {archetypes[0].archetype}."
    )
    
    result_id = str(uuid.uuid4())
    try:
        await db.execute(text("""
            INSERT INTO wsi_results (
                id, session_id, candidate_id, job_vacancy_id,
                technical_wsi, behavioral_wsi, overall_wsi, classification
            )
            VALUES (:id, :session_id, :candidate_id, :job_vacancy_id,
                    :technical_wsi, :behavioral_wsi, :overall_wsi, :classification)
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": result_id,
            "session_id": request.session_id,
            "candidate_id": request.candidate_id,
            "job_vacancy_id": request.job_vacancy_id or "",
            "technical_wsi": avg_score,
            "behavioral_wsi": avg_score,
            "overall_wsi": avg_score,
            "classification": classification
        })
        
        await db.execute(text("""
            UPDATE wsi_sessions SET status = 'completed', completed_at = CURRENT_TIMESTAMP
            WHERE id = :session_id
        """), {"session_id": request.session_id})
        
        await db.commit()
    except Exception as e:
        logger.warning(f"Failed to save result: {e}")
    
    # Create WSI Opinion after successful screening completion
    try:
        company_id = "demo_company"  # TODO: Get from request or context
        
        # Archive previous WSI opinions for same candidate/vacancy
        if request.job_vacancy_id:
            await db.execute(text("""
                UPDATE lia_opinions 
                SET is_current = false 
                WHERE candidate_id = :candidate_id 
                AND job_vacancy_id = :job_vacancy_id 
                AND opinion_type = 'wsi' 
                AND company_id = :company_id
                AND is_current = true
            """), {
                "candidate_id": request.candidate_id,
                "job_vacancy_id": request.job_vacancy_id,
                "company_id": company_id
            })
        
        # Get next version number
        version_result = await db.execute(text("""
            SELECT COALESCE(MAX(version), 0) + 1 as next_version
            FROM lia_opinions
            WHERE candidate_id = :candidate_id
            AND (job_vacancy_id = :job_vacancy_id OR (:job_vacancy_id IS NULL AND job_vacancy_id IS NULL))
            AND opinion_type = 'wsi'
            AND company_id = :company_id
        """), {
            "candidate_id": request.candidate_id,
            "job_vacancy_id": request.job_vacancy_id,
            "company_id": company_id
        })
        new_version = version_result.scalar() or 1
        
        # Determine recommendation based on score
        if avg_score >= 4.0:
            recommendation = "approved"
        elif avg_score >= 3.0:
            recommendation = "pending_review"
        else:
            recommendation = "not_approved"
        
        # Categorize recommendations into strengths, concerns, and gaps
        strengths = [r for r in recommendations if "sólido" in r.lower() or "demonstra" in r.lower()]
        concerns = [r for r in recommendations if "desenvolver" in r.lower() or "trabalhar" in r.lower()]
        gaps = [r for r in recommendations if "ganhar" in r.lower() or "experiência" in r.lower()]
        
        # Insert new WSI opinion
        opinion_id = str(uuid.uuid4())
        await db.execute(text("""
            INSERT INTO lia_opinions (
                id, candidate_id, job_vacancy_id, company_id, opinion_type, source,
                score, wsi_score, archetype, recommendation, summary, score_breakdown,
                strengths, concerns, gaps, matched_skills, missing_skills,
                next_steps, is_current, version, created_at, updated_at
            ) VALUES (
                :id, :candidate_id, :job_vacancy_id, :company_id, 'wsi', 'wsi_screening',
                :score, :wsi_score, :archetype, :recommendation, :summary, :score_breakdown::jsonb,
                :strengths::jsonb, :concerns::jsonb, :gaps::jsonb, :skills_match::jsonb, :skills_missing::jsonb,
                :next_steps::jsonb, true, :version, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
        """), {
            "id": opinion_id,
            "candidate_id": request.candidate_id,
            "job_vacancy_id": request.job_vacancy_id,
            "company_id": company_id,
            "score": round(avg_score, 2),
            "wsi_score": round(avg_score, 2),
            "archetype": archetypes[0].archetype if archetypes else "Perfil Equilibrado",
            "recommendation": recommendation,
            "summary": summary,
            "score_breakdown": json.dumps({
                "bloom_level": round(avg_bloom),
                "dreyfus_level": round(avg_dreyfus),
                "cognitive_score": round(avg_bloom / 6 * 100),
                "proficiency_score": round(avg_dreyfus / 5 * 100)
            }),
            "strengths": json.dumps(strengths),
            "concerns": json.dumps(concerns),
            "gaps": json.dumps(gaps),
            "skills_match": json.dumps([]),
            "skills_missing": json.dumps([]),
            "next_steps": json.dumps(recommendations),
            "version": new_version
        })
        
        await db.commit()
        logger.info(f"Created WSI opinion {opinion_id} for candidate {request.candidate_id}, vacancy {request.job_vacancy_id}")
        
    except Exception as e:
        logger.warning(f"Failed to create WSI opinion: {e}")
        # Don't fail the whole request - WSI result is still saved
    
    return CompleteScreeningResponse(
        result_id=result_id,
        candidate_id=request.candidate_id,
        job_vacancy_id=request.job_vacancy_id,
        overall_score=round(avg_score, 2),
        classification=classification,
        cognitive_level={
            "level": round(avg_bloom),
            "name": bloom_level_name["name"],
            "name_pt": bloom_level_name["name_pt"],
            "description": bloom_level_name["description"]
        },
        proficiency_level={
            "level": round(avg_dreyfus),
            "name": dreyfus_level_name["name"],
            "name_pt": dreyfus_level_name["name_pt"],
            "description": dreyfus_level_name["description"]
        },
        big_five_profile=avg_big_five,
        archetype_indicators=archetypes,
        summary=summary,
        recommendations=recommendations,
        response_analyses=response_analyses
    )


@router.get("/session/{session_id}")
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get WSI session details with questions and responses."""
    try:
        result = await db.execute(text("""
            SELECT id, candidate_id, job_vacancy_id, screening_type, mode, status, started_at, completed_at
            FROM wsi_sessions WHERE id = :session_id
        """), {"session_id": session_id})
        session = result.fetchone()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        questions_result = await db.execute(text("""
            SELECT id, competency, framework, question_type, question_text, weight
            FROM wsi_questions WHERE session_id = :session_id ORDER BY sequence_order
        """), {"session_id": session_id})
        questions = questions_result.fetchall()
        
        return {
            "session": {
                "id": session[0],
                "candidate_id": session[1],
                "job_vacancy_id": session[2],
                "screening_type": session[3],
                "mode": session[4],
                "status": session[5],
                "started_at": session[6].isoformat() if session[6] else None,
                "completed_at": session[7].isoformat() if session[7] else None
            },
            "questions": [
                {"id": q[0], "competency": q[1], "framework": q[2],
                 "question_type": q[3], "question_text": q[4], "weight": float(q[5])}
                for q in questions
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/{candidate_id}")
async def get_candidate_results(
    candidate_id: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get WSI results for a specific candidate."""
    try:
        result = await db.execute(text("""
            SELECT r.id, r.job_vacancy_id, r.overall_wsi, r.classification, r.created_at,
                   s.screening_type
            FROM wsi_results r
            JOIN wsi_sessions s ON r.session_id = s.id
            WHERE r.candidate_id = :candidate_id
            ORDER BY r.created_at DESC
            LIMIT :limit
        """), {"candidate_id": candidate_id, "limit": limit})
        
        results = result.fetchall()
        
        return {
            "candidate_id": candidate_id,
            "total_screenings": len(results),
            "results": [
                {
                    "result_id": r[0],
                    "job_vacancy_id": r[1],
                    "overall_score": float(r[2]),
                    "classification": r[3],
                    "created_at": r[4].isoformat() if r[4] else None,
                    "screening_type": r[5]
                }
                for r in results
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# WSI Interview Graph — entrevistas síncronas passo-a-passo
# ---------------------------------------------------------------------------

from app.services.interview_session_store import interview_session_store


class InterviewGraphStartRequest(BaseModel):
    candidate_id: str
    job_id: str
    company_id: str
    interview_level: str = Field(default="standard", pattern="^(quick|standard|full)$")


class InterviewGraphRespondRequest(BaseModel):
    response: str = Field(..., description="Resposta do candidato à pergunta atual")


@router.post("/interview-graph/sessions", summary="Inicia sessão de entrevista WSI síncrona")
async def start_interview_graph_session(
    request: InterviewGraphStartRequest,
    db: AsyncSession = Depends(get_db),
):
    """Cria uma nova sessão de entrevista WSI usando o WSIInterviewGraph.

    Carrega o contexto (vaga + candidato), gera o banco de perguntas e
    apresenta a primeira pergunta. Use `POST /interview-graph/sessions/{session_id}/respond`
    para cada resposta subsequente do candidato.
    """
    from app.domains.cv_screening.agents.wsi_interview_graph import wsi_interview_graph

    state = wsi_interview_graph.create_session(
        candidate_id=request.candidate_id,
        job_id=request.job_id,
        company_id=request.company_id,
        interview_level=request.interview_level,
    )

    # Pré-carrega contexto da vaga para o grafo (que não tem acesso direto ao DB)
    try:
        job_result = await db.execute(text("""
            SELECT title, description, seniority_level
            FROM job_vacancies WHERE id = :job_id AND company_id = :company_id
            LIMIT 1
        """), {"job_id": request.job_id, "company_id": request.company_id})
        job_row = job_result.fetchone()
        if job_row:
            state.job_requirements = {
                "title": job_row[0] or "",
                "description": job_row[1] or "",
                "seniority": job_row[2],
            }
    except Exception as exc:
        logger.warning(f"[WSIInterviewGraph] Failed to load job context: {exc}")

    state = await wsi_interview_graph.start(state)
    await interview_session_store.set(state.session_id, state)

    current_question = None
    if state.current_question:
        current_question = {
            "block_id": state.current_question.block_id,
            "block_type": state.current_question.block_type,
            "question": state.current_question.question,
            "competency": state.current_question.competency,
        }

    return {
        "session_id": state.session_id,
        "stage": state.stage.value,
        "is_complete": state.is_complete,
        "progress_pct": round(state.progress_pct, 1),
        "questions_total": len(state.question_blocks),
        "awaiting_response": state.awaiting_response,
        "current_question": current_question,
    }


@router.post(
    "/interview-graph/sessions/{session_id}/respond",
    summary="Envia resposta do candidato na entrevista WSI síncrona",
)
async def respond_interview_graph(session_id: str, request: InterviewGraphRespondRequest):
    """Processa a resposta do candidato, pontua e avança para a próxima pergunta.

    Retorna a próxima pergunta (se houver) ou o resultado final (se a entrevista encerrou).
    """
    from app.domains.cv_screening.agents.wsi_interview_graph import wsi_interview_graph

    state = await interview_session_store.get(session_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Sessão '{session_id}' não encontrada")

    state = await wsi_interview_graph.submit_response(state, request.response)
    await interview_session_store.set(session_id, state)

    next_question = None
    if state.current_question and state.awaiting_response:
        next_question = {
            "block_id": state.current_question.block_id,
            "block_type": state.current_question.block_type,
            "question": state.current_question.question,
            "competency": state.current_question.competency,
        }

    result = None
    if state.is_complete and state.wsi_final_score is not None:
        result = {
            "wsi_final_score": state.wsi_final_score,
            "recommendation": state.recommendation,
            "scores": {
                "technical": round(state.technical_score, 2),
                "behavioral": round(state.behavioral_score, 2),
                "situational": round(state.situational_score, 2),
                "eligibility": round(state.eligibility_score, 2),
            },
        }
        await interview_session_store.delete(session_id)

    return {
        "session_id": session_id,
        "stage": state.stage.value,
        "is_complete": state.is_complete,
        "progress_pct": round(state.progress_pct, 1),
        "awaiting_response": state.awaiting_response,
        "next_question": next_question,
        "result": result,
    }


@router.get(
    "/interview-graph/sessions/{session_id}",
    summary="Resumo auditável da sessão de entrevista WSI",
)
async def get_interview_graph_session(session_id: str):
    """Retorna o resumo completo da sessão para fins de auditoria e compliance."""
    from app.domains.cv_screening.agents.wsi_interview_graph import wsi_interview_graph

    state = await interview_session_store.get(session_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Sessão '{session_id}' não encontrada")

    return wsi_interview_graph.get_session_summary(state)
