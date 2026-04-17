"""
lia_assistant package — splits the original 3160-line god module into focused sub-modules.

Sub-modules:
  _shared.py        — all imports, constants, shared Pydantic models, helpers
  suggestions.py    — GET /lia/suggestions
  wizard.py         — POST /lia/job-wizard/* (interpret, orchestrate, salary-benchmark, evaluate, step)
  insights.py       — POST /lia/job-insights, POST /lia/expanded-prompt
  conversational.py — POST /lia/conversational, GET/DELETE /lia/job-draft/*, GET /lia/context-suggestions

The previously-extracted Sprint E stub routers (lia_voice, lia_multimodal,
lia_autonomous, lia_feedback) were empty placeholders and have been removed.
"""
from fastapi import APIRouter

from .conversational import router as _conversational_router
from .insights import router as _insights_router

# --- This package's sub-routers ---
from .suggestions import router as _suggestions_router
from .wizard import router as _wizard_router

# Main router exposed to main.py (same prefix as before)
router = APIRouter(prefix="/lia", tags=["lia-assistant"])

# This package's route groups
router.include_router(_suggestions_router)
router.include_router(_wizard_router)
router.include_router(_insights_router)
router.include_router(_conversational_router)

# Re-export shared graph types for backwards compatibility
# (graph routes live in lia_assistant_graph.py, registered separately in main.py)
from app.api.v1.lia_assistant_graph import (
    GraphInfoResponse,
    GraphOrchestratorRequest,
    GraphOrchestratorResponse,
    SessionStateResponse,
)

__all__ = [
    "router",
    # graph compat re-exports
    "GraphOrchestratorRequest",
    "GraphOrchestratorResponse",
    "SessionStateResponse",
    "GraphInfoResponse",
]
