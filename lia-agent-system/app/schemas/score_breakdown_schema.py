"""
2.5: Schema Pydantic canônico para score_breakdown JSONB.

Este schema é a fonte única de verdade para o que pode ser armazenado em
vacancy_candidates.ai_analysis quando produzido pelo calculate_ranking_score.
Campos opcionais (wsi_score_raw, formula) acomodam metadados do bloco 2.3.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WeightedComponentsSchema(BaseModel):
    """Componentes ponderados do score (saída de RankingScoreBreakdown)."""

    model_config = ConfigDict(extra="allow")  # permite campos futuros

    rubricas: float = 0.0
    wsi: float = 0.0
    prerequisites: float = 0.0
    recency: float = 0.0


class ScoreBreakdownSchema(BaseModel):
    """Schema canônico para vacancy_candidates.ai_analysis (score_breakdown).

    Espelha RankingScoreBreakdown.to_dict() com validações de bounds.
    Campos opcionais adicionados pelo bloco 2.3 são aceitos via Annotated.
    """

    model_config = ConfigDict(extra="allow")  # tolera campos opcionais futuros

    # Campos obrigatórios — presentes em todo to_dict()
    rubricas_score: float = Field(..., ge=0.0, le=100.0)
    prerequisites_score: float = Field(0.0, ge=0.0, le=100.0)
    recency_boost: float = Field(0.0, ge=0.0, le=100.0)
    calibration_adjustment: float = Field(0.0, ge=-20.0, le=20.0)
    completeness_factor: float = Field(..., ge=0.0, le=1.0)
    data_availability: str = Field("cv_only")
    raw_score: float = Field(..., ge=0.0)
    final_score: float = Field(..., ge=0.0, le=100.0)

    # Campos opcionais
    wsi_score: float | None = Field(None, ge=0.0, le=100.0)
    weighted_components: WeightedComponentsSchema | None = None
    weights_used: dict[str, float] | None = None

    # Campos adicionados pelo bloco 2.3
    wsi_score_raw: float | None = Field(None, ge=0.0, le=10.0)
    formula: str | None = None

    @field_validator("data_availability")
    @classmethod
    def validate_data_availability(cls, v: str) -> str:
        allowed = {"cv_only", "cv_wsi", "full", "wsi_only", "unknown"}
        if v not in allowed:
            raise ValueError(f"data_availability deve ser um de {allowed}, recebido: {v!r}")
        return v


def parse_ai_analysis(raw: Any) -> ScoreBreakdownSchema | None:
    """Tenta validar raw como ScoreBreakdownSchema. Retorna None se inválido.

    Use no read-path para leitura segura de vacancy_candidates.ai_analysis.
    Nunca levanta exceção — falha silenciosa é intencional (dado legado pode
    estar em formato antigo ou None).
    """
    if not isinstance(raw, dict):
        return None
    try:
        return ScoreBreakdownSchema.model_validate(raw)
    except Exception:
        return None
