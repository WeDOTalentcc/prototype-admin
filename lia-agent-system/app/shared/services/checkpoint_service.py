"""Backwards-compatibility shim — real implementation in app/domains/cv_screening/services."""
from app.domains.cv_screening.services.checkpoint_service import *  # noqa: F401,F403
# Private helpers are not exported by star-import; expose them explicitly so
# tests and internal callers can reach them via this canonical shim path.
from app.domains.cv_screening.services.checkpoint_service import (  # noqa: F401
    _sanitize_state,
    _is_json_serializable,
    _FIELDS_NOT_TO_PERSIST,
)
