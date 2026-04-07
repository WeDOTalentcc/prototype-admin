"""Backwards-compatibility shim — canonical implementation in domain layer."""
from app.shared.services.rag_pipeline_service import *  # noqa: F401, F403
from app.shared.services.rag_pipeline_service import (  # noqa: F401
    _check_fairness,
    _merge_candidate_results,
    _normalize,
)
