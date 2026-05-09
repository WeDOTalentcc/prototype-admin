"""Shim: re-exports from app.shared.services.token_budget_service (canonical location).

Tests patch via app.services.token_budget_service — this shim ensures importability.
"""
from app.shared.services.token_budget_service import *  # noqa: F401, F403
try:
    from app.shared.services.token_budget_service import *  # noqa: F401, F403
except ImportError:
    pass
