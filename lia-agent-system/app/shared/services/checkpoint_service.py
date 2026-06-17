"""Backwards-compatibility shim — real implementation in app/domains/cv_screening/services."""
from app.domains.cv_screening.services.checkpoint_service import *  # noqa: F401,F403
# Explicit export of private symbols for test imports
try:
    from app.domains.cv_screening.services.checkpoint_service import _sanitize_state  # noqa: F401
except ImportError:
    pass
