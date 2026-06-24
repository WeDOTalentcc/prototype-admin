"""
test_briefing_calendar_events_guard.py — harness fix 2026-06-06.

Contexto: `calendar_events` e uma tabela RAILS-OWNED que pode nao existir no DB
que o FastAPI usa (ex: dev sem as migrations Rails de calendar). A query crua em
`_get_today_schedule` disparava `asyncpg.UndefinedTableError`; capturada por
try/except SEM rollback, deixava a transacao compartilhada ABORTADA, cascateando
em `InFailedSQLTransactionError` nas queries seguintes (`_get_active_alerts`,
`_get_recruiter_metrics`) — degradando briefing + proactive insights.

Fix no produtor: pre-checar a existencia da tabela com `to_regclass` antes de
consultar. Tabela ausente -> a query crua NUNCA roda -> transacao nunca e
envenenada. Defesa em profundidade: o try/except permanece.

Sensor: garante que o SELECT em calendar_events nunca executa quando a tabela
nao existe (to_regclass = NULL).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest


def _make_db(table_exists: bool):
    """AsyncSession mock que registra todo SQL executado.

    `to_regclass(...)` -> retorna um oid fake se table_exists, senao None.
    Demais queries -> resultado vazio (scalars/fetchall).
    """
    executed_sql: list[str] = []

    async def fake_execute(stmt, params=None):
        sql_str = str(stmt)
        executed_sql.append(sql_str)
        m = MagicMock()
        if "to_regclass" in sql_str:
            m.scalar = MagicMock(return_value=("oid-fake" if table_exists else None))
        else:
            m.scalar = MagicMock(return_value=None)
        m.scalars = MagicMock(return_value=iter([]))
        m.fetchall = MagicMock(return_value=[])
        return m

    db = MagicMock()
    db.execute = AsyncMock(side_effect=fake_execute)
    return db, executed_sql


@pytest.mark.asyncio
async def test_calendar_query_skipped_when_table_absent():
    from app.shared.services.briefing_service import BriefingService

    svc = BriefingService()
    db, executed_sql = _make_db(table_exists=False)
    now = datetime.now(timezone.utc)

    await svc._get_today_schedule(
        db, user_id="11111111-1111-4111-8111-111111111111",
        today_start=now - timedelta(hours=1), today_end=now + timedelta(hours=23),
    )

    # to_regclass DEVE ser chamado (guard presente)...
    assert any("to_regclass" in s for s in executed_sql), (
        "guard ausente: _get_today_schedule deve pre-checar calendar_events com to_regclass"
    )
    # ...e o SELECT cru em calendar_events NUNCA roda quando a tabela nao existe
    # (e isso que evitava a UndefinedTableError que envenenava a transacao).
    assert not any("FROM calendar_events" in s for s in executed_sql), (
        "SELECT em calendar_events executou mesmo com a tabela ausente — "
        "vai disparar UndefinedTableError e abortar a transacao compartilhada"
    )


@pytest.mark.asyncio
async def test_calendar_query_runs_when_table_exists():
    from app.shared.services.briefing_service import BriefingService

    svc = BriefingService()
    db, executed_sql = _make_db(table_exists=True)
    now = datetime.now(timezone.utc)

    await svc._get_today_schedule(
        db, user_id="11111111-1111-4111-8111-111111111111",
        today_start=now - timedelta(hours=1), today_end=now + timedelta(hours=23),
    )

    # Tabela presente -> a query de compromissos roda normalmente.
    assert any("FROM calendar_events" in s for s in executed_sql), (
        "com a tabela presente, o briefing deve consultar calendar_events"
    )
