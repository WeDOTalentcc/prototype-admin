"""Single source of truth for wizard contracts shared with the frontend.

Audit finding **N-12** (Rev 4) — the recruiter UI was carrying a
hand-maintained ``wizard-types.ts`` (~250 lines) that drifted from the
Python ``JobCreationState`` ``TypedDict`` whenever a node added or
renamed a field. This module exposes Pydantic v2 ``BaseModel``s that
mirror the runtime ``TypedDict``s and feed
``scripts/generate_wizard_types.py``, which produces
``plataforma-lia/src/types/generated/wizard-contract.ts`` deterministically.

**Authoring rules**

- Fields here MUST track 1:1 with the runtime ``TypedDict``s in
  ``app/domains/job_creation/state.py`` (and the payload models in
  ``app/domains/job_creation/schemas.py``). When you add or rename a
  field there, mirror the change here in the same PR — the
  ``check:wizard-types`` npm script enforces "no drift" in CI.
- Only contract data goes here. Internal-only fields (e.g.
  ``auth_token``, server-side audit blobs) stay out of the export so
  they never leak to the browser.
- Use ``Field(..., description="…")`` whenever the meaning is not
  obvious from the name — the description ends up as a JSDoc comment in
  the generated TypeScript.
- Keep the export list ``WIZARD_CONTRACT_MODELS`` in sync with what you
  want shipped. The generator only emits what is listed there.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


WizardStage = Literal[
    "intake",
    "jd_enrichment",
    # Sprint Pipeline Templates 2026-05-26 — Opção B (Paulo aprovou):
    # stage formal entre jd_enrichment e bigfive. LIA pergunta qual template
    # de pipeline de recrutamento aplicar (Médicos Afya / Liderança / TI / etc.),
    # ou usar padrão da empresa. Pipeline define a forma estrutural do processo —
    # toda config posterior (bigfive/salary/competency/wsi_questions) depende dele.
    # Skippable: recrutador pode escolher "Padrão da Empresa" e seguir.
    "pipeline_template",
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
    "scheduling",
]

ScreeningMode = Literal["compact", "full"]
SourcingMode = Literal["local", "global", "hybrid"]
QuestionFramework = Literal["CBI", "Bloom", "Dreyfus", "BigFive"]
QuestionBlock = Literal["technical", "behavioral"]
QuestionCompetency = Literal["technical", "behavioral", "logistical"]
EligibilityAnswer = Literal["yes", "no"]
CalibrationDecision = Literal["approved", "rejected"]


class _ContractModel(BaseModel):
    """Base for every exported model.

    ``populate_by_name`` lets the frontend send camelCase or snake_case
    aliases without breaking; ``extra='forbid'`` keeps the contract
    tight in tests but is relaxed for the runtime serializer (we
    instantiate from runtime ``TypedDict``s that may carry extra
    transitional fields during a multi-PR migration).
    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class BigFiveProfileContract(_ContractModel):
    """OCEAN scores extracted from the recruiter brief (F2)."""

    openness: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    conscientiousness: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    extraversion: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    agreeableness: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    stability: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    evidences: Optional[Dict[str, List[str]]] = Field(
        default=None,
        description="Per-trait list of textual evidence quotes from the brief.",
    )


class TraitRankingContract(_ContractModel):
    """One Big Five trait after F3 ranking."""

    trait: str
    score: float = Field(..., ge=0.0, le=1.0)
    rank: int = Field(..., ge=1, le=5)
    weight: float = Field(..., ge=0.0, le=1.0)


class ScreeningQuestionContract(_ContractModel):
    """A single WSI screening question (F6)."""

    id: str
    question: str
    ideal_answer: str
    scoring_rubric: Dict[str, str] = Field(default_factory=dict)
    framework: QuestionFramework
    block: QuestionBlock
    competency: QuestionCompetency = Field(
        ...,
        description=(
            "Coarse bucket used by the voice interview UI — "
            "behavioral/technical/logistical."
        ),
    )
    skill: str
    trait_ocean: Optional[str] = None
    bloom_level: Optional[int] = Field(default=None, ge=1, le=6)
    dreyfus_level: Optional[int] = Field(default=None, ge=1, le=5)
    weight: float = Field(default=1.0, ge=0.0)
    source: str = Field(
        default="wsi_wizard",
        description='One of "wsi_wizard", "wsi_compact", "custom".',
    )
    max_duration_s: int = Field(
        default=120,
        description="Voice interview max duration per question, in seconds.",
    )
    approved: Optional[bool] = Field(
        default=None,
        description="HITL approval state (wizard-only).",
    )
    edited_text: Optional[str] = Field(
        default=None,
        description="Recruiter edit overriding the generated question.",
    )


class EligibilityQuestionContract(_ContractModel):
    """Pre-screening yes/no question shown before WSI."""

    id: str
    question: str
    required_answer: EligibilityAnswer
    eliminatory: bool = Field(
        default=True,
        description="If true, a wrong answer disqualifies the candidate immediately.",
    )


class CalibrationCandidateContract(_ContractModel):
    """One candidate shown in the calibration step (3+ profiles)."""

    id: str
    name: str
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    match_score: float = Field(..., ge=0.0, le=1.0)
    match_criteria: List[Dict[str, Any]] = Field(default_factory=list)
    decision: Optional[CalibrationDecision] = None
    reason: Optional[str] = None


class WizardStagePayloadContract(_ContractModel):
    """Payload of every ``ws_stage_payload`` event sent over the WS.

    Mirrors the TypedDict the WS handler emits via ``serialize_panel_update``.
    The recruiter UI reads this to know which step to render and whether
    to show an HITL approval prompt.
    """

    type: Literal["wizard_stage"] = "wizard_stage"
    stage: WizardStage
    # Onda 2 (PLAN_FIX_wizard_memory_loss 2026-05-10): thread_id explicito
    # para o FE persistir e reabrir sessao apos refresh/HITL. Optional ate
    # rollout completo dos call sites do backend (defesa em profundidade
    # do P0-C). agent_chat_ws.py:929 inclui no payload spread.
    thread_id: Optional[str] = Field(
        default=None,
        description=(
            "LangGraph checkpointer thread_id derivado de "
            "WizardSessionService.derive_thread_id(msg, session_id). "
            "Frontend persiste para continuidade entre turnos / refresh."
        ),
    )
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Stage-specific payload (shape depends on stage).",
    )
    completeness: float = Field(..., ge=0.0, le=1.0)
    requires_approval: bool = Field(default=False)


class JobCreationStateContract(_ContractModel):
    """Snapshot of the LangGraph wizard state shipped to the recruiter UI.

    This is the "browser-safe" subset of ``JobCreationState`` — internal
    fields like ``auth_token`` are intentionally excluded. Every field
    is optional because the state accumulates across nodes and the UI
    must tolerate partial snapshots during the run.
    """

    # session metadata
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    workspace_id: Optional[int] = None
    language: Optional[str] = Field(default=None, description='IETF tag, e.g. "pt-BR".')

    # navigation
    current_stage: Optional[WizardStage] = None
    stage_history: List[WizardStage] = Field(default_factory=list)
    error: Optional[str] = None

    # intake
    raw_input: Optional[str] = None
    parsed_title: Optional[str] = None
    parsed_department: Optional[str] = None
    parsed_seniority: Optional[str] = None
    parsed_location: Optional[str] = None
    parsed_model: Optional[str] = Field(
        default=None, description='One of "remote", "hybrid", "onsite".'
    )
    intake_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    # JD enrichment (F1)
    jd_raw: Optional[str] = None
    jd_enriched: Optional[Dict[str, Any]] = Field(
        default=None,
        description="EnrichedJobDescription payload — see EnrichedJobDescription in schemas.",
    )
    jd_quality_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    jd_quality_warnings: List[str] = Field(default_factory=list)
    jd_approved: Optional[bool] = None

    # Big Five + ranking (F2/F3)
    bigfive_profile: Optional[BigFiveProfileContract] = None
    trait_rankings: List[TraitRankingContract] = Field(default_factory=list)

    # salary
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = Field(default=None, description='ISO 4217, default "BRL".')
    benefits: List[str] = Field(default_factory=list)
    salary_benchmark: Optional[Dict[str, Any]] = None

    # competency (F4/F5)
    seniority_resolved: Optional[str] = None
    seniority_signals: List[Dict[str, Any]] = Field(default_factory=list)
    screening_mode: Optional[ScreeningMode] = None
    question_distribution: Optional[Dict[str, int]] = Field(
        default=None,
        description='Per-block counts, e.g. {"technical": 4, "behavioral": 3}.',
    )
    competency_tree: List[Dict[str, Any]] = Field(default_factory=list)

    # WSI questions (F6)
    wsi_questions: List[ScreeningQuestionContract] = Field(default_factory=list)
    questions_approved: Optional[bool] = None
    questions_approval_details: List[Dict[str, Any]] = Field(default_factory=list)
    wsi_dropped_questions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Questions removed by FairnessGuard during F6. "
            "Each item: {question, category, blocked_terms, message}."
        ),
    )

    # eligibility
    eligibility_questions: List[EligibilityQuestionContract] = Field(default_factory=list)

    # review
    readiness_check: Optional[Dict[str, Any]] = None
    company_defaults_applied: List[str] = Field(default_factory=list)

    # publish
    job_id: Optional[int] = Field(default=None, description="Rails job ID after creation.")
    job_uid: Optional[str] = None
    publish_platforms: List[str] = Field(default_factory=list)
    sourcing_mode: Optional[SourcingMode] = None
    contact_channels: List[str] = Field(default_factory=list)

    # calibration
    calibration_candidates: List[CalibrationCandidateContract] = Field(default_factory=list)

    # presentation payload (last emitted)
    ws_stage_payload: Optional[WizardStagePayloadContract] = None


# Order matters: dependencies first, so the generator can reference them.
WIZARD_CONTRACT_MODELS: List[type[BaseModel]] = [
    BigFiveProfileContract,
    TraitRankingContract,
    ScreeningQuestionContract,
    EligibilityQuestionContract,
    CalibrationCandidateContract,
    WizardStagePayloadContract,
    JobCreationStateContract,
]


__all__ = [
    "WizardStage",
    "ScreeningMode",
    "SourcingMode",
    "QuestionFramework",
    "QuestionBlock",
    "QuestionCompetency",
    "EligibilityAnswer",
    "CalibrationDecision",
    "BigFiveProfileContract",
    "TraitRankingContract",
    "ScreeningQuestionContract",
    "EligibilityQuestionContract",
    "CalibrationCandidateContract",
    "WizardStagePayloadContract",
    "JobCreationStateContract",
    "WIZARD_CONTRACT_MODELS",
]
