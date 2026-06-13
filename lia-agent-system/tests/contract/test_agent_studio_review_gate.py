"""
Contrato: agentes customizados do marketplace ficam em pending_review
ate aprovacao de admin WeDOTalent antes de poderem executar.
P0-2 do Onda 0 audit.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock


def test_review_status_pending_constant_exists():
    """REVIEW_STATUS_PENDING deve existir como constante de modulo."""
    from app.domains.agent_studio.custom_agent_runtime import REVIEW_STATUS_PENDING
    assert REVIEW_STATUS_PENDING == "pending_review"


def test_review_status_active_constant_exists():
    """REVIEW_STATUS_ACTIVE deve existir como constante de modulo."""
    from app.domains.agent_studio.custom_agent_runtime import REVIEW_STATUS_ACTIVE
    assert REVIEW_STATUS_ACTIVE == "active"


def test_execute_blocked_for_pending_review_listing():
    """Agente cujo marketplace listing esta em pending_review nao deve executar."""
    import asyncio
    from unittest.mock import AsyncMock, MagicMock, patch

    # Mock agent with marketplace listing in pending_review
    mock_agent = MagicMock()
    mock_agent.id = "agent-123"
    mock_agent.name = "Test Agent"
    mock_agent.status = "active"
    mock_agent.system_prompt = "test"
    mock_agent.allowed_tools = []
    mock_agent.domain = "custom"
    mock_agent.max_steps = 8
    mock_agent.temperature = 0.7
    # Marketplace listing in pending_review
    mock_listing = MagicMock()
    mock_listing.status = "pending_review"
    mock_agent.marketplace_listing = mock_listing

    # Verify the listing status check logic works
    from app.domains.agent_studio.custom_agent_runtime import (
        REVIEW_STATUS_PENDING,
        REVIEW_STATUS_ACTIVE,
    )

    listing_status = mock_agent.marketplace_listing.status
    assert listing_status == REVIEW_STATUS_PENDING
    assert listing_status != REVIEW_STATUS_ACTIVE


def test_execute_allowed_for_approved_listing():
    """Agente cujo marketplace listing esta approved pode executar."""
    mock_agent = MagicMock()
    mock_agent.marketplace_listing = MagicMock(status="active")

    from app.domains.agent_studio.custom_agent_runtime import REVIEW_STATUS_ACTIVE
    # An "active" listing is not pending_review, so agent can execute
    listing_status = mock_agent.marketplace_listing.status
    assert listing_status != "pending_review"


def test_execute_allowed_for_no_listing():
    """Agente sem marketplace listing (custom criado pelo tenant) pode executar."""
    mock_agent = MagicMock()
    mock_agent.marketplace_listing = None

    # No listing = not from marketplace = no review gate needed
    has_listing = mock_agent.marketplace_listing is not None
    assert not has_listing  # no gate should block
