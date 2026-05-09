"""Shim: re-exports from app.shared.services.suggestion_interaction_service (canonical location).

Tests patch via app.services.suggestion_interaction_service — this shim ensures importability.
"""
from app.shared.services.suggestion_interaction_service import *  # noqa: F401, F403
try:
    from app.shared.services.suggestion_interaction_service import *  # noqa: F401, F403
except ImportError:
    pass
