"""
SourcingEngagementAgent Tool Registry — Z2-02.

Expõe tools da etapa outreach: envio, geração de mensagens e rastreamento.
send_outreach é GUARDRAIL — requer confirmação HITL (AUD-4).
"""

from lia_agents_core.tool_adapter import ToolDefinition

from app.domains.sourcing.agents.sourcing_tool_registry import _TOOL_MAP
from app.shared.compliance.safety_category import SafetyCategory

_ENGAGEMENT_TOOLS = ["send_outreach", "generate_message", "track_response"]

# Tools que requerem HITL (AUD-4): não são chamadas sem aprovação humana
GUARDRAIL_TOOLS: dict[str, SafetyCategory] = {
    "send_outreach": SafetyCategory.OUTREACH,
}


def get_engagement_tools() -> list[ToolDefinition]:
    return [_TOOL_MAP[name] for name in _ENGAGEMENT_TOOLS if name in _TOOL_MAP]
