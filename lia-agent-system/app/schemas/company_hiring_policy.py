"""
Pydantic schemas for CompanyHiringPolicy API.
"""
from typing import Any

from pydantic import BaseModel, Field, ConfigDict, ValidationError, create_model
from app.shared.types import WeDoBaseModel


class PipelineRulesSchema(BaseModel):
    min_interviews_before_offer: int = Field(default=2, ge=1, le=10)
    manager_approval_for_offer: bool = Field(default=True)
    # P3a (2026-06-01): reclassificados de campos narrativos -> gates tipados.
    manager_approval_sla_hours: int = Field(default=24, ge=1, le=720)
    vacancy_approval_required: bool = Field(default=False)
    max_days_in_stage: dict[str, int] = Field(default_factory=dict)


class SchedulingRulesSchema(BaseModel):
    allowed_days: list[str] = Field(default=["mon", "tue", "wed", "thu", "fri"])
    allowed_hours: dict[str, str] = Field(default={"start": "09:00", "end": "18:00"})
    default_duration_minutes: int = Field(default=60, ge=15, le=480)
    self_scheduling_enabled: bool = Field(default=False)


class CommunicationRulesSchema(BaseModel):
    auto_rejection_feedback: bool = Field(default=False)
    rejection_feedback_deadline_hours: int = Field(default=48, ge=1, le=720)
    preferred_channel: str = Field(default="whatsapp")
    lia_tone: str = Field(default="professional")


class ScreeningRulesSchema(BaseModel):
    salary_expectation_filter: bool = Field(default=False)
    salary_tolerance_percent: int = Field(default=15, ge=0, le=100)
    experience_policy: str = Field(default="per_job")
    # P3a (2026-06-01): reclassificado de campo narrativo -> gate tipado.
    minimum_compatibility_score: int = Field(default=0, ge=0, le=100)
    default_screening_questions: list[str] = Field(default_factory=list)


class AutomationRulesSchema(BaseModel):
    auto_screening: bool = Field(default=False)
    auto_scheduling: bool = Field(default=False)
    auto_stage_advance: bool = Field(default=False)
    autonomy_level: str = Field(default="low")


class PipelineTemplateSchema(BaseModel):
    name: str
    stages: list[str] = Field(default_factory=list)
    rules: dict[str, Any] = Field(default_factory=dict)


class LearnedPatternSchema(BaseModel):
    pattern: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    source: str = Field(default="observation")
    data: dict[str, Any] = Field(default_factory=dict)
    observation_count: int = Field(default=1, ge=0)
    last_observed: str | None = None


class CompanyHiringPolicyCreate(WeDoBaseModel):
    company_id: str
    pipeline_rules: PipelineRulesSchema | None = None
    scheduling_rules: SchedulingRulesSchema | None = None
    communication_rules: CommunicationRulesSchema | None = None
    screening_rules: ScreeningRulesSchema | None = None
    automation_rules: AutomationRulesSchema | None = None
    pipeline_templates: list[PipelineTemplateSchema] | None = None


class CompanyHiringPolicyUpdate(WeDoBaseModel):
    pipeline_rules: dict[str, Any] | None = None
    scheduling_rules: dict[str, Any] | None = None
    communication_rules: dict[str, Any] | None = None
    screening_rules: dict[str, Any] | None = None
    automation_rules: dict[str, Any] | None = None
    pipeline_templates: list[dict[str, Any]] | None = None
    updated_by: str | None = None


class CompanyHiringPolicyBlockUpdate(WeDoBaseModel):
    block: str = Field(..., description="Block name: pipeline_rules, scheduling_rules, communication_rules, screening_rules, automation_rules, pipeline_templates")
    data: dict[str, Any] = Field(..., description="Block data to merge")
    updated_by: str | None = None


class CompanyHiringPolicyResponse(BaseModel):
    id: str
    company_id: str
    pipeline_rules: dict[str, Any]
    scheduling_rules: dict[str, Any]
    communication_rules: dict[str, Any]
    screening_rules: dict[str, Any]
    automation_rules: dict[str, Any]
    pipeline_templates: list[dict[str, Any]]
    learned_patterns: list[dict[str, Any]]
    setup_progress: int
    setup_completed_at: str | None = None
    created_by: str | None = None
    updated_by: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    class Config:
        from_attributes = True


class PolicyProgressResponse(BaseModel):
    company_id: str
    setup_progress: int
    setup_completed_at: str | None = None
    blocks_completed: dict[str, bool]


class PolicyChatMessage(BaseModel):
    """# T-06 R2 fix canonical: PolicyChatMessage company_id field removed.

    Multi-tenancy via path /{company_id}/chat + require_company_id_strict_match.
    """
    model_config = ConfigDict(extra='forbid')

    message: str
    user_id: str | None = None
    session_id: str | None = None
    conversation_history: list[dict[str, Any]] | None = Field(default_factory=list)


class PolicyChatResponse(BaseModel):
    reply: str
    current_block: str | None = None
    current_question: int | None = None
    total_questions: int = 19
    setup_progress: int = 0
    updated_fields: dict[str, Any] = Field(default_factory=dict)
    block_completed: bool = False
    all_completed: bool = False
    session_id: str | None = None


# ---------------------------------------------------------------------------
# P0.a — Canonical anti-corruption boundary for hiring-policy block writes
# ---------------------------------------------------------------------------
# Audit 2026-06-01: the three write paths (PUT /, PATCH /, PATCH /block) merged
# ``data: dict[str, Any]`` blindly into typed gate slots. The narrative Políticas
# UI wrote free-text strings ("Sim"/"Não"/prose) into boolean/int gates; consumers
# read raw values where the string "Não" is Python-truthy → automations turned ON
# silently. This boundary is the SINGLE place that validates+coerces a partial
# block payload before it ever touches the model. Fix at the producer, never the
# consumer (CLAUDE.md canonical-fix).

BLOCK_SCHEMAS: dict[str, type[BaseModel]] = {
    "pipeline_rules": PipelineRulesSchema,
    "scheduling_rules": SchedulingRulesSchema,
    "communication_rules": CommunicationRulesSchema,
    "screening_rules": ScreeningRulesSchema,
    "automation_rules": AutomationRulesSchema,
}

_BOOL_TRUE_TOKENS = {
    "sim", "true", "1", "yes", "on", "verdadeiro",
    "habilitado", "habilitada", "ativo", "ativa", "ativado", "ativada",
}
_BOOL_FALSE_TOKENS = {
    "não", "nao", "false", "0", "no", "off", "falso",
    "desabilitado", "desabilitada", "inativo", "inativa", "desativado", "desativada",
    "não definido", "nao definido", "",
}


class PolicyBlockValidationError(ValueError):
    """Raised when a hiring-policy block payload has wrong-typed/unknown fields.

    Endpoints convert this into HTTP 422 (fail loud, never silently coerce a
    typed gate from free text)."""


def _precoerce_bool(field: str, value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        token = value.strip().lower()
        if token in _BOOL_TRUE_TOKENS:
            return True
        if token in _BOOL_FALSE_TOKENS:
            return False
        raise PolicyBlockValidationError(
            f"Campo '{field}' é um gate booleano (Sim/Não), recebeu texto livre {value!r}. "
            f"→ Fix: enviar true/false (ou Sim/Não). Texto descritivo deve virar uma "
            f"instrução da LIA (LiaFieldToggle.comment), nunca um gate de automação."
        )
    raise PolicyBlockValidationError(
        f"Campo '{field}' é um gate booleano, recebeu {type(value).__name__}."
    )


def coerce_and_validate_block(block: str, data: dict[str, Any]) -> dict[str, Any]:
    """Validate + coerce a PARTIAL block payload against its typed schema.

    - Coerces PT-BR "Sim"/"Não" → bool on boolean gate slots.
    - Lets Pydantic coerce numeric strings ("3" → 3) and enforce Field ranges.
    - Rejects unknown keys (extra='forbid') so ghost fields never persist.
    - Returns ONLY the provided keys (partial merge — no defaults injected).
    - Structural/non-gate blocks (pipeline_templates) pass through untouched.
    """
    schema = BLOCK_SCHEMAS.get(block)
    if schema is None:
        return data
    if not isinstance(data, dict):
        raise PolicyBlockValidationError(
            f"Bloco '{block}' espera um objeto, recebeu {type(data).__name__}."
        )

    model_fields = schema.model_fields
    unknown = set(data) - set(model_fields)
    if unknown:
        raise PolicyBlockValidationError(
            f"Campos desconhecidos no bloco '{block}': {sorted(unknown)}. "
            f"→ Fix: usar apenas {sorted(model_fields)}."
        )

    precoerced: dict[str, Any] = {}
    for key, value in data.items():
        annotation = model_fields[key].annotation
        if annotation is bool:
            precoerced[key] = _precoerce_bool(key, value)
        else:
            precoerced[key] = value

    partial_fields = {
        key: (model_fields[key].annotation, model_fields[key]) for key in precoerced
    }
    PartialModel = create_model(
        f"{schema.__name__}__Partial",
        __config__=ConfigDict(extra="forbid"),
        **partial_fields,
    )
    try:
        validated = PartialModel(**precoerced)
    except ValidationError as exc:
        raise PolicyBlockValidationError(
            f"Bloco '{block}' inválido: {exc.errors(include_url=False)}"
        ) from exc

    return {key: getattr(validated, key) for key in precoerced}
