"""
WSI package — shared imports, constants, models, and utility functions.
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
from app.domains.cv_screening.services.screening_question_set_service import screening_question_set_service

logger = logging.getLogger(__name__)

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


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

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


class SaveQuestionsRequest(BaseModel):
    job_id: str
    questions: List[Dict[str, Any]]
    source: Optional[str] = "manual"


class SuggestQuestionRequest(BaseModel):
    prompt: str
    job_title: Optional[str] = None
    block_id: Optional[int] = None
    technical_skills: Optional[List[str]] = None
    behavioral_competencies: Optional[List[str]] = None
    seniority: Optional[str] = None
    description: Optional[str] = None


# ---------------------------------------------------------------------------
# JD evaluate constants
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Anthropic client helpers
# ---------------------------------------------------------------------------

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
