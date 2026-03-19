"""
State Machine Types for LangGraph-style Job Wizard.

Defines the state structure and stage enum for the multi-step
reasoning engine used in job creation wizard.
"""
from typing import TypedDict, List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


class WizardStage(str, Enum):
    """Stages in the job wizard flow."""
    INITIAL = "initial"
    TITLE_DEPARTMENT = "title_department"
    JOB_SUMMARY = "job_summary"
    SALARY = "salary"
    COMPETENCIES = "competencies"
    SCREENING = "screening"
    REVIEW = "review"
    COMPLETE = "complete"


class WizardIntent(str, Enum):
    """Possible user intents in the wizard."""
    # Initial journey choices
    START_FROM_SCRATCH = "start_from_scratch"  # User wants to create job from scratch
    USE_EXISTING = "use_existing"              # User wants to duplicate/adapt existing job
    USE_TEMPLATE = "use_template"              # User wants to use a template
    
    # Standard wizard intents
    PROVIDE_INFO = "provide_info"
    ASK_QUESTION = "ask_question"
    CONFIRM = "confirm"
    REJECT = "reject"
    MODIFY = "modify"
    SKIP = "skip"
    GO_BACK = "go_back"
    HELP = "help"
    UNKNOWN = "unknown"


class ResponseType(str, Enum):
    """Types of responses LIA can generate."""
    ASK_CLARIFY = "ask_clarify"      # Pedir esclarecimento
    PROPOSE = "propose"               # Propor informação
    CONFIRM = "confirm"               # Confirmar e avançar
    SUMMARIZE = "summarize"           # Resumir progresso
    CORRECT = "correct"               # Corrigir informação
    WELCOME = "welcome"               # Boas-vindas inicial
    WAITING = "waiting"               # Aguardando confirmação


class JobWizardState(TypedDict):
    """
    State for the job wizard graph.
    
    This is the central state object passed between nodes.
    All nodes can read and write to this state.
    """
    messages: List[Dict[str, str]]
    current_stage: str
    
    job_draft: Dict[str, Any]
    confidence_scores: Dict[str, float]
    
    reasoning_steps: List[str]
    next_action: Optional[str]
    intent: Optional[str]
    
    tool_calls: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    
    session_id: str
    company_id: str
    user_id: str
    
    should_continue: bool
    needs_clarification: bool
    error: Optional[str]
    
    response_text: Optional[str]
    extracted_fields: Dict[str, Any]
    current_node: str
    auto_transition: bool
    awaiting_confirmation: bool


class ReasoningStep(BaseModel):
    """A single step in the reasoning chain."""
    step_number: int = Field(..., description="Step order in the chain")
    node_name: str = Field(..., description="Name of the node executing this step")
    action: str = Field(..., description="Description of what this step does")
    input_summary: Optional[str] = Field(default=None, description="Summary of inputs used")
    output_summary: Optional[str] = Field(default=None, description="Summary of outputs produced")
    duration_ms: Optional[float] = Field(default=None, description="Execution time in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class GraphExecutionLog(BaseModel):
    """Log of a complete graph execution."""
    session_id: str
    execution_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_duration_ms: Optional[float] = None
    nodes_visited: List[str] = Field(default_factory=list)
    reasoning_steps: List[ReasoningStep] = Field(default_factory=list)
    final_state: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    success: bool = True


class IntentClassificationResult(BaseModel):
    """Result from intent classification node."""
    intent: WizardIntent
    confidence: float = Field(ge=0, le=1)
    entities: Dict[str, Any] = Field(default_factory=dict)
    requires_extraction: bool = False
    requires_tool_call: bool = False


class FieldExtractionResult(BaseModel):
    """Result from field extraction node."""
    extracted_fields: Dict[str, Any] = Field(default_factory=dict)
    confidence_scores: Dict[str, float] = Field(default_factory=dict)
    unresolved_fields: List[str] = Field(default_factory=list)
    validation_errors: List[str] = Field(default_factory=list)


class ToolRoutingDecision(BaseModel):
    """Decision from tool router node."""
    should_call_tools: bool = False
    tools_to_call: List[Dict[str, Any]] = Field(default_factory=list)
    reasoning: str = ""
    skip_reason: Optional[str] = None


class StageTransitionDecision(BaseModel):
    """Decision from stage transition node."""
    should_advance: bool = False
    target_stage: Optional[WizardStage] = None
    should_loop: bool = False
    completion_percentage: float = Field(default=0, ge=0, le=100)
    missing_fields: List[str] = Field(default_factory=list)
    reasoning: str = ""


def create_initial_state(
    session_id: str,
    company_id: str,
    user_id: str,
    user_message: str,
    existing_draft: Optional[Dict[str, Any]] = None,
    current_stage: str = WizardStage.INITIAL.value
) -> JobWizardState:
    """
    Create an initial state for a new graph execution.
    
    Args:
        session_id: Unique session identifier
        company_id: Company ID for multi-tenancy
        user_id: User making the request
        user_message: Initial user message
        existing_draft: Optional existing job draft to continue
        current_stage: Starting stage
        
    Returns:
        Initialized JobWizardState
    """
    return {
        "messages": [{"role": "user", "content": user_message}],
        "current_stage": current_stage,
        "job_draft": existing_draft or {},
        "confidence_scores": {},
        "reasoning_steps": [],
        "next_action": None,
        "intent": None,
        "tool_calls": [],
        "tool_results": [],
        "session_id": session_id,
        "company_id": company_id,
        "user_id": user_id,
        "should_continue": True,
        "needs_clarification": False,
        "error": None,
        "response_text": None,
        "extracted_fields": {},
        "current_node": "start",
        "auto_transition": False,
        "awaiting_confirmation": False,
    }


def get_stage_order() -> List[WizardStage]:
    """Get the ordered list of wizard stages."""
    return [
        WizardStage.INITIAL,
        WizardStage.TITLE_DEPARTMENT,
        WizardStage.JOB_SUMMARY,
        WizardStage.SALARY,
        WizardStage.COMPETENCIES,
        WizardStage.SCREENING,
        WizardStage.REVIEW,
        WizardStage.COMPLETE
    ]


def get_next_stage(current_stage: WizardStage) -> Optional[WizardStage]:
    """Get the next stage in the wizard flow."""
    stages = get_stage_order()
    try:
        current_index = stages.index(current_stage)
        if current_index < len(stages) - 1:
            return stages[current_index + 1]
    except ValueError:
        pass
    return None


def get_previous_stage(current_stage: WizardStage) -> Optional[WizardStage]:
    """Get the previous stage in the wizard flow."""
    stages = get_stage_order()
    try:
        current_index = stages.index(current_stage)
        if current_index > 0:
            return stages[current_index - 1]
    except ValueError:
        pass
    return None


CANONICAL_FIELD_SCHEMA: Dict[str, Dict[str, Any]] = {
    "title": {"type": "string", "label": "Cargo", "panel_key": "cargo"},
    "department": {"type": "string", "label": "Departamento/Área", "panel_key": "departamento"},
    "seniority": {"type": "string", "label": "Senioridade", "panel_key": "senioridadeIdiomas"},
    "location": {"type": "string", "label": "Localização", "panel_key": "localizacao"},
    "work_model": {"type": "string", "label": "Modelo de Trabalho", "panel_key": "modeloTrabalho"},
    "manager": {"type": "string", "label": "Gestor/Líder", "panel_key": "gestorArea"},
    "manager_email": {"type": "string", "label": "Email do Gestor", "panel_key": None},
    "salary_min": {"type": "number", "label": "Salário Mínimo", "panel_key": "salario"},
    "salary_max": {"type": "number", "label": "Salário Máximo", "panel_key": "salario"},
    "currency": {"type": "string", "label": "Moeda", "panel_key": None},
    "required_skills": {"type": "array", "label": "Competências Técnicas", "panel_key": "competenciasTecnicas"},
    "soft_skills": {"type": "array", "label": "Competências Comportamentais", "panel_key": "competenciasComportamentais"},
    "responsibilities": {"type": "array", "label": "Responsabilidades", "panel_key": "responsabilidades"},
    "experience": {"type": "string", "label": "Experiência Mínima", "panel_key": "experienciaMinima"},
    "education_level": {"type": "string", "label": "Formação", "panel_key": "formacao"},
    "languages": {"type": "array", "label": "Idiomas", "panel_key": "idiomas"},
    "certifications": {"type": "array", "label": "Certificações", "panel_key": "certificacoes"},
    "tools": {"type": "array", "label": "Ferramentas", "panel_key": "ferramentas"},
    "benefits": {"type": "array", "label": "Benefícios", "panel_key": "beneficiosMencionados"},
    "bonus": {"type": "string", "label": "Bônus", "panel_key": "bonus"},
    "contract_type": {"type": "string", "label": "Tipo de Contrato", "panel_key": "tipoContrato"},
    "screening_questions": {"type": "array", "label": "Perguntas de Triagem", "panel_key": None},
    "is_affirmative": {"type": "boolean", "label": "Vaga Afirmativa", "panel_key": "isAffirmative"},
    "affirmative_criteria": {"type": "string", "label": "Critérios Afirmativos", "panel_key": "affirmativeCriteriaPrimary"},
    "deadline": {"type": "string", "label": "Prazo", "panel_key": None},
}

STAGE_REQUIRED_FIELDS: Dict[WizardStage, List[str]] = {
    WizardStage.INITIAL: [],
    WizardStage.TITLE_DEPARTMENT: ["title", "department"],
    WizardStage.JOB_SUMMARY: [],
    WizardStage.SALARY: ["salary_min", "salary_max"],
    WizardStage.COMPETENCIES: ["required_skills"],
    WizardStage.SCREENING: [],
    WizardStage.REVIEW: [],
    WizardStage.COMPLETE: []
}


STAGE_OPTIONAL_FIELDS: Dict[WizardStage, List[str]] = {
    WizardStage.INITIAL: ["manager", "responsibilities"],
    WizardStage.TITLE_DEPARTMENT: ["seniority", "location", "work_model", "manager", "responsibilities"],
    WizardStage.JOB_SUMMARY: ["responsibilities", "required_skills", "soft_skills"],
    WizardStage.SALARY: ["bonus", "benefits", "currency"],
    WizardStage.COMPETENCIES: ["soft_skills", "education_level", "certifications", "languages", "tools", "experience"],
    WizardStage.SCREENING: ["screening_questions", "is_affirmative", "affirmative_criteria"],
    WizardStage.REVIEW: [],
    WizardStage.COMPLETE: []
}


STAGE_MINIMUM_FIELDS: Dict[WizardStage, List[str]] = {
    WizardStage.INITIAL: ["title"],
    WizardStage.TITLE_DEPARTMENT: ["title", "department"],
    WizardStage.JOB_SUMMARY: ["title", "department"],
    WizardStage.SALARY: ["salary_min", "salary_max"],
    WizardStage.COMPETENCIES: ["required_skills"],
    WizardStage.SCREENING: [],
    WizardStage.REVIEW: [],
    WizardStage.COMPLETE: []
}


AUTO_TRANSITION_CONFIDENCE_THRESHOLD: float = 0.7

STAGE_REQUIRES_CONFIRMATION: Dict[WizardStage, bool] = {
    WizardStage.INITIAL: True,
    WizardStage.TITLE_DEPARTMENT: True,
    WizardStage.JOB_SUMMARY: True,
    WizardStage.SALARY: True,
    WizardStage.COMPETENCIES: True,
    WizardStage.SCREENING: True,
    WizardStage.REVIEW: True,
    WizardStage.COMPLETE: False
}


def calculate_stage_readiness(job_draft: Dict[str, Any], stage: WizardStage) -> float:
    """
    Calculate readiness score for advancing from current stage.
    
    Returns a value between 0.0 and 1.0 indicating how ready the stage is
    for auto-transition based on minimum required fields.
    """
    minimum_fields = STAGE_MINIMUM_FIELDS.get(stage, [])
    if not minimum_fields:
        return 1.0
    filled = [f for f in minimum_fields if job_draft.get(f)]
    return len(filled) / len(minimum_fields)


def calculate_average_confidence(confidence_scores: Dict[str, float], fields: List[str]) -> float:
    """
    Calculate average confidence score for a set of fields.
    
    Returns the average confidence for filled fields, or 0.0 if no fields have scores.
    """
    if not fields or not confidence_scores:
        return 0.0
    
    relevant_scores = [confidence_scores.get(f, 0.0) for f in fields if f in confidence_scores]
    if not relevant_scores:
        return 0.8
    
    return sum(relevant_scores) / len(relevant_scores)


def should_auto_advance(
    job_draft: Dict[str, Any],
    confidence_scores: Dict[str, float],
    stage: WizardStage
) -> tuple[bool, str]:
    """
    Determine if the wizard should automatically advance to the next stage.
    
    Uses minimum viable completion and confidence thresholds to decide.
    
    Returns:
        Tuple of (should_advance, reasoning)
    """
    minimum_fields = STAGE_MINIMUM_FIELDS.get(stage, [])
    
    if not minimum_fields:
        return True, "Stage has no minimum field requirements"
    
    filled_fields = [f for f in minimum_fields if job_draft.get(f)]
    missing_fields = [f for f in minimum_fields if not job_draft.get(f)]
    
    if missing_fields:
        return False, f"Missing minimum fields: {missing_fields}"
    
    avg_confidence = calculate_average_confidence(confidence_scores, filled_fields)
    
    if avg_confidence >= AUTO_TRANSITION_CONFIDENCE_THRESHOLD:
        return True, f"All minimum fields present with avg confidence {avg_confidence:.2f}"
    else:
        return False, f"Confidence too low ({avg_confidence:.2f} < {AUTO_TRANSITION_CONFIDENCE_THRESHOLD})"


BACKEND_TO_FRONTEND_FIELDS: Dict[str, str] = {
    "title": "job_title",
    "required_skills": "technical_skills",
    "soft_skills": "behavioral_skills",
    "screening_questions": "wsi_questions",
    "affirmative_criteria": "affirmative_criteria_primary",
}


FRONTEND_TO_BACKEND_FIELDS: Dict[str, str] = {
    "job_title": "title",
    "technical_skills": "required_skills",
    "behavioral_skills": "soft_skills",
    "wsi_questions": "screening_questions",
    "affirmative_criteria_primary": "affirmative_criteria",
}


def normalize_fields_for_frontend(backend_fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize backend field names to frontend expected names.
    
    Transforms:
    - title → job_title
    - required_skills → technical_skills
    - soft_skills → behavioral_skills
    - screening_questions → wsi_questions
    - affirmative_criteria → affirmative_criteria_primary
    
    Also keeps original fields for backwards compatibility.
    
    Args:
        backend_fields: Dictionary with backend field names
        
    Returns:
        Dictionary with both normalized frontend names and original backend names
    """
    normalized = {}
    
    for key, value in backend_fields.items():
        if value is None:
            continue
            
        # Add normalized name if mapping exists
        if key in BACKEND_TO_FRONTEND_FIELDS:
            frontend_key = BACKEND_TO_FRONTEND_FIELDS[key]
            normalized[frontend_key] = value
        
        # Always keep original key too for backwards compatibility
        normalized[key] = value
    
    return normalized


def normalize_fields_from_frontend(frontend_fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize frontend field names to backend expected names.
    
    Transforms:
    - job_title → title
    - technical_skills → required_skills
    - behavioral_skills → soft_skills
    - wsi_questions → screening_questions
    - affirmative_criteria_primary → affirmative_criteria
    
    Also keeps original fields for backwards compatibility.
    
    Args:
        frontend_fields: Dictionary with frontend field names
        
    Returns:
        Dictionary with both normalized backend names and original frontend names
    """
    normalized = {}
    
    for key, value in frontend_fields.items():
        if value is None:
            continue
            
        # Add normalized name if mapping exists
        if key in FRONTEND_TO_BACKEND_FIELDS:
            backend_key = FRONTEND_TO_BACKEND_FIELDS[key]
            normalized[backend_key] = value
        
        # Always keep original key too
        normalized[key] = value
    
    return normalized
