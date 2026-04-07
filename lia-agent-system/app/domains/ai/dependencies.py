"""FastAPI dependency factories for the AI domain."""
from app.domains.ai.services.llm import LLMService, get_llm_service

__all__ = ["LLMService", "get_llm_service"]
