"""
orchestrator/routing/ — mapeamento de domínios e roteamento de agentes.

Re-exports de compatibilidade: app.orchestrator.domain_mappings ainda funciona
via __init__.py do pacote pai (não precisa atualizar callers externos).
"""
from app.orchestrator.routing.domain_mappings import AGENT_TYPE_TO_DOMAIN, resolve_domain

__all__ = [
    "AGENT_TYPE_TO_DOMAIN",
    "resolve_domain",
]
