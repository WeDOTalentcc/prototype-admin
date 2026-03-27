"""
Schemas para Job Description Enrichment.

Define estruturas para sugestões enriquecidas com justificativas,
métricas de impacto e contexto para tomada de decisão do recrutador.
"""
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class SuggestionSource(str, Enum):
    MARKET_BENCHMARK = "market_benchmark"
    COMPANY_HISTORY = "company_history"
    SKILLS_CATALOG = "skills_catalog"
    COMPANY_CONFIG = "company_config"
    ATS_INTEGRATION = "ats_integration"


class SuggestionImpactLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EnrichedSuggestion(BaseModel):
    """Sugestão enriquecida com contexto e justificativa motivadora."""
    id: str
    value: str
    source: SuggestionSource
    justification: str = Field(description="Explicação de por que esta sugestão é relevante")
    metrics: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Métricas que suportam a sugestão (ex: {'market_percentage': 85, 'history_count': 12})"
    )
    impact_description: Optional[str] = Field(
        default=None,
        description="Descrição do impacto esperado (ex: 'Aumenta chances de fechamento em 23%')"
    )
    impact_level: SuggestionImpactLevel = SuggestionImpactLevel.MEDIUM
    wsi_quality_note: Optional[str] = Field(
        default=None,
        description="Nota sobre impacto na qualidade das perguntas WSI"
    )
    is_new: bool = True
    accepted: Optional[bool] = None
    category: Optional[str] = None


class ResponsibilitySuggestion(EnrichedSuggestion):
    """Sugestão de responsabilidade com contexto específico."""
    related_skills: List[str] = Field(default_factory=list)
    seniority_fit: Optional[str] = None


class TechnicalSkillSuggestion(EnrichedSuggestion):
    """Sugestão de competência técnica com dados de mercado."""
    proficiency_level: Optional[str] = None
    years_experience: Optional[int] = None
    market_demand_trend: Optional[Literal["rising", "stable", "declining"]] = None
    related_skills: List[str] = Field(default_factory=list)


class BehavioralCompetencySuggestion(EnrichedSuggestion):
    """Sugestão de competência comportamental com impacto em WSI."""
    big_five_mapping: Optional[str] = None
    assessment_methods: List[str] = Field(default_factory=list)


class SalarySuggestion(BaseModel):
    """Sugestão de faixa salarial com benchmark de mercado."""
    id: str
    suggested_min: float
    suggested_max: float
    current_min: Optional[float] = None
    current_max: Optional[float] = None
    source: SuggestionSource = SuggestionSource.MARKET_BENCHMARK
    justification: str
    market_percentile: Optional[int] = None
    market_comparison: Optional[str] = Field(
        default=None,
        description="Ex: '12% abaixo do mercado para SP'"
    )
    impact_description: Optional[str] = Field(
        default=None,
        description="Ex: 'Ajustar pode aumentar aplicações qualificadas em 40%'"
    )
    sources_consulted: List[str] = Field(default_factory=list)
    sample_size: Optional[int] = None
    accepted: Optional[bool] = None


class BonusSuggestion(BaseModel):
    """Sugestão de bônus com práticas do setor."""
    id: str
    suggested_percentage_min: Optional[float] = None
    suggested_percentage_max: Optional[float] = None
    suggested_salary_months: Optional[str] = Field(
        default=None,
        description="Ex: '2-4 salários'"
    )
    source: SuggestionSource = SuggestionSource.MARKET_BENCHMARK
    justification: str
    sector_practice: Optional[str] = None
    accepted: Optional[bool] = None


class SectionSuggestions(BaseModel):
    """Sugestões para uma seção específica do JD."""
    section_name: str
    section_title: str
    detected_items: List[str] = Field(default_factory=list)
    suggestions: List[EnrichedSuggestion] = Field(default_factory=list)
    missing_count: int = 0
    recommended_count: Optional[int] = None
    quality_note: Optional[str] = None


class CompensationSuggestions(BaseModel):
    """Sugestões consolidadas de remuneração."""
    salary: Optional[SalarySuggestion] = None
    bonus: Optional[BonusSuggestion] = None
    benefits_suggestions: List[EnrichedSuggestion] = Field(default_factory=list)
    total_compensation_note: Optional[str] = None


class EnrichedJobDescription(BaseModel):
    """Job Description completo com sugestões enriquecidas por seção."""
    job_id: Optional[str] = None
    company_id: str
    
    title: str
    department: Optional[str] = None
    seniority: Optional[str] = None
    location: Optional[str] = None
    work_model: Optional[str] = None
    
    responsibilities: SectionSuggestions = Field(
        default_factory=lambda: SectionSuggestions(
            section_name="responsibilities",
            section_title="Responsabilidades"
        )
    )
    technical_skills: SectionSuggestions = Field(
        default_factory=lambda: SectionSuggestions(
            section_name="technical_skills",
            section_title="Competências Técnicas"
        )
    )
    behavioral_competencies: SectionSuggestions = Field(
        default_factory=lambda: SectionSuggestions(
            section_name="behavioral_competencies",
            section_title="Competências Comportamentais"
        )
    )
    compensation: CompensationSuggestions = Field(
        default_factory=CompensationSuggestions
    )
    
    total_suggestions_count: int = 0
    wsi_quality_score: Optional[float] = None
    wsi_quality_warnings: List[str] = Field(default_factory=list)
    completeness_score: float = 0.0
    
    analysis_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Contexto da análise feita (fontes consultadas, métricas agregadas)"
    )
    
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Desenvolvedor Python Sênior",
                "company_id": "company-123",
                "responsibilities": {
                    "section_name": "responsibilities",
                    "section_title": "Responsabilidades",
                    "detected_items": ["Gerenciar time de desenvolvedores"],
                    "suggestions": [
                        {
                            "id": "resp-1",
                            "value": "Conduzir code reviews semanais",
                            "source": "company_history",
                            "justification": "Presente em 80% das vagas de Dev Sênior da sua empresa",
                            "impact_description": "Melhora qualidade do código e reduz bugs em produção",
                            "is_new": True
                        }
                    ],
                    "missing_count": 0,
                    "recommended_count": 5
                },
                "technical_skills": {
                    "section_name": "technical_skills",
                    "section_title": "Competências Técnicas",
                    "detected_items": ["Python 5+ anos"],
                    "suggestions": [
                        {
                            "id": "tech-1",
                            "value": "Docker",
                            "source": "market_benchmark",
                            "justification": "85% das vagas similares no mercado incluem Docker",
                            "impact_description": "Vagas com Docker fecham 23% mais rápido",
                            "metrics": {"market_percentage": 85, "time_to_fill_improvement": 23},
                            "is_new": True
                        }
                    ]
                },
                "behavioral_competencies": {
                    "section_name": "behavioral_competencies",
                    "section_title": "Competências Comportamentais",
                    "detected_items": ["Liderança"],
                    "suggestions": [
                        {
                            "id": "behav-1",
                            "value": "Comunicação assertiva",
                            "source": "wsi_requirement",
                            "justification": "92% dos cargos de liderança técnica pedem esta skill",
                            "wsi_quality_note": "Essencial para perguntas WSI de qualidade sobre gestão",
                            "is_new": True
                        }
                    ],
                    "missing_count": 2,
                    "quality_note": "Adicione +2 competências comportamentais para perguntas WSI completas"
                },
                "compensation": {
                    "salary": {
                        "id": "salary-1",
                        "suggested_min": 20000,
                        "suggested_max": 25000,
                        "current_min": 18000,
                        "current_max": 22000,
                        "justification": "Sua faixa está 12% abaixo do mercado para SP",
                        "market_comparison": "12% abaixo do mercado",
                        "impact_description": "Ajustar pode aumentar aplicações qualificadas em 40%",
                        "market_percentile": 45
                    }
                },
                "total_suggestions_count": 8,
                "wsi_quality_score": 0.75,
                "wsi_quality_warnings": ["Faltam 2 competências comportamentais para perguntas WSI de qualidade"],
                "completeness_score": 0.85
            }
        }


class EnrichmentRequest(BaseModel):
    """Request para enriquecimento de Job Description."""
    company_id: str
    job_draft_id: Optional[str] = None
    
    title: str
    department: Optional[str] = None
    seniority: Optional[str] = None
    location: Optional[str] = None
    work_model: Optional[str] = None
    
    detected_responsibilities: List[str] = Field(default_factory=list)
    detected_technical_skills: List[str] = Field(default_factory=list)
    detected_behavioral_competencies: List[str] = Field(default_factory=list)
    
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    
    is_affirmative: bool = False
    affirmative_type: Optional[str] = None
    
    raw_input: Optional[str] = None


class EnrichmentResponse(BaseModel):
    """Response do enriquecimento de Job Description."""
    success: bool
    enriched_jd: Optional[EnrichedJobDescription] = None
    summary_message: str = ""
    error: Optional[str] = None


class SuggestionAcceptanceRequest(BaseModel):
    """Request para aceitar/rejeitar sugestões."""
    job_draft_id: str
    accepted_suggestion_ids: List[str] = Field(default_factory=list)
    rejected_suggestion_ids: List[str] = Field(default_factory=list)
    accept_all: bool = False
    reject_all: bool = False


class SuggestionAcceptanceResponse(BaseModel):
    """Response após processar aceitação de sugestões."""
    success: bool
    accepted_count: int = 0
    rejected_count: int = 0
    updated_job_draft: Optional[Dict[str, Any]] = None
    next_stage_ready: bool = False
    error: Optional[str] = None
