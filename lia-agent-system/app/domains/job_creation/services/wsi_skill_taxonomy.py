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


class WsiSkill(BaseModel):
    """Schema de uma skill na taxonomia."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name_pt: str
    description: str
    seniority_min: str
    source: str
    fairness_flag: str | None = None


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
