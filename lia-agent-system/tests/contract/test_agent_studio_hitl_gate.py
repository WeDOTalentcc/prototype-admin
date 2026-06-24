"""
Contrato: Agent Studio não pode executar tools sensíveis sem HITL gate.
P0-1 do Onda 0 audit.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

SENSITIVE_TOOLS = [
    "publish_job",
    "send_offer",
    "reject_candidate",
    "bulk_update_candidates",
    "send_email_bulk",
]


def test_hitl_required_tools_constant_exists():
    """HITL_REQUIRED_TOOLS deve existir e conter as tools sensíveis."""
    from app.domains.agent_studio.custom_agent_runtime import HITL_REQUIRED_TOOLS
    for tool in SENSITIVE_TOOLS:
        assert tool in HITL_REQUIRED_TOOLS, f"{tool} deve estar em HITL_REQUIRED_TOOLS"


def test_sensitive_tool_in_constant():
    """publish_job e send_offer devem estar em HITL_REQUIRED_TOOLS."""
    from app.domains.agent_studio.custom_agent_runtime import HITL_REQUIRED_TOOLS
    assert "publish_job" in HITL_REQUIRED_TOOLS
    assert "send_offer" in HITL_REQUIRED_TOOLS
    assert "reject_candidate" in HITL_REQUIRED_TOOLS


def test_search_candidates_not_in_hitl_required():
    """search_candidates não é sensível e não deve estar em HITL_REQUIRED_TOOLS."""
    from app.domains.agent_studio.custom_agent_runtime import HITL_REQUIRED_TOOLS
    assert "search_candidates" not in HITL_REQUIRED_TOOLS
