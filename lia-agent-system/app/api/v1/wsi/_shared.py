"""
WSI package — shared imports, constants, models, and utility functions.
"""

import asyncio
import json
import logging
import os
from typing import Any

from pydantic import BaseModel, Field
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

AI_INTEGRATIONS_ANTHROPIC_API_KEY = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY")
AI_INTEGRATIONS_ANTHROPIC_BASE_URL = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL")


BLOOM_LEVELS = {
    1: {"name": "Remember", "name_pt": "Recordar", "description": "Recall facts and basic concepts"},
    2: {"name": "Understand", "name_pt": "Compreender", "description": "Explain ideas and concepts"},
    3: {"name": "Apply", "name_pt": "Aplicar", "description": "Use information in new situations"},
    4: {"name": "Analyze", "name_pt": "Analisar", "description": "Draw connections among ideas"},
    5: {"name": "Evaluate", "name_pt": "Avaliar", "description": "Justify decisions or positions"},
    6: {"name": "Create", "name_pt": "Criar", "description": "Produce new or original work"},
}

DREYFUS_LEVELS = {
    1: {"name": "Novice", "name_pt": "Iniciante", "description": "Follows rigid rules"},
    2: {"name": "Advanced Beginner", "name_pt": "Básico", "description": "Recognizes situational aspects"},
    3: {"name": "Competent", "name_pt": "Intermediário", "description": "Conscious planning, prioritization"},
    4: {"name": "Proficient", "name_pt": "Avançado", "description": "Holistic view, fluid adaptation"},
    5: {"name": "Expert", "name_pt": "Especialista", "description": "Deep intuition, transcends rules"},
}

BIG_FIVE_TRAITS = {
    "openness": {
        "name": "Openness",
        "name_pt": "Abertura a mudanças",
        "high": "Curious, creative",
        "low": "Conventional, routine-oriented",
    },
    "conscientiousness": {
        "name": "Conscientiousness",
        "name_pt": "Organização e disciplina",
        "high": "Organized, disciplined",
        "low": "Flexible, spontaneous",
    },
    "extraversion": {
        "name": "Extraversion",
        "name_pt": "Sociabilidade",
        "high": "Outgoing, assertive",
        "low": "Reserved, reflective",
    },
    "agreeableness": {
        "name": "Agreeableness",
        "name_pt": "Cooperação",
        "high": "Cooperative, empathetic",
        "low": "Competitive, independent",
    },
    "neuroticism": {
        "name": "Neuroticism",
        "name_pt": "Estabilidade emocional",
        "high": "Sensitive, anxious",
        "low": "Calm, resilient",
    },
}

WSI_CLASSIFICATION_MAP = {
    "excepcional": {"label": "Excepcional", "min_score": 4.5, "color": "emerald-700"},
    "excelente": {"label": "Excelente", "min_score": 4.0, "color": "green-600"},
    "alto": {"label": "Alto", "min_score": 3.5, "color": "blue-600"},
    "medio": {"label": "Médio", "min_score": 3.0, "color": "amber-600"},
    "abaixo_da_media": {"label": "Abaixo da média", "min_score": 2.25, "color": "orange-600"},
    "regular": {"label": "Regular / Baixo", "min_score": 0.0, "color": "red-600"},
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
    block_id: int | None = None
    category: str | None = None
    is_eliminatory: bool | None = False


class GenerateQuestionsRequest(WeDoBaseModel):
    job_vacancy_id: str | None = None
    candidate_id: str | None = None  # Onda 2.2 fix (2026-05-23)
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


class BigFiveIndicators(BaseModel):
    """Big Five traits as int 0-100.

    Phase 2.5 boy-scout (A5): the canonical trait taxonomy in this codebase
    is OPENNESS / CONSCIENTIOUSNESS / EXTRAVERSION / AGREEABLENESS / STABILITY
    (see ALLOWED_TRAITS in app/domains/job_creation/services/bigfive_service.py:34).
    The historical `neuroticism` field name (its INVERSE) lives on for
    backward compatibility with the orphan /wsi/evaluate endpoint and the
    /big-five/* routes; new code MUST consume `.stability` (the computed
    inverse) instead. Future cleanup: rename the field after callers
    migrate.
    """
    openness: int = Field(ge=0, le=100, description="Curiosity, creativity, openness to new experiences")
    conscientiousness: int = Field(ge=0, le=100, description="Organization, discipline, goal-orientation")
    extraversion: int = Field(ge=0, le=100, description="Sociability, assertiveness, energy")
    agreeableness: int = Field(ge=0, le=100, description="Cooperation, empathy, teamwork")
    neuroticism: int = Field(
        ge=0,
        le=100,
        description=(
            "DEPRECATED — use `stability` (the inverse) for new code. "
            "Kept for backward compat with /wsi/evaluate and /big-five/*. "
            "stability = 100 - neuroticism."
        ),
    )

    @property
    def stability(self) -> int:
        """Phase 2.5 canonical alias matching ALLOWED_TRAITS taxonomy
        (openness / conscientiousness / extraversion / agreeableness /
        stability). Computed as 100 - neuroticism. New code consumes this."""
        return 100 - self.neuroticism


class AnalyzeResponseRequest(WeDoBaseModel):
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
    star_completeness: float | None = None
    feedback: str
    evidences: list[str]
    red_flags: list[str]


class ResponseInput(WeDoBaseModel):
    question_id: str
    response_text: str


class CompleteScreeningRequest(WeDoBaseModel):
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
    overall_score: float = Field(ge=0, le=5)
    classification: str
    cognitive_level: dict[str, Any]
    proficiency_level: dict[str, Any]
    big_five_profile: BigFiveIndicators
    archetype_indicators: list[ArchetypeIndicator]
    summary: str
    recommendations: list[str]
    response_analyses: list[AnalyzeResponseOutput]


class JDEvaluateRequest(WeDoBaseModel):
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


class SaveQuestionsRequest(WeDoBaseModel):
    job_id: str
    questions: list[dict[str, Any]]
    source: str | None = "manual"


class SuggestQuestionRequest(WeDoBaseModel):
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

# Consolidação WSI Fase 3: constantes + lógica JD-quality movidas para o
# canônico cv_screening (single source). Re-exportadas para compat.
from app.domains.cv_screening.services.wsi_service.jd_quality import (  # noqa: E402
    _JD_SENIORITY_KEYWORDS,
    _BIAS_TERMS,
    _JD_BANDS,
    _jd_get_band,
    evaluate_jd_quality,
)


# ---------------------------------------------------------------------------
# LLM factory helpers (Task #93 migration)
# ---------------------------------------------------------------------------


async def get_anthropic_client(
    *,
    company_id: str | None = None,
    domain: str | None = "wsi",
    operation: str | None = None,
):
    """DEPRECATED: Returns a ProviderContainer via LLMProviderFactory (Task #93).

    Callers should migrate to using generate_with_llm() directly.
    Returns None only on critical init failure.

    R-002 (Sprint 1 Quick Wins): emite track_llm_usage_start antes de retornar
    o container — sensor de spend tenant-aware. Aceita company_id + domain +
    operation opcionais para enriquecer o log.
    """
    try:
        from app.domains.credits.services.token_budget_service import track_llm_usage_start
        from app.shared.providers.llm_factory import get_provider_for_tenant

        track_llm_usage_start(company_id, model=None, domain=domain, operation=operation)
        return get_provider_for_tenant()
    except Exception as e:
        logger.error(f"Failed to get LLM provider: {e}", exc_info=True)
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


async def _run_anthropic_sync(client, model: str, max_tokens: int, messages: list, timeout: float = 30.0):
    """
    MIGRATED: Now uses LLMProviderFactory instead of direct Anthropic SDK (Task #93).
    Returns a _FakeResponse shim so callers can still access response.content[0].text.
    """
    try:
        prompt = "\n".join(m.get("content", "") for m in messages if m.get("role") == "user")
        text = await asyncio.wait_for(
            client.generate_with_fallback(prompt, agent_type="WSIAgent"),
            timeout=timeout,
        )
        return _FakeResponse(text)
    except TimeoutError:
        logger.warning(f"LLM call timed out after {timeout}s")
        return None
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"LLM call failed: {type(e).__name__}: {e}", exc_info=True)
        return None
