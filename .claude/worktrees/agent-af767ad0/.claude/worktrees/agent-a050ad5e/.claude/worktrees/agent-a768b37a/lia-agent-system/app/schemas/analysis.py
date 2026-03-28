"""
Schemas for LIA Candidate Analysis.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum


class AnalysisType(str, Enum):
    CONTEXTUAL = "contextual"
    GENERAL = "general"


class ArchetypeEnum(str, Enum):
    CATALISADOR_VISIONARIO = "Catalisador Visionário"
    EXECUTOR_CONFIAVEL = "Executor Confiável"
    GUARDIAO_CLIENTES = "Guardião de Clientes"
    ESTRATEGISTA_ANALITICO = "Estrategista Analítico"
    MEDIADOR_ADAPTAVEL = "Mediador Adaptável"
    RAINMAKER_AUDACIOSO = "Rainmaker Audacioso"
    OPERADOR_RESILIENTE = "Operador Resiliente"
    ARQUITETO_METODICO = "Arquiteto Metódico"


class CandidateInput(BaseModel):
    id: str
    name: str
    position: Optional[str] = None
    location: Optional[str] = None
    company: Optional[str] = None
    cv_text: Optional[str] = None
    skills: Optional[List[str]] = []
    experience_years: Optional[int] = None
    education: Optional[str] = None
    seniority_level: Optional[str] = None


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
    strengths: List[str] = Field(..., description="Top 3 strengths")
    gaps: List[str] = Field(..., description="Areas to develop")
    recommendation: str = Field(..., description="Hiring recommendation")
    recommendation_level: Literal["highly_recommended", "recommended", "potential", "low_match", "not_recommended"]
    explanation: str = Field(..., description="Detailed explanation of the score")
    score_breakdown: Optional[ScoreBreakdown] = None
    potential_roles: Optional[List[str]] = None


class AnalysisRequest(BaseModel):
    candidates: List[CandidateInput]
    job_vacancy_id: Optional[str] = None
    analysis_type: AnalysisType = AnalysisType.GENERAL
    job_title: Optional[str] = None
    job_requirements: Optional[List[str]] = None
    job_description: Optional[str] = None


class AnalysisResponse(BaseModel):
    success: bool
    total_analyzed: int
    average_score: float
    results: List[CandidateAnalysisResult]
    insights: Optional[dict] = None
    recommendations: Optional[List[str]] = None
    alerts: Optional[List[dict]] = None
