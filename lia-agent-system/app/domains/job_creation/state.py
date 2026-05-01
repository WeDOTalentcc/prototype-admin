"""
JobCreationState — LangGraph state for the Wizard WSI pipeline.

Accumulative state that flows through F1->F6 + publish + calibration + handoff.
Each node reads what it needs and writes its output fields.

WSI Methodology mapping:
  intake_evaluation -> Pre-F1 (parse initial input)
  jd_enrichment     -> F1 (JdEnrichmentService)
  bigfive_extraction-> F2+F3 (Big Five + trait ranking)
  salary_benefits   -> salary validation
  competency_mapping-> F4+F5 (seniority + question distribution)
  wsi_questions     -> F6 (question generation)
  eligibility       -> pre-screening yes/no questions
  review_publish    -> readiness check
  publish_and_screen-> publish + auto-screening
  calibration       -> 3+ profile calibration
  handoff           -> navigate to job page
"""

from typing import Any, Dict, List, Literal, Optional

from typing_extensions import TypedDict


class BigFiveProfile(TypedDict, total=False):
    openness: float
    conscientiousness: float
    extraversion: float
    agreeableness: float
    stability: float
    evidences: Dict[str, List[str]]


class TraitRanking(TypedDict, total=False):
    trait: str
    score: float
    rank: int
    weight: float


class ScreeningQuestion(TypedDict, total=False):
    id: str
    question: str
    ideal_answer: str
    scoring_rubric: Dict[str, str]
    framework: Literal["CBI", "Bloom", "Dreyfus", "BigFive"]
    block: Literal["technical", "behavioral"]
    competency: Literal["technical", "behavioral", "logistical"]  # lia-hardening compat
    skill: str
    trait_ocean: Optional[str]
    bloom_level: Optional[int]
    dreyfus_level: Optional[int]
    weight: float
    source: str  # "wsi_wizard", "wsi_compact", "custom" — lia-hardening compat
    max_duration_s: int  # voice interview duration — lia-hardening compat
    approved: Optional[bool]  # HITL tracking (wizard-only)
    edited_text: Optional[str]  # HITL tracking (wizard-only)


class EligibilityQuestion(TypedDict, total=False):
    id: str
    question: str
    required_answer: Literal["yes", "no"]
    eliminatory: bool


class CalibrationCandidate(TypedDict, total=False):
    id: str
    name: str
    current_title: str
    current_company: str
    match_score: float
    match_criteria: List[Dict[str, Any]]
    decision: Optional[Literal["approved", "rejected"]]
    reason: Optional[str]


WizardStage = Literal[
    "intake",
    "jd_enrichment",
    "bigfive",
    "salary",
    "competency",
    "wsi_questions",
    "eligibility",
    "review",
    "publish",
    "calibration",
    "handoff",
    "done",
]

ScreeningMode = Literal["compact", "full"]


class JobCreationState(TypedDict, total=False):
    """Accumulative state for the job creation wizard.

    Each graph node reads its dependencies and writes its outputs.
    The state is persisted via LangGraph checkpointer (thread_id per wizard session).
    """

    # --- Session metadata ---
    session_id: str
    user_id: str
    workspace_id: int
    auth_token: str
    language: str  # default "pt-BR"

    # --- Current stage ---
    current_stage: WizardStage
    stage_history: List[WizardStage]
    error: Optional[str]

    # --- User input (raw) ---
    user_query: str  # latest user message
    conversation_messages: List[Dict[str, Any]]  # full chat history

    # --- Pre-F1: Intake ---
    raw_input: str  # original user text ("quero criar uma vaga de PM senior")
    parsed_title: Optional[str]
    parsed_department: Optional[str]
    parsed_seniority: Optional[str]
    parsed_location: Optional[str]
    parsed_model: Optional[str]  # remote/hybrid/onsite
    intake_confidence: float

    # --- F1: JD Enrichment ---
    jd_raw: Optional[str]  # recruiter's original JD text
    jd_enriched: Optional[Dict[str, Any]]  # EnrichedJobDescription from JdEnrichmentService
    jd_quality_score: float  # 0-100 deterministic
    jd_quality_warnings: List[str]
    jd_approved: Optional[bool]  # HITL point 1

    # --- F2+F3: Big Five + Trait Ranking ---
    bigfive_profile: Optional[BigFiveProfile]
    trait_rankings: List[TraitRanking]

    # --- Salary ---
    salary_min: Optional[int]
    salary_max: Optional[int]
    salary_currency: str  # default "BRL"
    benefits: List[str]
    salary_benchmark: Optional[Dict[str, Any]]

    # --- F4+F5: Competency + Distribution ---
    seniority_resolved: Optional[str]  # from seniority_resolver
    seniority_signals: List[Dict[str, Any]]  # 5 signals used
    screening_mode: Optional[ScreeningMode]  # recruiter chooses compact(7q) or full(12q)
    question_distribution: Optional[Dict[str, int]]  # {"technical": N, "behavioral": M}
    competency_tree: List[Dict[str, Any]]  # skills with weights

    # --- F6: WSI Questions ---
    wsi_questions: List[ScreeningQuestion]
    questions_approved: Optional[bool]  # HITL point 2
    questions_approval_details: List[Dict[str, Any]]  # per-question decisions

    # --- Eligibility ---
    eligibility_questions: List[EligibilityQuestion]

    # --- Review ---
    readiness_check: Optional[Dict[str, Any]]
    company_defaults_applied: List[str]  # which defaults from Settings were loaded

    # --- Publish ---
    job_id: Optional[int]  # Rails job ID after creation
    job_uid: Optional[str]
    publish_platforms: List[str]  # ["linkedin", "indeed", "website"]
    sourcing_mode: Optional[Literal["local", "global", "hybrid"]]
    contact_channels: List[str]  # ["email", "whatsapp", "phone"]
    share_link: Optional[str]
    screening_pipeline_id: Optional[str]
    auto_screen_enabled: bool

    # --- Calibration ---
    calibration_candidates: List[CalibrationCandidate]
    calibration_threshold: int  # default 3
    calibration_complete: bool

    # --- Handoff ---
    handoff_url: Optional[str]  # URL to the job page

    # --- WS protocol fields ---
    ws_stage_payload: Optional[Dict[str, Any]]  # last wizard_stage WS message sent
    requires_approval: bool  # current stage needs HITL
    completeness: float  # 0.0 to 1.0 overall wizard progress


# Stage order for progress calculation
STAGE_ORDER: List[WizardStage] = [
    "intake",
    "jd_enrichment",
    "bigfive",
    "salary",
    "competency",
    "wsi_questions",
    "eligibility",
    "review",
    "publish",
    "calibration",
    "handoff",
    "done",
]


def calculate_completeness(current_stage: WizardStage) -> float:
    """Calculate wizard progress as 0.0-1.0 based on current stage."""
    if current_stage not in STAGE_ORDER:
        return 0.0
    idx = STAGE_ORDER.index(current_stage)
    return round(idx / (len(STAGE_ORDER) - 1), 2)


# HITL approval stages
HITL_STAGES: set[WizardStage] = {"jd_enrichment", "wsi_questions"}
