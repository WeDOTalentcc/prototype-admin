"""
candidates package — re-exports a single combined APIRouter.

Sub-module routes are appended directly to avoid FastAPI empty-prefix/path conflict
(which occurs when include_router is used with both prefix="" and path="").
"""
from fastapi import APIRouter

from .candidates_crud import router as crud_router
from .candidates_search import router as search_router
from .candidates_metadata import router as metadata_router
from .candidates_consent import router as consent_router
from .candidates_quick_ask import router as quick_ask_router

router = APIRouter()

for _sub in (crud_router, search_router, metadata_router, consent_router, quick_ask_router):
    router.routes.extend(_sub.routes)

__all__ = ["router"]
