"""
COMPAT STUB — W4-035 Fase 1.
Módulo movido para app/orchestrator/memory/semantic_cache.py.
Este stub mantém compatibilidade de imports existentes (incluindo símbolos privados usados em testes).
"""
from app.orchestrator.memory.semantic_cache import (  # noqa: F401
    SemanticCache,
    semantic_cache,
    _cache_key,
)

__all__ = ["SemanticCache", "semantic_cache", "_cache_key"]
