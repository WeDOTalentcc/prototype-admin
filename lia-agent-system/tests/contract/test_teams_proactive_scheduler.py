"""Sensor A2a: AutomationScheduler aciona o TeamsProactivityEngine periodicamente.

Antes (censo 2026-06-09): TeamsProactivityEngine so era chamado por REST manual
(teams.py) — nenhum scheduler o acionava, entao os cards proativos do Teams
(pipelines parados, deadlines, digest) nunca eram postados autonomamente.
Decisao Paulo: ativar o engine completo. Estes wrappers dao o trigger.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


def _engine_mock(monkeypatch):
    import app.domains.communication.services.teams_proactivity_engine as tpe_mod

    engine = MagicMock()
    engine.check_stalled_pipelines = AsyncMock(return_value=2)
    engine.check_approaching_deadlines = AsyncMock(return_value=1)
    engine.send_daily_digest = AsyncMock(return_value=3)
    monkeypatch.setattr(tpe_mod, "teams_proactivity_engine", engine)
    return engine


@pytest.mark.asyncio
async def test_scheduler_runs_teams_proactive_checks(monkeypatch):
    from app.domains.automation.services.automation_scheduler import AutomationScheduler

    engine = _engine_mock(monkeypatch)
    sched = AutomationScheduler()

    await sched.run_teams_proactive_checks()

    assert engine.check_stalled_pipelines.called, "deve checar pipelines parados (Teams)"
    assert engine.check_approaching_deadlines.called, "deve checar deadlines (Teams)"


@pytest.mark.asyncio
async def test_scheduler_runs_teams_daily_digest(monkeypatch):
    from app.domains.automation.services.automation_scheduler import AutomationScheduler

    engine = _engine_mock(monkeypatch)
    sched = AutomationScheduler()

    await sched.run_teams_daily_digest()

    assert engine.send_daily_digest.called, "deve enviar o digest diario no Teams"
