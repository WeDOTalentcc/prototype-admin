"""
Job Stage Config — Stage definitions and helper functions for the Job Creation Wizard.

Extracted from job_intake_agent.py (Sprint 5) so non-agent code can import these
without triggering the DeprecationWarning on the legacy agent module.
"""
from typing import Any

from app.schemas.job_management import StageConfig  # R-026

JOB_CREATION_STAGES: list[dict[str, Any]] = [
    {
        "stage": 1,
        "name": "criteria_detection",
        "panel": "Critérios Detectados",
        "min_criteria": 2,
        "skip_if_confident": False,
        "skippable_fields": [],
        "confidence_threshold": 0.0,
    },
    {
        "stage": 2,
        "name": "basic_info",
        "panel": "Informações Básicas",
        "skip_if_confident": True,
        "skippable_fields": ["seniority", "department", "location"],
        "confidence_threshold": 0.85,
        "skip_message": "Informações básicas preenchidas automaticamente com alta confiança",
    },
    {
        "stage": 3,
        "name": "technical_requirements",
        "panel": "Requisitos Técnicos",
        "skip_if_confident": True,
        "skippable_fields": ["skills", "competencias_tecnicas"],
        "confidence_threshold": 0.80,
        "use_skills_deduplication": True,
        "skip_message": "Skills técnicas detectadas com alta confiança",
    },
    {
        "stage": 4,
        "name": "behavioral_competencies",
        "panel": "Competências Comportamentais",
        "skip_if_confident": False,
        "skippable_fields": [],
        "confidence_threshold": 0.0,
    },
    {
        "stage": 5,
        "name": "salary_benefits",
        "panel": "Salário e Benefícios",
        "skip_if_confident": False,
        "skippable_fields": [],
        "confidence_threshold": 0.0,
    },
    {
        "stage": 6,
        "name": "screening_questions",
        "panel": "Perguntas de Triagem WSI",
        "skip_if_confident": False,
        "skippable_fields": [],
        "confidence_threshold": 0.0,
    },
    {
        "stage": 7,
        "name": "pipeline_config",
        "panel": "Configuração do Pipeline",
        "skip_if_confident": False,
        "skippable_fields": [],
        "confidence_threshold": 0.0,
    },
    {
        "stage": 8,
        "name": "review_publish",
        "panel": "Resumo da Vaga",
        "skip_if_confident": False,
        "skippable_fields": [],
        "confidence_threshold": 0.0,
    },
]


def get_stage_config(stage_number: int) -> StageConfig:
    """Return the stage configuration dict for *stage_number*, or {} if not found."""
    for stage in JOB_CREATION_STAGES:
        if stage["stage"] == stage_number:
            return stage
    return {}


def should_skip_stage(
    stage_number: int,
    detected_criteria: dict[str, Any],
    already_confirmed: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    """
    Determine if a stage can be auto-skipped based on confidence thresholds.

    Returns:
        (should_skip, reason)
    """
    stage_config = get_stage_config(stage_number)

    if not stage_config.get("skip_if_confident", False):
        return False, "Stage not configured for auto-skip"

    threshold = stage_config.get("confidence_threshold", 0.0)
    skippable_fields = stage_config.get("skippable_fields", [])

    if not skippable_fields:
        return False, "No skippable fields configured"

    _CONFIDENCE_MAP = {
        "alta": 0.9, "média": 0.6, "baixa": 0.3,
        "high": 0.9, "medium": 0.6, "low": 0.3,
    }

    confident_fields = 0
    for field in skippable_fields:
        field_data = detected_criteria.get(field, {})
        if isinstance(field_data, dict):
            confidence = field_data.get("confidence", 0)
            if isinstance(confidence, str):
                confidence = _CONFIDENCE_MAP.get(confidence, 0)
            if confidence >= threshold and field_data.get("value"):
                confident_fields += 1
        elif field_data:
            confident_fields += 1

    if confident_fields >= len(skippable_fields) * 0.8:
        return True, stage_config.get(
            "skip_message", f"Stage {stage_number} skipped due to high confidence"
        )

    return False, "Confidence threshold not met"
