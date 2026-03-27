"""
Schemas para geração de Job Description em duas versões:
- JD Preview (v1): Validação após coleta inicial com indicadores de sugestão da LIA
- JD Final (v2): Versão completa para publicação com todas as informações
"""
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class SuggestionSource(str, Enum):
    DETECTED = "detected"
    LIA_CATALOG = "lia_catalog"
    LIA_MARKET = "lia_market"
    COMPANY_DEFAULT = "company_default"
    RECRUITER = "recruiter"


class RequirementLevel(str, Enum):
    REQUIRED = "required"
    NICE_TO_HAVE = "nice_to_have"


class WorkModel(str, Enum):
    REMOTE = "remoto"
    HYBRID = "hibrido"
    ONSITE = "presencial"


class ContractType(str, Enum):
    CLT = "CLT"
    PJ = "PJ"
    ESTAGIO = "Estágio"
    TEMPORARIO = "Temporário"
    FREELANCER = "Freelancer"


class Priority(str, Enum):
    LOW = "baixa"
    MEDIUM = "media"
    HIGH = "alta"
    URGENT = "urgente"


class SuggestedItem(BaseModel):
    """Item com indicação de origem (detectado, sugerido pela LIA, etc.)"""
    value: str
    source: SuggestionSource = SuggestionSource.RECRUITER
    confidence: Optional[float] = None
    is_new: bool = False


class Competency(BaseModel):
    """Competência técnica ou comportamental"""
    name: str
    level: RequirementLevel = RequirementLevel.REQUIRED
    source: SuggestionSource = SuggestionSource.RECRUITER
    years_experience: Optional[int] = None
    proficiency: Optional[str] = None
    is_new: bool = False


class Responsibility(BaseModel):
    """Responsabilidade do cargo"""
    description: str
    source: SuggestionSource = SuggestionSource.RECRUITER
    is_new: bool = False


class Benefit(BaseModel):
    """Benefício oferecido"""
    name: str
    description: Optional[str] = None
    value: Optional[str] = None


class CompensationData(BaseModel):
    """Dados de compensação"""
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "BRL"
    show_salary: bool = True
    bonus_percentage: Optional[float] = None
    bonus_description: Optional[str] = None
    plr: Optional[str] = None
    equity: Optional[str] = None
    benefits: List[Benefit] = Field(default_factory=list)
    
    market_comparison: Optional[str] = None
    market_percentile: Optional[int] = None
    has_alert: bool = False
    alert_message: Optional[str] = None


class InterviewStage(BaseModel):
    """Etapa do processo seletivo"""
    order: int
    name: str
    format: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None
    responsible: Optional[str] = None
    responsible_email: Optional[str] = None


class CompanyInfo(BaseModel):
    """Informações da empresa para o JD"""
    name: str
    about: Optional[str] = None
    mission: Optional[str] = None
    size: Optional[str] = None
    industry: Optional[str] = None
    values: List[Dict[str, str]] = Field(default_factory=list)
    evp: Optional[Dict[str, str]] = None
    diversity_statement: Optional[str] = None
    careers_url: Optional[str] = None
    contact_email: Optional[str] = None


class HiringManager(BaseModel):
    """Gestor da vaga (dados internos, não publicados)"""
    name: str
    email: str
    department: Optional[str] = None


class JobMetadata(BaseModel):
    """Metadados internos da vaga (não publicados)"""
    hiring_manager: Optional[HiringManager] = None
    is_confidential: bool = False
    priority: Priority = Priority.MEDIUM
    open_date: Optional[datetime] = None
    target_date: Optional[datetime] = None
    sla_days: Optional[int] = None


class JobDescriptionBase(BaseModel):
    """Campos comuns entre v1 e v2"""
    title: str
    department: Optional[str] = None
    seniority: Optional[str] = None
    num_positions: int = 1
    
    work_model: WorkModel = WorkModel.HYBRID
    office_days_per_week: Optional[int] = None
    contract_type: ContractType = ContractType.CLT
    location: Optional[str] = None
    
    is_affirmative: bool = False
    affirmative_type: Optional[str] = None
    
    description: Optional[str] = None


class JobDescriptionPreview(JobDescriptionBase):
    """
    JD v1 - Preview de Validação
    
    Exibida após a coleta inicial para validar entendimento.
    Inclui indicadores de sugestões da LIA (💡).
    NÃO inclui Interview Process.
    """
    responsibilities: List[Responsibility] = Field(default_factory=list)
    
    technical_competencies: List[Competency] = Field(default_factory=list)
    behavioral_competencies: List[Competency] = Field(default_factory=list)
    
    compensation: Optional[CompensationData] = None
    
    company: Optional[CompanyInfo] = None
    
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
    responsibilities: List[str] = Field(default_factory=list)
    
    required_technical: List[str] = Field(default_factory=list)
    required_behavioral: List[str] = Field(default_factory=list)
    nice_to_have: List[str] = Field(default_factory=list)
    
    compensation: Optional[CompensationData] = None
    
    company: Optional[CompanyInfo] = None
    
    interview_process: List[InterviewStage] = Field(default_factory=list)
    total_timeline: Optional[str] = None
    
    apply_url: Optional[str] = None
    contact_email: Optional[str] = None
    
    metadata: Optional[JobMetadata] = None
    
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


class JDGenerationRequest(BaseModel):
    """Request para gerar Job Description"""
    job_id: Optional[str] = None
    company_id: str
    recruiter_id: Optional[str] = None
    
    title: str
    department: Optional[str] = None
    seniority: Optional[str] = None
    num_positions: int = 1
    
    work_model: WorkModel = WorkModel.HYBRID
    office_days_per_week: Optional[int] = None
    contract_type: ContractType = ContractType.CLT
    location: Optional[str] = None
    
    is_affirmative: bool = False
    affirmative_type: Optional[str] = None
    
    description: Optional[str] = None
    raw_input: Optional[str] = None
    
    detected_responsibilities: List[str] = Field(default_factory=list)
    detected_technical_skills: List[str] = Field(default_factory=list)
    detected_behavioral_skills: List[str] = Field(default_factory=list)
    
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    bonus_percentage: Optional[float] = None
    
    hiring_manager_name: Optional[str] = None
    hiring_manager_email: Optional[str] = None
    
    is_confidential: bool = False
    priority: Priority = Priority.MEDIUM
    target_date: Optional[datetime] = None
    
    interview_stages: List[InterviewStage] = Field(default_factory=list)


class JDPreviewResponse(BaseModel):
    """Response da geração de JD Preview"""
    success: bool
    preview: Optional[JobDescriptionPreview] = None
    markdown: Optional[str] = None
    suggestions_applied: int = 0
    alerts: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class JDFinalResponse(BaseModel):
    """Response da geração de JD Final"""
    success: bool
    final: Optional[JobDescriptionFinal] = None
    markdown: Optional[str] = None
    html: Optional[str] = None
    ready_to_publish: bool = False
    missing_fields: List[str] = Field(default_factory=list)
    error: Optional[str] = None
