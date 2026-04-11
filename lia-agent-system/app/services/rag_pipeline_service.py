"""Backwards-compatibility shim — canonical implementation in app.domains.ai.services.rag_pipeline_service."""
from app.domains.ai.services.rag_pipeline_service import *  # noqa: F401,F403
from app.domains.ai.services.rag_pipeline_service import (  # noqa: F401
    _check_fairness,
    _merge_candidate_results,
    _normalize,
    generate_embedding,
    RAGPipelineService,
    RAGSearchResult,
    normalize_domain,
    DOMAIN_ALIASES,
)
