"""Organization catalog data — loaded from JSON, hydrated into dataclass instances.

The canonical data lives in ``app/data/organization_catalog.json``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_JSON_PATH = Path(__file__).resolve().parents[3] / "data" / "organization_catalog.json"

_cache: dict | None = None

_NAMES = frozenset({
    "AREAS_CATALOG",
    "SENIORITY_LEVELS",
    "BEHAVIORAL_SKILLS",
    "TECHNICAL_SKILLS",
    "ROLES_CATALOG",
})


def _load_catalog() -> dict:
    from .organization_catalog_service import (
        Area,
        SeniorityLevel,
        Role,
        TechnicalSkill,
        BehavioralSkill,
    )

    with open(_JSON_PATH, "r", encoding="utf-8") as fh:
        raw = json.load(fh)

    return {
        "AREAS_CATALOG": {k: Area(**v) for k, v in raw["AREAS_CATALOG"].items()},
        "SENIORITY_LEVELS": {k: SeniorityLevel(**v) for k, v in raw["SENIORITY_LEVELS"].items()},
        "BEHAVIORAL_SKILLS": {k: BehavioralSkill(**v) for k, v in raw["BEHAVIORAL_SKILLS"].items()},
        "TECHNICAL_SKILLS": {k: TechnicalSkill(**v) for k, v in raw["TECHNICAL_SKILLS"].items()},
        "ROLES_CATALOG": {k: Role(**v) for k, v in raw["ROLES_CATALOG"].items()},
    }


def __getattr__(name: str):
    global _cache
    if name in _NAMES:
        if _cache is None:
            _cache = _load_catalog()
            # Inject into module dict so future accesses skip __getattr__
            mod = sys.modules[__name__]
            for k, v in _cache.items():
                setattr(mod, k, v)
        return _cache[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
