"""
GithubSourcingAgent — Sub-agente para sourcing técnico via GitHub API.

Especializado na busca de desenvolvedores por linguagem de programação,
repositórios públicos e contribuições. Integra FairnessGuard (Layer 1+3)
para garantir que filtros de busca não sejam discriminatórios.

Tools: github_search_developers, github_get_profile, github_get_repos
"""
import logging

from app.domains.sourcing.agents.github_tool_registry import get_github_tools
from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
from app.shared.agents.agent_registry import register_agent

logger = logging.getLogger(__name__)


@register_agent("sourcing_github")  # W1-001 (2026-05-22)
class GithubSourcingAgent(SourcingReActAgent):
    """
    Sub-agente de sourcing via GitHub.

    Busca desenvolvedores por linguagem, localização, repositórios e
    contribuições. Ideal para vagas tech que exigem evidência de produção
    em projetos open-source ou stack específica.
    """

    def __init__(self) -> None:
        super().__init__()
        logger.info("[GithubSourcingAgent] Initialized (tools=%d)", len(get_github_tools()))

    @property
    def domain_name(self) -> str:
        return "sourcing_github"

    def _get_tools(self) -> list:
        from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool
        tool_defs = get_github_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]
