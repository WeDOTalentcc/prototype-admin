"""Tool registry for CandidateSelfServiceAgent — whitelist of 4 read-only tools ONLY."""
from lia_agents_core.tool_adapter import ToolDefinition

from app.domains.candidate_self_service.tools.get_application_status import get_application_status
from app.domains.candidate_self_service.tools.get_interview_info import get_interview_info
from app.domains.candidate_self_service.tools.get_wsi_feedback import get_wsi_feedback
from app.domains.candidate_self_service.tools.explain_candidate_decision import (
    explain_candidate_decision,
)

# WHITELIST: exactly 4 tools. Any tool not here is inaccessible from this domain.
_CANDIDATE_TOOLS: list[ToolDefinition] = [
    get_application_status,
    get_interview_info,
    get_wsi_feedback,
    explain_candidate_decision,
]


def get_candidate_tools() -> list[ToolDefinition]:
    """Return the immutable whitelist of candidate self-service tools."""
    return list(_CANDIDATE_TOOLS)
