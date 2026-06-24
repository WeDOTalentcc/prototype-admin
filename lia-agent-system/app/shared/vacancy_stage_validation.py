"""GAP-06-002: Per-stage required field validation for job vacancies.

Lifecycle stages (derived, not stored — see analytics._classify_job_lifecycle_stage):
  rascunho → ats_importada → enriquecida → wsi_config → aguardando_aprovacao → publicada → ao_vivo

Each stage progressively requires more fields to be filled. This module provides
a helper that returns missing fields for a target stage, enabling pre-transition
validation without breaking existing flows.

Status transitions (stored in job.status):
  Rascunho → Ativa (publish) — uses VALID_JOB_STATUSES

This validator covers BOTH: derived lifecycle stages AND stored status transitions.
For status="Ativa" (publish), the "publicada" stage rules apply.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Stage → required fields map
# Conservative: only fields that genuinely make no sense to be empty at that stage.
# Fields reference JobVacancy model columns (job_vacancy.py).
# ---------------------------------------------------------------------------

STAGE_REQUIRED_FIELDS: dict[str, list[str]] = {
    # Minimal — just a title to save as draft
    "rascunho": ["title"],
    "ats_importada": ["title"],
    # JD enrichment needs at least a description
    "enriquecida": ["title", "description"],
    # WSI (screening) needs JD context to generate questions
    "wsi_config": ["title", "description"],
    # Approval needs enough context for the approver
    "aguardando_aprovacao": ["title", "description", "department"],
    # Publication = full validation — vacancy must be presentable
    "publicada": ["title", "description", "department", "employment_type"],
    "ao_vivo": ["title", "description", "department", "employment_type"],
}

# Map stored status values → lifecycle stage for validation purposes
_STATUS_TO_STAGE: dict[str, str] = {
    "Ativa": "publicada",
}


def validate_stage_requirements(
    vacancy: Any,
    target_stage: str,
) -> list[str]:
    """Return list of missing fields for the target stage. Empty list = valid.

    Parameters
    ----------
    vacancy : JobVacancy (or any object with the expected attributes)
    target_stage : str
        Either a lifecycle stage name ("rascunho", "enriquecida", "publicada", ...)
        or a stored status name ("Ativa") — mapped automatically.

    Returns
    -------
    list[str]
        Field names that are missing/empty. Empty list means the vacancy is valid
        for the target stage.
    """
    # Map stored status → lifecycle stage if needed
    effective_stage = _STATUS_TO_STAGE.get(target_stage, target_stage)

    required = STAGE_REQUIRED_FIELDS.get(effective_stage, [])
    if not required:
        # Unknown stage or no requirements — allow transition (additive, not blocking)
        return []

    missing: list[str] = []
    for field in required:
        value = getattr(vacancy, field, None)
        if value is None:
            missing.append(field)
        elif isinstance(value, str) and not value.strip():
            missing.append(field)
    return missing


def get_stage_requirements(stage: str) -> list[str]:
    """Return the list of required fields for a given stage (for documentation/UI)."""
    effective = _STATUS_TO_STAGE.get(stage, stage)
    return list(STAGE_REQUIRED_FIELDS.get(effective, []))
