"""
recruitment_stages package
==========================
Splits the original 2 400-line recruitment_stages.py into focused sub-modules.

Public API (identical to the original module):
    router                    – main APIRouter for /api/v1/recruitment-stages
    screening_questions_router – APIRouter for /api/v1/screening-questions
"""
from fastapi import APIRouter

from .stages_crud import router as _crud_router
from .stages_substatus import router as _substatus_router
from .stages_ats_mapping import router as _ats_router
from .stages_pipeline import router as _pipeline_router
from .stages_transition import router as _transition_router
from .stages_return_events import router as _events_router
from .stages_screening_questions import router as screening_questions_router  # re-exported as-is

# Main router — aggregates all sub-module routers (no prefix here; prefix is
# applied in routes.py with prefix="/api/v1/recruitment-stages").
router = APIRouter()
router.include_router(_crud_router)
router.include_router(_substatus_router)
router.include_router(_ats_router)
router.include_router(_pipeline_router)
router.include_router(_transition_router)
router.include_router(_events_router)

# screening_questions_router is intentionally NOT included in `router` because
# routes.py mounts it separately at prefix="/api/v1" (not "/api/v1/recruitment-stages").

__all__ = ["router", "screening_questions_router"]
