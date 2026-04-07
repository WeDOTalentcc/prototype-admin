"""Backwards-compatibility shim — canonical implementation in domain layer."""
from app.domains.ai.services.llm import *  # noqa: F401, F403
from app.domains.ai.services.llm import get_llm_service  # noqa: F401
