"""
WSI package — shared imports, constants, models, and utility functions.
"""
import asyncio
import json
import logging
import os
from typing import Any

from pydantic import BaseModel, Field

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

from app.domains.cv_screening.constants.wsi_scale import (
    CLASSIFY_ABAIXO_MEDIA,
    CLASSIFY_ALTO,
    CLASSIFY_EXCELENTE,
    CLASSIFY_EXCEPCIONAL,
    CLASSIFY_MEDIO,
    SCALE_MAX,
)

WSI_CLASSIFICATION_MAP = {
    "excepcional":     {"label": "Excepcional",      "min_score": CLASSIFY_EXCEPCIONAL,  "color": "emerald-700"},
    "excelente":       {"label": "Excelente",         "min_score": CLASSIFY_EXCELENTE,    "color": "green-600"},
    "alto":            {"label": "Alto",               "min_score": CLASSIFY_ALTO,         "color": "blue-600"},
    "medio":           {"label": "Médio",              "min_score": CLASSIFY_MEDIO,        "color": "amber-600"},
    "abaixo_da_media": {"label": "Abaixo da média",   "min_score": CLASSIFY_ABAIXO_MEDIA, "color": "orange-600"},
    "regular":         {"label": "Regular / Baixo",   "min_score": 0.0,                   "color": "red-600"},
}


def classify_wsi_score(score: float) -> str:
    """Classifica o score WSI nos 6 níveis canônicos (spec Seção 9.5, escala /10)."""
    if score >= CLASSIFY_EXCEPCIONAL:
        return "excepcional"
    if score >= CLASSIFY_EXCELENTE:
        return "excelente"
    if score >= CLASSIFY_ALTO:
        return "alto"
    if score >= CLASSIFY_MEDIO:
        return "medio"
    if score >= CLASSIFY_ABAIXO_MEDIA:
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
    block_id: int | None = None
    category: str | None = None
    is_eliminatory: bool | None = False


class GenerateQuestionsRequest(BaseModel):
    job_vacancy_id: str | None = None
    company_id: str | None = None
    job_title: str | None = None
    requirements: list[str] | None = None
    skills: list[str] | None = None
    technical_skills: list[str] | None = None
    behavioral_competencies: list[str] | None = None
    responsibilities: list[str] | None = None
    seniority_level: str | None = "pleno"
    seniority: str | None = None
    department: str | None = None
    description: str | None = None
    num_questions: int = Field(default=5, ge=3, le=12)
    max_questions: int | None = None


class GenerateQuestionsResponse(BaseModel):
    session_id: str
    questions: list[WSIQuestionOutput]
    job_title: str | None
    methodology: str = "WSI (Bloom + Dreyfus + Big Five)"
    fairness_warnings: list[str] = Field(default_factory=list)
    fairness_blocked_count: int = 0


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
    score: float = Field(ge=0, le=10)  # Escala 0.0 – 10.0 (PR2 #497)
    score_max: float = 10.0
    score_normalized: float = 0.0
    star_completeness: float | None = None
    feedback: str
    evidences: list[str]
    red_flags: list[str]


class ResponseInput(BaseModel):
    question_id: str
    response_text: str


class CompleteScreeningRequest(BaseModel):
    session_id: str
    candidate_id: str
    job_vacancy_id: str | None = None
    responses: list[ResponseInput]


class ArchetypeIndicator(BaseModel):
    archetype: str
    match_score: int = Field(ge=0, le=100)
    description: str


class CompleteScreeningResponse(BaseModel):
    result_id: str
    candidate_id: str
    job_vacancy_id: str | None
    overall_score: float = Field(ge=0, le=10)
    classification: str
    cognitive_level: dict[str, Any]
    proficiency_level: dict[str, Any]
    big_five_profile: BigFiveIndicators
    archetype_indicators: list[ArchetypeIndicator]
    summary: str
    recommendations: list[str]
    response_analyses: list[AnalyzeResponseOutput]


class JDEvaluateRequest(BaseModel):
    job_title: str
    responsibilities: list[str] | None = None
    technical_skills: list[str] | None = None
    behavioral_competencies: list[str] | None = None
    seniority: str | None = None
    department: str | None = None
    description: str | None = None


class JDEvaluateResponse(BaseModel):
    success: bool = True
    score: int
    max_score: int = 100
    band: str
    band_label: str
    indicators: list[dict[str, Any]]
    lia_suggestion: str
    can_generate: bool
    details: dict[str, Any]


class SaveQuestionsRequest(BaseModel):
    job_id: str
    questions: list[dict[str, Any]]
    source: str | None = "manual"


class SuggestQuestionRequest(BaseModel):
    prompt: str
    job_title: str | None = None
    block_id: int | None = None
    technical_skills: list[str] | None = None
    behavioral_competencies: list[str] | None = None
    seniority: str | None = None
    description: str | None = None


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
# LLM factory helpers (Task #93 migration)
# ---------------------------------------------------------------------------

async def get_anthropic_client():
    """Returns a tenant-aware ProviderContainer via LLMProviderFactory.

    Reads company_id from AuthEnforcementMiddleware contextvar so BYOK
    key is respected. Falls back to platform defaults when no tenant set.
    """
    try:
        from app.shared.tenant_llm_context import get_current_llm_tenant
        tenant_id = get_current_llm_tenant()
        if tenant_id:
            from app.shared.providers.llm_factory import get_provider_for_tenant_from_db
            return await get_provider_for_tenant_from_db(tenant_id)
        from app.shared.providers.llm_factory import get_provider_for_tenant
        return get_provider_for_tenant()
    except Exception as e:
        logger.error(f"Failed to get LLM provider: {e}")
        return None


def parse_json_response(content: str, fallback: dict) -> dict:
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


class _FakeResponse:
    """Shim so callers can do response.content[0].text without refactoring."""
    def __init__(self, text: str):
        self.content = [type("Block", (), {"text": text})()]


async def _run_anthropic_sync(
    client, model: str, max_tokens: int, messages: list,
    timeout: float = 30.0, task_type: str = "chat",
):
    """
    MIGRATED: Now uses LLMProviderFactory instead of direct Anthropic SDK (Task #93).
    Returns a _FakeResponse shim so callers can still access response.content[0].text.
    task_type activates Quality Tier Guard — use "wsi" for screening analysis.
    """
    try:
        prompt = "\n".join(m.get("content", "") for m in messages if m.get("role") == "user")
        text = await asyncio.wait_for(
            client.generate_with_fallback(prompt, task_type=task_type),
            timeout=timeout,
        )
        return _FakeResponse(text)
    except TimeoutError:
        logger.warning(f"LLM call timed out after {timeout}s")
        return None
    except Exception as e:
        logger.error(f"LLM call failed: {type(e).__name__}: {e}")
        return None
