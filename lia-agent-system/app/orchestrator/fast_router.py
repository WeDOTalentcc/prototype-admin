# app/orchestrator/fast_router.py
# W4-035 Fase 2 compatibility stub -- arquivo real: app/orchestrator/routing/fast_router.py
# Exporta todos os simbolos necessarios (publicos e privados).
from app.orchestrator.routing.fast_router import *  # noqa: F401, F403
from app.orchestrator.routing.fast_router import (  # noqa: F401
    FastRouter,
    FastRouteResult,
    normalize_domain_id,
    DOMAIN_PATTERNS,
    _COMPILED_PATTERNS,
    _HARDCODED_DOMAIN_PATTERNS,
    _ensure_compiled,
    _get_domain_matcher,
    _load_domain_patterns,
)
