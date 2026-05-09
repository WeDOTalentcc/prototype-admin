"""Shim: re-exports from app.shared.services.consent_checker_service (canonical location).

Tests patch via app.services.consent_checker_service — this shim ensures importability.
"""
from app.shared.services.consent_checker_service import *  # noqa: F401, F403
try:
    from app.shared.services.consent_checker_service import *  # noqa: F401, F403
except ImportError:
    pass
