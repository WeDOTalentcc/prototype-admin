"""
job_vacancies package — aggregates all sub-routers into a single `router`
and re-exports `router_public` for unauthenticated candidate flows.

Sub-modules:
  _shared    — shared imports, helpers, Pydantic schemas
  crud       — GET/POST/PUT/DELETE/PATCH + finalize/search/duplicate/clone (14 routes)
  lifecycle  — publish, confirm-global-search, sourcing-status, bulk ops, close (15 routes)
  analytics  — metrics, analytics, history, stats/overview, job report (6 routes)
  screening  — screening-config GET/PUT, screening-status PUT (3 routes)
  public     — generate-public-link, share-link (auth) + /p/{slug} GET/POST (4 routes)
  export     — PDF/Excel export (2 routes)
"""

from fastapi import APIRouter

from .crud import router as _crud_router
from .lifecycle import router as _lifecycle_router
from .analytics import router as _analytics_router
from .screening import router as _screening_router
from .public import router as _public_router, router_public
from .export import router as _export_router

# Main aggregated router
router = APIRouter()

router.include_router(_crud_router)
router.include_router(_lifecycle_router)
router.include_router(_analytics_router)
router.include_router(_screening_router)
router.include_router(_public_router)
router.include_router(_export_router)

# router_public is already exported above — used as:
#   app.include_router(job_vacancies.router_public, prefix="/api/v1/public-vacancies", ...)

__all__ = ["router", "router_public"]
