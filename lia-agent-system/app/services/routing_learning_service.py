"""Shim: re-exports from app.shared.services.routing_learning_service (canonical location).

Tests patch via app.services.routing_learning_service — this shim ensures importability.
"""
from app.shared.services.routing_learning_service import *  # noqa: F401, F403
try:
    from app.shared.services.routing_learning_service import *  # noqa: F401, F403
except ImportError:
    pass
