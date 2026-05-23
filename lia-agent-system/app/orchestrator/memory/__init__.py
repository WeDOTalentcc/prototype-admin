"""
orchestrator/memory/ — módulos de cache semântico para roteamento.

Re-exports de compatibilidade: imports existentes via app.orchestrator.semantic_cache
continuam funcionando através do __init__.py do pacote pai.
"""
from app.orchestrator.memory.semantic_cache import SemanticCache, semantic_cache
from app.orchestrator.memory.vector_semantic_cache import VectorSemanticCache

__all__ = [
    "SemanticCache",
    "semantic_cache",
    "VectorSemanticCache",
]
