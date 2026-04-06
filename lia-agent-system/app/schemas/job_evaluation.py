"""
Pydantic schemas for Job Evaluation.

Defines the structured response for proactive job evaluation,
combining insights from multiple services.
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.compensation_analysis import CompensationAnalysisResult


class EvaluationResponse(BaseModel):
    """Resultado estruturado da avaliação proativa da vaga."""
    
    detected_fields: dict[str, Any] = Field(
        default_factory=dict,
        description="Campos detectados do input (título, senioridade, departamento, etc)"
    )
    
    completeness_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Score de completude da vaga (0-100)"
    )
    missing_critical_fields: list[str] = Field(
        default_factory=list,
        description="Campos críticos que estão faltando"
    )
    missing_probable_fields: list[str] = Field(
        default_factory=list,
        description="Campos provavelmente necessários que estão faltando"
    )
    
    company_alignment: dict[str, Any] = Field(
        default_factory=dict,
        description="Análise de alinhamento com a empresa (culture_match, skills_from_catalog, suggested_benefits)"
    )
    
    market_alignment: dict[str, Any] = Field(
        default_factory=dict,
        description="Análise de alinhamento com mercado (salary_percentile, market_demand, competing_companies)"
    )
    
    compensation_analysis: CompensationAnalysisResult | None = Field(
        default=None,
        description="Análise detalhada de compensação (salário, bônus, benefícios)"
    )
    
    success_patterns: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Padrões de sucesso detectados de vagas similares"
    )
    
    suggestions: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Sugestões personalizadas [{field, suggested, reason, source}]"
    )
    
    overall_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confiança geral na avaliação (0-1)"
    )
    recommended_action: str = Field(
        default="proceed",
        description="Ação recomendada: 'proceed', 'review_compensation', 'missing_critical'"
    )
    
    evaluated_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Timestamp da avaliação"
    )
    services_used: list[str] = Field(
        default_factory=list,
        description="Lista de serviços utilizados na avaliação"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "detected_fields": {
                    "title": "Desenvolvedor Python Sênior",
                    "seniority": "Sênior",
                    "department": "Tecnologia",
                    "location": "São Paulo"
                },
                "completeness_score": 85.0,
                "missing_critical_fields": [],
                "missing_probable_fields": ["salary_max"],
                "company_alignment": {
                    "culture_match": 0.85,
                    "skills_from_catalog": ["Python", "AWS", "Docker"],
                    "suggested_benefits": ["VA", "VR", "Plano de Saúde"]
                },
                "market_alignment": {
                    "salary_percentile": 75,
                    "market_demand": "high",
                    "competing_companies": 15
                },
                "compensation_analysis": None,
                "success_patterns": [
                    {"pattern": "salary_range", "value": "12000-18000", "confidence": 0.8}
                ],
                "suggestions": [
                    {
                        "field": "salary_min",
                        "suggested": 18000,
                        "reason": "Baseado em dados de mercado para Python Sênior em SP",
                        "source": "market_benchmark"
                    }
                ],
                "overall_confidence": 0.85,
                "recommended_action": "proceed",
                "evaluated_at": "2026-01-25T10:30:00",
                "services_used": [
                    "intelligence_layer",
                    "skills_catalog",
                    "market_benchmark",
                    "compensation_analysis"
                ]
            }
        }
