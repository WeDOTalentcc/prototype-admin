"""
Schemas for LIA Candidate Analysis.
"""
from enum import Enum, StrEnum
from typing import Literal

from pydantic import BaseModel, Field
from app.shared.types import WeDoBaseModel


class AnalysisType(StrEnum):
    CONTEXTUAL = "contextual"
    GENERAL = "general"


class ArchetypeEnum(StrEnum):
    CATALISADOR_VISIONARIO = "Catalisador Visionário"
    EXECUTOR_CONFIAVEL = "Executor Confiável"
    GUARDIAO_CLIENTES = "Guardião de Clientes"
    ESTRATEGISTA_ANALITICO = "Estrategista Analítico"
    MEDIADOR_ADAPTAVEL = "Mediador Adaptável"
    RAINMAKER_AUDACIOSO = "Rainmaker Audacioso"
    OPERADOR_RESILIENTE = "Operador Resiliente"
    ARQUITETO_METODICO = "Arquiteto Metódico"


class CandidateInput(WeDoBaseModel):
    id: str
    name: str
    position: str | None = None
    location: str | None = None
    company: str | None = None
    cv_text: str | None = None
    skills: list[str] | None = []
    experience_years: int | None = None
    education: str | None = None
    seniority_level: str | None = None


class ScoreBreakdown(BaseModel):
    match_tecnico: float = Field(..., description="Technical skills match (35%)")
    fit_personalidade: float = Field(..., description="Personality fit (25%)")
    relevancia_experiencia: float = Field(..., description="Experience relevance (20%)")
    alinhamento_cultural: float = Field(..., description="Cultural alignment (20%)")


class CandidateAnalysisResult(BaseModel):
    candidate_id: str
    candidate_name: str
    lia_score: float = Field(..., ge=0, le=100, description="Overall LIA score")
    fit_score: float = Field(..., ge=0, le=100, description="Personality fit score")
    archetype: str = Field(..., description="Big Five archetype")
    strengths: list[str] = Field(..., description="Top 3 strengths")
    gaps: list[str] = Field(..., description="Areas to develop")
    recommendation: str = Field(..., description="Hiring recommendation")
    recommendation_level: Literal["highly_recommended", "recommended", "potential", "low_match", "not_recommended"]
    explanation: str = Field(..., description="Detailed explanation of the score")
    score_breakdown: ScoreBreakdown | None = None
    potential_roles: list[str] | None = None


class AnalysisRequest(WeDoBaseModel):
    candidates: list[CandidateInput]
    job_vacancy_id: str | None = None
    analysis_type: AnalysisType = AnalysisType.GENERAL
    job_title: str | None = None
    job_requirements: list[str] | None = None
    job_description: str | None = None


class AnalysisResponse(BaseModel):
    success: bool
    total_analyzed: int
    average_score: float
    results: list[CandidateAnalysisResult]
    insights: dict | None = None
    recommendations: list[str] | None = None
    alerts: list[dict] | None = None
