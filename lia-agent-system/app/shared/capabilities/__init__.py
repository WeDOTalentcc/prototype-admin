"""Aggregated read-only capability views derived from existing registries.

This package never declares a new hand-maintained registry — it *reads* the
canonical registries (domain ``capabilities.yaml`` intent maps, the tool
registry, ``app/tools/categories.py``) and exposes a consolidated, tenant-aware
view so that prompts and meta-question handlers all state the SAME truth.

See ADR-008 (Capability Single Source of Truth).
"""
from app.shared.capabilities.job_creation_capabilities import (
    CreationMode,
    answer_can_create_question,
    get_creation_modes,
    render_creation_modes_block,
)

__all__ = [
    "CreationMode",
    "answer_can_create_question",
    "get_creation_modes",
    "render_creation_modes_block",
]
