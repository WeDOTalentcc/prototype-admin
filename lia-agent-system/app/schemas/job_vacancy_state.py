"""
Job Vacancy State schema for conversational job creation.
Tracks all fields, collection status, and workflow metadata.
"""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class TechnicalRequirement(BaseModel):
    """Individual technical requirement."""
    category: Literal["Linguagens", "Frameworks", "Banco de Dados", "Cloud", "Containers", "CI/CD", "Outros"]
    technology: str
    level: Literal["Básico", "Intermediário", "Avançado"]
    required: bool


class Language(BaseModel):
    """Language requirement."""
    language: str
    level: Literal["Básico", "Intermediário", "Avançado", "Fluente"]
    required: bool


class BehavioralCompetency(BaseModel):
    """Behavioral competency."""
    competency: str
    weight: Literal["Essencial", "Importante", "Desejável"]


# DUPLICATE_OF_INTENT: app/schemas/job_description.py:100 — state-tracking variant with similar 6-field shape (Sprint Q.4: M-bucket pending verify single canonical)
class InterviewStage(BaseModel):
    """Interview stage details."""
    stage_name: str
    interviewers: list[str]
    format: str  # "Comportamental", "Técnica", "Cultural"
    duration: int  # minutes
    scheduling_window: str  # "Terças e Quintas à tarde"
    has_script: bool = False


class ScreeningQuestion(BaseModel):
    """Screening question for candidates."""
    id: str
    question: str
    type: Literal["text", "multiple_choice", "rating"]
    expected_answer: str | None = None
    weight: int | None = None


class ScreeningQuestionsConfig(BaseModel):
    """Configuration for quick screening questions per job vacancy."""
    use_standard_screening: bool = True  # Use the 6 default questions
    custom_questions: list[str] = Field(default_factory=list)  # Custom questions to add
    questions_to_skip: list[str] = Field(default_factory=list)  # Default questions to skip
    use_wsi_after_screening: bool = True  # Continue with WSI after screening
    
    # The 6 standard screening questions (can be customized)
    standard_questions: list[dict[str, Any]] = Field(default_factory=lambda: [
        {"id": "interesse", "question": "O que te interessou nesta vaga?", "required": True},
        {"id": "disponibilidade", "question": "Qual sua disponibilidade para início?", "required": True},
        {"id": "pretensao_salarial", "question": "Qual sua pretensão salarial?", "required": True},
        {"id": "experiencia", "question": "Resuma sua experiência relevante para esta vaga.", "required": True},
        {"id": "modelo_trabalho", "question": "Qual modelo de trabalho você prefere (presencial/híbrido/remoto)?", "required": True},
        {"id": "outros_processos", "question": "Está participando de outros processos seletivos?", "required": False}
    ])


class SalaryRange(BaseModel):
    """Salary range with bonus."""
    min: float
    max: float
    currency: str = "BRL"
    bonus_min: float | None = None
    bonus_max: float | None = None
    bonus_criteria: str | None = None


class TeamComposition(BaseModel):
    """Team member composition."""
    role: str
    count: int
    level: str


class OrganizationalStructure(BaseModel):
    """Organizational structure."""
    direct_manager: str
    team_size: int
    team_composition: list[TeamComposition]


class WeeklyBreakdown(BaseModel):
    """Weekly timeline breakdown."""
    week: int
    focus: str
    deadline: str
    status: Literal["pending", "in_progress", "completed"] = "pending"


class Timeline(BaseModel):
    """Job vacancy timeline."""
    shortlist_deadline: str | None = None
    total_weeks: int
    weekly_breakdown: list[WeeklyBreakdown]


class GovernanceRules(BaseModel):
    """LIA autonomy levels."""
    auto_schedule_interviews: bool = False
    auto_send_negative_feedback: bool = False
    requires_validation_before_shortlist: bool = True


class SourcingStrategy(BaseModel):
    """Sourcing strategy for candidate search."""
    target_sectors: list[str] = Field(default_factory=list)
    target_segments: list[str] = Field(default_factory=list)
    target_companies: list[str] = Field(default_factory=list)
    excluded_companies: list[str] = Field(default_factory=list)
    geography_preference: str | None = None
    remote_acceptable: bool = True
    experience_range_min: int | None = None
    experience_range_max: int | None = None


class TalentPoolEstimate(BaseModel):
    """Estimate of available talent pool."""
    total_estimated: int
    local_database: int
    pearch_available: int
    breakdown_by_source: dict[str, int] = Field(default_factory=dict)
    confidence_score: float = 0.8


class MarketBenchmark(BaseModel):
    """Market salary benchmark data."""
    market_min: float
    market_max: float
    market_median: float
    percentile_25: float
    percentile_75: float
    sample_size: int
    data_source: str = "market_analysis"
    is_competitive: bool = True
    recommendation: str | None = None


class WSICompetencySuggestion(BaseModel):
    """WSI competency suggestion from analysis."""
    name: str
    type: Literal["technical", "behavioral", "cultural"]
    weight: float
    framework: str | None = None
    big_five_mapping: str | None = None
    is_critical: bool = False


class BiasAnalysis(BaseModel):
    """Inclusive bias analysis for job description."""
    overall_score: float
    issues_found: list[dict[str, str]] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    gendered_terms: list[str] = Field(default_factory=list)
    inclusive_alternatives: dict[str, str] = Field(default_factory=dict)
    is_inclusive: bool = True


class FieldStatus(BaseModel):
    """Track collection status per field."""
    field_name: str
    status: Literal["collected", "pending", "invalid"] = "pending"
    collected_at: datetime | None = None
    collected_from_message: str | None = None  # Message ID that provided this field


class JobVacancyState(BaseModel):
    """
    Complete state for job vacancy creation workflow.
    Tracks all fields, collection status, and workflow metadata.
    """
    
    # =============================================
    # BASIC INFORMATION
    # =============================================
    job_title: str | None = None
    department: str | None = None
    location: str | None = None
    work_model: Literal["presencial", "híbrido", "remoto"] | None = None
    seniority: Literal["Júnior", "Pleno", "Sênior", "Especialista"] | None = None
    employment_type: Literal["CLT", "PJ", "Temporário"] | None = None
    is_confidential: bool | None = None  # Legacy - use visibility instead
    
    # NEW: Visibility Control
    # public: todos recrutadores da empresa veem
    # internal: só equipe interna, não publica em job boards  
    # confidential: só owner + access_list + admin veem
    # hidden: só admin vê
    visibility: Literal["public", "internal", "confidential", "hidden"] | None = "public"
    
    # Lista de acesso para vagas confidenciais (emails que podem ver)
    access_list: list[str] = Field(default_factory=list)
    
    # Nome mascarado para publicação anônima
    masked_company_name: str | None = None
    
    # Exclusão de sincronização com ATS externos
    exclude_from_sync: bool = False
    
    # =============================================
    # REMUNERATION
    # =============================================
    salary_range: SalaryRange | None = None
    benefits: list[str] = Field(default_factory=list)
    
    # =============================================
    # ORGANIZATIONAL STRUCTURE
    # =============================================
    organizational_structure: OrganizationalStructure | None = None
    
    # =============================================
    # TECHNICAL REQUIREMENTS
    # =============================================
    technical_requirements: list[TechnicalRequirement] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)  # Legacy simple list
    preferred_skills: list[str] = Field(default_factory=list)
    
    # =============================================
    # LANGUAGES & COMPETENCIES
    # =============================================
    languages: list[Language] = Field(default_factory=list)
    behavioral_competencies: list[BehavioralCompetency] = Field(default_factory=list)
    
    # =============================================
    # INTERVIEW PROCESS
    # =============================================
    interview_stages: list[InterviewStage] = Field(default_factory=list)
    screening_questions: list[ScreeningQuestion] = Field(default_factory=list)
    screening_config: ScreeningQuestionsConfig | None = None  # Job-specific screening configuration
    
    # =============================================
    # TIMELINE & GOVERNANCE
    # =============================================
    timeline: Timeline | None = None
    governance_rules: GovernanceRules | None = None
    
    # =============================================
    # TARGETING (for sourcing)
    # =============================================
    target_sector: str | None = None  # "Fintechs", "Bancos Digitais"
    target_segment: str | None = None  # "Meios de Pagamento"
    target_audience: str | None = None
    sourcing_strategy: SourcingStrategy | None = None
    talent_pool_estimate: TalentPoolEstimate | None = None
    
    # =============================================
    # MARKET ANALYSIS
    # =============================================
    market_benchmark: MarketBenchmark | None = None
    
    # =============================================
    # WSI COMPETENCIES (Auto-suggested)
    # =============================================
    wsi_competencies: list[WSICompetencySuggestion] = Field(default_factory=list)
    wsi_competencies_confirmed: bool = False
    
    # =============================================
    # JOB DESCRIPTION
    # =============================================
    job_description_generated: str | None = None
    bias_analysis: BiasAnalysis | None = None
    job_description_approved: bool = False
    
    # =============================================
    # WHATSAPP TEMPLATE
    # =============================================
    whatsapp_template_type: Literal["cold", "reengagement", "confidential"] | None = None
    selected_communication_templates: list[str] = Field(default_factory=list)
    
    # =============================================
    # ONBOARDING & WORKFLOW TRACKING
    # =============================================
    onboarding_completed: bool = False
    current_step: int = 1
    total_steps: int = 13
    
    # =============================================
    # ADDITIONAL DATA
    # =============================================
    description: str | None = None
    years_experience: int | None = None
    manager_name: str | None = None
    manager_email: str | None = None
    recruiter_name: str | None = None
    recruiter_email: str | None = None
    
    # =============================================
    # WORKFLOW METADATA
    # =============================================
    fields_collected: list[str] = Field(default_factory=list)  # List of field names collected
    fields_pending: list[str] = Field(default_factory=list)  # List of field names still needed
    field_statuses: list[FieldStatus] = Field(default_factory=list)  # Detailed status tracking
    
    current_panel: str | None = None  # "remuneracao", "requisitos_tecnicos", etc
    current_frame: str | None = None  # "matriz_tecnica", "cronograma", etc
    
    change_requests: list[dict[str, Any]] = Field(default_factory=list)  # History of changes
    
    needs_confirmation: bool = False
    ready_to_publish: bool = False
    published_at: datetime | None = None
    
    # Next question to ask (for routing)
    next_question: str | None = None
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def mark_field_collected(self, field_name: str, message_id: str | None = None):
        """Mark a field as collected."""
        if field_name not in self.fields_collected:
            self.fields_collected.append(field_name)
        
        if field_name in self.fields_pending:
            self.fields_pending.remove(field_name)
        
        # Update field status
        existing_status = next((fs for fs in self.field_statuses if fs.field_name == field_name), None)
        if existing_status:
            existing_status.status = "collected"
            existing_status.collected_at = datetime.utcnow()
            existing_status.collected_from_message = message_id
        else:
            self.field_statuses.append(FieldStatus(
                field_name=field_name,
                status="collected",
                collected_at=datetime.utcnow(),
                collected_from_message=message_id
            ))
        
        self.updated_at = datetime.utcnow()
    
    def get_next_pending_field(self) -> str | None:
        """Get next field to collect based on 13-step priority."""
        priority_fields = [
            "onboarding",
            "job_title",
            "seniority",
            "is_confidential",
            "salary_range",
            "organizational_structure",
            "sourcing_strategy",
            "technical_requirements",
            "wsi_competencies",
            "languages",
            "behavioral_competencies",
            "interview_stages",
            "communication_templates",
            "screening_questions",
            "governance_rules",
            "job_description",
            "publication"
        ]
        
        for field in priority_fields:
            if field not in self.fields_collected:
                return field
        
        return None
    
    def get_step_for_field(self, field: str) -> int:
        """Get step number for a given field."""
        step_mapping = {
            "onboarding": 1,
            "job_title": 2,
            "salary_range": 3,
            "organizational_structure": 4,
            "technical_requirements": 5,
            "sourcing_strategy": 6,
            "wsi_competencies": 7,
            "interview_stages": 8,
            "timeline": 9,
            "governance_rules": 10,
            "communication_templates": 11,
            "job_description": 12,
            "publication": 13
        }
        return step_mapping.get(field, 0)
    
    def calculate_completion_percentage(self) -> float:
        """Calculate completion percentage based on 13 steps."""
        all_steps = [
            "onboarding", "job_title", "salary_range", "organizational_structure",
            "technical_requirements", "sourcing_strategy", "wsi_competencies",
            "interview_stages", "timeline", "governance_rules",
            "communication_templates", "job_description", "publication"
        ]
        collected_count = sum(1 for f in all_steps if f in self.fields_collected)
        return (collected_count / len(all_steps)) * 100
    
    def is_ready_for_publication(self) -> bool:
        """Check if all required fields are collected for publication."""
        required_fields = [
            "job_title", "seniority", "is_confidential",
            "salary_range", "technical_requirements", "interview_stages",
            "governance_rules", "job_description"
        ]
        return all(f in self.fields_collected for f in required_fields)
    
    def get_workflow_summary(self) -> dict[str, Any]:
        """Get summary of workflow progress for dashboard."""
        completed_steps = len([f for f in self.fields_collected if self.get_step_for_field(f) > 0])
        return {
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "completed_steps": completed_steps,
            "completion_percentage": self.calculate_completion_percentage(),
            "is_ready": self.is_ready_for_publication(),
            "has_wsi_competencies": len(self.wsi_competencies) > 0,
            "has_bias_analysis": self.bias_analysis is not None,
            "has_pool_estimate": self.talent_pool_estimate is not None
        }
