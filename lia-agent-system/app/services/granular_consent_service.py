"""Shim: re-exports from app.domains.lgpd.services.granular_consent_service (canonical location).

Tests patch via app.services.granular_consent_service — this shim ensures importability.
"""
from app.domains.lgpd.services.granular_consent_service import *  # noqa: F401, F403
try:
    from app.domains.lgpd.services.granular_consent_service import *  # noqa: F401, F403
except ImportError:
    pass
