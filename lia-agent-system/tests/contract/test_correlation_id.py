"""Testes contract para o sistema de correlation_id cross-domain.

Sprint A (2026-06-13) — rastreabilidade cross-domain.
"""
import pytest


def test_request_id_middleware_exposes_contextvar():
    """RequestIdMiddleware exporta get_correlation_id() e ContextVar."""
    from app.middleware.request_id import get_correlation_id, _current_correlation_id
    assert callable(get_correlation_id)
    # Fora de request, retorna string vazia (default seguro)
    result = get_correlation_id()
    assert isinstance(result, str)


def test_set_correlation_id_from_request():
    """Helper canonical popula o ContextVar."""
    from app.middleware.request_id import _set_correlation_id_from_request, get_correlation_id
    _set_correlation_id_from_request("test-corr-123")
    assert get_correlation_id() == "test-corr-123"
    # Limpar
    _set_correlation_id_from_request("")


def test_platform_event_has_correlation_id_field():
    """PlatformEvent tem campo correlation_id opcional."""
    from app.shared.messaging.platform_events import PlatformEvent
    fields = PlatformEvent.model_fields
    assert "correlation_id" in fields
    # Campo e opcional (None por default)
    evt = PlatformEvent(
        event_type="test.event",
        company_id="company-123",
        payload={},
        source_api="lia-agent-system"
    )
    assert evt.correlation_id is None


def test_platform_event_accepts_correlation_id():
    """PlatformEvent aceita correlation_id explicito."""
    from app.shared.messaging.platform_events import PlatformEvent
    evt = PlatformEvent(
        event_type="test.event",
        company_id="company-123",
        payload={},
        source_api="lia-agent-system",
        correlation_id="req-abc-456"
    )
    assert evt.correlation_id == "req-abc-456"


def test_audit_log_model_has_correlation_id_column():
    """AuditLog model tem coluna correlation_id."""
    from lia_models.audit_log import AuditLog
    cols = {c.key for c in AuditLog.__table__.columns}
    assert "correlation_id" in cols, (
        "AuditLog deve ter coluna correlation_id para rastreabilidade cross-domain"
    )


def test_agent_execution_log_has_correlation_id():
    """AgentExecutionLog model tem coluna correlation_id."""
    from lia_models.agent_execution_log import AgentExecutionLog
    cols = {c.key for c in AgentExecutionLog.__table__.columns}
    assert "correlation_id" in cols


def test_pool_agent_run_has_correlation_id():
    """PoolAgentRun model tem coluna correlation_id."""
    from lia_models.pool_agent_run import PoolAgentRun
    cols = {c.key for c in PoolAgentRun.__table__.columns}
    assert "correlation_id" in cols


def test_correlation_id_propagates_via_contextvar():
    """correlation_id setado via _set_correlation_id_from_request e lido por get_correlation_id."""
    import asyncio
    from app.middleware.request_id import _set_correlation_id_from_request, get_correlation_id

    async def inner():
        _set_correlation_id_from_request("propagated-id-789")
        # Simula chamada a servico downstream na mesma coroutine context
        return get_correlation_id()

    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(inner())
    finally:
        loop.close()
    assert result == "propagated-id-789"
    # Limpar
    _set_correlation_id_from_request("")
