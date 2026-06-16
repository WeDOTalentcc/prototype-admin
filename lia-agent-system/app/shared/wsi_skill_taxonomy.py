"""Canonical shim — re-exports WSI Skill Taxonomy from domain layer.

ADR-001: shared layer must not import from domain layer directly in business
logic, but a pure re-export shim is explicitly allowed as a thin alias so
callers outside the job_creation domain can do:

    from app.shared.wsi_skill_taxonomy import WsiSkill, THRESHOLD_BY_BIAS_RISK

without creating a cross-domain dependency chain.
"""
from app.domains.job_creation.services.wsi_skill_taxonomy import (  # noqa: F401
    WsiSkill,
    WsiParent,
    WsiTaxonomy,
    THRESHOLD_BY_BIAS_RISK,
    DECAY_LAMBDA_BY_TYPE,
    ALLOWED_OCEAN,
    ALLOWED_BIAS_RISK,
    ALLOWED_DECAY_RATE,
    load_taxonomy,
    find_skill,
    parent_of,
    all_skill_ids,
    all_parent_ids,
    skills_by_parent,
    get_skills_by_ocean,
    get_skills_by_bias_risk,
    get_sample_threshold,
    get_decay_lambda,
)

__all__ = [
    "WsiSkill",
    "WsiParent",
    "WsiTaxonomy",
    "THRESHOLD_BY_BIAS_RISK",
    "DECAY_LAMBDA_BY_TYPE",
    "ALLOWED_OCEAN",
    "ALLOWED_BIAS_RISK",
    "ALLOWED_DECAY_RATE",
    "load_taxonomy",
    "find_skill",
    "parent_of",
    "all_skill_ids",
    "all_parent_ids",
    "skills_by_parent",
    "get_skills_by_ocean",
    "get_skills_by_bias_risk",
    "get_sample_threshold",
    "get_decay_lambda",
]
