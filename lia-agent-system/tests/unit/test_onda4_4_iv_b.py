"""Onda 4.4 IV.B — Briefing greeting wire tests."""
from __future__ import annotations

from pathlib import Path


def test_ivb_marker_in_main_orchestrator() -> None:
    """IV.B: main_orchestrator must contain IV.B marker."""
    import app.orchestrator.main_orchestrator as mo

    source = Path(mo.__file__).read_text(encoding="utf-8")
    assert "IV.B" in source
    assert "_maybe_build_briefing_context" in source
    assert "briefing_context" in source


def test_briefing_method_on_class() -> None:
    """IV.B: _maybe_build_briefing_context is an async method."""
    import inspect

    from app.orchestrator.main_orchestrator import MainOrchestrator

    assert hasattr(MainOrchestrator, "_maybe_build_briefing_context")
    assert inspect.iscoroutinefunction(MainOrchestrator._maybe_build_briefing_context)


def test_briefing_returns_summary_on_greeting() -> None:
    """IV.B: 'oi' → summary from briefing service."""
    import asyncio
    from unittest.mock import AsyncMock, MagicMock, patch

    from app.orchestrator.main_orchestrator import MainOrchestrator

    ctx = MagicMock()
    ctx.message = "oi"
    ctx.user_id = "user-iv-test"
    ctx.company_id = "co-iv-test"

    orch = MainOrchestrator.__new__(MainOrchestrator)

    with patch(
        "app.domains.recruiter_assistant.services.lia_briefing_formatter.get_cached_briefing",
        new=AsyncMock(return_value={"urgent_actions": [{"id": 1}, {"id": 2}]}),
    ):
        with patch(
            "app.domains.recruiter_assistant.services.lia_briefing_formatter.format_briefing_for_greeting",
            return_value="Temos 2 ações urgentes.",
        ):
            out = asyncio.run(orch._maybe_build_briefing_context(ctx, MagicMock()))

    assert out == "Temos 2 ações urgentes."


def test_briefing_returns_none_on_non_greeting() -> None:
    """IV.B: 'buscar candidatos python' → None (não é greeting)."""
    import asyncio
    from unittest.mock import MagicMock

    from app.orchestrator.main_orchestrator import MainOrchestrator

    ctx = MagicMock()
    ctx.message = "buscar candidatos python senior em SP"
    ctx.user_id = "u"
    ctx.company_id = "c"

    orch = MainOrchestrator.__new__(MainOrchestrator)
    out = asyncio.run(orch._maybe_build_briefing_context(ctx, MagicMock()))
    assert out is None


def test_briefing_recognizes_common_patterns() -> None:
    """IV.B: múltiplas greeting patterns → todas detectadas."""
    import asyncio
    from unittest.mock import AsyncMock, MagicMock, patch

    from app.orchestrator.main_orchestrator import MainOrchestrator

    orch = MainOrchestrator.__new__(MainOrchestrator)

    with patch(
        "app.domains.recruiter_assistant.services.lia_briefing_formatter.get_cached_briefing",
        new=AsyncMock(return_value={"urgent_actions": [{}]}),
    ):
        with patch(
            "app.domains.recruiter_assistant.services.lia_briefing_formatter.format_briefing_for_greeting",
            return_value="Temos 1 ação urgente.",
        ):
            for greeting in ("oi", "olá", "bom dia", "boa tarde", "boa noite", "oi lia"):
                ctx = MagicMock()
                ctx.message = greeting
                ctx.user_id = "u"
                ctx.company_id = "c"
                result = asyncio.run(orch._maybe_build_briefing_context(ctx, MagicMock()))
                assert result == "Temos 1 ação urgente.", (
                    f"IV.B: greeting {greeting!r} should produce summary"
                )


def test_briefing_fails_safe_on_service_error() -> None:
    """IV.B: briefing service exception → None (non-fatal)."""
    import asyncio
    from unittest.mock import AsyncMock, MagicMock, patch

    from app.orchestrator.main_orchestrator import MainOrchestrator

    ctx = MagicMock()
    ctx.message = "oi"
    ctx.user_id = "u"
    ctx.company_id = "c"

    orch = MainOrchestrator.__new__(MainOrchestrator)

    with patch(
        "app.domains.recruiter_assistant.services.lia_briefing_formatter.get_cached_briefing",
        new=AsyncMock(side_effect=RuntimeError("service down")),
    ):
        out = asyncio.run(orch._maybe_build_briefing_context(ctx, MagicMock()))

    assert out is None


def test_briefing_empty_summary_returns_none() -> None:
    """IV.B: empty string from formatter → None (don't inject empty)."""
    import asyncio
    from unittest.mock import AsyncMock, MagicMock, patch

    from app.orchestrator.main_orchestrator import MainOrchestrator

    ctx = MagicMock()
    ctx.message = "oi"
    ctx.user_id = "u"
    ctx.company_id = "c"

    orch = MainOrchestrator.__new__(MainOrchestrator)

    with patch(
        "app.domains.recruiter_assistant.services.lia_briefing_formatter.get_cached_briefing",
        new=AsyncMock(return_value={}),
    ):
        with patch(
            "app.domains.recruiter_assistant.services.lia_briefing_formatter.format_briefing_for_greeting",
            return_value="",
        ):
            out = asyncio.run(orch._maybe_build_briefing_context(ctx, MagicMock()))

    assert out is None
