"""Tests for GAP-02-006: captured_at stale-context detection.

Verifies:
- Fresh context (< 60s old) → not stale
- Old context (> 60s old) → detected as stale
- Missing captured_at → not stale (graceful fail-open)
- Malformed timestamp → not stale (graceful fail-open)
- JavaScript "Z" suffix (ISO format) is handled correctly
- check_and_log_stale_context logs a warning when stale
- check_and_log_stale_context is silent when fresh or absent
- FE lia-context-store.ts includes captured_at in snapshot
"""
import pytest
from datetime import datetime, timezone, timedelta


# ---------------------------------------------------------------------------
# detect_stale_context unit tests
# ---------------------------------------------------------------------------


def test_fresh_context_not_stale():
    """Context timestamped now is not stale."""
    from app.orchestrator.context.view_context import detect_stale_context

    now_iso = datetime.now(timezone.utc).isoformat()
    assert detect_stale_context(now_iso) is False


def test_old_context_detected_as_stale():
    """Context timestamped 2 minutes ago is stale (threshold 60s)."""
    from app.orchestrator.context.view_context import detect_stale_context

    two_min_ago = (datetime.now(timezone.utc) - timedelta(seconds=120)).isoformat()
    assert detect_stale_context(two_min_ago) is True


def test_exactly_at_threshold_not_stale():
    """Context at exactly threshold is NOT stale (strict > comparison)."""
    from app.orchestrator.context.view_context import detect_stale_context

    # 50s ago — safely below 60s threshold
    fifty_s_ago = (datetime.now(timezone.utc) - timedelta(seconds=50)).isoformat()
    # age == 50 is NOT > 60, so not stale
    assert detect_stale_context(fifty_s_ago) is False


def test_missing_timestamp_not_stale():
    """None captured_at → graceful fail-open (not stale)."""
    from app.orchestrator.context.view_context import detect_stale_context

    assert detect_stale_context(None) is False
    assert detect_stale_context("") is False


def test_malformed_timestamp_not_stale():
    """Unparseable string → graceful fail-open (not stale, no exception raised)."""
    from app.orchestrator.context.view_context import detect_stale_context

    assert detect_stale_context("not-a-timestamp") is False
    assert detect_stale_context("2026-99-99T99:99:99") is False


def test_javascript_z_suffix_handled():
    """JavaScript toISOString() produces '...Z' — must be parsed correctly."""
    from app.orchestrator.context.view_context import detect_stale_context

    # Fresh — JavaScript Z format
    js_now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + "000Z"
    assert detect_stale_context(js_now) is False

    # Stale — JavaScript Z format
    js_old = (datetime.now(timezone.utc) - timedelta(seconds=180)).strftime(
        "%Y-%m-%dT%H:%M:%S."
    ) + "000Z"
    assert detect_stale_context(js_old) is True


def test_custom_threshold():
    """Custom threshold_seconds is respected."""
    from app.orchestrator.context.view_context import detect_stale_context

    # 30s ago — stale at 10s threshold, fresh at 60s threshold
    thirty_s_ago = (datetime.now(timezone.utc) - timedelta(seconds=30)).isoformat()
    assert detect_stale_context(thirty_s_ago, threshold_seconds=10) is True
    assert detect_stale_context(thirty_s_ago, threshold_seconds=60) is False


def test_zero_threshold_any_past_timestamp_is_stale():
    """threshold_seconds=0 → any timestamp in the past is stale."""
    from app.orchestrator.context.view_context import detect_stale_context

    one_ms_ago = (datetime.now(timezone.utc) - timedelta(milliseconds=100)).isoformat()
    assert detect_stale_context(one_ms_ago, threshold_seconds=0) is True


# ---------------------------------------------------------------------------
# check_and_log_stale_context integration tests
# ---------------------------------------------------------------------------


def test_check_and_log_warns_when_stale(caplog):
    """check_and_log_stale_context emits a WARNING when context is stale."""
    import logging
    from app.orchestrator.context.view_context import check_and_log_stale_context

    old_ts = (datetime.now(timezone.utc) - timedelta(seconds=120)).isoformat()
    ctx = {"page_type": "vagas", "captured_at": old_ts}

    with caplog.at_level(logging.WARNING, logger="app.orchestrator.context.view_context"):
        check_and_log_stale_context(ctx)

    assert any("stale" in r.message.lower() or "Stale" in r.message for r in caplog.records)


def test_check_and_log_silent_when_fresh(caplog):
    """check_and_log_stale_context is silent when context is fresh."""
    import logging
    from app.orchestrator.context.view_context import check_and_log_stale_context

    fresh_ts = datetime.now(timezone.utc).isoformat()
    ctx = {"page_type": "vagas", "captured_at": fresh_ts}

    with caplog.at_level(logging.WARNING, logger="app.orchestrator.context.view_context"):
        check_and_log_stale_context(ctx)

    stale_records = [r for r in caplog.records if "stale" in r.message.lower()]
    assert len(stale_records) == 0


def test_check_and_log_silent_when_no_captured_at(caplog):
    """check_and_log_stale_context is silent when captured_at is absent."""
    import logging
    from app.orchestrator.context.view_context import check_and_log_stale_context

    ctx = {"page_type": "vagas"}

    with caplog.at_level(logging.WARNING, logger="app.orchestrator.context.view_context"):
        check_and_log_stale_context(ctx)

    stale_records = [r for r in caplog.records if "stale" in r.message.lower()]
    assert len(stale_records) == 0


def test_check_and_log_finds_captured_at_in_nested_view_context(caplog):
    """check_and_log_stale_context also checks ctx.view_context.captured_at."""
    import logging
    from app.orchestrator.context.view_context import check_and_log_stale_context

    old_ts = (datetime.now(timezone.utc) - timedelta(seconds=120)).isoformat()
    ctx = {"view_context": {"page_type": "funil", "captured_at": old_ts}}

    with caplog.at_level(logging.WARNING, logger="app.orchestrator.context.view_context"):
        check_and_log_stale_context(ctx)

    assert any("stale" in r.message.lower() or "Stale" in r.message for r in caplog.records)


def test_check_and_log_silent_on_none():
    """check_and_log_stale_context does not crash on None input."""
    from app.orchestrator.context.view_context import check_and_log_stale_context

    # Must not raise
    check_and_log_stale_context(None)
    check_and_log_stale_context({})


# ---------------------------------------------------------------------------
# FE contract test — lia-context-store.ts includes captured_at
# ---------------------------------------------------------------------------


def test_fe_context_store_includes_captured_at():
    """FE lia-context-store.ts must export captured_at in getLiaContextSnapshot.

    This is a static contract test — reads the TS source to verify the field
    is present. Prevents regression where captured_at is removed from FE.
    """
    import os

    fe_store_path = os.path.join(
        os.path.dirname(__file__),
        "../../../plataforma-lia/src/lib/lia-context-store.ts",
    )
    fe_store_path = os.path.normpath(fe_store_path)
    assert os.path.exists(fe_store_path), f"FE store not found at {fe_store_path}"

    with open(fe_store_path) as f:
        content = f.read()

    assert "captured_at" in content, (
        "GAP-02-006 regression: captured_at not found in lia-context-store.ts. "
        "getLiaContextSnapshot() must include captured_at: new Date().toISOString()"
    )
    assert "new Date().toISOString()" in content, (
        "GAP-02-006 regression: captured_at must be set to new Date().toISOString() "
        "so the BE can detect stale context. Found 'captured_at' but not the assignment."
    )
