"""
pipeline_rules — Single source of truth for pipeline stage semantics.

Consumers should import from here instead of defining stage sets inline.

Usage:
    from app.shared.pipeline_rules import is_offer_stage, OFFER_STAGES

Sensor: tests/contract/test_gap05_pipeline_rules.py
"""
from __future__ import annotations

# Canonical set of stage names that count as "offer/proposta" stage.
# These names trigger offer-related policy checks (min_interviews, manager_approval).
# NEVER define this list inline in endpoints — import from here.
OFFER_STAGES: frozenset[str] = frozenset({
    "proposta",
    "offer",
    "proposal",
    "contratação",
    "contratacao",  # accent-stripped variant for URL-safe contexts
    "hiring",
})


def is_offer_stage(stage_name: str | None) -> bool:
    """Return True if the stage name is in the canonical OFFER_STAGES set.

    Case-insensitive. Returns False for None/empty.
    """
    if not stage_name:
        return False
    return stage_name.strip().lower() in OFFER_STAGES
