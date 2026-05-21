"""Backwards-compatibility shim — real implementation in app/domains/policy/services."""
from app.domains.policy.services.policy_engine_service import *  # noqa: F401,F403  # DEPRECATED-IMPORT-EXEMPT: Shim canonical (callers legacy em app.shared.services.* path) — re-export de app.domains.policy.services.policy_engine_service canonical
