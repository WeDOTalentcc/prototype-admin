"""Onda 4.1 shim — re-export LLMService at app.services.llm path.

Tests patch app.services.llm.LLMService; the actual class lives in
app.domains.ai.services.llm. This shim satisfies the canonical import
path that tests assume (and matches the conventional app/services/ layout).
"""
from app.domains.ai.services.llm import LLMService  # noqa: F401
