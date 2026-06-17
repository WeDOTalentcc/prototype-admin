"""
Orchestrator singleton registry -- shared neutral location.
Avoids circular imports between app.api and app.domains.

Usage:
    from app.orchestrator.execution.registry import get_orchestrator_instance, set_orchestrator_instance
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.orchestrator.legacy.orchestrator import Orchestrator

logger = logging.getLogger(__name__)

# Module-level singleton -- set via initialize_orchestrator() at startup
_orchestrator_instance: "Orchestrator | None" = None


def get_orchestrator_instance() -> "Orchestrator | None":
    """Return the current orchestrator instance (None if not yet initialized)."""
    return _orchestrator_instance


def set_orchestrator_instance(orch: "Orchestrator") -> None:
    """Register the orchestrator instance (called once at startup)."""
    global _orchestrator_instance
    _orchestrator_instance = orch
    logger.info("Orchestrator instance registered in registry")
