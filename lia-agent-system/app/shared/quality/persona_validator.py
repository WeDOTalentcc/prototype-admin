"""Onda 3.4 Init VIII (2026-04-21) — Persona consistency validator.

Deterministic validator for recorded LIA responses against persona scenarios
(tests/persona_scenarios.yaml). Checks expected_anchors AND forbidden_anchors
per scenario.

v1 is deterministic string matching — cheap, runs in CI without LLM cost.
v2 (Init VIII.B) will add LLM-as-judge scoring per dimension via Init VI
infra when cost governance (G4) green-lights sustained judge calls.

Usage:
    from app.shared.quality.persona_validator import validate_response
    verdict = validate_response("PC-001", recorded_response_text)
    if not verdict.passed:
        print(verdict.failures)

Canonical-fix: scenarios YAML is single producer for consistency spec.
Python validator is thin consumer.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_PERSONA_VALIDATOR_ENABLED = os.environ.get(
    "LIA_PERSONA_VALIDATOR_ENABLED", "true"
).lower() == "true"


@dataclass
class ValidationVerdict:
    """Per-scenario validation outcome."""
    scenario_id: str
    dimension: str
    passed: bool
    failures: list[str] = field(default_factory=list)
    expected_hits: list[str] = field(default_factory=list)
    forbidden_hits: list[str] = field(default_factory=list)


@lru_cache(maxsize=1)
def _load_scenarios() -> dict[str, dict[str, Any]]:
    """Load tests/persona_scenarios.yaml. Cached — restart to reload."""
    # Walk up from this file until we find the repo root that has tests/persona_scenarios.yaml
    here = Path(__file__).resolve()
    for parent in here.parents:
        cand = parent / "tests/persona_scenarios.yaml"
        if cand.exists():
            data = yaml.safe_load(cand.read_text(encoding="utf-8")) or {}
            return {s["id"]: s for s in data.get("scenarios", [])}
    logger.warning("Init VIII: tests/persona_scenarios.yaml not found")
    return {}


def list_scenario_ids() -> list[str]:
    """Return all scenario IDs registered."""
    return sorted(_load_scenarios().keys())


def list_dimensions() -> list[str]:
    """Return unique dimension tags across all scenarios."""
    scs = _load_scenarios()
    return sorted({s.get("dimension", "unknown") for s in scs.values()})


def validate_response(scenario_id: str, response_text: str) -> ValidationVerdict | None:
    """Deterministic string-match validation against scenario anchors.

    Rules:
      - All expected_anchors must appear (case-insensitive)
      - NO forbidden_anchors may appear (case-insensitive)
      - Returns ValidationVerdict with failures listed

    Returns None when scenario unknown or disabled.
    """
    if not _PERSONA_VALIDATOR_ENABLED:
        return None

    scs = _load_scenarios()
    sc = scs.get(scenario_id)
    if sc is None:
        return None

    text_lower = (response_text or "").lower()
    expected = sc.get("expected_anchors", []) or []
    forbidden = sc.get("forbidden_anchors", []) or []
    dimension = sc.get("dimension", "unknown")

    expected_hits = [a for a in expected if a.lower() in text_lower]
    forbidden_hits = [a for a in forbidden if a.lower() in text_lower]

    failures: list[str] = []
    for a in expected:
        if a.lower() not in text_lower:
            failures.append(f"missing expected anchor: {a!r}")
    for a in forbidden_hits:
        failures.append(f"forbidden anchor present: {a!r}")

    return ValidationVerdict(
        scenario_id=scenario_id,
        dimension=dimension,
        passed=not failures,
        failures=failures,
        expected_hits=expected_hits,
        forbidden_hits=forbidden_hits,
    )


def batch_validate(responses: dict[str, str]) -> dict[str, ValidationVerdict]:
    """Validate a batch of {scenario_id: response_text} → {scenario_id: verdict}."""
    return {
        sid: v for sid, text in responses.items()
        if (v := validate_response(sid, text)) is not None
    }
