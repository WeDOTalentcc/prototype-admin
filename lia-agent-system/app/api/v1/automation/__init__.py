"""
Automation API package.

Aggregates all automation sub-routers into a single router
with the /automation prefix, preserving the original API contract.

Sub-modules:
- triggers.py       : trigger management + general routes (8 routes)
- event_handlers.py : /handle-trigger/* routes (9 routes)
- suggestions.py    : suggestion management routes (9 routes)
- _shared.py        : imports, constants, Pydantic models
"""
from fastapi import APIRouter

from .event_handlers import router as event_handlers_router
from .suggestions import router as suggestions_router
from .triggers import router as triggers_router

# Main router with the /automation prefix — same as original automation.py
router = APIRouter(prefix="/automation", tags=["automation"])

router.include_router(triggers_router)
router.include_router(event_handlers_router)
router.include_router(suggestions_router)

__all__ = ["router"]
