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
import asyncio
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
    1: {"name": "Remember", "name_pt": "Recordar", "description": "Recall facts and basic concepts"},
    2: {"name": "Understand", "name_pt": "Compreender", "description": "Explain ideas and concepts"},
    3: {"name": "Apply", "name_pt": "Aplicar", "description": "Use information in new situations"},
    4: {"name": "Analyze", "name_pt": "Analisar", "description": "Draw connections among ideas"},
    5: {"name": "Evaluate", "name_pt": "Avaliar", "description": "Justify decisions or positions"},
    6: {"name": "Create", "name_pt": "Criar", "description": "Produce new or original work"}
}

DREYFUS_LEVELS = {
    1: {"name": "Novice",            "name_pt": "Iniciante",     "description": "Follows rigid rules"},
    2: {"name": "Advanced Beginner", "name_pt": "Básico",        "description": "Recognizes situational aspects"},
    3: {"name": "Competent",         "name_pt": "Intermediário", "description": "Conscious planning, prioritization"},
    4: {"name": "Proficient",        "name_pt": "Avançado",      "description": "Holistic view, fluid adaptation"},
    5: {"name": "Expert",            "name_pt": "Especialista",  "description": "Deep intuition, transcends rules"}
}

BIG_FIVE_TRAITS = {
    "openness":          {"name": "Openness",          "name_pt": "Abertura a mudanças",       "high": "Curious, creative",         "low": "Conventional, routine-oriented"},
    "conscientiousness": {"name": "Conscientiousness", "name_pt": "Organização e disciplina",  "high": "Organized, disciplined",    "low": "Flexible, spontaneous"},
    "extraversion":      {"name": "Extraversion",      "name_pt": "Sociabilidade",             "high": "Outgoing, assertive",       "low": "Reserved, reflective"},
    "agreeableness":     {"name": "Agreeableness",     "name_pt": "Cooperação",                "high": "Cooperative, empathetic",   "low": "Competitive, independent"},
    "neuroticism":       {"name": "Neuroticism",        "name_pt": "Estabilidade emocional",   "high": "Sensitive, anxious",        "low": "Calm, resilient"},
}

WSI_CLASSIFICATION_MAP = {
    "excepcional":     {"label": "Excepcional",      "min_score": 4.5,  "color": "emerald-700"},
    "excelente":       {"label": "Excelente",         "min_score": 4.0,  "color": "green-600"},
    "alto":            {"label": "Alto",               "min_score": 3.5,  "color": "blue-600"},
    "medio":           {"label": "Médio",              "min_score": 3.0,  "color": "amber-600"},
    "abaixo_da_media": {"label": "Abaixo da média",   "min_score": 2.25, "color": "orange-600"},
    "regular":         {"label": "Regular / Baixo",   "min_score": 0.0,  "color": "red-600"},
}


def classify_wsi_score(score: float) -> str:
    """Classifica o score WSI nos 6 níveis canônicos (spec Seção 9.5, escala /5)."""
    if score >= 4.5:
        return "excepcional"
    if score >= 4.0:
        return "excelente"
    if score >= 3.5:
        return "alto"
    if score >= 3.0:
        return "medio"
    if score >= 2.25:
        return "abaixo_da_media"
    return "regular"


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
    score: float = Field(ge=0, le=5)  # Escala 0.0 – 5.0
    score_max: float = 5.0
    score_normalized: float = 0.0
    star_completeness: Optional[float] = None
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


async def _run_anthropic_sync(client, model: str, max_tokens: int, messages: list, timeout: float = 30.0):
    """
    Wraps synchronous Anthropic client.messages.create() in a thread pool executor
    to avoid blocking the FastAPI async event loop.
    Applies a hard timeout to prevent indefinite hangs.
    """
    loop = asyncio.get_event_loop()
    try:
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    messages=messages
                )
            ),
            timeout=timeout
        )
        return response
    except asyncio.TimeoutError:
        logger.warning(f"Anthropic call timed out after {timeout}s (model={model})")
        return None
    except Exception as e:
        logger.error(f"Anthropic call failed: {type(e).__name__}: {e}")
        return None



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
        
        response = await _run_anthropic_sync(
            client,
            model="claude-sonnet-4-6",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
            timeout=30.0
        )
        try:
            if response is None:
                raise ValueError("Anthropic call timed out or failed")
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
    band: str
    band_label: str
    indicators: List[Dict[str, Any]]
    lia_suggestion: str
    can_generate: bool
    details: Dict[str, Any]


_JD_SENIORITY_KEYWORDS = {
    "estagiario": ["estagiário", "estagiaria", "estágio", "trainee"],
    "junior": ["junior", "júnior", "jr"],
    "pleno": ["pleno", "pl"],
    "senior": ["sênior", "senior", "sr"],
    "lead": ["lead", "líder", "tech lead"],
    "principal": ["principal", "staff"],
    "diretor": ["diretor", "diretora", "director"],
    "vp": ["vp", "vice-presidente", "cxo", "cto", "cpo"],
}
_BIAS_TERMS = [
    "boa aparência", "apresentação pessoal", "jovem", "recém-formado",
    "native speaker", "universidades de primeira linha", "faculdade de ponta",
    "perfil adequado", "escola particular", "bairros nobres", "morar próximo",
    "boa família", "estado civil", "filho", "filha", "casado", "solteiro",
]
_JD_BANDS = [
    (85, "excelente",     "Excelente"),
    (70, "bom",           "Bom"),
    (50, "adequado",      "Adequado"),
    (30, "insuficiente",  "Insuficiente"),
    (0,  "critico",       "Crítico"),
]


def _jd_get_band(score: int):
    for threshold, band_key, band_label in _JD_BANDS:
        if score >= threshold:
            return band_key, band_label
    return "critico", "Crítico"


@router.post("/jd-evaluate")
async def evaluate_jd(request: JDEvaluateRequest):
    """Evaluate job description quality using 9 dimensions (spec F1.B).
    Hard block if score < 30 (band=Crítico). 5 quality bands."""
    resp_count   = len(request.responsibilities or [])
    tech_count   = len(request.technical_skills or [])
    behav_count  = len(request.behavioral_competencies or [])
    has_seniority = bool(request.seniority)
    desc = (request.description or "").lower()
    title = (request.job_title or "").lower()
    dept = (request.department or "")

    score = 0
    indicators = []

    title_has_seniority = any(
        kw in title
        for keywords in _JD_SENIORITY_KEYWORDS.values()
        for kw in keywords
    )
    pts_1 = 10 if (title_has_seniority or has_seniority) else 0
    score += pts_1
    indicators.append({
        "dimension": "D1",
        "label": "Clareza do título",
        "weight": 10,
        "earned": pts_1,
        "status": "sufficient" if pts_1 == 10 else "insufficient",
        "detail": f"{'Indicador de senioridade detectado' if pts_1 else 'Título sem indicador de senioridade'}",
    })

    if resp_count >= 5:
        pts_2 = 15
        st_2 = "sufficient"
    elif resp_count >= 2:
        pts_2 = 7
        st_2 = "partial"
    else:
        pts_2 = 0
        st_2 = "insufficient"
    score += pts_2
    indicators.append({
        "dimension": "D2",
        "label": "Responsabilidades",
        "weight": 15,
        "earned": pts_2,
        "count": resp_count,
        "minimum": 5,
        "status": st_2,
        "detail": f"{resp_count} responsabilidade(s) — mínimo ideal: 5",
    })

    # D3 — Spec Task #43: mínimo ideal = 9 skills técnicas para cobertura Full WSI
    _D3_MIN_IDEAL = 9
    if tech_count >= _D3_MIN_IDEAL:
        pts_3 = 15
        st_3 = "sufficient"
    elif tech_count >= 3:
        pts_3 = 7
        st_3 = "partial"
    else:
        pts_3 = 0
        st_3 = "insufficient"
    score += pts_3
    indicators.append({
        "dimension": "D3",
        "label": "Skills técnicas",
        "weight": 15,
        "earned": pts_3,
        "count": tech_count,
        "minimum": _D3_MIN_IDEAL,
        "status": st_3,
        "detail": f"{tech_count} skill(s) técnica(s) — mínimo ideal: {_D3_MIN_IDEAL}",
    })

    # D4 — Spec Task #43: mínimo ideal = 5 competências comportamentais (1 por trait Big Five)
    _D4_MIN_IDEAL = 5
    if behav_count >= _D4_MIN_IDEAL:
        pts_4 = 10
        st_4 = "sufficient"
    elif behav_count >= 2:
        pts_4 = 5
        st_4 = "partial"
    else:
        pts_4 = 0
        st_4 = "insufficient"
    score += pts_4
    indicators.append({
        "dimension": "D4",
        "label": "Comp. comportamentais",
        "weight": 10,
        "earned": pts_4,
        "count": behav_count,
        "minimum": _D4_MIN_IDEAL,
        "status": st_4,
        "detail": f"{behav_count} comportamental(is) — mínimo ideal: {_D4_MIN_IDEAL}",
    })

    if has_seniority and resp_count >= 3:
        pts_5 = 15
        st_5 = "sufficient"
    elif has_seniority or resp_count >= 2:
        pts_5 = 7
        st_5 = "partial"
    else:
        pts_5 = 0
        st_5 = "insufficient"
    score += pts_5
    indicators.append({
        "dimension": "D5",
        "label": "Consistência senioridade",
        "weight": 15,
        "earned": pts_5,
        "status": st_5,
        "detail": "Senioridade declarada com responsabilidades compatíveis" if pts_5 == 15 else "Senioridade ou responsabilidades insuficientes para calibração",
    })

    desc_words = len(desc.split()) if desc else 0
    has_contradiction = (
        ("autonomia" in desc and "aprovação" in desc) or
        ("independente" in desc and "acompanhamento diário" in desc)
    )
    pts_6 = 0 if has_contradiction else (10 if desc_words > 80 else 5)
    score += pts_6
    indicators.append({
        "dimension": "D6",
        "label": "Ausência de inconsistências",
        "weight": 10,
        "earned": pts_6,
        "status": "insufficient" if has_contradiction else ("sufficient" if pts_6 == 10 else "partial"),
        "detail": "Contradição detectada (autonomia vs. aprovação)" if has_contradiction else "Sem inconsistências detectadas",
    })

    has_context = bool(dept) or any(kw in desc for kw in ["empresa", "equipe", "time", "setor", "segmento", "startup", "corporati"])
    pts_7 = 10 if has_context else 0
    score += pts_7
    indicators.append({
        "dimension": "D7",
        "label": "Contexto organizacional",
        "weight": 10,
        "earned": pts_7,
        "status": "sufficient" if pts_7 == 10 else "insufficient",
        "detail": "Contexto de empresa/time/setor presente" if pts_7 else "Sem contexto organizacional (empresa, time, setor)",
    })

    found_bias = [t for t in _BIAS_TERMS if t in desc or t in title]
    pts_8 = 0 if found_bias else 10
    score += pts_8
    indicators.append({
        "dimension": "D8",
        "label": "Linguagem inclusiva",
        "weight": 10,
        "earned": pts_8,
        "status": "insufficient" if found_bias else "sufficient",
        "detail": f"Termo(s) de viés encontrado(s): {', '.join(found_bias[:3])}" if found_bias else "Linguagem neutra e inclusiva",
    })

    all_text = " ".join(filter(None, [
        request.description,
        " ".join(request.responsibilities or []),
        " ".join(request.technical_skills or []),
        " ".join(request.behavioral_competencies or []),
    ]))
    total_words = len(all_text.split())
    pts_9 = 5 if total_words >= 150 else 0
    score += pts_9
    indicators.append({
        "dimension": "D9",
        "label": "Densidade total",
        "weight": 5,
        "earned": pts_9,
        "word_count": total_words,
        "minimum": 150,
        "status": "sufficient" if pts_9 == 5 else "insufficient",
        "detail": f"{total_words} palavras — mínimo ideal: 150",
    })

    band_key, band_label = _jd_get_band(score)

    if score >= 85:
        suggestion = f"JD excelente para {request.job_title}. Perguntas WSI serão altamente calibradas com {tech_count} competências técnicas e {behav_count} comportamentais."
    elif score >= 70:
        suggestion = f"JD bem estruturado. Perguntas WSI geradas com boa qualidade. Recomenda-se enriquecer contexto organizacional para maximizar precisão."
    elif score >= 50:
        missing = []
        if resp_count < 5: missing.append(f"responsabilidades (tem {resp_count}, ideal ≥5)")
        if tech_count < 3: missing.append(f"skills técnicas (tem {tech_count}, ideal ≥3)")
        if behav_count < 2: missing.append(f"comportamentais (tem {behav_count}, ideal ≥2)")
        suggestion = f"JD adequado mas com lacunas. Melhore: {'; '.join(missing) or 'contexto e densidade'}."
    elif score >= 30:
        suggestion = "JD insuficiente para gerar perguntas de alta qualidade. Adicione responsabilidades detalhadas, skills técnicas específicas e senioridade."
    else:
        suggestion = "JD crítico — perguntas WSI bloqueadas. Adicione no mínimo: título com senioridade, 2+ responsabilidades, 1+ skill técnica e senioridade definida."

    if score < 30:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "qualidade_insuficiente",
                "message": suggestion,
                "score": score,
                "max_score": 100,
                "band": band_key,
                "band_label": band_label,
                "indicators": [i.dict() if hasattr(i, 'dict') else i for i in indicators],
                "can_generate": False,
            }
        )

    return JDEvaluateResponse(
        success=True,
        score=score,
        max_score=100,
        band=band_key,
        band_label=band_label,
        indicators=indicators,
        lia_suggestion=suggestion,
        can_generate=True,
        details={
            "responsibilities_count": resp_count,
            "technical_skills_count": tech_count,
            "behavioral_competencies_count": behav_count,
            "seniority_defined": has_seniority,
            "total_word_count": total_words,
            "has_context": has_context,
            "bias_terms_found": found_bias,
            "has_inconsistency": has_contradiction,
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

        response = await _run_anthropic_sync(
            client,
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
            timeout=30.0
        )
        try:
            if response is None:
                raise ValueError("Anthropic call timed out or failed")
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
    
    # Compute star_completeness: proportion of STAR elements present in response
    _star_keywords = [
        ["situação", "situacao", "situation", "contexto", "context"],
        ["tarefa", "task", "objetivo", "objetivo", "responsabilidade"],
        ["ação", "acao", "action", "fiz", "implementei", "desenvolvi", "criei"],
        ["resultado", "result", "outcome", "conquista", "entregamos", "consegui"],
    ]
    _resp_lower = request.response_text.lower()
    _found = sum(1 for group in _star_keywords if any(kw in _resp_lower for kw in group))
    star_completeness = round(_found / 4.0, 2)

    _score = data.get("score", 3.0)

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
        score=_score,
        score_max=5.0,
        score_normalized=round(_score / 5.0 * 10.0, 1),
        star_completeness=star_completeness,
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
    
    classification = classify_wsi_score(avg_score)
    
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
    
    class_label = WSI_CLASSIFICATION_MAP.get(classification, {}).get("label", classification)
    summary = (
        f"Candidato avaliado como {class_label} (Score: {avg_score:.1f}/5.0). "
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


# ─────────────────────────────────────────────────────────────────────────────
# F11 — RELATÓRIO COMPLETO DO CONSULTOR (spec sections 11.1–11.5)
# ─────────────────────────────────────────────────────────────────────────────

import hashlib
from datetime import datetime


class CBIQuestion(BaseModel):
    question_number: int
    area: str
    competencia_label: str
    gap_focus: str
    question_text: str
    bloom_target: int
    bloom_label: str
    dreyfus_target: int
    dreyfus_label: str
    expected_evidence: str
    red_flags: str


class GateStatus(BaseModel):
    g1_elegibilidade: bool
    g1_detail: str
    g2_prompt_injection: bool
    g2_detail: str
    g3_wsi_tecnico: bool
    g3_detail: str
    g4_skill_critica: bool
    g4_detail: str
    g5_engajamento: bool
    g5_detail: str
    g6_inflacao: bool
    g6_detail: str
    all_passed: bool
    failed_gates: List[str]


class F11ReportResponse(BaseModel):
    session_id: str
    result_id: Optional[str]
    candidate_name: str
    candidate_id: str
    job_title: str
    job_vacancy_id: Optional[str]
    seniority: Optional[str]
    mode: str
    screening_type: str
    duration_minutes: Optional[float]
    started_at: Optional[str]
    completed_at: Optional[str]
    overall_wsi: float
    technical_wsi: float
    behavioral_wsi: float
    classification: str
    classification_label: str
    gates: GateStatus
    decision_result: str
    decision_confidence: str
    decision_reason: Optional[str]
    human_review_required: bool = False
    already_generated: bool = False
    responses_hash: str
    response_analyses: List[Dict[str, Any]]
    interview_questions: List[CBIQuestion]
    strengths: List[str]
    gaps: List[Dict[str, Any]]
    question_count: int = 0
    seniority_weights: Optional[Dict[str, float]] = None
    attention_flags: List[str] = []
    generated_at: str
    methodology_version: str = "WSI v2.0"


_GATE_G3_THRESHOLD = 2.0   # /5 scale (= 4.0/10)
_GATE_G4_THRESHOLD = 1.5   # /5 scale (= 3.0/10)
_INJECTION_KEYWORDS = ["ignore", "esquece", "esqueça", "novo prompt", "sys:", "system:", "jailbreak", "prompt injection"]

_SENIORITY_WEIGHTS = {
    "estagiario": {"technical": 0.6875, "behavioral": 0.3125},
    "junior":     {"technical": 0.625,  "behavioral": 0.375},
    "pleno":      {"technical": 0.6875, "behavioral": 0.3125},
    "senior":     {"technical": 0.5625, "behavioral": 0.4375},
    "lead":       {"technical": 0.4375, "behavioral": 0.5625},
    "principal":  {"technical": 0.50,   "behavioral": 0.50},
    "diretor":    {"technical": 0.3125, "behavioral": 0.6875},
    "vp_clevel":  {"technical": 0.25,   "behavioral": 0.75},
}


def _get_seniority_weights(seniority: Optional[str]) -> Optional[Dict[str, float]]:
    if not seniority:
        return None
    key = seniority.lower().strip().replace(" ", "_")
    return _SENIORITY_WEIGHTS.get(key)


def _build_attention_flags(analyses: List[Dict], gates: GateStatus) -> List[str]:
    flags = []
    if gates.g1_eliminatory and gates.g1_eliminatory.get("passed") is False:
        flags.append("Questão eliminatória reprovada (G1)")
    if gates.g2_injection and gates.g2_injection.get("passed") is False:
        flags.append("Tentativa de prompt injection detectada (G2)")
    gap_count = sum(1 for a in analyses if a.get("gap_status") == "gap")
    if gap_count >= 3:
        flags.append(f"{gap_count} competências com gap identificado")
    low_star = sum(1 for a in analyses if sum(a.get("star", {}).values()) <= 1)
    if low_star >= 2:
        flags.append(f"{low_star} respostas com STAR incompleto")
    critical_gaps = [a for a in analyses if a.get("is_critical") and a.get("final_score", 5) < 3.0]
    if critical_gaps:
        flags.append(f"{len(critical_gaps)} competência(s) crítica(s) abaixo do esperado")
    return flags


def _compute_decision_confidence(
    overall_wsi: float,
    failed_gates: List[str],
    llm_fallback_count: int,
    score_variance: float,
) -> tuple:
    """F10-6 — Computa decision.confidence e human_review_required de forma determinística.

    Regras (ordem de precedência):
    1. baixa: G2 (prompt injection), ou ≥2 LLM fallbacks, ou variância de scores > 2.0
       → força human_review_required=True
    2. alta: aprovação clara (≥4.5/5, sem gates) OU rejeição clara por G1/G3/G4
    3. media: todo o resto (zona borderline, G5/G6 apenas, 1 fallback)

    Returns: (confidence: str, human_review_required: bool)
    """
    # Baixa — qualidade da triagem comprometida
    ambiguous_gates = {"G2", "G5", "G6"}
    clear_reject_gates = {"G1", "G3", "G4"}
    if (
        "G2" in failed_gates
        or llm_fallback_count >= 2
        or score_variance > 2.0
    ):
        return "baixa", True

    # Aprovação clara
    if overall_wsi >= 4.5 and not failed_gates:
        return "alta", False

    # Rejeição clara por gate não-ambíguo
    if failed_gates and clear_reject_gates.intersection(failed_gates) and not ambiguous_gates.intersection(failed_gates):
        return "alta", False

    # Zona borderline EM_AVALIACAO
    if 3.0 <= overall_wsi < 3.75:
        return "media", True

    # Aprovação sólida mas não excepcional
    if 3.75 <= overall_wsi < 4.5 and not failed_gates:
        return "media", False

    # Rejeição por gate ambíguo (G5/G6) — pode ser falso positivo
    if failed_gates and ambiguous_gates.issuperset(failed_gates):
        return "media", True

    return "media", overall_wsi < 3.75


async def _generate_cbi_questions_llm(
    gaps: List[Dict[str, Any]],
    strengths: List[str],
    previous_questions: List[str],
    seniority: str,
    job_title: str,
) -> List[CBIQuestion]:
    """Gera 2 perguntas CBI via LLM (temp=0.6, max_tokens=600, retry≤3). Spec 11.5."""
    import anthropic as _anthropic

    gaps_formatted = "\n".join(
        f"[{g.get('severity','MÉDIO')}] {g.get('competency','')} ({g.get('type','técnico')}) — score {g.get('score',0):.1f}/5 — sinais ausentes: {g.get('missing_signals','n/a')}"
        for g in gaps[:3]
    ) or "Nenhum gap crítico identificado — perguntas de aprofundamento"

    strengths_formatted = "\n".join(f"✓ {s}" for s in strengths[:2]) or "N/A"

    prev_qs_formatted = "\n".join(f"- {q}" for q in previous_questions[:5]) or "Nenhuma"

    bloom_expected = max((g.get("bloom_target", 3) for g in gaps[:1]), default=3)
    dreyfus_expected = max((g.get("dreyfus_target", 3) for g in gaps[:1]), default=3)
    bloom_lbl = BLOOM_LEVELS.get(bloom_expected, BLOOM_LEVELS[3])["name_pt"]
    dreyfus_lbl = DREYFUS_LEVELS.get(dreyfus_expected, DREYFUS_LEVELS[3])["name_pt"]

    system_prompt = (
        "Você é um especialista em entrevistas comportamentais estruturadas (CBI).\n"
        "Gere EXATAMENTE 2 perguntas para entrevista presencial com base nos gaps identificados na triagem.\n\n"
        "REGRAS:\n"
        "- Pergunta 1: foco no gap de MAIOR severidade (técnico ou comportamental)\n"
        "- Pergunta 2: foco no segundo maior gap — de tipo DIFERENTE do primeiro\n"
        "- Formato CBI-STAR: pedir situação real passada + ação + resultado\n"
        "- Linguagem NEUTRA em gênero: 'a pessoa candidata', 'você', 'o time' — sem pronomes binários\n"
        "- Cenários exclusivamente profissionais\n"
        "- Não repetir perguntas da triagem\n"
        "- Retorne JSON válido sem texto adicional\n"
    )

    user_prompt = f"""Senioridade da vaga: {seniority or 'Não especificada'}
Cargo: {job_title}
Bloom esperado: {bloom_expected} — {bloom_lbl}
Dreyfus esperado: {dreyfus_expected} — {dreyfus_lbl}

Gaps identificados (ALTO→MÉDIO→BAIXO):
{gaps_formatted}

Pontos fortes (não perguntar sobre estes):
{strengths_formatted}

Perguntas JÁ feitas na triagem (não repetir):
{prev_qs_formatted}

Retorne JSON:
{{
  "interview_questions": [
    {{
      "question_number": 1,
      "area": "technical",
      "competencia_label": "nome da competência",
      "gap_focus": "descrição do gap em 1 frase",
      "question_text": "pergunta completa pronta para o consultor ler",
      "bloom_target": 1-6,
      "bloom_label": "label Bloom",
      "dreyfus_target": 1-5,
      "dreyfus_label": "label Dreyfus",
      "expected_evidence": "2-3 comportamentos/ações esperados",
      "red_flags": "2-3 sinais de que o gap persiste"
    }},
    {{
      "question_number": 2,
      "area": "behavioral",
      "competencia_label": "nome da competência",
      "gap_focus": "descrição do gap em 1 frase",
      "question_text": "pergunta completa pronta para o consultor ler",
      "bloom_target": 1-6,
      "bloom_label": "label Bloom",
      "dreyfus_target": 1-5,
      "dreyfus_label": "label Dreyfus",
      "expected_evidence": "2-3 comportamentos/ações esperados",
      "red_flags": "2-3 sinais de que o gap persiste"
    }}
  ]
}}"""

    api_key = AI_INTEGRATIONS_ANTHROPIC_API_KEY
    base_url = AI_INTEGRATIONS_ANTHROPIC_BASE_URL

    if not api_key:
        logger.warning("F11: No Anthropic key — returning deterministic fallback questions")
        return _f11_fallback_questions(gaps)

    client = _anthropic.AsyncAnthropic(api_key=api_key, base_url=base_url)
    last_err = None

    for attempt in range(1, 4):
        try:
            msg = await client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=600,
                temperature=0.6,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            raw = msg.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw)
            qs = data.get("interview_questions", [])
            if len(qs) >= 2:
                q1_area = qs[0].get("area", "technical")
                q2_area = qs[1].get("area", "behavioral")
                if q1_area == q2_area and attempt < 3:
                    logger.info(f"F11 CBI attempt {attempt}: both questions are '{q1_area}', retrying for type alternation")
                    continue
                result = []
                for q in qs[:2]:
                    result.append(CBIQuestion(
                        question_number=q.get("question_number", len(result) + 1),
                        area=q.get("area", "technical"),
                        competencia_label=q.get("competencia_label", ""),
                        gap_focus=q.get("gap_focus", ""),
                        question_text=q.get("question_text", ""),
                        bloom_target=int(q.get("bloom_target", 3)),
                        bloom_label=q.get("bloom_label", "Aplicar"),
                        dreyfus_target=int(q.get("dreyfus_target", 3)),
                        dreyfus_label=q.get("dreyfus_label", "Intermediário"),
                        expected_evidence=q.get("expected_evidence", ""),
                        red_flags=q.get("red_flags", ""),
                    ))
                return result
        except Exception as e:
            last_err = e
            logger.warning(f"F11 CBI generation attempt {attempt}/3 failed: {e}")

    logger.error(f"F11: All 3 LLM attempts failed ({last_err}) — returning deterministic fallback")
    return _f11_fallback_questions(gaps)


def _f11_fallback_questions(gaps: List[Dict[str, Any]]) -> List[CBIQuestion]:
    """Fallback determinístico quando LLM falha 3x. Spec 11.5 edge case."""
    types = ["technical", "behavioral"]
    result = []
    used_types: set = set()
    for i, gap in enumerate(gaps[:3]):
        area = gap.get("type", "technical")
        if area in used_types:
            area = "behavioral" if area == "technical" else "technical"
        used_types.add(area)
        competency = gap.get("competency", f"Competência {i+1}")
        result.append(CBIQuestion(
            question_number=i + 1,
            area=area,
            competencia_label=competency,
            gap_focus=f"Aprofundar evidências sobre {competency}",
            question_text=f"Descreva uma situação passada em que você precisou demonstrar {competency}. Qual foi a ação que tomou e qual foi o resultado?",
            bloom_target=3,
            bloom_label="Aplicar",
            dreyfus_target=3,
            dreyfus_label="Intermediário",
            expected_evidence=f"Situação concreta, ação clara e resultado mensurável em {competency}",
            red_flags=f"Resposta vaga ou hipotética sobre {competency}",
        ))
        if len(result) == 2:
            break

    while len(result) < 2:
        result.append(CBIQuestion(
            question_number=len(result) + 1,
            area="behavioral",
            competencia_label="Resolução de problemas",
            gap_focus="Avaliar capacidade geral de resolução de problemas",
            question_text="Descreva uma situação desafiadora que você enfrentou no trabalho. Qual foi a ação que tomou e qual foi o resultado?",
            bloom_target=4,
            bloom_label="Analisar",
            dreyfus_target=3,
            dreyfus_label="Intermediário",
            expected_evidence="Situação real, raciocínio estruturado, resultado concreto",
            red_flags="Resposta vaga, ausência de resultado ou situação hipotética",
        ))
    return result[:2]


@router.get("/f11-report/{session_id}", summary="F11 — Relatório completo do consultor WSI")
async def get_f11_report(session_id: str, db: AsyncSession = Depends(get_db)):
    """Gera o relatório completo F11 para uma sessão WSI concluída.

    Inclui: G1-G6 gates, SHA-256 das respostas brutas, 2 perguntas CBI para
    entrevista presencial (LLM temp=0.6, retry≤3) e decisão estruturada.
    Spec: WSI_METHODOLOGY_COMPLETE_v2.md sections 11.1–11.5.
    """
    try:
        # F11-3 — garantir que a coluna de cache existe (idempotente)
        try:
            await db.execute(text(
                "ALTER TABLE wsi_results ADD COLUMN IF NOT EXISTS f11_report_json JSONB"
            ))
            await db.commit()
        except Exception:
            await db.rollback()

        # F11-3 — verificar cache antes de regenerar
        cache_r = await db.execute(text("""
            SELECT f11_report_json FROM wsi_results
            WHERE session_id = :sid AND f11_report_json IS NOT NULL
            ORDER BY created_at DESC LIMIT 1
        """), {"sid": session_id})
        cached = cache_r.fetchone()
        if cached and cached[0]:
            report = F11ReportResponse(**cached[0])
            report.already_generated = True
            return report

        sess_r = await db.execute(text("""
            SELECT s.id, s.candidate_id, s.job_vacancy_id, s.screening_type, s.mode,
                   s.status, s.started_at, s.completed_at,
                   c.name AS candidate_name,
                   j.title AS job_title, j.seniority_level
            FROM wsi_sessions s
            LEFT JOIN candidates c ON c.id = s.candidate_id
            LEFT JOIN job_vacancies j ON j.id = s.job_vacancy_id
            WHERE s.id = :sid
        """), {"sid": session_id})
        session = sess_r.fetchone()
        if not session:
            raise HTTPException(status_code=404, detail="Sessão WSI não encontrada")

        (sid, cand_id, jv_id, screening_type, mode, status,
         started_at, completed_at, candidate_name, job_title, seniority) = session

        res_r = await db.execute(text("""
            SELECT id, technical_wsi, behavioral_wsi, overall_wsi, classification
            FROM wsi_results WHERE session_id = :sid ORDER BY created_at DESC LIMIT 1
        """), {"sid": session_id})
        result_row = res_r.fetchone()

        if result_row:
            result_id, tech_wsi, behav_wsi, overall_wsi, classification = result_row
            result_id = str(result_id)
            tech_wsi = float(tech_wsi)
            behav_wsi = float(behav_wsi)
            overall_wsi = float(overall_wsi)
        else:
            result_id = None
            tech_wsi = behav_wsi = overall_wsi = 0.0
            classification = "regular"

        classification_label = WSI_CLASSIFICATION_MAP.get(classification, {}).get("label", classification)

        qs_r = await db.execute(text("""
            SELECT id, competency, framework, question_type, question_text, weight, sequence_order,
                   scoring_criteria
            FROM wsi_questions WHERE session_id = :sid ORDER BY sequence_order
        """), {"sid": session_id})
        questions = qs_r.fetchall()

        ana_r = await db.execute(text("""
            SELECT ra.id, ra.question_id, ra.competency, ra.response_text,
                   ra.autodeclaration_score, ra.context_score, ra.bloom_level, ra.dreyfus_level,
                   ra.evidences, ra.red_flags, ra.consistency_penalty, ra.final_score, ra.justification
            FROM wsi_response_analyses ra
            WHERE ra.session_id = :sid
        """), {"sid": session_id})
        analyses = ana_r.fetchall()

        responses_hash = hashlib.sha256(
            "".join(a[3] or "" for a in analyses).encode("utf-8")
        ).hexdigest()

        q_map = {str(q[0]): q for q in questions}

        analyses_list = []
        for a in analyses:
            (a_id, q_id, competency, resp_text, auto_score, ctx_score,
             bloom_lv, dreyfus_lv, evidences, red_flags, cons_pen, final_score, justification) = a
            q = q_map.get(str(q_id), None)
            bloom_info  = BLOOM_LEVELS.get(bloom_lv or 3, BLOOM_LEVELS[3])
            dreyfus_info = DREYFUS_LEVELS.get(dreyfus_lv or 3, DREYFUS_LEVELS[3])

            q_scoring = (q[7] if q and q[7] else {}) or {}
            if isinstance(q_scoring, str):
                import json as _json
                try:
                    q_scoring = _json.loads(q_scoring)
                except Exception:
                    q_scoring = {}
            q_bloom_expected = int(q_scoring.get("bloom_level", q_scoring.get("expected_bloom", bloom_lv or 3)))
            q_dreyfus_expected = int(q_scoring.get("dreyfus_level", q_scoring.get("expected_dreyfus", dreyfus_lv or 3)))
            # G4: usar campo estruturado is_critical de scoring_criteria (spec WSI F8);
            # fallback para weight >= 1.5 em sessões antigas sem o campo.
            if q and q_scoring.get("is_critical") is not None:
                q_is_critical = bool(q_scoring["is_critical"])
            else:
                q_is_critical = float(q[5]) >= 1.5 if q else False

            bloom_exp_info = BLOOM_LEVELS.get(q_bloom_expected, BLOOM_LEVELS[3])
            dreyfus_exp_info = DREYFUS_LEVELS.get(q_dreyfus_expected, DREYFUS_LEVELS[3])

            demonstrated_bloom = bloom_lv or 3
            demonstrated_dreyfus = dreyfus_lv or 3
            if demonstrated_bloom > q_bloom_expected and demonstrated_dreyfus >= q_dreyfus_expected:
                gap_status = "acima"
            elif demonstrated_bloom < q_bloom_expected or demonstrated_dreyfus < q_dreyfus_expected:
                gap_status = "gap"
            else:
                gap_status = "ok"

            resp_lower = (resp_text or "").lower()
            star_s = any(kw in resp_lower for kw in ["contexto", "situação", "cenário", "quando", "empresa", "projeto"])
            star_t = any(kw in resp_lower for kw in ["objetivo", "tarefa", "desafio", "responsabilidade", "missão", "meta"])
            star_a = any(kw in resp_lower for kw in ["implementei", "desenvolvi", "criei", "resolvi", "apliquei", "fiz", "liderei"])
            star_r = any(kw in resp_lower for kw in ["resultado", "impacto", "melhoria", "redução", "aumento", "uptime", "%", "kpi"])

            analyses_list.append({
                "analysis_id": str(a_id),
                "question_id": str(q_id),
                "competency": competency,
                "question_text": q[4] if q else "",
                "question_type": q[3] if q else "technical",
                "framework": q[2] if q else "",
                "weight": float(q[5]) if q else 1.0,
                "is_critical": q_is_critical,
                "response_text": resp_text or "",
                "response_word_count": len((resp_text or "").split()),
                "autodeclaration_score": float(auto_score) if auto_score else 0.0,
                "context_score": float(ctx_score) if ctx_score else 0.0,
                "bloom_level": demonstrated_bloom,
                "bloom_label": bloom_info["name_pt"],
                "bloom_expected": q_bloom_expected,
                "bloom_expected_label": bloom_exp_info["name_pt"],
                "dreyfus_level": demonstrated_dreyfus,
                "dreyfus_label": dreyfus_info["name_pt"],
                "dreyfus_expected": q_dreyfus_expected,
                "dreyfus_expected_label": dreyfus_exp_info["name_pt"],
                "gap_status": gap_status,
                "star": {"S": star_s, "T": star_t, "A": star_a, "R": star_r},
                "evidences": evidences or [],
                "red_flags": red_flags or [],
                "consistency_penalty": float(cons_pen) if cons_pen else 0.0,
                "final_score": float(final_score) if final_score else 0.0,
                "justification": justification or "",
            })

        g1_failed = any(
            a["question_type"] == "eligibility" and a["final_score"] == 0.0
            for a in analyses_list
        )
        injection_count = sum(
            1 for a in analyses_list
            if any(kw in (a.get("response_text") or "").lower() for kw in _INJECTION_KEYWORDS)
        )
        # G2: spec WSI — 1 tentativa de injeção já é suficiente para reprovar (era 2)
        g2_failed = injection_count >= 1

        g3_failed = tech_wsi < _GATE_G3_THRESHOLD and tech_wsi > 0.0

        # G4: verificar campo estruturado is_critical (lido de scoring_criteria["is_critical"])
        g4_failed = any(
            a["final_score"] < _GATE_G4_THRESHOLD and a["final_score"] > 0.0
            and a.get("is_critical", False)
            for a in analyses_list
        )

        short_responses = sum(1 for a in analyses_list if a["response_word_count"] < 30)
        total_qs = len(analyses_list)
        g5_failed = (total_qs > 0) and (short_responses / total_qs >= 0.5)

        # G6 — usa flags_structured["is_inflation"] (campo estruturado) quando disponível;
        # fallback para busca em string para retrocompatibilidade com sessões antigas.
        inflation_count = sum(
            1 for a in analyses_list
            if (
                (a.get("flags_structured") or {}).get("is_inflation", False)
                or any(
                    "inflação" in str(rf).lower() or "inflation" in str(rf).lower()
                    for rf in (a.get("red_flags") or [])
                )
            )
        )
        g6_failed = inflation_count >= 3

        failed_gates = []
        if g1_failed: failed_gates.append("G1")
        if g2_failed: failed_gates.append("G2")
        if g3_failed: failed_gates.append("G3")
        if g4_failed: failed_gates.append("G4")
        if g5_failed: failed_gates.append("G5")
        if g6_failed: failed_gates.append("G6")

        gates = GateStatus(
            g1_elegibilidade=not g1_failed,
            g1_detail="Elegibilidade confirmada" if not g1_failed else "Requisito de elegibilidade não atendido",
            g2_prompt_injection=not g2_failed,
            g2_detail=f"{injection_count} tentativa(s) de manipulação detectada(s)" if g2_failed else "Sem injeção de prompt detectada",
            g3_wsi_tecnico=not g3_failed,
            g3_detail=f"WSI Técnico {tech_wsi:.2f}/5 {'< limiar 2.0 — reprovado' if g3_failed else '≥ limiar 2.0 — aprovado'}",
            g4_skill_critica=not g4_failed,
            g4_detail="Skill crítica com score abaixo do mínimo absoluto" if g4_failed else "Nenhuma skill crítica abaixo do mínimo",
            g5_engajamento=not g5_failed,
            g5_detail=f"{short_responses}/{total_qs} respostas com < 30 palavras {'— engajamento insuficiente' if g5_failed else '— engajamento adequado'}",
            g6_inflacao=not g6_failed,
            g6_detail=f"{inflation_count} resposta(s) com inflação detectada" if g6_failed else "Sem padrão de inflação sistemática",
            all_passed=len(failed_gates) == 0,
            failed_gates=failed_gates,
        )

        # F10-6 — variância de scores (input para confidence)
        all_scores = [a["final_score"] for a in analyses_list if a["final_score"] > 0]
        score_variance = (max(all_scores) - min(all_scores)) if len(all_scores) >= 2 else 0.0
        llm_fallback_count = sum(
            1 for a in analyses_list
            if (a.get("flags_structured") or {}).get("_llm_fallback", False)
        )

        gate_labels = {
            "G1": "elegibilidade", "G2": "injeção de prompt",
            "G3": "competência técnica mínima", "G4": "skill crítica",
            "G5": "engajamento insuficiente", "G6": "inflação sistemática",
        }
        if len(failed_gates) > 0:
            decision_result = "REPROVADO"
            gate_reasons = [gate_labels.get(g, g) for g in failed_gates]
            decision_reason = f"Gate(s) ativado(s): {', '.join(gate_reasons)}"
        elif overall_wsi >= 3.75:
            decision_result = "APROVADO"
            decision_reason = None
        elif overall_wsi >= 3.0:
            decision_result = "EM_AVALIACAO"
            decision_reason = f"Score WSI {overall_wsi:.2f}/5 requer revisão humana (faixa 3.0–3.74)"
        else:
            decision_result = "REPROVADO"
            decision_reason = f"Score WSI {overall_wsi:.2f}/5 abaixo do mínimo (< 3.0)"

        # F10-6 — confidence determinística (substitui hardcoded "alta")
        decision_confidence, human_review_required = _compute_decision_confidence(
            overall_wsi=overall_wsi,
            failed_gates=failed_gates,
            llm_fallback_count=llm_fallback_count,
            score_variance=score_variance,
        )

        sorted_analyses = sorted(analyses_list, key=lambda x: x["final_score"], reverse=True)
        strengths = [
            f"{a['competency']} — {a['final_score']:.1f}/5"
            for a in sorted_analyses[:3]
            if a["final_score"] >= 3.5
        ]

        gap_items = [
            a for a in sorted_analyses if a["final_score"] < 3.0 and a["final_score"] > 0.0
        ]
        gap_items.sort(key=lambda x: x["final_score"])
        gaps = []
        for a in gap_items[:3]:
            delta = 3.0 - a["final_score"]
            severity = "ALTO" if delta >= 1.5 else ("MÉDIO" if delta >= 0.75 else "BAIXO")
            gaps.append({
                "competency": a["competency"],
                "type": a["question_type"],
                "score": a["final_score"],
                "delta": round(delta, 2),
                "severity": severity,
                "missing_signals": ", ".join(str(rf) for rf in (a.get("red_flags") or [])[:2]) or "n/a",
                "bloom_target": a["bloom_level"],
                "dreyfus_target": a["dreyfus_level"],
            })

        previous_questions = [a["question_text"] for a in analyses_list if a["question_text"]]
        interview_questions = await _generate_cbi_questions_llm(
            gaps=gaps,
            strengths=strengths,
            previous_questions=previous_questions,
            seniority=str(seniority or ""),
            job_title=str(job_title or ""),
        )

        duration_minutes = None
        if started_at and completed_at:
            diff = (completed_at - started_at).total_seconds() / 60
            duration_minutes = round(diff, 1)

        report = F11ReportResponse(
            session_id=str(sid),
            result_id=result_id,
            candidate_name=candidate_name or "Candidato",
            candidate_id=str(cand_id),
            job_title=job_title or "Vaga",
            job_vacancy_id=str(jv_id) if jv_id else None,
            seniority=str(seniority) if seniority else None,
            mode=mode or "compact",
            screening_type=screening_type or "text",
            duration_minutes=duration_minutes,
            started_at=started_at.isoformat() if started_at else None,
            completed_at=completed_at.isoformat() if completed_at else None,
            overall_wsi=round(overall_wsi, 3),
            technical_wsi=round(tech_wsi, 3),
            behavioral_wsi=round(behav_wsi, 3),
            classification=classification,
            classification_label=classification_label,
            gates=gates,
            decision_result=decision_result,
            decision_confidence=decision_confidence,
            decision_reason=decision_reason,
            human_review_required=human_review_required,
            responses_hash=responses_hash,
            response_analyses=analyses_list,
            interview_questions=interview_questions,
            strengths=strengths,
            gaps=gaps,
            question_count=len(questions),
            seniority_weights=_get_seniority_weights(str(seniority) if seniority else None),
            attention_flags=_build_attention_flags(analyses_list, gates),
            generated_at=datetime.utcnow().isoformat() + "Z",
        )

        # F11-3 — persistir no cache para evitar re-geração
        if result_id:
            try:
                import json as _json
                await db.execute(text("""
                    UPDATE wsi_results SET f11_report_json = :payload
                    WHERE id = :rid
                """), {"rid": result_id, "payload": _json.dumps(report.model_dump())})
                await db.commit()
            except Exception as _cache_err:
                logger.warning(f"F11-3: falha ao persistir cache do relatório: {_cache_err}")
                await db.rollback()

        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"F11 report generation failed for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao gerar relatório F11: {str(e)}")


# ---------------------------------------------------------------------------
# F11-6 — Ranking e Comparativo entre candidatos (Tab 3)
# ---------------------------------------------------------------------------

@router.get("/ranking/{job_vacancy_id}", summary="F11-6 — Ranking de candidatos por vaga")
async def get_vacancy_ranking(
    job_vacancy_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retorna o ranking completo de candidatos triados para uma vaga.

    Spec: WSI_METHODOLOGY_COMPLETE_v2.md §11.6.4 Tab 3.
    Ordena por overall_wsi DESC e calcula rank, percentil e médias do pool.
    """
    try:
        rows_r = await db.execute(text("""
            SELECT
                r.id            AS result_id,
                r.candidate_id,
                COALESCE(c.name, 'Candidato') AS candidate_name,
                COALESCE(c.current_position, '') AS candidate_title,
                r.overall_wsi,
                r.technical_wsi,
                r.behavioral_wsi,
                r.classification,
                s.screening_type,
                r.created_at
            FROM wsi_results r
            LEFT JOIN wsi_sessions s ON s.id = r.session_id
            LEFT JOIN candidates c   ON c.id::text = r.candidate_id
            WHERE r.job_vacancy_id = :jv_id
            ORDER BY r.overall_wsi DESC, r.created_at DESC
        """), {"jv_id": job_vacancy_id})
        rows = rows_r.fetchall()

        if not rows:
            return {
                "job_vacancy_id": job_vacancy_id,
                "total_screened": 0,
                "averages": {"overall": 0.0, "technical": 0.0, "behavioral": 0.0},
                "ranking": [],
            }

        total = len(rows)
        overall_vals  = [float(r[4]) for r in rows]
        tech_vals     = [float(r[5]) for r in rows]
        behav_vals    = [float(r[6]) for r in rows]

        ranking = []
        for rank, row in enumerate(rows, start=1):
            score = float(row[4])
            # percentil: proporção de candidatos com score ≤ score deste
            below_or_eq = sum(1 for v in overall_vals if v <= score)
            percentile = round((below_or_eq / total) * 100)
            ranking.append({
                "rank": rank,
                "total": total,
                "result_id": str(row[0]),
                "candidate_id": str(row[1]),
                "candidate_name": row[2],
                "candidate_title": row[3],
                "overall_wsi": round(score * 2, 2),        # /5 → /10
                "technical_wsi": round(float(row[5]) * 2, 2),
                "behavioral_wsi": round(float(row[6]) * 2, 2),
                "classification": row[7] or "regular",
                "percentile": percentile,
                "screening_type": row[8] or "text",
                "created_at": row[9].isoformat() if row[9] else None,
            })

        return {
            "job_vacancy_id": job_vacancy_id,
            "total_screened": total,
            "averages": {
                "overall":    round(sum(overall_vals) / total * 2, 2),
                "technical":  round(sum(tech_vals) / total * 2, 2),
                "behavioral": round(sum(behav_vals) / total * 2, 2),
            },
            "ranking": ranking,
        }
    except Exception as e:
        logger.error(f"F11-6 vacancy ranking failed for {job_vacancy_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/candidate/{candidate_id}/ranking/{job_vacancy_id}",
    summary="F11-6 — Posição do candidato no ranking da vaga",
)
async def get_candidate_ranking(
    candidate_id: str,
    job_vacancy_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retorna a posição do candidato no ranking da vaga (rank #N de M).

    Spec: WSI_METHODOLOGY_COMPLETE_v2.md §11.6.4 Tab 3.
    """
    try:
        # Busca o resultado mais recente do candidato para esta vaga
        cand_r = await db.execute(text("""
            SELECT id, overall_wsi FROM wsi_results
            WHERE candidate_id = :cid AND job_vacancy_id = :jv_id
            ORDER BY created_at DESC LIMIT 1
        """), {"cid": candidate_id, "jv_id": job_vacancy_id})
        cand_row = cand_r.fetchone()

        if not cand_row:
            return {"candidate_id": candidate_id, "job_vacancy_id": job_vacancy_id, "ranked": False}

        cand_score = float(cand_row[1])

        # Total de candidatos e posição
        total_r = await db.execute(text("""
            SELECT COUNT(*), SUM(CASE WHEN overall_wsi > :score THEN 1 ELSE 0 END)
            FROM wsi_results WHERE job_vacancy_id = :jv_id
        """), {"jv_id": job_vacancy_id, "score": cand_score})
        total_row = total_r.fetchone()
        total = int(total_row[0]) if total_row else 1
        above  = int(total_row[1] or 0) if total_row else 0
        rank   = above + 1  # rank 1 = melhor

        return {
            "candidate_id": candidate_id,
            "job_vacancy_id": job_vacancy_id,
            "ranked": True,
            "rank": rank,
            "total": total,
            "overall_wsi": round(cand_score * 2, 2),
        }
    except Exception as e:
        logger.error(f"F11-6 candidate ranking failed for {candidate_id}/{job_vacancy_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
