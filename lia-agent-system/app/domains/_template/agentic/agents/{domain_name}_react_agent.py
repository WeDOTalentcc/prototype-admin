from app.shared.agents.tenant_aware_agent import TenantAwareAgentMixin
from libs.agents_core.lia_agents_core.langgraph_react_base import LangGraphReActBase
from libs.agents_core.lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
from app.agents.agent_registry import register_agent

from .{domain_name}_tool_registry import TOOLS


@register_agent("{domain_name}")
class {DomainName}ReActAgent(TenantAwareAgentMixin, LangGraphReActBase, EnhancedAgentMixin):
    domain_name = "{domain_name}"

    def _get_tools(self):
        return TOOLS

    def _get_system_prompt(self, **kwargs):
        return "You are a specialized {domain_name} assistant."

    def _state_to_output(self, state):
        messages = state.get("messages", [])
        if messages:
            return messages[-1].content
        return "No response generated."
