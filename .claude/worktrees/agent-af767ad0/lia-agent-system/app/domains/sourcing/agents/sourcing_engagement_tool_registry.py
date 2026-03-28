"""
SourcingEngagementAgent Tool Registry — Z2-02.

Expõe tools da etapa outreach: envio, geração de mensagens e rastreamento.
send_outreach é GUARDRAIL — requer confirmação HITL (AUD-4).
"""
from app.domains.sourcing.agents.sourcing_tool_registry import _TOOL_MAP
from app.shared.agents.react_loop import ToolDefinition
from typing import List

_ENGAGEMENT_TOOLS = ["send_outreach", "generate_message", "track_response"]

# Tools que requerem HITL (AUD-4): não são chamadas sem aprovação humana
GUARDRAIL_TOOLS = ["send_outreach"]


def get_engagement_tools() -> List[ToolDefinition]:
    return [_TOOL_MAP[name] for name in _ENGAGEMENT_TOOLS if name in _TOOL_MAP]
