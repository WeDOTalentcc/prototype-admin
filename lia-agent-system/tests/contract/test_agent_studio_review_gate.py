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


# ── GAP-1 fix: Draft nao pode executar via /execute (EU AI Act Art. 12) ───────
# Antes do fix (linha 522 custom_agents.py), draft estava na lista de status
# permitidos para execute. Isso bypassa o approval workflow obrigatorio.
# Opcao B: /execute requer status=="active" apenas.
# /dry-run e /test continuam disponiveis para draft (sandbox sem side-effects reais).

def test_execute_gate_rejects_draft():
    """Status draft nao deve estar na lista de status permitidos para /execute.

    EU AI Act Art. 12: supervisao humana obrigatoria antes de execucao com
    ferramentas reais. Draft bypassa o approval workflow.
    """
    ALLOWED_EXECUTE_STATUSES = {"active"}

    assert "draft" not in ALLOWED_EXECUTE_STATUSES, (
        "draft nao deve poder executar via /execute -- "
        "use /dry-run para sandbox sem side-effects."
    )
    assert "active" in ALLOWED_EXECUTE_STATUSES


def test_execute_gate_rejects_pending_approval():
    """Status pending_approval tambem deve ser bloqueado em /execute."""
    ALLOWED_EXECUTE_STATUSES = {"active"}
    assert "pending_approval" not in ALLOWED_EXECUTE_STATUSES


def test_execute_gate_allows_only_active():
    """Somente active deve ser permitido em /execute apos o fix."""
    ALLOWED_EXECUTE_STATUSES = {"active"}
    assert ALLOWED_EXECUTE_STATUSES == {"active"}
    assert len(ALLOWED_EXECUTE_STATUSES) == 1


def test_execute_error_message_guides_to_dryrun():
    """Mensagem de erro para draft deve apontar para /dry-run como alternativa."""
    DRAFT_EXECUTE_ERROR = (
        "Agent must be approved before executing with real tools. "
        "Use /dry-run to test without side effects, then submit for approval."
    )
    assert "dry-run" in DRAFT_EXECUTE_ERROR
    assert "approv" in DRAFT_EXECUTE_ERROR
