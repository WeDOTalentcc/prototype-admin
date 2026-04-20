"""Tests for the recruiter assistant GoalService.

Covers the real (non-stub) shape produced by ``GoalService.get_user_goals``:
period normalization, ``company_id`` scoping passed to the repo, and the
on-track / at-risk / achieved aggregation.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from app.services.goal_service import (
    GoalService,
    _classify,
    aggregate_goals,
)


def _make_goal(
    *,
    name: str = "Goal",
    progress: float = 0.0,
    status: str = "in_progress",
    target: float = 10,
    current: float = 0,
    period: str = "monthly",
    category: str = "recruitment",
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    unit: str | None = "hires",
    description: str | None = None,
):
    return SimpleNamespace(
        id=uuid.uuid4(),
        name=name,
        description=description,
        category=category,
        period=period,
        status=status,
        target=target,
        current=current,
        unit=unit,
        progress=progress,
        start_date=start_date,
        end_date=end_date,
    )


def test_classify_buckets():
    now = datetime(2026, 4, 20)

    achieved = _make_goal(progress=100, status="achieved")
    overdue = _make_goal(progress=20, status="overdue")
    on_track = _make_goal(
        progress=60,
        start_date=now - timedelta(days=10),
        end_date=now + timedelta(days=10),
    )
    behind = _make_goal(
        progress=10,
        start_date=now - timedelta(days=18),
        end_date=now + timedelta(days=2),
    )

    assert _classify(achieved, now=now) == "achieved"
    assert _classify(overdue, now=now) == "at_risk"
    assert _classify(on_track, now=now) == "on_track"
    assert _classify(behind, now=now) == "at_risk"


def test_aggregate_goals_counts_buckets():
    now = datetime(2026, 4, 20)
    goals = [
        _make_goal(name="A", progress=100, status="achieved"),
        _make_goal(name="B", progress=20, status="overdue"),
        _make_goal(
            name="C",
            progress=70,
            start_date=now - timedelta(days=10),
            end_date=now + timedelta(days=10),
        ),
    ]
    items, summary = aggregate_goals(goals, now=now)

    assert summary == {"total": 3, "on_track": 1, "at_risk": 1, "achieved": 1}
    assert {item["name"] for item in items} == {"A", "B", "C"}
    by_name = {item["name"]: item for item in items}
    assert by_name["A"]["bucket"] == "achieved"
    assert by_name["B"]["bucket"] == "at_risk"
    assert by_name["C"]["bucket"] == "on_track"
    # serialized payload exposes real values, not a stub
    assert by_name["A"]["target"] == 10
    assert by_name["A"]["unit"] == "hires"


@pytest.mark.asyncio
async def test_get_user_goals_uses_repo_and_returns_real_shape(monkeypatch):
    company_id = uuid.uuid4()
    captured: dict = {}

    async def fake_fetch(self, *, user_id, company_id, period):
        captured["user_id"] = user_id
        captured["company_id"] = company_id
        captured["period"] = period
        return [
            _make_goal(name="Hires", progress=100, status="achieved"),
            _make_goal(name="TTF", progress=40, status="overdue"),
            _make_goal(name="NPS", progress=50, status="in_progress"),
        ]

    monkeypatch.setattr(GoalService, "_fetch_goals", fake_fetch)

    service = GoalService()
    result = await service.get_user_goals(
        user_id="recruiter-1",
        company_id=str(company_id),
        period="current_month",
    )

    # Period was normalized to the column value before hitting the repo.
    assert captured["period"] == "monthly"
    # company_id was coerced to UUID for the scoped query.
    assert captured["company_id"] == company_id
    assert captured["user_id"] == "recruiter-1"

    # Real shape — not the simulation stub.
    assert result["success"] is True
    assert "simulation_stub" not in result
    assert result["normalized_period"] == "monthly"
    assert result["summary"] == {
        "total": 3,
        "on_track": 1,
        "at_risk": 1,
        "achieved": 1,
    }
    assert len(result["goals"]) == 3
    assert {g["bucket"] for g in result["goals"]} == {
        "achieved",
        "at_risk",
        "on_track",
    }


@pytest.mark.asyncio
async def test_get_user_goals_empty_results_for_scoped_query(monkeypatch):
    captured: dict = {}

    async def fake_fetch(self, *, user_id, company_id, period):
        captured["called"] = True
        captured["user_id"] = user_id
        captured["company_id"] = company_id
        captured["period"] = period
        return []

    monkeypatch.setattr(GoalService, "_fetch_goals", fake_fetch)

    company_id = uuid.uuid4()
    result = await GoalService().get_user_goals(
        user_id="r1", company_id=str(company_id), period="current_quarter"
    )

    assert captured["called"] is True
    assert captured["company_id"] == company_id
    assert captured["user_id"] == "r1"
    assert captured["period"] == "quarterly"
    assert result["success"] is True
    assert result["normalized_period"] == "quarterly"
    assert result["goals"] == []
    assert result["summary"] == {
        "total": 0,
        "on_track": 0,
        "at_risk": 0,
        "achieved": 0,
    }
    assert "simulation_stub" not in result


@pytest.mark.asyncio
async def test_get_user_goals_rejects_missing_company_id(monkeypatch):
    """Fail-closed: no company_id means we must NOT touch the repository."""
    called = {"hit": False}

    async def fake_fetch(self, *, user_id, company_id, period):
        called["hit"] = True
        return []

    monkeypatch.setattr(GoalService, "_fetch_goals", fake_fetch)

    result = await GoalService().get_user_goals(
        user_id="r1", company_id=None, period="current_month"
    )

    assert called["hit"] is False
    assert result["success"] is False
    assert result["error"] == "missing_company_id"
    assert result["goals"] == []


@pytest.mark.asyncio
async def test_get_user_goals_rejects_invalid_company_id(monkeypatch):
    called = {"hit": False}

    async def fake_fetch(self, *, user_id, company_id, period):
        called["hit"] = True
        return []

    monkeypatch.setattr(GoalService, "_fetch_goals", fake_fetch)

    result = await GoalService().get_user_goals(
        user_id="r1", company_id="not-a-uuid", period="monthly"
    )

    assert called["hit"] is False
    assert result["success"] is False
    assert result["error"] == "invalid_company_id"


@pytest.mark.asyncio
async def test_get_user_goals_rejects_missing_user_id(monkeypatch):
    called = {"hit": False}

    async def fake_fetch(self, *, user_id, company_id, period):
        called["hit"] = True
        return []

    monkeypatch.setattr(GoalService, "_fetch_goals", fake_fetch)

    result = await GoalService().get_user_goals(
        user_id="", company_id=str(uuid.uuid4()), period="monthly"
    )

    assert called["hit"] is False
    assert result["success"] is False
    assert result["error"] == "missing_user_id"


@pytest.mark.asyncio
async def test_get_user_goals_rejects_unknown_period(monkeypatch):
    called = {"hit": False}

    async def fake_fetch(self, *, user_id, company_id, period):
        called["hit"] = True
        return []

    monkeypatch.setattr(GoalService, "_fetch_goals", fake_fetch)

    result = await GoalService().get_user_goals(
        user_id="r1", company_id=str(uuid.uuid4()), period="weekly"
    )

    assert called["hit"] is False
    assert result["success"] is False
    assert result["error"] == "invalid_period"


@pytest.mark.asyncio
async def test_get_user_goals_repo_failure_returns_error(monkeypatch):
    async def fake_fetch(self, *, user_id, company_id, period):
        raise RuntimeError("db down")

    monkeypatch.setattr(GoalService, "_fetch_goals", fake_fetch)

    result = await GoalService().get_user_goals(
        user_id="r1", company_id=str(uuid.uuid4()), period="monthly"
    )

    assert result["success"] is False
    assert result["error"] == "goal_fetch_failed"
    assert result["summary"]["total"] == 0
