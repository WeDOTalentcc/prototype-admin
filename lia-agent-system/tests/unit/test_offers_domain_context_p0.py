"""Regression test: DomainContext must be instantiable in offers.py handlers.

P0 fix 2026-06-10: DomainContext.__init__() requires domain_id and session_id
as positional fields. All 3 sites in offers.py were missing these args, causing
HTTP 500 when moving candidate to Proposta column in kanban.
"""
import pytest
from app.domains.base import DomainContext


def test_domain_context_offer_instantiation():
    """DomainContext com domain_id e session_id nao lanca TypeError."""
    ctx = DomainContext(
        domain_id="offer",
        session_id="user-123",
        user_id="user-123",
        tenant_id="company-456",
        metadata={},
    )
    assert ctx.domain_id == "offer"
    assert ctx.session_id == "user-123"
    assert ctx.user_id == "user-123"
    assert ctx.tenant_id == "company-456"


def test_domain_context_offer_missing_domain_id_raises():
    """DomainContext sem domain_id deve lancar TypeError (regressao)."""
    with pytest.raises(TypeError):
        DomainContext(
            user_id="user-123",
            tenant_id="company-456",
            metadata={},
        )


def test_domain_context_offer_missing_session_id_raises():
    """DomainContext sem session_id deve lancar TypeError (regressao)."""
    with pytest.raises(TypeError):
        DomainContext(
            domain_id="offer",
            user_id="user-123",
            tenant_id="company-456",
            metadata={},
        )
