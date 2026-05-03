"""
lia_assistant package — splits the original 3160-line god module into focused sub-modules.

Sub-modules:
  _shared.py        — all imports, constants, shared Pydantic models, helpers
  suggestions.py    — GET /lia/suggestions
  wizard.py         — POST /lia/job-wizard/* (interpret, orchestrate, salary-benchmark, evaluate, step)
  insights.py       — POST /lia/job-insights, POST /lia/expanded-prompt
  conversational.py — POST /lia/conversational, GET/DELETE /lia/job-draft/*, GET /lia/context-suggestions

Previously extracted sub-routers (Sprint E / Phase 5) are still included here so
main.py only needs to import from this package:
  lia_voice, lia_multimodal, lia_autonomous, lia_feedback
"""
from fastapi import APIRouter

from app.api.v1.lia_autonomous import autonomous_router
from app.api.v1.lia_feedback import feedback_router
from app.api.v1.lia_multimodal import multimodal_router

# --- Previously-extracted Sprint-E sub-routers ---
from app.api.v1.lia_voice import voice_router

from .conversational import router as _conversational_router
from .insights import router as _insights_router

# --- This package's sub-routers ---
from .suggestions import router as _suggestions_router
from .wizard import router as _wizard_router

# Main router exposed to main.py (same prefix as before)
router = APIRouter(prefix="/lia", tags=["lia-assistant"])

# Sprint E sub-routers (no extra prefix — they already have /lia/... paths internally)
router.include_router(voice_router)
router.include_router(multimodal_router)
router.include_router(autonomous_router)
router.include_router(feedback_router)

# This package's route groups
router.include_router(_suggestions_router)
router.include_router(_wizard_router)
router.include_router(_insights_router)
router.include_router(_conversational_router)

__all__ = [
    "router",
]
