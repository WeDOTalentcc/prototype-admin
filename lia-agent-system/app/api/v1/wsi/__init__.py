"""
WSI package — aggregates all sub-routers into a single APIRouter.

Sub-modules:
  questions   — generate-questions, regenerate-questions, suggest-question, save, versions
  evaluation  — jd-evaluate, analyze-response, complete-screening
  sessions    — session CRUD, interview-graph sessions
  reports     — f11-report, ranking, candidate-ranking
"""
from fastapi import APIRouter

from . import evaluation, questions, reports, sessions

router = APIRouter(prefix="/api/v1/wsi", tags=["WSI Text Screening"])

router.include_router(questions.router)
router.include_router(evaluation.router)
router.include_router(sessions.router)
router.include_router(reports.router)

__all__ = ["router"]
