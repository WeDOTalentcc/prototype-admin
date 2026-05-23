# Re-exports canonicos (ordem de subdirs: memory/ routing/ legacy/ + root modules)

# memory/
from .memory.semantic_cache import SemanticCache, semantic_cache
# vector_semantic_cache não re-exportado aqui (sem importadores externos via __init__)

# routing/
from .routing.domain_mappings import AGENT_TYPE_TO_DOMAIN, resolve_domain

# legacy/
from .legacy.orchestrator import Orchestrator

# root modules (inalterados — muitos importadores externos)
from .cascaded_router import CascadedRouter
from .llm_cascade import LLMCascadeRouter, llm_cascade_router
from .state_manager import StateManager
from .task_planner import TaskPlanner
from .tenant_budget import TenantBudget, tenant_budget

__all__ = [
    "TaskPlanner",
    "StateManager",
    "Orchestrator",
    "CascadedRouter",
    "AGENT_TYPE_TO_DOMAIN",
    "resolve_domain",
    "SemanticCache",
    "semantic_cache",
    "TenantBudget",
    "tenant_budget",
    "LLMCascadeRouter",
    "llm_cascade_router",
]
