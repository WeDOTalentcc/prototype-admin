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
    # Sprint F.3 multi-tenancy fix: LangGraph filters undeclared keys;
    # without this, company_id from JWT gets stripped before nodes run,
    # breaking ADR-LGPD-001/ADR-029 fail-closed audit. JobCreationState must
    # carry company_id as UUID string sourced from require_company_id JWT dep.
    company_id: str
    auth_token: str
    language: str  # default "pt-BR"

    # --- Create-from-source (PR-A) ---
    seed_source: Optional[Dict[str, Any]]      # {"type","id","name"} of the chosen template/vacancy
    seed_provenance: Dict[str, Any]            # per-field provenance for the review surface

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
    parsed_employment_type: Optional[str]  # CLT/PJ/estagio/temporario/freelancer (P0-A)
    parsed_manager_name: Optional[str]  # gestor responsavel (FASE 5 ficha viva)
    parsed_manager_email: Optional[str]  # email do gestor (FASE 5 ficha viva)
    parsed_recruiter_name: Optional[str]  # recrutador responsavel (W0-A)
    parsed_recruiter_email: Optional[str]  # email do recrutador (W0-A)
    jd_similar_reuse_id: Optional[str]  # ID da JD similar reutilizada pelo recruiter (W0-B)
    intake_confidence: float

    # --- F1: JD Enrichment ---
    jd_raw: Optional[str]  # recruiter's original JD text
    jd_enriched: Optional[Dict[str, Any]]  # EnrichedJobDescription from JdEnrichmentService
    jd_quality_score: float  # 0-100 deterministic
    jd_quality_warnings: List[str]
    jd_approved: Optional[bool]  # HITL point 1
    jd_rejection_feedback: Optional[str]

    # --- F1.5: JD Enrichment auxiliary (subset propagated to ws_stage_payload) ---
    jd_enrichment_used_fallback: bool
    jd_enrichment_fallback_reason: Optional[str]
    jd_enrichment_blocked: bool
    jd_enrichment_awaiting_input: bool
    jd_enriched_present: bool

    # --- Gate fields (Task #1085/T2-T6 LLM-based gates) ---
    # Sprint F.2 root cause fix (2026-05-20): these MUST be declared in the
    # TypedDict schema. LangGraph filters undeclared keys during state merge,
    # which silently dropped gate_seen_user_query / gate_last_intent /
    # gate_clarify_message / gate_resume_message between node invocations.
    # Symptom: gate self-loop saw _is_fresh_turn=True every iteration because
    # gate_seen_user_query did not survive, causing infinite classifier loop
    # until LangGraph recursion limit aborted (GraphRecursionError observed
    # 2026-05-20 in lia-backend logs, 46 self-loops in ~60s, single turn).
    # Same precedent: company_id (lines 105-108 above, Sprint F.3).
    gate_seen_user_query: Optional[str]
    gate_last_intent: Optional[str]
    gate_last_confidence: float
    gate_clarify_message: Optional[str]
    gate_resume_message: Optional[str]

    # --- Fairness L1 guard (Sprint F.2 schema fix — same root cause) ---
    fairness_blocked: bool
    fairness_block_reason: Optional[str]
    fairness_category: Optional[str]
    fairness_warning: Optional[str]
    fairness_blocked_output: Optional[str]
    jd_fairness_blocked: bool

    # --- WSI questions pending markers (Task #1087 / #1089 follow-up) ---
    wsi_regenerate_pending: bool
    wsi_questions_pending_edit: Optional[Dict[str, Any]]
    wsi_questions_pending_add: Optional[Dict[str, Any]]

    # --- F2+F3: Big Five + Trait Ranking ---
    bigfive_profile: Optional[BigFiveProfile]
    trait_rankings: List[TraitRanking]

    # --- Salary ---
    salary_min: Optional[int]
    salary_max: Optional[int]
    salary_currency: str  # default "BRL"
    # Beneficios da vaga: aceita shape legado (List[str]) e o canonical
    # VagaBenefit (snapshot+ref) serializado como dict. Normalizado no
    # boundary (publish_node) via helpers.vaga_benefits.parse_vaga_benefits.
    benefits: List[Any]
    variable_compensation: Optional[List[Dict[str, Any]]]
    salary_benchmark: Optional[Dict[str, Any]]
    # Fase 5 — recrutador confirmou a faixa via right_panel_form (salary_node).
    # Declarado p/ sobreviver ao merge do LangGraph (mesmo motivo de company_id).
    salary_confirmed: Optional[bool]
    salary_provenance: Optional[str]  # company_salary_band | market_benchmark | manual (audit 2026-06-06)
    # Recrutador optou explicitamente por seguir SEM divulgar faixa
    # (set_salary decline_to_disclose=true). Conta como 'salário tratado'
    # no gate de geração de triagem — não é pulo silencioso.
    salary_skipped: Optional[bool]

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

    # T6 (Task #1088) — tenant ATS integrations habilitadas (intersect com
    # _REVIEW_DESTINATIONS_ALLOWLIST canônica em review_gate_node). Quando
    # vazio/ausente, gate cai para a allowlist canônica completa
    # (fail-soft em dev, mas review_gate_node loga warning).
    tenant_enabled_ats: List[str]

    # T6 (Task #1088) — confirmation_method da decisão de publish
    # (chat | dual | button) propagado do review_gate_node para o
    # publish_node final audit (rastreabilidade SOX 7y).
    publish_confirmation_method: str
    sourcing_mode: Optional[Literal["local", "global", "hybrid"]]
    contact_channels: List[str]  # ["email", "whatsapp", "phone"]
    share_link: Optional[str]
    screening_pipeline_id: Optional[str]
    auto_screen_enabled: bool

    # W1-B (2026-06-12): vaga afirmativa detectada via NLP no intake.
    is_affirmative: bool
    affirmative_criteria_primary: Optional[str]
    affirmative_criteria_secondary: Optional[str]  # segundo critério (ex: mulheres negras = gender + race)
    affirmative_description: Optional[str]
    affirmative_document_required: bool  # exige laudo/autodeclaração do candidato
    affirmative_document_types: List[str]  # ex: ['laudo_pcd', 'autodeclaracao_racial']

    # --- T6 (Task #1088) review gate dual-confirmation ---
    # ``pending_publish_confirmation`` é setado por ``review_gate_node``
    # no PRIMEIRO ``publish_now`` (chat). Segundo ``publish_now`` dentro
    # da janela TTL (default 300s) seta ``policy_confirmed_publish=True``
    # — que destrava o ``publish_node`` PolicyGate (HITL_REQUIRED).
    # ``publish_confirmation_ts`` é epoch seconds; expirado → reseta.
    # ``review_request_changes_pending`` carrega o último target_section
    # + instruction do recrutador (extracted_data validado pelo gate).
    pending_publish_confirmation: bool
    publish_confirmation_ts: Optional[float]
    # Sprint F.5 fix (2026-05-20): MUST be declared (same precedent as
    # gate_seen_user_query L159 + company_id L105-108). Set by
    # review_gate_node on 2nd publish_now within TTL → unlocks publish_node
    # PolicyGate. Without this declaration LangGraph filtered the key,
    # leaving job_vacancy_id=None forever (wizard E2E observed 2026-05-20).
    policy_confirmed_publish: bool
    review_request_changes_pending: Optional[Dict[str, Any]]

    # --- Calibration ---
    calibration_candidates: List[CalibrationCandidate]
    calibration_threshold: int  # default 3
    calibration_complete: bool

    # --- Handoff ---
    handoff_url: Optional[str]  # URL to the job page

    # --- intake_gate fields (Frente 2 — 2026-05-29) ---
    # Sprint conversacional: intake gate antes do jd_enrichment.
    # Declarados aqui para sobreviver ao merge do LangGraph (mesma razão
    # que gate_seen_user_query + company_id — LangGraph filtra keys não-declaradas).
    intake_approved: Optional[bool]              # True quando recrutador confirmou criação
    intake_salary_suggested: Optional[bool]      # True após sugestão salarial emitida
    intake_gate_seen_user_query: Optional[str]   # evita re-processar mesma msg (anti-loop)

    # --- Fase 3 (2026-05-30): confirmação assistida de competências ---
    # intake_gate sugere competências (via CompetencyBenchmarkService, Fase 2),
    # dimensionadas pelo modo; recruiter confirma/edita via painel (Fase 5).
    # confirmed_* são consumidos pelo jd_enrichment invertido (Fase 4).
    intake_competencies_suggested: Optional[bool]       # True após sugestão de competências emitida
    confirmed_technical_competencies: List[Dict[str, Any]]   # [{skill, contexto}] confirmadas
    confirmed_behavioral_competencies: List[Dict[str, Any]]  # [{competencia, contexto, trait_big_five}]
    # Responsabilidades confirmadas pelo recrutador (item #2 2026-05-31). Não-obrigatório:
    # se ausente, o jd_enrichment gera; se presente, sobrescreve verbatim (Fase 4).
    confirmed_responsibilities: List[str]
    # Idiomas exigidos (item #3): [{language, level, required}] -> coluna languages.
    confirmed_languages: List[Dict[str, Any]]



    # --- Pipeline Template (Sprint Pipeline Templates 2026-05-26 — Opção B) ---
    # Set by pipeline_template_node when recruiter applies a template.
    # interview_stages = canonical translated stages (translate_template_stages_to_interview_stages).
    # Persisted via PipelineTemplateService.apply_to_vacancy AFTER publish (vacancy_id existe).
    pipeline_template_id: Optional[str]
    pipeline_template_skipped: Optional[bool]  # True quando recrutador opta por "Usar Padrão da Empresa"
    pipeline_template_score: Optional[float]
    interview_stages: List[Dict[str, Any]]
    # Derived from interview_stages.sla_days by pipeline_template_node.
    # Shape: [{name, order, sla_days, offset_start, offset_end}]
    # FE computes absolute dates as: today + offset_end days.
    derived_chronogram: Optional[List[Dict[str, Any]]]

    # --- WS protocol fields ---
    ws_stage_payload: Optional[Dict[str, Any]]  # last wizard_stage WS message sent
    requires_approval: bool  # current stage needs HITL
    completeness: float  # 0.0 to 1.0 overall wizard progress


# Stage order for progress calculation
STAGE_ORDER: List[WizardStage] = [
    "intake",
    "jd_enrichment",
    # Sprint Pipeline Templates 2026-05-26 — Opção B (Paulo aprovou).
    # Posicionamento canonical: APÓS jd_enrichment (department/seniority/job_family
    # já extraídos), ANTES de bigfive (primeira stage que depende estruturalmente
    # do pipeline). Skippable — recrutador pode dizer "padrão da empresa".
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
]


def calculate_completeness(current_stage: WizardStage) -> float:
    """Calculate wizard progress as 0.0-1.0 based on current stage."""
    if current_stage not in STAGE_ORDER:
        return 0.0
    idx = STAGE_ORDER.index(current_stage)
    return round(idx / (len(STAGE_ORDER) - 1), 2)


# HITL approval stages
# Sprint Pipeline Templates 2026-05-26 — Opção B (Paulo aprovou):
# pipeline_template é HITL stage canonical. requires_approval=True bloqueia
# graph até recrutador escolher template OR optar por padrão da empresa.
HITL_STAGES: set[WizardStage] = {"jd_enrichment", "pipeline_template", "wsi_questions"}
