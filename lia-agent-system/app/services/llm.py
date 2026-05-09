"""Shim: re-exports LLMService from canonical app.domains.ai.services.llm.

Tests and handlers that patch app.services.llm.LLMService use this shim.
"""
from app.domains.ai.services.llm import LLMService  # noqa: F401
from app.domains.ai.services.llm import *  # noqa: F401, F403
