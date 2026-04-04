"""
Candidate Search package - aggregates all sub-routers.

Sub-modules:
  core_search   - /candidates, /evaluate-for-job, /candidates/import, /candidates/promote,
                  /candidates/persist-revealed, /candidates/estimate, /similar, /similar/combine-profiles
  jd_search     - /by-job-description, /candidates/refine, /candidates/local, /parse-query
  contact       - /reveal/cost, /reveal, /suggestions
  archetypes    - all /archetypes/* routes
  misc_search   - /from-cv, /analyze, /enhance-prompt
  calibration   - /calibration/*, /vacancy/*
"""
from fastapi import APIRouter

from .core_search import router as core_search_router
from .jd_search import router as jd_search_router
from .contact import router as contact_router
from .archetypes import router as archetypes_router
from .misc_search import router as misc_search_router
from .calibration import router as calibration_router

router = APIRouter(prefix=/search, tags=[candidate-search])

router.include_router(core_search_router)
router.include_router(jd_search_router)
router.include_router(contact_router)
router.include_router(archetypes_router)
router.include_router(misc_search_router)
router.include_router(calibration_router)

__all__ = [router]
