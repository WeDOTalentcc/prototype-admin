"""
candidates package — re-exports a single combined APIRouter.
"""
from fastapi import APIRouter

from .candidates_crud import router as crud_router
from .candidates_search import router as search_router
from .candidates_metadata import router as metadata_router
from .candidates_consent import router as consent_router

router = APIRouter()
router.include_router(crud_router)
router.include_router(search_router)
router.include_router(metadata_router)
router.include_router(consent_router)

__all__ = ["router"]
