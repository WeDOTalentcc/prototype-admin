"""Shim: re-exports from app.shared.services.policy_engine_service (canonical location).

Tests patch via app.services.policy_engine_service — this shim ensures importability.
"""
from app.shared.services.policy_engine_service import *  # noqa: F401, F403
try:
    from app.shared.services.policy_engine_service import *  # noqa: F401, F403
except ImportError:
    pass
