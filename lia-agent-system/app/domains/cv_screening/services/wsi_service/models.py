"""
WSI Data Models - Dataclasses and Pydantic models.
"""
import json
import logging
from dataclasses import dataclass
from dataclasses import field as dc_field
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# F2 Big Five Pipeline — modelos e constantes (spec WSI F2.5/F3/F5)
# ---------------------------------------------------------------------------

@dataclass
class OceanTraitScore:
    """Score de relevância 0-100 de um trait OCEAN para a vaga (F2.5 NEO-PI-R rubric)."""
    trait: str              # openness | conscientiousness | extraversion | agreeableness | stability
    score: int              # 0-100: intensidade com que a vaga exige o trait
    confidence: str = "medium"                          # high | medium | low
    evidence: list[str] = dc_field(default_factory=list)  # citações literais do JD


# Número de traits OCEAN selecionados por nível de senioridade (F5)
SENIORITY_BIGFIVE_TOP_N: dict[str, int] = {
    "estagiario": 2,
    "junior":     2,
    "pleno":      3,
    "senior":     3,
    "lead":       4,
    "principal":  4,
    "diretor":    5,
    "vp_clevel":  5,
}


# ============================================================================
# HELPER FUNCTIONS - Error Handling & Robustness
# ============================================================================

def safe_json_parse(content: Any, fallback: dict | None = None) -> dict:
    """
    Safely parse JSON content from LLM response with robust error handling.
    
    Args:
        content: LLM response content (str, dict, or AIMessage)
        fallback: Optional fallback dict if parsing fails
        
    Returns:
        Parsed dict or fallback
        
    Raises:
        ValueError: If parsing fails and no fallback provided
    """
    try:
        # Handle different content types
        if isinstance(content, dict):
            return content
        
        content_str = content if isinstance(content, str) else str(content)
        
        # Try to extract JSON from markdown code blocks
        if "```json" in content_str:
            start = content_str.find("```json") + 7
            end = content_str.find("```", start)
            content_str = content_str[start:end].strip()
        elif "```" in content_str:
            start = content_str.find("```") + 3
            end = content_str.find("```", start)
            content_str = content_str[start:end].strip()
        
        # Parse JSON
        parsed = json.loads(content_str)
        return parsed
        
    except (json.JSONDecodeError, ValueError, AttributeError) as e:
        logger.error(f"Failed to parse JSON from LLM response: {e}")
        logger.debug(f"Content was: {content}")
        
        if fallback is not None:
            logger.warning(f"Using fallback: {fallback}")
            return fallback
        
        raise ValueError(f"Failed to parse JSON and no fallback provided: {e}")


def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    """
    Normalize weights to sum to 1.0.
    
    Args:
        weights: Dict of competency -> weight
        
    Returns:
        Normalized weights dict
        
    Raises:
        ValueError: If total weight is 0
    """
    total = sum(weights.values())
    
    if total == 0:
        raise ValueError("Total weights cannot be zero")
    
    if abs(total - 1.0) < 0.01:  # Already normalized
        return weights
    
    normalized = {k: v / total for k, v in weights.items()}
    logger.info(f"Normalized weights from sum={total:.2f} to sum=1.0")
    
    return normalized


class Competency(BaseModel):
    """Competência a ser avaliada."""
    name: str
    type: Literal["technical", "behavioral", "cultural"]
    weight: float = Field(ge=0, le=1)
    seniority_level: Literal["junior", "pleno", "senior", "lead", "executive"]
    is_critical: bool = False
    big_five_mapping: str | None = None  # F6.6: trait OCEAN pré-mapeado (openness|conscientiousness|extraversion|agreeableness|stability)


class CompetencySuggestion(BaseModel):
    """Sugestão automática de competências baseada em JD."""
    technical_competencies: list[Competency]
    behavioral_competencies: list[Competency]
    cultural_competencies: list[Competency]
    suggested_weights: dict[str, float]
    confidence_score: float


class WSIQuestion(BaseModel):
    """Pergunta WSI estruturada."""
    id: str
    competency: str
    framework: Literal["CBI", "Bloom", "Dreyfus", "BigFive"]
    question_type: Literal["autodeclaration", "contextual", "microcase", "situational"]
    question_text: str
    weight: float
    expected_signals: list[str]
    scoring_criteria: dict[str, Any]
    is_critical: bool = False
    # F6.8 — validação pós-geração
    needs_manual_review: bool = False
    validation_flags: dict[str, Any] = Field(default_factory=dict)


class ResponseAnalysis(BaseModel):
    """Análise de resposta do candidato."""
    question_id: str
    competency: str
    response_text: str
    
    autodeclaration_score: float | None = Field(None, ge=1, le=5)
    context_score: float | None = Field(None, ge=1, le=5)
    bloom_level: int | None = Field(None, ge=1, le=6)
    dreyfus_level: int | None = Field(None, ge=1, le=5)
    
    evidences: list[str]
    red_flags: list[str]
    consistency_penalty: float = 0.0
    
    final_score: float = Field(ge=1, le=5)
    justification: str

    # Audit task #498 — categoria explícita da competência avaliada nesta resposta
    # (derivada do `WSIQuestion.framework` pelo response_analyzer). Permite ao
    # scorer dividir tech vs behav SEM cair no heurístico por peso quando os
    # callers não passam `competencies` tipado. None = não informado, usar
    # fallback existente (competencies map ou heurístico).
    category: Literal["technical", "behavioral", "cultural"] | None = None


class WSIResult(BaseModel):
    """Resultado final da avaliação WSI."""
    candidate_id: str
    job_vacancy_id: str
    
    technical_wsi: float = Field(ge=0, le=5)
    behavioral_wsi: float = Field(ge=0, le=5)
    overall_wsi: float = Field(ge=0, le=5)
    
    classification: Literal[
        "excepcional", "excelente", "alto", "medio",
        "regular", "abaixo_da_media", "baixo"
    ]
    percentile: int | None = None
    
    response_analyses: list[ResponseAnalysis]
    created_at: datetime = Field(default_factory=datetime.now)


class StructuredReport(BaseModel):
    """Parecer estruturado do candidato."""
    candidate_id: str
    wsi_result: WSIResult
    
    executive_summary: str
    
    technical_analysis: dict[str, Any]
    behavioral_analysis: dict[str, Any]
    cultural_fit: dict[str, Any]
    
    recommendation: dict[str, Any]


class CandidateFeedback(BaseModel):
    """Feedback estruturado para o candidato."""
    candidate_id: str
    decision: Literal["aprovado", "aguardando", "nao_aprovado"]
    
    main_message: str
    technical_strengths: list[str]
    development_opportunities: list[str]
    behavioral_strengths: list[str]
    
    next_steps: str
    personalized_tip: str | None = None
    development_plan: dict[str, list[str]] | None = None
    recommended_resources: list[str] | None = None


