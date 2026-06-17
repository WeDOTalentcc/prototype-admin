# Re-exports canonicos (ordem de subdirs: memory/ routing/ legacy/ execution/ guards/)

# memory/
from .memory.semantic_cache import SemanticCache, semantic_cache
# vector_semantic_cache nao re-exportado aqui (sem importadores externos via __init__)

# routing/
from .routing.domain_mappings import AGENT_TYPE_TO_DOMAIN, resolve_domain
from .routing.cascaded_router import CascadedRouter
from .routing.llm_cascade import LLMCascadeRouter, llm_cascade_router

# legacy/
from .legacy.orchestrator import Orchestrator

# execution/
from .execution.state_manager import StateManager
from .execution.task_planner import TaskPlanner

# guards/
from .guards.tenant_budget import TenantBudget, tenant_budget

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
