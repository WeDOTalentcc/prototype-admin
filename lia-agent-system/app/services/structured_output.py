"""Backwards-compatibility shim — canonical implementation in domain layer."""
from app.domains.ai.services.structured_output import *  # noqa: F401,F403
from app.domains.ai.services.structured_output import _get_json_type  # noqa: F401
