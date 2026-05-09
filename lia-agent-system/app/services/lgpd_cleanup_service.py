"""Shim: re-exports from app.shared.services.lgpd_cleanup_service (canonical location).

Tests patch via app.services.lgpd_cleanup_service — this shim ensures importability.
"""
from app.shared.services.lgpd_cleanup_service import *  # noqa: F401, F403
try:
    from app.shared.services.lgpd_cleanup_service import *  # noqa: F401, F403
except ImportError:
    pass
