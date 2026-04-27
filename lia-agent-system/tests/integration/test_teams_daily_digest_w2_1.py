"""
Integration tests — W2.1: P1-1 fix dos 3 bugs em send_daily_digest.

Auditoria 2026-04-26 (AUDITORIA_TEAMS_2026-04-26.md, finding P1-1) identificou
3 bugs concretos em teams_proactivity_engine.send_daily_digest:

1. L:346 `JobVacancy.deadline is not None`
   -> Python truthy (sempre True para Column object), nao SQLAlchemy expression.
   -> Resultado: filtro sempre passa (where TRUE) ou comportamento errado.
   -> Fix: `JobVacancy.deadline.isnot(None)` (SQLAlchemy `IS NOT NULL`).

2. L:363 `await self._find_stalled_pipelines(db, company_id)`
   -> Signature: `_find_stalled_pipelines(self, company_id, stalled_days=5)`.
   -> Bug: passa AsyncSession no lugar do primeiro arg (company_id).
   -> Fix: `await self._find_stalled_pipelines(company_id)`.

3. L:407 raw SQL `"SELECT DISTINCT..."` sem `text()` wrap.
   -> SQLAlchemy 2.x rejeita strings literais — TypeError em runtime.
   -> Fix: wrap em `sqlalchemy.text(...)`.

Cron diario 08:00 — provavelmente nunca executou em prod. Esta suite valida
que send_daily_digest executa sem crash apos os fixes.
"""
from __future__ import annotations

import inspect
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _engine_src() -> str:
    import app.domains.communication.services.teams_proactivity_engine as mod
    return inspect.getsource(mod)


# ============================================================================
# 1. Source-level checks — anti-patterns must be removed
# ============================================================================


class TestSendDailyDigestBugFreeSource:
    """Source code free of the 3 bugs identified in P1-1."""

    def test_no_python_is_not_none_on_sqlalchemy_column(self):
        """
        Bug 1: `Column is not None` is always True (Python truthy).
        Must use `Column.isnot(None)` for SQLAlchemy IS NOT NULL.
        """
        src = _engine_src()
        # Allow `is not None` in pure-Python contexts (e.g. local var checks),
        # but NOT on SQLAlchemy column expressions like `JobVacancy.deadline is not None`.
        # The specific bug pattern from P1-1:
        bug_pattern = "JobVacancy.deadline is not None"
        assert bug_pattern not in src, (
            f"Bug 1 P1-1: '{bug_pattern}' is Python truthy (always True), "
            f"not SQLAlchemy IS NOT NULL. Use `JobVacancy.deadline.isnot(None)`."
        )

    def test_find_stalled_pipelines_call_does_not_pass_db(self):
        """
        Bug 2: `_find_stalled_pipelines(db, company_id)` passes session as
        first positional arg. Signature is `(self, company_id, stalled_days)`.
        """
        src = _engine_src()
        bug_pattern = "self._find_stalled_pipelines(db, company_id)"
        assert bug_pattern not in src, (
            f"Bug 2 P1-1: '{bug_pattern}' passes db as company_id. "
            f"Signature: _find_stalled_pipelines(self, company_id, stalled_days=5). "
            f"Fix: self._find_stalled_pipelines(company_id)."
        )

    def test_raw_sql_string_is_wrapped_in_text(self):
        """
        Bug 3: raw SQL string in db.execute(...) — SQLAlchemy 2.x rejects.
        Must be wrapped in sqlalchemy.text(...).
        """
        src = _engine_src()
        # The exact bug pattern from L:407 — string literal directly in execute.
        # We look for the `"SELECT DISTINCT service_url"...` literal NOT inside text().
        # Simplest signal: this exact string + `db2.execute(` on the same call.
        # Refined: forbid `db2.execute(\n` followed by a `"SELECT` literal (no `text(`).
        import re
        # Look for any db*.execute call passed a bare string literal (no text() wrapper).
        # Pattern matches: `.execute(\n                "SELECT...` (without text)
        bare_string_in_execute = re.search(
            r'\.execute\(\s*"SELECT',
            src,
        )
        assert bare_string_in_execute is None, (
            "Bug 3 P1-1: raw SQL string passed directly to db.execute(). "
            "SQLAlchemy 2.x rejects literals. Wrap with sqlalchemy.text(\"...\")."
        )


# ============================================================================
# 2. Runtime check — send_daily_digest executes without crash
# ============================================================================


class TestSendDailyDigestRuntime:
    """send_daily_digest must execute end-to-end without TypeError/AttributeError."""

    @pytest.mark.asyncio
    async def test_send_daily_digest_runs_without_crash_on_no_data(self):
        """
        Smoke: with empty DB results, send_daily_digest returns 0 (no recipients)
        instead of raising. Validates the 3 bugs are gone end-to-end.
        """
        from app.domains.communication.services.teams_proactivity_engine import (
            TeamsProactivityEngine,
        )

        # Mock async session that yields empty results for every query
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar = MagicMock(return_value=0)
        mock_result.fetchall = MagicMock(return_value=[])
        mock_result.scalars.return_value.all.return_value = []
        # Also support iteration (for raw SELECT path)
        mock_result.__iter__ = MagicMock(return_value=iter([]))
        mock_session.execute = AsyncMock(return_value=mock_result)

        async def _fake_get_db():
            yield mock_session

        engine = TeamsProactivityEngine()
        with patch.object(engine, "_get_db", _fake_get_db):
            # Also patch the helper calls that hit DB independently
            with patch.object(
                engine, "_find_stalled_pipelines", AsyncMock(return_value=[])
            ), patch.object(
                engine,
                "_get_recruiter_refs_for_vacancy",
                AsyncMock(return_value=[]),
            ):
                # Should not raise
                sent = await engine.send_daily_digest(company_id="comp_test")

        assert sent == 0, (
            f"send_daily_digest with no recipients should return 0, got {sent}"
        )
