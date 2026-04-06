"""
Field Typology Schema for Job Wizard Enhancement.

Defines the classification system for job vacancy fields,
enabling intelligent field handling during wizard flow.
"""
from dataclasses import dataclass
from enum import Enum, StrEnum
from typing import Any



class FieldTypology(StrEnum):
    """
    Classification of job vacancy fields by their nature and source.
    
    - IMPLICIT: Fields with fixed/default values that don't need user input
    - PROBABLE: Fields that can be inferred from company data with high confidence
    - CONDITIONAL: Fields that depend on other field values
    - CRITICAL: Core fields that must be explicitly confirmed
    - OPERATIONAL: System-managed fields for tracking
    - DERIVED: Fields generated/calculated from other data
    """
    IMPLICIT = "implicit"
    PROBABLE = "probable"
    CONDITIONAL = "conditional"
    CRITICAL = "critical"
    OPERATIONAL = "operational"
    DERIVED = "derived"


@dataclass
class FieldDefinition:
    """
    Definition of a job vacancy field including its typology and behavior.
    
    Attributes:
        name: Field identifier (matches database column)
        typology: Classification of the field
        required: Whether the field is mandatory for job publication
        default_source: Source for default value (e.g., 'company_profile', 'benchmark')
        condition: Condition that must be true for conditional fields
        confidence_threshold: Minimum confidence required for auto-application
    """
    name: str
    typology: FieldTypology
    required: bool = False
    default_source: str | None = None
    condition: str | None = None
    confidence_threshold: float = 0.70


FIELD_DEFINITIONS: dict[str, FieldDefinition] = {
    "job_title": FieldDefinition(
        name="job_title",
        typology=FieldTypology.CRITICAL,
        required=True,
        confidence_threshold=0.90
    ),
    "seniority": FieldDefinition(
        name="seniority",
        typology=FieldTypology.CRITICAL,
        required=True,
        default_source="text_extraction",
        confidence_threshold=0.85
    ),
    "salary_min": FieldDefinition(
        name="salary_min",
        typology=FieldTypology.CRITICAL,
        required=True,
        default_source="benchmark",
        confidence_threshold=0.80
    ),
    "salary_max": FieldDefinition(
        name="salary_max",
        typology=FieldTypology.CRITICAL,
        required=True,
        default_source="benchmark",
        confidence_threshold=0.80
    ),
    "department": FieldDefinition(
        name="department",
        typology=FieldTypology.PROBABLE,
        required=False,
        default_source="company_profile",
        confidence_threshold=0.75
    ),
    "location": FieldDefinition(
        name="location",
        typology=FieldTypology.PROBABLE,
        required=False,
        default_source="company_profile",
        confidence_threshold=0.80
    ),
    "work_model": FieldDefinition(
        name="work_model",
        typology=FieldTypology.PROBABLE,
        required=False,
        default_source="company_profile",
        confidence_threshold=0.75
    ),
    "employment_type": FieldDefinition(
        name="employment_type",
        typology=FieldTypology.PROBABLE,
        required=False,
        default_source="company_profile",
        confidence_threshold=0.80
    ),
    "skills": FieldDefinition(
        name="skills",
        typology=FieldTypology.PROBABLE,
        required=False,
        default_source="text_extraction",
        confidence_threshold=0.70
    ),
    "behavioral_competencies": FieldDefinition(
        name="behavioral_competencies",
        typology=FieldTypology.PROBABLE,
        required=False,
        default_source="similar_jobs",
        confidence_threshold=0.65
    ),
    "benefits": FieldDefinition(
        name="benefits",
        typology=FieldTypology.PROBABLE,
        required=False,
        default_source="company_profile",
        confidence_threshold=0.85
    ),
    "pipeline_stages": FieldDefinition(
        name="pipeline_stages",
        typology=FieldTypology.PROBABLE,
        required=False,
        default_source="company_profile",
        confidence_threshold=0.85
    ),
    "hybrid_days": FieldDefinition(
        name="hybrid_days",
        typology=FieldTypology.CONDITIONAL,
        required=False,
        default_source="company_profile",
        condition="work_model == 'hybrid'",
        confidence_threshold=0.80
    ),
    "pj_rate": FieldDefinition(
        name="pj_rate",
        typology=FieldTypology.CONDITIONAL,
        required=False,
        default_source="benchmark",
        condition="employment_type == 'PJ'",
        confidence_threshold=0.70
    ),
    "currency": FieldDefinition(
        name="currency",
        typology=FieldTypology.IMPLICIT,
        required=True,
        default_source="fixed:BRL",
        confidence_threshold=0.95
    ),
    "country": FieldDefinition(
        name="country",
        typology=FieldTypology.IMPLICIT,
        required=True,
        default_source="fixed:Brasil",
        confidence_threshold=0.95
    ),
    "company_id": FieldDefinition(
        name="company_id",
        typology=FieldTypology.OPERATIONAL,
        required=True,
        default_source="session",
        confidence_threshold=1.0
    ),
    "created_by": FieldDefinition(
        name="created_by",
        typology=FieldTypology.OPERATIONAL,
        required=True,
        default_source="session",
        confidence_threshold=1.0
    ),
    "updated_at": FieldDefinition(
        name="updated_at",
        typology=FieldTypology.OPERATIONAL,
        required=True,
        default_source="system",
        confidence_threshold=1.0
    ),
    "job_description": FieldDefinition(
        name="job_description",
        typology=FieldTypology.DERIVED,
        required=False,
        default_source="ai_generation",
        confidence_threshold=0.70
    ),
    "screening_questions": FieldDefinition(
        name="screening_questions",
        typology=FieldTypology.DERIVED,
        required=False,
        default_source="ai_generation",
        confidence_threshold=0.65
    ),
    "estimated_ttf": FieldDefinition(
        name="estimated_ttf",
        typology=FieldTypology.DERIVED,
        required=False,
        default_source="benchmark",
        confidence_threshold=0.60
    ),
    "job_complexity": FieldDefinition(
        name="job_complexity",
        typology=FieldTypology.DERIVED,
        required=False,
        default_source="calculation",
        confidence_threshold=0.70
    ),
}


def get_fields_by_typology(typology: FieldTypology) -> dict[str, FieldDefinition]:
    """Get all field definitions for a specific typology."""
    return {
        name: defn for name, defn in FIELD_DEFINITIONS.items()
        if defn.typology == typology
    }


def get_critical_fields() -> dict[str, FieldDefinition]:
    """Get all critical fields that require explicit confirmation."""
    return get_fields_by_typology(FieldTypology.CRITICAL)


def get_conditional_fields() -> dict[str, FieldDefinition]:
    """Get all conditional fields with their conditions."""
    return get_fields_by_typology(FieldTypology.CONDITIONAL)


def is_field_active(field_name: str, context: dict[str, Any]) -> bool:
    """
    Check if a conditional field is active based on current context.
    
    Args:
        field_name: Name of the field to check
        context: Current form/draft values
    
    Returns:
        True if field is active (non-conditional or condition met)
    """
    field_def = FIELD_DEFINITIONS.get(field_name)
    if not field_def:
        return False
    
    if field_def.typology != FieldTypology.CONDITIONAL:
        return True
    
    if not field_def.condition:
        return True
    
    try:
        import ast as _ast
        import operator as _op
        _ops = {
            _ast.Gt: _op.gt, _ast.GtE: _op.ge,
            _ast.Lt: _op.lt, _ast.LtE: _op.le,
            _ast.Eq: _op.eq, _ast.NotEq: _op.ne,
        }
        tree = _ast.parse(field_def.condition.strip(), mode="eval")
        body = tree.body
        if isinstance(body, _ast.Compare) and len(body.ops) == 1:
            def _val(n):
                if isinstance(n, _ast.Name):
                    return context.get(n.id)
                if isinstance(n, _ast.Constant):
                    return n.value
                raise ValueError("unsupported")
            left = _val(body.left)
            right = _val(body.comparators[0])
            op_fn = _ops.get(type(body.ops[0]))
            if op_fn:
                return op_fn(left, right)
        if isinstance(body, _ast.Name):
            return bool(context.get(body.id))
        return False
    except Exception:
        return False
