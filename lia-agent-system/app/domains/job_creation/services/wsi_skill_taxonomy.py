"""WSI Skill Taxonomy Loader - Sprint B Phase 3.

Carrega e valida wsi_skill_taxonomy.json (ADR-004 fixtures pattern).
Cache lazy + lookup O(1) por skill_id ou parent_id.

Multi-tenancy: nao aplica - taxonomia eh global, nao por empresa.
LGPD: nao processa PII - so metadados de skill.
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)


# ADR-004: fixture path
TAXONOMY_FIXTURE = (
    Path(__file__).resolve().parents[4]
    / "app" / "data" / "fixtures" / "wsi_skill_taxonomy.json"
)


# Allowed seniority enum
ALLOWED_SENIORITY = frozenset({"jr", "pl", "sr", "ld"})

# Allowed sources
ALLOWED_SOURCES = frozenset({"ONET", "BEI", "Lominger", "Custom", "HCAHPS"})


# ── Learning system constants ────────────────────────────────────────────────

# Adaptive sample thresholds per bias-risk level (Sprint B Phase 3).
# High-risk skills need more evidence before influencing question generation.
THRESHOLD_BY_BIAS_RISK: dict[str, int] = {
    "high":   30,   # AI-adjacent, demographic-correlated (age, background)
    "medium": 20,   # Default — matches previous MIN_SAMPLES_FOR_DISCRIMINATION
    "low":    12,   # Stable soft skills with well-established behavioural anchors
}

# Temporal decay λ per skill stability type (exponential decay).
# Fast-evolving skills (AI tools) go stale faster than stable human traits.
DECAY_LAMBDA_BY_TYPE: dict[str, float] = {
    "fast":   0.12,   # AI/tech skills — market changes quarter-to-quarter
    "normal": 0.05,   # Most skills — aligned with BigFive department decay
    "slow":   0.02,   # Core human traits: integrity, empathy, service vocation
}

# Valid values (used by validators)
ALLOWED_OCEAN        = frozenset({"O", "C", "E", "A", "N"})
ALLOWED_BIAS_RISK    = frozenset({"low", "medium", "high"})
ALLOWED_DECAY_RATE   = frozenset({"fast", "normal", "slow"})


class WsiSkill(BaseModel):
    """Schema de uma skill na taxonomia."""

    model_config = ConfigDict(frozen=True, extra="ignore")  # extra="ignore" for forward compat

    id: str
    name_pt: str
    description: str
    seniority_min: str
    source: str
    fairness_flag: str | None = None

    # ── Learning system metadata (Sprint B Phase 3) ──────────────────────
    primary_ocean: str | None = None   # 'O'|'C'|'E'|'A'|'N' — OCEAN dimension
    bias_risk: str = "medium"          # 'low'|'medium'|'high' — sample threshold
    decay_rate: str = "normal"         # 'fast'|'normal'|'slow' — λ decay speed


class WsiParent(BaseModel):
    """Schema de uma categoria parent."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name_pt: str
    scope: str
    seniority_typical: str
    skills: list[WsiSkill]


class WsiTaxonomy(BaseModel):
    """Schema completa carregada da fixture."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    version: str
    total_skills: int
    total_parents: int
    parents: dict[str, WsiParent]


def _validate_skill(skill: dict[str, Any]) -> None:
    if skill["seniority_min"] not in ALLOWED_SENIORITY:
        raise ValueError(
            f"skill {skill['id']!r}: seniority_min "
            f"{skill['seniority_min']!r} not in {sorted(ALLOWED_SENIORITY)}",
        )
    if skill["source"] not in ALLOWED_SOURCES:
        raise ValueError(
            f"skill {skill['id']!r}: source {skill['source']!r} "
            f"not in {sorted(ALLOWED_SOURCES)}",
        )
    if not skill["id"].replace("_", "").isalnum() or not skill["id"].islower():
        raise ValueError(
            f"skill id {skill['id']!r} must be lowercase snake_case",
        )


@lru_cache(maxsize=1)
def load_taxonomy() -> WsiTaxonomy:
    """Carrega taxonomia da fixture com validacao + cache.

    Raises:
        FileNotFoundError: se fixture nao existe
        ValueError: se validacao falha (skill malformada, source/seniority invalida)
    """
    if not TAXONOMY_FIXTURE.exists():
        raise FileNotFoundError(
            f"WSI taxonomy fixture not found: {TAXONOMY_FIXTURE}. "
            "Run app/data/fixtures setup or check ADR-004 path.",
        )
    raw = json.loads(TAXONOMY_FIXTURE.read_text(encoding="utf-8"))

    # Validate every skill before pydantic build (early errors)
    for parent_id, parent in raw["parents"].items():
        if not parent_id.replace("_", "").isalnum() or not parent_id.islower():
            raise ValueError(
                f"parent id {parent_id!r} must be lowercase snake_case",
            )
        for skill in parent["skills"]:
            _validate_skill(skill)

    # Strip internal index field if present (was for json convenience)
    raw.pop("_skill_to_parent_index", None)
    return WsiTaxonomy(**raw)


@lru_cache(maxsize=1)
def get_skill_to_parent_index() -> dict[str, str]:
    """Returns dict skill_id -> parent_id for O(1) lookup."""
    tax = load_taxonomy()
    out: dict[str, str] = {}
    for parent_id, parent in tax.parents.items():
        for skill in parent.skills:
            out[skill.id] = parent_id
    return out


def find_skill(skill_id: str) -> WsiSkill | None:
    """Lookup skill por id. Returns None se nao existe."""
    tax = load_taxonomy()
    parent_id = get_skill_to_parent_index().get(skill_id)
    if parent_id is None:
        return None
    parent = tax.parents[parent_id]
    for skill in parent.skills:
        if skill.id == skill_id:
            return skill
    return None


def parent_of(skill_id: str) -> str | None:
    """Returns parent_id de uma skill, ou None se nao existe."""
    return get_skill_to_parent_index().get(skill_id)


def all_skill_ids() -> list[str]:
    """Lista todos skill_ids da taxonomia (para enum dinamico)."""
    return sorted(get_skill_to_parent_index().keys())


def all_parent_ids() -> list[str]:
    """Lista todos parent_ids da taxonomia."""
    tax = load_taxonomy()
    return sorted(tax.parents.keys())


def skills_by_parent(parent_id: str) -> list[WsiSkill]:
    """Returns skills de um parent. Empty list se parent nao existe."""
    tax = load_taxonomy()
    parent = tax.parents.get(parent_id)
    if parent is None:
        return []
    return list(parent.skills)


def get_skills_by_ocean(ocean_dim: str) -> list[WsiSkill]:
    """Returns all skills with primary_ocean == ocean_dim.

    Args:
        ocean_dim: One of 'O', 'C', 'E', 'A', 'N'. Returns [] for invalid.

    Example:
        >> get_skills_by_ocean('A')  # Agreeableness — empathy, teamwork, service
    """
    if ocean_dim not in ALLOWED_OCEAN:
        return []
    tax = load_taxonomy()
    result: list[WsiSkill] = []
    for parent in tax.parents.values():
        for skill in parent.skills:
            if skill.primary_ocean == ocean_dim:
                result.append(skill)
    return result


def get_skills_by_bias_risk(risk_level: str) -> list[WsiSkill]:
    """Returns all skills with bias_risk == risk_level.

    Useful for fairness auditing — identify which skills need extended
    observation before influencing question generation.

    Args:
        risk_level: 'low' | 'medium' | 'high'
    """
    tax = load_taxonomy()
    return [
        skill
        for parent in tax.parents.values()
        for skill in parent.skills
        if skill.bias_risk == risk_level
    ]


def get_sample_threshold(skill: WsiSkill) -> int:
    """Returns the required sample count before this skill influences question gen.

    Wraps THRESHOLD_BY_BIAS_RISK — use this instead of the dict directly so
    future calibration changes propagate automatically.
    """
    return THRESHOLD_BY_BIAS_RISK.get(skill.bias_risk, THRESHOLD_BY_BIAS_RISK["medium"])


def get_decay_lambda(skill: WsiSkill) -> float:
    """Returns the temporal decay λ for this skill's effectiveness score.

    Wraps DECAY_LAMBDA_BY_TYPE — use this instead of the dict directly.
    """
    return DECAY_LAMBDA_BY_TYPE.get(skill.decay_rate, DECAY_LAMBDA_BY_TYPE["normal"])
