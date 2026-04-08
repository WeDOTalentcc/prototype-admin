"""
Core search routes - thin orchestrator.

Route implementations live in:
  search.py              - POST /candidates
  evaluation.py          - POST /evaluate-for-job
  import_export.py       - POST /candidates/import, POST /candidates/promote/{id}
  contact_persistence.py - POST /candidates/persist-revealed
  credits.py             - POST /candidates/estimate
  similar_search.py      - POST /similar, POST /similar/combine-profiles
"""
from fastapi import APIRouter

from .search import router as _search_router
from .evaluation import router as _evaluation_router
from .import_export import router as _import_export_router
from .contact_persistence import router as _contact_persistence_router
from .credits import router as _credits_router
from .similar_search import router as _similar_search_router

# Re-export shared models for backward compatibility
from ._shared import (  # noqa: F401
    CandidateSearchResultDTO,
    CreditEstimateDTO,
    EducationDTO,
    EvaluateForJobRequest,
    EvaluateForJobResponse,
    EvaluateForJobResult,
    ExperienceDTO,
    IdMapping,
    ImportCandidateDTO,
    ImportCandidateExperienceDTO,
    ImportCandidatesRequest,
    ImportCandidatesResponse,
    LanguageDTO,
    SearchRequestDTO,
    SearchResponseDTO,
    _normalize_priority,
)

router = APIRouter()
router.include_router(_search_router)
router.include_router(_evaluation_router)
router.include_router(_import_export_router)
router.include_router(_contact_persistence_router)
router.include_router(_credits_router)
router.include_router(_similar_search_router)
