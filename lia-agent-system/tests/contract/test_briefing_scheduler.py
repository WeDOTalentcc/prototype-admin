"""Contract sensor — briefing dispatch respects AlertConfig.briefing_frequency.

Wave 3 Camada 3 Item 2 — registered 2026-05-22
==============================================

Covers 6 invariants:

1. test_daily_task_filters_by_canonical_frequencies — dispatch_daily
   only loads AlertConfig rows with frequency in {daily, twice_daily}.
2. test_weekly_task_filters_by_canonical_frequency — dispatch_weekly
   only loads rows with frequency='weekly'.
3. test_monthly_task_filters_by_canonical_frequency — dispatch_monthly
   only loads rows with frequency='monthly'.
4. test_skip_when_briefing_frequency_invalid — REGRA 4: invalid/None
   frequency emits warning log and skipped_invalid_frequency counter
   (no silent eat).
5. test_skip_global_configs_without_company_id — TENANT-EXEMPT global
   configs (company_id NULL) are NOT loaded by the repository query.
6. test_dispatch_metric_emitted_per_event — every dispatch attempt
   emits one Prometheus counter increment with canonical labels.

Pure-unit: mocked AsyncSession, no real DB or Celery worker.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest


def _make_alert_config(
    *,
    company_id: str | None,
    user_id: str | None,
    briefing_frequency: str | None,
    is_active: bool = True,
) -> MagicMock:
    cfg = MagicMock()
    cfg.id = str(uuid.uuid4())
    cfg.company_id = company_id
    cfg.user_id = user_id
    cfg.briefing_frequency = briefing_frequency
    cfg.is_active = is_active
    return cfg


def _make_db_with_configs(configs: list[MagicMock]) -> MagicMock:
    db = MagicMock()
    db.add = MagicMock()
    db.flush = AsyncMock()

    async def fake_execute(stmt):
        # The repository call is `db.execute(select(...)).scalars().all()`
        result = MagicMock()
        scalars = MagicMock()
        scalars.all = MagicMock(return_value=configs)
        result.scalars = MagicMock(return_value=scalars)
        return result

    db.execute = AsyncMock(side_effect=fake_execute)
    return db


# ───────────────────────────────────────────────────────────────────────
# Test 1 — daily task loads only daily + twice_daily
# ───────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_daily_task_filters_by_canonical_frequencies(monkeypatch):
    """dispatch_daily should call _list_tenants_with_briefing_frequency with
    ['daily', 'twice_daily'] — not 'weekly', not 'monthly'.

    Sprint D+1 partial (2026-05-22): listing function renamed to
    _list_tenants_with_briefing_frequency (returns dicts with canonical
    frequency resolved from HiringPolicy preferred / AlertConfig fallback).
    """
    from app.jobs.tasks import briefing_dispatch as mod

    captured_frequencies: list[list[str]] = []

    async def fake_list(db, frequencies):
        captured_frequencies.append(list(frequencies))
        return []

    monkeypatch.setattr(mod, "_list_tenants_with_briefing_frequency", fake_list)

    # Replace AsyncSessionLocal with a no-op context manager
    class _FakeSession:
        async def __aenter__(self):
            return _make_db_with_configs([])

        async def __aexit__(self, *a):
            return None

    monkeypatch.setattr(
        "app.core.database.AsyncSessionLocal", lambda: _FakeSession()
    )

    await mod._dispatch_for_frequency_async(
        frequencies=["daily", "twice_daily"],
        task_name="briefing.dispatch_daily",
    )

    assert captured_frequencies == [["daily", "twice_daily"]], (
        f"daily task must filter by daily+twice_daily; got {captured_frequencies}"
    )


# ───────────────────────────────────────────────────────────────────────
# Test 2 — weekly task loads only weekly
# ───────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_weekly_task_filters_by_canonical_frequency(monkeypatch):
    from app.jobs.tasks import briefing_dispatch as mod

    captured: list[list[str]] = []

    async def fake_list(db, frequencies):
        captured.append(list(frequencies))
        return []

    monkeypatch.setattr(mod, "_list_tenants_with_briefing_frequency", fake_list)

    class _FakeSession:
        async def __aenter__(self):
            return _make_db_with_configs([])

        async def __aexit__(self, *a):
            return None

    monkeypatch.setattr(
        "app.core.database.AsyncSessionLocal", lambda: _FakeSession()
    )

    await mod._dispatch_for_frequency_async(
        frequencies=["weekly"],
        task_name="briefing.dispatch_weekly",
    )

    assert captured == [["weekly"]]


# ───────────────────────────────────────────────────────────────────────
# Test 3 — monthly task loads only monthly
# ───────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_monthly_task_filters_by_canonical_frequency(monkeypatch):
    from app.jobs.tasks import briefing_dispatch as mod

    captured: list[list[str]] = []

    async def fake_list(db, frequencies):
        captured.append(list(frequencies))
        return []

    monkeypatch.setattr(mod, "_list_tenants_with_briefing_frequency", fake_list)

    class _FakeSession:
        async def __aenter__(self):
            return _make_db_with_configs([])

        async def __aexit__(self, *a):
            return None

    monkeypatch.setattr(
        "app.core.database.AsyncSessionLocal", lambda: _FakeSession()
    )

    await mod._dispatch_for_frequency_async(
        frequencies=["monthly"],
        task_name="briefing.dispatch_monthly",
    )

    assert captured == [["monthly"]]


# ───────────────────────────────────────────────────────────────────────
# Test 4 — invalid frequency emits warning + metric (REGRA 4)
# ───────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_skip_when_briefing_frequency_invalid(monkeypatch, caplog):
    """REGRA 4 — frequency not in CANONICAL_FREQUENCIES warns + increments
    skipped_invalid_frequency, does NOT silently skip.

    Sprint D+1 partial: _list_tenants_with_briefing_frequency returns dicts
    {company_id, user_id, frequency, source}. Invalid frequency bypassed
    the resolver guard means the dict goes straight to the REGRA 4 sentinel.
    """
    from app.jobs.tasks import briefing_dispatch as mod

    bad_tenant = {
        "company_id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "frequency": "hourly",  # not canonical
        "source": "alert_config_legacy",
    }

    async def fake_list(db, frequencies):
        return [bad_tenant]

    monkeypatch.setattr(mod, "_list_tenants_with_briefing_frequency", fake_list)

    metric_calls: list[dict] = []

    def fake_metric(**kwargs):
        metric_calls.append(kwargs)

    monkeypatch.setattr(mod, "_emit_dispatch_metric", fake_metric)

    class _FakeSession:
        async def __aenter__(self):
            return _make_db_with_configs([])

        async def __aexit__(self, *a):
            return None

    monkeypatch.setattr(
        "app.core.database.AsyncSessionLocal", lambda: _FakeSession()
    )

    import logging
    with caplog.at_level(logging.WARNING):
        result = await mod._dispatch_for_frequency_async(
            frequencies=["daily", "twice_daily"],
            task_name="briefing.dispatch_daily",
        )

    assert result["skipped_invalid_frequency"] == 1
    assert result["sent"] == 0
    # Warning was emitted (no silent eat)
    assert any(
        "invalid briefing_frequency" in record.message
        for record in caplog.records
    ), "REGRA 4 — invalid frequency must emit warning"
    # Metric emitted with canonical labels
    assert any(
        m.get("result") == "skipped_invalid_frequency" for m in metric_calls
    )


# ───────────────────────────────────────────────────────────────────────
# Test 5 — global configs (company_id NULL) are filtered by query
# ───────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_skip_global_configs_without_company_id(monkeypatch):
    """_list_alert_configs_for_frequency query MUST exclude company_id IS NULL
    rows. We assert the WHERE clause includes ``AlertConfig.company_id.is_not(None)``."""
    from app.jobs.tasks import briefing_dispatch as mod

    captured_stmt = {}

    async def fake_execute(stmt):
        captured_stmt["stmt"] = stmt
        # Return empty
        result = MagicMock()
        scalars = MagicMock()
        scalars.all = MagicMock(return_value=[])
        result.scalars = MagicMock(return_value=scalars)
        return result

    db = MagicMock()
    db.execute = AsyncMock(side_effect=fake_execute)

    await mod._list_alert_configs_for_frequency(db, ["daily"])

    # Render compiled SQL — string contains "IS NOT NULL"
    sql = str(captured_stmt["stmt"].compile(compile_kwargs={"literal_binds": True}))
    assert "IS NOT NULL" in sql.upper() or "IS_NOT" in sql.upper(), (
        f"query must filter company_id IS NOT NULL; got:\n{sql}"
    )


# ───────────────────────────────────────────────────────────────────────
# Test 6 — metric emitted with canonical labels per event
# ───────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_dispatch_metric_emitted_per_event(monkeypatch):
    """Every iteration of the dispatch loop must emit exactly one metric.

    We do NOT assert on the underlying Prometheus client (best-effort);
    we assert ``_emit_dispatch_metric`` is called once per dispatched tenant.

    Sprint D+1 partial: _list_tenants_with_briefing_frequency returns
    dicts {company_id, user_id, frequency, source} with frequency already
    resolved (HiringPolicy preferred / AlertConfig fallback).
    """
    from app.jobs.tasks import briefing_dispatch as mod

    company_a = str(uuid.uuid4())
    user_a = str(uuid.uuid4())
    tenant = {
        "company_id": company_a,
        "user_id": user_a,
        "frequency": "daily",
        "source": "hiring_policy",
    }

    async def fake_list(db, frequencies):
        return [tenant]

    monkeypatch.setattr(mod, "_list_tenants_with_briefing_frequency", fake_list)

    metric_calls: list[dict] = []
    monkeypatch.setattr(
        mod,
        "_emit_dispatch_metric",
        lambda **kwargs: metric_calls.append(kwargs),
    )

    # Stub BriefingService to avoid touching real DB
    class _FakeBriefing:
        async def generate_daily_briefing(self, *, user_id, db, company_id):
            return {"urgent_actions": [], "date": "2026-05-22"}

    monkeypatch.setattr(
        "app.shared.services.briefing_service.BriefingService",
        lambda: _FakeBriefing(),
    )

    # Stub notification_service.send_notification
    class _FakeNotif:
        async def send_notification(self, **kw):
            return None

    monkeypatch.setattr(
        "app.services.notification_service.notification_service", _FakeNotif()
    )

    class _FakeSession:
        async def __aenter__(self):
            return _make_db_with_configs([])

        async def __aexit__(self, *a):
            return None

    monkeypatch.setattr(
        "app.core.database.AsyncSessionLocal", lambda: _FakeSession()
    )

    result = await mod._dispatch_for_frequency_async(
        frequencies=["daily", "twice_daily"],
        task_name="briefing.dispatch_daily",
    )

    assert result["sent"] == 1
    # Exactly one metric for the sent event
    sent_metrics = [m for m in metric_calls if m.get("result") == "sent"]
    assert len(sent_metrics) == 1, (
        f"expected 1 sent metric, got {sent_metrics}"
    )
    # Canonical labels present
    m = sent_metrics[0]
    assert m["frequency"] == "daily"
    # company_id_hash present, NOT the raw uuid (LGPD-safe)
    assert m.get("company_id_hash") is not None
    assert company_a not in str(m["company_id_hash"])
