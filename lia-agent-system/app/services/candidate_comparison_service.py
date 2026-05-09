"""Shim: re-exports from canonical app.domains.candidates.services.candidate_comparison_service."""
from app.domains.candidates.services.candidate_comparison_service import *  # noqa: F401, F403
try:
    from app.domains.candidates.services.candidate_comparison_service import (
        CandidateComparisonService, get_candidate_comparison_service,
    )
except ImportError:
    pass
