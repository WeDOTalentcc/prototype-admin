"""conditions_canonical.py — Sprint A.8 canonical source.

Operators + condition fields que SentenceBuilder usa pra construir frases.
Esta lista é o source of truth — atualizar aqui propaga via endpoint
GET /automations/operators/available + /automations/condition-fields/available.

Audit ref: AUTOMATIONS_SPRINT_PLAN_ADR.md Sprint A.8 + IMPECCABLE_CRITIQUE.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OperatorMetadata:
    value: str
    label_pt: str
    label_en: str
    applicable_types: list[str]  # ["number", "string", "boolean", "list"]


@dataclass(frozen=True)
class ConditionFieldMetadata:
    value: str  # canonical path "candidate.wsi_score"
    label_pt: str
    label_en: str
    type: str  # "number" | "string" | "boolean" | "list"
    category: str  # "candidate" | "job" | "pipeline" | "company"
    description: str | None = None


OPERATORS_CATALOG: list[OperatorMetadata] = [
    OperatorMetadata(
        value="eq",
        label_pt="for igual a",
        label_en="equals",
        applicable_types=["number", "string", "boolean"],
    ),
    OperatorMetadata(
        value="neq",
        label_pt="for diferente de",
        label_en="not equals",
        applicable_types=["number", "string", "boolean"],
    ),
    OperatorMetadata(
        value="gt",
        label_pt="for maior que",
        label_en="greater than",
        applicable_types=["number"],
    ),
    OperatorMetadata(
        value="gte",
        label_pt="for maior ou igual a",
        label_en="greater or equal",
        applicable_types=["number"],
    ),
    OperatorMetadata(
        value="lt",
        label_pt="for menor que",
        label_en="less than",
        applicable_types=["number"],
    ),
    OperatorMetadata(
        value="lte",
        label_pt="for menor ou igual a",
        label_en="less or equal",
        applicable_types=["number"],
    ),
    OperatorMetadata(
        value="contains",
        label_pt="contém",
        label_en="contains",
        applicable_types=["string", "list"],
    ),
    OperatorMetadata(
        value="not_contains",
        label_pt="não contém",
        label_en="not contains",
        applicable_types=["string", "list"],
    ),
    OperatorMetadata(
        value="in",
        label_pt="está em",
        label_en="in",
        applicable_types=["string", "list"],
    ),
    OperatorMetadata(
        value="is_empty",
        label_pt="está vazio",
        label_en="is empty",
        applicable_types=["string", "list"],
    ),
]


CONDITION_FIELDS_CATALOG: list[ConditionFieldMetadata] = [
    # Candidate-level
    ConditionFieldMetadata(
        value="candidate.wsi_score",
        label_pt="score WSI",
        label_en="WSI score",
        type="number",
        category="candidate",
    ),
    ConditionFieldMetadata(
        value="candidate.big_five.openness",
        label_pt="abertura (Big Five)",
        label_en="openness (Big Five)",
        type="number",
        category="candidate",
    ),
    ConditionFieldMetadata(
        value="candidate.big_five.conscientiousness",
        label_pt="conscienciosidade (Big Five)",
        label_en="conscientiousness (Big Five)",
        type="number",
        category="candidate",
    ),
    ConditionFieldMetadata(
        value="candidate.big_five.extraversion",
        label_pt="extroversão (Big Five)",
        label_en="extraversion (Big Five)",
        type="number",
        category="candidate",
    ),
    ConditionFieldMetadata(
        value="candidate.big_five.agreeableness",
        label_pt="amabilidade (Big Five)",
        label_en="agreeableness (Big Five)",
        type="number",
        category="candidate",
    ),
    ConditionFieldMetadata(
        value="candidate.big_five.neuroticism",
        label_pt="neuroticismo (Big Five)",
        label_en="neuroticism (Big Five)",
        type="number",
        category="candidate",
    ),
    ConditionFieldMetadata(
        value="candidate.years_experience",
        label_pt="anos de experiência",
        label_en="years of experience",
        type="number",
        category="candidate",
    ),
    ConditionFieldMetadata(
        value="candidate.expected_salary",
        label_pt="pretensão salarial",
        label_en="expected salary",
        type="number",
        category="candidate",
    ),
    ConditionFieldMetadata(
        value="candidate.salary_outside_range",
        label_pt="está fora da faixa salarial",
        label_en="salary outside range",
        type="boolean",
        category="candidate",
    ),
    ConditionFieldMetadata(
        value="candidate.location_city",
        label_pt="cidade",
        label_en="city",
        type="string",
        category="candidate",
    ),
    # Job-level
    ConditionFieldMetadata(
        value="job.seniority",
        label_pt="senioridade da vaga",
        label_en="job seniority",
        type="string",
        category="job",
    ),
    ConditionFieldMetadata(
        value="job.is_remote",
        label_pt="vaga é remota",
        label_en="job is remote",
        type="boolean",
        category="job",
    ),
    # Pipeline-level
    ConditionFieldMetadata(
        value="pipeline.current_stage",
        label_pt="etapa atual",
        label_en="current stage",
        type="string",
        category="pipeline",
    ),
    ConditionFieldMetadata(
        value="pipeline.days_in_stage",
        label_pt="dias na etapa atual",
        label_en="days in current stage",
        type="number",
        category="pipeline",
    ),
]


def operators_to_api_response() -> list[dict]:
    """Shape canonical para resposta do endpoint /automations/operators/available."""
    return [
        {
            "value": op.value,
            "name": op.label_pt,
            "label_pt": op.label_pt,
            "label_en": op.label_en,
            "applicable_types": list(op.applicable_types),
        }
        for op in OPERATORS_CATALOG
    ]


def condition_fields_to_api_response() -> list[dict]:
    """Shape canonical para /automations/condition-fields/available."""
    return [
        {
            "value": f.value,
            "name": f.label_pt,
            "label_pt": f.label_pt,
            "label_en": f.label_en,
            "type": f.type,
            "category": f.category,
            "description": f.description,
        }
        for f in CONDITION_FIELDS_CATALOG
    ]


def get_operator(value: str) -> OperatorMetadata | None:
    """Lookup fail-CLOSED. Retorna None se operator desconhecido."""
    for op in OPERATORS_CATALOG:
        if op.value == value:
            return op
    return None


def get_condition_field(value: str) -> ConditionFieldMetadata | None:
    """Lookup fail-CLOSED. Retorna None se field desconhecido."""
    for f in CONDITION_FIELDS_CATALOG:
        if f.value == value:
            return f
    return None
