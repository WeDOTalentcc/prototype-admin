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
from .command_catalog import router as _command_catalog_router
from .suggestion_click import router as _suggestion_click_router
from .suggestions import router as _suggestions_router
from .wizard import router as _wizard_router
from .wizard_session import router as _wizard_session_router

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
# Task #1128 — canonical GET/DELETE wizard session endpoints. Must come AFTER
# `_wizard_router` because that file owns the tombstone (HTTP 410) POSTs on
# the same `/job-wizard/*` namespace; FastAPI matches by exact path so order
# is informational only — sentinel `test_wizard_session_endpoints_t1128.py`
# guards against the GET/DELETE being shadowed accidentally.
router.include_router(_wizard_session_router)
router.include_router(_insights_router)
router.include_router(_conversational_router)

# Onda 4-Fase8 P1-3 Fase 2 (2026-05-24): canonical click logging
router.include_router(_suggestion_click_router)

# Fase 2 (2026-06-06): catálogo de comandos acionáveis (Ctrl+/ + Cmd+K)
router.include_router(_command_catalog_router)

__all__ = [
    "router",
]
