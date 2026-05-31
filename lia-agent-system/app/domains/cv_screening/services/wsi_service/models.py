"""
WSI Data Models - Dataclasses and Pydantic models.
"""
import json
import logging
from dataclasses import dataclass
from dataclasses import field as dc_field
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator

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
    """Pergunta WSI estruturada.

    P0.D SIBLINGS (audit 2026-05-21): campos ``fallback_used`` /
    ``llm_failure_mode`` / ``llm_error_message`` adicionados pra surface
    explícita de quando a pergunta foi gerada por LLM (canonical) vs por
    fallback template stock (degraded). Antes, fallback era SILENT — pergunta
    template caía no payload sem flag, recrutador via WSIQuestion como se
    fosse output legitimo da LIA.

    Diferente de StructuredReport (que setou ``needs_manual_review_on_fail=True``),
    questions fallback NÃO setam ``needs_manual_review=True`` automaticamente:
    o campo ``needs_manual_review`` já é usado por F6.8 (validação pós-geração
    de ancoragem JD). Mantemos a semântica original do campo intacta — o
    sinal de LLM failure vive separado em ``fallback_used`` /
    ``llm_failure_mode`` / ``llm_error_message``.

    REGRA 4 (CLAUDE.md): handlers tocando LLM/critical IO DEVEM fail-loud.
    Estes campos compõem o envelope canonical (mesmo contrato que
    ``app.shared.llm.safe_response.LLMResponseEnvelope``).

    Default ``fallback_used=False`` preserva backward-compat.
    """
    id: str
    competency: str
    framework: Literal["CBI", "Bloom", "Dreyfus", "BigFive"]
    question_type: Literal["autodeclaration", "contextual", "microcase", "situational"]
    question_text: str
    weight: float
    expected_signals: list[str]
    scoring_criteria: dict[str, Any]
    is_critical: bool = False
    # F6.8 — validação pós-geração (ancoragem JD). NÃO eh derivado de LLM failure.
    needs_manual_review: bool = False
    validation_flags: dict[str, Any] = Field(default_factory=dict)
    # Phase 2.5: trait OCEAN copied from Competency.big_five_mapping when
    # the question is constructed. Allows WSIResponseAnalyzer to forward
    # the trait into ResponseAnalysis for downstream aggregation. None
    # for technical/non-BigFive questions.
    big_five_mapping: str | None = None
    # P0.D SIBLINGS (audit 2026-05-21): envelope canonical de LLM failure.
    # Independente de needs_manual_review (que serve F6.8 ancoragem JD).
    fallback_used: bool = False
    llm_failure_mode: str | None = None  # LLMFailureMode.value when fallback_used
    llm_error_message: str | None = None  # human-readable when fallback_used

    # ── Consolidação WSI Fase 2 (2026-05-31): campos opcionais de painel ──
    # Direção B (decisão Paulo): portamos a riqueza por-pergunta do fork
    # job_creation para o canônico único. Todos OPCIONAIS (default None) →
    # backward-compat total com o fluxo de análise (ResponseAnalysis continua
    # sendo a fonte do bloom/dreyfus DEMONSTRADO; estes são os ALVOS de geração).
    block: Literal["technical", "behavioral"] | None = None  # bloco da triagem
    skill: str | None = None  # competência/skill alvo (espelha competency p/ painel)
    bloom_level: int | None = Field(default=None, ge=1, le=6)  # Bloom ALVO da pergunta
    dreyfus_level: int | None = Field(default=None, ge=1, le=5)  # Dreyfus ALVO
    ideal_answer: str | None = None  # resposta-modelo (derivada de scoring_criteria.score_5)
    trait_ocean: str | None = None  # espelho de big_five_mapping p/ contrato do painel

    @model_validator(mode="after")
    def _derive_panel_fields(self) -> "WSIQuestion":
        # DRY: deriva os campos baratos a partir do que já existe, sem exigir
        # que cada builder os preencha. skill↔competency, trait_ocean↔big_five_mapping,
        # ideal_answer↔scoring_criteria.score_5 (a âncora ideal do CBI).
        if self.skill is None:
            self.skill = self.competency
        if self.trait_ocean is None and self.big_five_mapping:
            self.trait_ocean = self.big_five_mapping
        # BigFive: o trait OCEAN é carregado em scoring_criteria["ocean_trait"]
        # pelo _generate_bigfive_question — espelha p/ o painel.
        if self.trait_ocean is None and isinstance(self.scoring_criteria, dict):
            _ot = self.scoring_criteria.get("ocean_trait")
            if isinstance(_ot, str) and _ot.strip():
                self.trait_ocean = _ot
        if self.ideal_answer is None and isinstance(self.scoring_criteria, dict):
            _score5 = self.scoring_criteria.get("score_5")
            if isinstance(_score5, str) and _score5.strip():
                self.ideal_answer = _score5
        # BigFive são sempre comportamentais; demais frameworks default técnico
        # quando o builder não setou block explicitamente.
        if self.block is None:
            self.block = "behavioral" if self.framework == "BigFive" else "technical"
        return self


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
    # Camada 2 (LLM enrichment) — optional, populated when Layer2Extractor runs
    layer2_signals: Optional["Layer2Signals"] = None
    layer2_degraded_reason: Optional[str] = None
    # Phase 2.5: BigFive trait of the originating WSIQuestion (propagated
    # from WSIQuestion.big_five_mapping by WSIResponseAnalyzer). Carries
    # the response's score-to-trait association so WSIScoreCalculator can
    # aggregate ocean_traits for record_hire downstream. None for
    # technical/non-BigFive questions.
    trait_ocean: str | None = None


class WSIResult(BaseModel):
    """Resultado final da avaliação WSI."""
    candidate_id: str
    job_vacancy_id: str

    technical_wsi: float = Field(ge=0, le=5)
    behavioral_wsi: float = Field(ge=0, le=5)
    overall_wsi: float = Field(ge=0, le=5)

    classification: Literal["excepcional", "excelente", "alto", "medio", "regular", "baixo"]
    percentile: int | None = None

    response_analyses: list[ResponseAnalysis]
    created_at: datetime = Field(default_factory=datetime.now)
    # Phase 2.5: per-trait aggregate of OCEAN scores normalized to 0..1.
    # Built by WSIScoreCalculator from response_analyses with non-null
    # trait_ocean. Persisted by handlers_screening into
    # LiaOpinion.behavioral_analysis['ocean_traits'] and consumed by
    # _hook_conclusion_hired to populate
    # BigFiveDepartmentService.record_hire (ADR-LGPD-001 data source).
    # Empty dict when no BigFive-tagged responses exist.
    ocean_traits: dict[str, float] = Field(default_factory=dict)


class StructuredReport(BaseModel):
    """Parecer estruturado do candidato.

    P0.D (audit 2026-05-21): campos ``fallback_used`` / ``needs_manual_review``
    / ``llm_failure_mode`` adicionados pra surface explícita de quando o
    parecer foi gerado por LLM (canonical) vs por fallback template
    (degraded). Antes, fallback era SILENT — recrutador via decisao=AGUARDANDO
    com justificativa stock e nao tinha como saber que era fallback automatico.

    REGRA 4 (CLAUDE.md): handlers tocando LLM/critical IO DEVEM fail-loud.
    Estes campos compõem o envelope canonical (mesmo contrato que
    ``app.shared.llm.safe_response.LLMResponseEnvelope``).

    Default ``fallback_used=False`` preserva backward-compat: callers que nao
    consultam estes campos continuam funcionando, mas perdem visibilidade.
    Novos callers DEVEM checar ``fallback_used`` antes de exibir parecer
    como autoritativo.
    """
    candidate_id: str
    wsi_result: WSIResult

    executive_summary: str

    technical_analysis: dict[str, Any]
    behavioral_analysis: dict[str, Any]
    cultural_fit: dict[str, Any]

    recommendation: dict[str, Any]

    # P0.D (audit 2026-05-21): envelope canonical de LLM failure
    fallback_used: bool = False
    needs_manual_review: bool = False
    llm_failure_mode: str | None = None  # LLMFailureMode.value when fallback_used
    llm_error_message: str | None = None  # human-readable when fallback_used


class CandidateFeedback(BaseModel):
    """Feedback estruturado para o candidato.

    P0.D (audit 2026-05-21): mesmos campos canonical de envelope LLM-failure
    que StructuredReport. Quando LLM falha, fallback NEUTRO eh retornado COM
    flag ``fallback_used=True`` — preserva neutralidade de tom (REGRA pre-existente
    no docstring de generate_feedback) E sinaliza explicitamente que conteudo
    foi gerado por template, nao pela LLM.

    needs_manual_review=True → ops/recrutador deve revisar antes de enviar
    ao candidato (mensagem stock pode parecer impessoal). Mantemos envio
    automatico por compatibilidade, mas observabilidade ganha sinal.
    """
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

    # P0.D (audit 2026-05-21): envelope canonical de LLM failure
    fallback_used: bool = False
    needs_manual_review: bool = False
    llm_failure_mode: str | None = None
    llm_error_message: str | None = None




# ---------------------------------------------------------------------------
# Layer2Signals — LLM-extracted structural signals (Camada 2, audit rev.18 M01)
# ---------------------------------------------------------------------------

class Layer2Signals(BaseModel):
    """LLM-extracted structural signals from WSI response (Camada 2, audit rev.18 M01)."""

    is_paraphrase: bool = False
    is_first_person: bool = True
    has_R_outcome: bool = True
    language_consistency: bool = True
    prompt_injection_detected: bool = False
    word_count_band: str = "50-150"
    trait_signals_count: int = 0
    has_quantification: bool = False
    semantic_inflation: bool = False
    bloom_demonstrated: int = Field(default=3, ge=1, le=6, description="Bloom taxonomy level (1..6)")
    dreyfus_demonstrated: int = Field(default=3, ge=1, le=5, description="Dreyfus skill level (1..5)")
    confidence: float = 1.0
    extraction_warnings: list[str] = []
