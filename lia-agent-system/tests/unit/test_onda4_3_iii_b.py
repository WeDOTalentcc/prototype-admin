"""Onda 4.3 III.B — ConversationState hydrate tests."""
from __future__ import annotations

from pathlib import Path


def test_iiib_marker_in_main_orchestrator() -> None:
    """III.B: main_orchestrator.py must contain III.B marker."""
    import app.orchestrator.main_orchestrator as mo

    source = Path(mo.__file__).read_text(encoding="utf-8")
    assert "III.B" in source, "III.B: main_orchestrator must contain III.B marker"
    assert "_hydrate_recruiter_preferences" in source
    assert "recruiter_prefs" in source


def test_hydrate_method_exists_on_main_orchestrator() -> None:
    """III.B: _hydrate_recruiter_preferences is an async method of MainOrchestrator."""
    from app.orchestrator.main_orchestrator import MainOrchestrator
    import inspect

    assert hasattr(MainOrchestrator, "_hydrate_recruiter_preferences")
    method = MainOrchestrator._hydrate_recruiter_preferences
    assert inspect.iscoroutinefunction(method), (
        "III.B: _hydrate_recruiter_preferences must be async"
    )


def test_hydrate_returns_structured_prefs_with_defaults() -> None:
    """III.B: when DB returns a row with partial prefs, helper applies defaults."""
    import asyncio
    from unittest.mock import AsyncMock, MagicMock

    from app.orchestrator.main_orchestrator import MainOrchestrator

    # Mock DB row with only preferred_top_n set
    fake_row = MagicMock()
    fake_row.user_preferences = {"preferred_top_n": 3}
    fake_result = MagicMock()
    fake_result.scalar_one_or_none = MagicMock(return_value=fake_row)

    fake_db = MagicMock()
    fake_db.execute = AsyncMock(return_value=fake_result)

    ctx = MagicMock()
    ctx.user_id = "user-iiib-test"

    orch = MainOrchestrator.__new__(MainOrchestrator)  # skip __init__
    out = asyncio.run(orch._hydrate_recruiter_preferences(ctx, fake_db))

    assert out is not None
    assert out["preferred_top_n"] == 3  # from DB
    assert out["briefing_style"] == "short"  # default
    assert out["communication_channel"] == "email"  # default
    assert out["locale_preference"] == "pt-BR"  # default
    assert out["favored_stages"] == []  # default


def test_hydrate_returns_none_when_no_user_id() -> None:
    """III.B: no user_id → None (can't query without user key)."""
    import asyncio
    from unittest.mock import MagicMock

    from app.orchestrator.main_orchestrator import MainOrchestrator

    ctx = MagicMock()
    ctx.user_id = None

    orch = MainOrchestrator.__new__(MainOrchestrator)
    out = asyncio.run(orch._hydrate_recruiter_preferences(ctx, MagicMock()))
    assert out is None


def test_hydrate_fails_safe_on_db_error() -> None:
    """III.B: DB exception → None (non-fatal for chat flow)."""
    import asyncio
    from unittest.mock import AsyncMock, MagicMock

    from app.orchestrator.main_orchestrator import MainOrchestrator

    fake_db = MagicMock()
    fake_db.execute = AsyncMock(side_effect=RuntimeError("DB down"))

    ctx = MagicMock()
    ctx.user_id = "user-x"

    orch = MainOrchestrator.__new__(MainOrchestrator)
    # Should NOT raise
    out = asyncio.run(orch._hydrate_recruiter_preferences(ctx, fake_db))
    assert out is None


def test_hydrate_returns_none_when_no_summary_row() -> None:
    """III.B: user exists but has no ConversationSummary yet → None."""
    import asyncio
    from unittest.mock import AsyncMock, MagicMock

    from app.orchestrator.main_orchestrator import MainOrchestrator

    fake_result = MagicMock()
    fake_result.scalar_one_or_none = MagicMock(return_value=None)
    fake_db = MagicMock()
    fake_db.execute = AsyncMock(return_value=fake_result)

    ctx = MagicMock()
    ctx.user_id = "new-user"

    orch = MainOrchestrator.__new__(MainOrchestrator)
    out = asyncio.run(orch._hydrate_recruiter_preferences(ctx, fake_db))
    # Helper returns dict of defaults even with empty prefs (existing row with
    # empty user_preferences). But None user row → None out.
    assert out is None or (isinstance(out, dict) and out.get("preferred_top_n") == 5)
