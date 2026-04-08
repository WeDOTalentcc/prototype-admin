"""
event_handlers package.

Aggregates all /handle-trigger/* routes from the four sub-modules and
re-exports a single ``router`` so existing callers require no changes:

    from .event_handlers import router as event_handlers_router  # unchanged

Sub-modules:
- handlers_screening.py  : screening-completed (WSI calculation)
- handlers_interview.py  : interview-scheduled, interview-completed
- handlers_lifecycle.py  : candidate-inactive, candidate-no-show,
                           offer-sent, candidate-hired, candidate-rejected
- handlers_ats_sync.py   : ats-sync
"""
from fastapi import APIRouter

from .handlers_screening import router as screening_router
from .handlers_screening import _normalize_weights
from .handlers_interview import router as interview_router
from .handlers_lifecycle import router as lifecycle_router
from .handlers_ats_sync import router as ats_router

router = APIRouter()
router.include_router(screening_router)
router.include_router(interview_router)
router.include_router(lifecycle_router)
router.include_router(ats_router)

__all__ = ["router", "_normalize_weights"]
