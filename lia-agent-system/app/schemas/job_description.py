
"""
Schemas para geração de Job Description em duas versões:
- JD Preview (v1): Validação após coleta inicial com indicadores de sugestão da LIA
- JD Final (v2): Versão completa para publicação com todas as informações
"""
from datetime import datetime
from enum import Enum, StrEnum

from pydantic import BaseModel, Field, ConfigDict
from app.shared.types import WeDoBaseModel


class SuggestionSource(StrEnum):
    DETECTED = "detected"
    LIA_CATALOG = "lia_catalog"
    LIA_MARKET = "lia_market"
    COMPANY_DEFAULT = "company_default"
    RECRUITER = "recruiter"


class RequirementLevel(StrEnum):
    REQUIRED = "required"
    NICE_TO_HAVE = "nice_to_have"


class WorkModel(StrEnum):
    REMOTE = "remoto"
    HYBRID = "hibrido"
    ONSITE = "presencial"


class ContractType(StrEnum):
    CLT = "CLT"
    PJ = "PJ"
    ESTAGIO = "Estágio"
    TEMPORARIO = "Temporário"
    FREELANCER = "Freelancer"


class Priority(StrEnum):
    LOW = "baixa"
    MEDIUM = "media"
    HIGH = "alta"
    URGENT = "urgente"


class SuggestedItem(BaseModel):
    """Item com indicação de origem (detectado, sugerido pela LIA, etc.)"""
    value: str
    source: SuggestionSource = SuggestionSource.RECRUITER
    confidence: float | None = None
    is_new: bool = False


class Competency(BaseModel):
    """Competência técnica ou comportamental"""
    name: str
    level: RequirementLevel = RequirementLevel.REQUIRED
    source: SuggestionSource = SuggestionSource.RECRUITER
    years_experience: int | None = None
    proficiency: str | None = None
    is_new: bool = False


class Responsibility(BaseModel):
    """Responsabilidade do cargo"""
    description: str
    source: SuggestionSource = SuggestionSource.RECRUITER
    is_new: bool = False


class Benefit(BaseModel):
    """Benefício oferecido"""
    name: str
    description: str | None = None
    value: str | None = None


class CompensationData(BaseModel):
    """Dados de compensação"""
    model_config = ConfigDict(extra='forbid')

    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str = "BRL"
    show_salary: bool = True
    bonus_percentage: float | None = None
    bonus_description: str | None = None
    plr: str | None = None
    equity: str | None = None
    benefits: list[Benefit] = Field(default_factory=list)
    
    market_comparison: str | None = None
    market_percentile: int | None = None
    has_alert: bool = False
    alert_message: str | None = None


class InterviewStage(BaseModel):
    """Etapa do processo seletivo"""
    order: int
    name: str
    format: str | None = None
    duration: str | None = None
    description: str | None = None
    responsible: str | None = None
    responsible_email: str | None = None


class CompanyInfo(BaseModel):
    """Informações da empresa para o JD"""
    name: str
    about: str | None = None
    mission: str | None = None
    size: str | None = None
    industry: str | None = None
    values: list[dict[str, str]] = Field(default_factory=list)
    evp: dict[str, str] | None = None
    diversity_statement: str | None = None
    careers_url: str | None = None
    contact_email: str | None = None


class HiringManager(BaseModel):
    """Gestor da vaga (dados internos, não publicados)"""
    name: str
    email: str
    department: str | None = None


class JobMetadata(BaseModel):
    """Metadados internos da vaga (não publicados)"""
    hiring_manager: HiringManager | None = None
    is_confidential: bool = False
    priority: Priority = Priority.MEDIUM
    open_date: datetime | None = None
    target_date: datetime | None = None
    sla_days: int | None = None


class JobDescriptionBase(BaseModel):
    """Campos comuns entre v1 e v2"""
    title: str
    department: str | None = None
    seniority: str | None = None
    num_positions: int = 1
    
    work_model: WorkModel = WorkModel.HYBRID
    office_days_per_week: int | None = None
    contract_type: ContractType = ContractType.CLT
    location: str | None = None
    
    is_affirmative: bool = False
    affirmative_type: str | None = None
    
    description: str | None = None


class JobDescriptionPreview(JobDescriptionBase):
    """
    JD v1 - Preview de Validação
    
    Exibida após a coleta inicial para validar entendimento.
    Inclui indicadores de sugestões da LIA (💡).
    NÃO inclui Interview Process.
    """
    responsibilities: list[Responsibility] = Field(default_factory=list)
    
    technical_competencies: list[Competency] = Field(default_factory=list)
    behavioral_competencies: list[Competency] = Field(default_factory=list)
    
    compensation: CompensationData | None = None
    
    company: CompanyInfo | None = None
    
    suggestions_count: int = 0
    alerts_count: int = 0
    completeness_score: float = 0.0
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Desenvolvedor Python Sênior",
                "department": "Tecnologia",
                "seniority": "Sênior",
                "num_positions": 2,
                "work_model": "hibrido",
                "office_days_per_week": 2,
                "contract_type": "CLT",
                "location": "São Paulo, SP",
                "is_affirmative": False,
                "responsibilities": [
                    {"description": "Desenvolver APIs REST", "source": "detected", "is_new": False},
                    {"description": "Liderar squad de desenvolvimento", "source": "lia_catalog", "is_new": True}
                ],
                "technical_competencies": [
                    {"name": "Python", "level": "required", "source": "detected", "years_experience": 5},
                    {"name": "AWS", "level": "nice_to_have", "source": "lia_catalog", "is_new": True}
                ],
                "suggestions_count": 5,
                "completeness_score": 0.85
            }
        }


class JobDescriptionFinal(JobDescriptionBase):
    """
    JD v2 - Versão Final para Publicação
    
    Versão completa com todas as informações consolidadas.
    Inclui Interview Process, Apply At, etc.
    Sem indicadores de sugestão (versão limpa).
    """
    responsibilities: list[str] = Field(default_factory=list)
    
    required_technical: list[str] = Field(default_factory=list)
    required_behavioral: list[str] = Field(default_factory=list)
    nice_to_have: list[str] = Field(default_factory=list)
    
    compensation: CompensationData | None = None
    
    company: CompanyInfo | None = None
    
    interview_process: list[InterviewStage] = Field(default_factory=list)
    total_timeline: str | None = None
    
    apply_url: str | None = None
    contact_email: str | None = None
    
    metadata: JobMetadata | None = None
    
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Desenvolvedor Python Sênior",
                "department": "Tecnologia",
                "seniority": "Sênior",
                "num_positions": 2,
                "work_model": "hibrido",
                "office_days_per_week": 2,
                "contract_type": "CLT",
                "location": "São Paulo, SP",
                "responsibilities": [
                    "Desenvolver APIs REST de alta performance",
                    "Liderar squad de desenvolvimento",
                    "Mentoria de desenvolvedores júnior"
                ],
                "required_technical": ["Python (5+ anos)", "SQL", "AWS"],
                "required_behavioral": ["Resolução de Problemas", "Colaboração"],
                "nice_to_have": ["Docker", "Kubernetes"],
                "interview_process": [
                    {"order": 1, "name": "Triagem LIA", "format": "WhatsApp", "duration": "~10 min"},
                    {"order": 2, "name": "Entrevista RH", "format": "Vídeo", "duration": "30 min"}
                ],
                "total_timeline": "2-3 semanas",
                "apply_url": "https://careers.empresa.com/vaga-xyz"
            }
        }


class JDGenerationRequest(WeDoBaseModel):
    """Request para gerar Job Description"""
    job_id: str | None = None
    company_id: str
    recruiter_id: str | None = None
    
    title: str
    department: str | None = None
    seniority: str | None = None
    num_positions: int = 1
    
    work_model: WorkModel = WorkModel.HYBRID
    office_days_per_week: int | None = None
    contract_type: ContractType = ContractType.CLT
    location: str | None = None
    
    is_affirmative: bool = False
    affirmative_type: str | None = None
    
    description: str | None = None
    raw_input: str | None = None
    
    detected_responsibilities: list[str] = Field(default_factory=list)
    detected_technical_skills: list[str] = Field(default_factory=list)
    detected_behavioral_skills: list[str] = Field(default_factory=list)
    
    salary_min: float | None = None
    salary_max: float | None = None
    bonus_percentage: float | None = None
    
    hiring_manager_name: str | None = None
    hiring_manager_email: str | None = None
    
    is_confidential: bool = False
    priority: Priority = Priority.MEDIUM
    target_date: datetime | None = None
    
    interview_stages: list[InterviewStage] = Field(default_factory=list)


class JDPreviewResponse(BaseModel):
    """Response da geração de JD Preview"""
    success: bool
    preview: JobDescriptionPreview | None = None
    markdown: str | None = None
    suggestions_applied: int = 0
    alerts: list[str] = Field(default_factory=list)
    error: str | None = None


class JDFinalResponse(BaseModel):
    """Response da geração de JD Final"""
    success: bool
    final: JobDescriptionFinal | None = None
    markdown: str | None = None
    html: str | None = None
    ready_to_publish: bool = False
    missing_fields: list[str] = Field(default_factory=list)
    error: str | None = None
