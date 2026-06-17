"""Canonical OCEAN trait constants — single source of truth.

Sprint B P1-2 fix: ALLOWED_TRAITS was duplicated in
bigfive_department_profile_repository.py AND score_calculator.py
(local valid_traits set). Both now import from here so any trait
taxonomy change propagates to all consumers automatically.

Note: "stability" is used here instead of "neuroticism" (raw OCEAN)
because CompanyCultureProfile and BigFiveDepartmentProfile store the
neuroticism dimension as stability (higher = better) for UX clarity.
The Phase 2.5 trait_ocean values must also use "stability" accordingly.
See app/api/v1/wsi/_shared.py BigFiveIndicators.stability property.
"""
from __future__ import annotations

ALLOWED_TRAITS: frozenset[str] = frozenset({
    "openness",
    "conscientiousness",
    "extraversion",
    "agreeableness",
    "stability",
})
