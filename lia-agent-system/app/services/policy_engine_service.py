"""Shim: re-exports the canonical PolicyEngineService module (path: app/shared/services/policy_engine_service.py).

Tests patch via app.services.policy_engine_service — this shim ensures importability.
"""
from app.shared.services.policy_engine_service import *  # noqa: F401, F403  # DEPRECATED-IMPORT-EXEMPT: Shim re-export para test patches backward-compat (tests patch via app.services.policy_engine_service path legacy)
try:
    from app.shared.services.policy_engine_service import *  # noqa: F401, F403  # DEPRECATED-IMPORT-EXEMPT: Shim re-export defensive try/except duplicate (test patch backward-compat) — canonical impl em app.domains.policy.services
except ImportError:
    pass
