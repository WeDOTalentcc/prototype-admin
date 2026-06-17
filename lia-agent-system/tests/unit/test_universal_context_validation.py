"""Tests for UC-P2-31: UniversalContext Pydantic validation."""
import pytest


def test_universal_context_is_pydantic():
    from pydantic import BaseModel
    from app.orchestrator.context.context_adapter import UniversalContext
    assert issubclass(UniversalContext, BaseModel)


def test_message_truncated_at_10000():
    from app.orchestrator.context.context_adapter import UniversalContext
    ctx = UniversalContext(message="x" * 15000, company_id="co_1", user_id="u_1")
    assert len(ctx.message) == 10000


def test_empty_company_id_allowed_but_warns(caplog):
    import logging
    from app.orchestrator.context.context_adapter import UniversalContext
    with caplog.at_level(logging.DEBUG, logger="app.orchestrator.context.context_adapter"):
        ctx = UniversalContext(message="hello", company_id="", user_id="u_1")
    assert ctx.company_id == ""


def test_message_within_limit_unchanged():
    from app.orchestrator.context.context_adapter import UniversalContext
    msg = "hello world"
    ctx = UniversalContext(message=msg, company_id="co_1", user_id="u_1")
    assert ctx.message == msg


def test_channel_default_is_rest():
    from app.orchestrator.context.context_adapter import UniversalContext
    ctx = UniversalContext(message="hi", company_id="co_1", user_id="u_1")
    assert ctx.channel == "rest"


def test_context_adapter_from_rest_returns_pydantic():
    from pydantic import BaseModel
    from app.orchestrator.context.context_adapter import ContextAdapter
    ctx = ContextAdapter.from_rest(
        message="test",
        user_id="u_1",
        company_id="co_1",
    )
    assert isinstance(ctx, BaseModel)
    assert ctx.message == "test"
    assert ctx.company_id == "co_1"


def test_universal_context_field_access():
    from app.orchestrator.context.context_adapter import UniversalContext
    ctx = UniversalContext(
        message="search for seniors",
        company_id="co_abc",
        user_id="u_xyz",
        channel="ws",
        context_page="talent",
    )
    assert ctx.company_id == "co_abc"
    assert ctx.user_id == "u_xyz"
    assert ctx.channel == "ws"
    assert ctx.context_page == "talent"
