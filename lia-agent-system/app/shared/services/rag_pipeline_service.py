"""Backwards-compatibility shim — canonical implementation in app.services.rag_pipeline_service."""
from app.services.rag_pipeline_service import *  # noqa: F401,F403
from app.services.rag_pipeline_service import (  # noqa: F401
    _DEFAULT_SEMANTIC_THRESHOLD,
    _FAIRNESS_MAX_SINGLE_GENDER_RATIO,
    _check_fairness,
    _merge_candidate_results,
    _normalize,
)
