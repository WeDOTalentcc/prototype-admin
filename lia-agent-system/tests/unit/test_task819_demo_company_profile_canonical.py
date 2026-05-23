"""Task #819 — close the last 2 demo-tenant config gaps.

Two pieces are validated together:

1. `_ensure_demo_company_profile` in `seed_service` writes `name`,
   `industry` and `company_size` into the canonical row of
   `company_profiles` (id = `DEMO_COMPANY_UUID`), with idempotent backfill
   that does not overwrite admin-entered values. `website` is deliberately
   omitted (preserves the legitimate trigger for `analyze_company_website`,
   contract §5.1).

2. `PreConditionChecker._check_company_profile_completeness` no longer
   considers `website` part of the "incomplete profile" signal. Website has
   its own dedicated hint (`company_website_missing`) so reporting it under
   `incomplete_company_profile` would surface the same gap twice and prevent
   the demo tenant from ever silencing the hint.

Together these guarantee that after `seed_demo_company_settings(db)` runs,
the only onboarding hint that still fires for the demo tenant is the
intentional `company_website_missing` info hint.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.tenant import DEMO_COMPANY_UUID
from app.shared.services.seed_service import (
    _DEMO_CULTURE_PROFILE,
    _ensure_demo_company_profile,
)


# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────


def _make_db_mock(*, inserted: bool) -> AsyncMock:
    """Mock AsyncSession.execute returning a result whose .first()[0] = inserted."""
    db = AsyncMock()
    result = MagicMock()
    result.first = MagicMock(return_value=(inserted,))
    db.execute = AsyncMock(return_value=result)
    return db


def _captured_sql_and_params(db_mock: AsyncMock) -> tuple[str, dict]:
    db_mock.execute.assert_awaited_once()
    args, _ = db_mock.execute.call_args
    sql_clause, params = args
    sql_text = str(getattr(sql_clause, "text", sql_clause))
    return sql_text, params


# ─────────────────────────────────────────────────────────────────────
# Seed function tests
# ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ensure_demo_company_profile_writes_canonical_fields():
    """The seed must pass name/industry/company_size as bound parameters."""
    db = _make_db_mock(inserted=True)

    created = await _ensure_demo_company_profile(db)

    assert created is True  # xmax=0 ⇒ new row inserted
    sql_text, params = _captured_sql_and_params(db)
    assert params["cid"] == DEMO_COMPANY_UUID
    assert params["name"], "name canonical field must not be empty"
    assert params["industry"] == _DEMO_CULTURE_PROFILE["industry"]
    assert params["company_size"] == _DEMO_CULTURE_PROFILE["company_size"]


@pytest.mark.asyncio
async def test_ensure_demo_company_profile_does_not_set_website():
    """Website stays NULL deliberately — preserves the analyze_company_website offer."""
    db = _make_db_mock(inserted=True)

    await _ensure_demo_company_profile(db)

    sql_text, params = _captured_sql_and_params(db)
    assert "website" not in params, (
        "website must not be passed as a parameter — it must remain NULL "
        "to keep triggering the analyze_company_website offer (contract §5.1)."
    )
    assert "website" not in sql_text.lower(), (
        "website must not appear in the SQL — filling it would mask a product feature."
    )


@pytest.mark.asyncio
async def test_ensure_demo_company_profile_is_idempotent_with_backfill():
    """ON CONFLICT must DO UPDATE (not DO NOTHING) so old rows get backfilled."""
    db = _make_db_mock(inserted=False)  # row already existed → DO UPDATE path

    created = await _ensure_demo_company_profile(db)

    assert created is False  # xmax != 0 ⇒ pre-existing row, only updated
    sql_text, _ = _captured_sql_and_params(db)
    upper = sql_text.upper()
    assert "ON CONFLICT" in upper
    assert "DO UPDATE" in upper, (
        "ON CONFLICT must be DO UPDATE for backfill — DO NOTHING would leave "
        "old rows with NULL industry/company_size."
    )
    assert "COALESCE" in upper, (
        "Backfill must use COALESCE/NULLIF so admin-entered values are not overwritten."
    )


@pytest.mark.asyncio
async def test_ensure_demo_company_profile_uses_xmax_to_detect_insert():
    """`created` must come from `xmax = 0`, not from `rowcount` (review #819).

    With ON CONFLICT DO UPDATE the rowcount is 1 in both insert and update
    paths, so relying on rowcount silently mislabels every re-run as
    "created". `RETURNING (xmax = 0) AS inserted` is the correct primitive.
    """
    db = _make_db_mock(inserted=True)
    await _ensure_demo_company_profile(db)

    sql_text, _ = _captured_sql_and_params(db)
    upper = sql_text.upper()
    assert "RETURNING" in upper
    assert "XMAX" in upper, (
        "Insert-vs-update detection requires RETURNING (xmax = 0) — without it "
        "the seed mislabels updates as inserts in the logs."
    )


@pytest.mark.asyncio
async def test_ensure_demo_company_profile_targets_canonical_columns():
    """Sanity check: SQL writes the columns the PreConditionChecker reads."""
    db = _make_db_mock(inserted=True)

    await _ensure_demo_company_profile(db)

    sql_text, _ = _captured_sql_and_params(db)
    lowered = sql_text.lower()
    for column in ("name", "industry", "company_size"):
        assert column in lowered, f"SQL must populate canonical column '{column}'"


# ─────────────────────────────────────────────────────────────────────
# PreConditionChecker tests
# ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_completeness_check_ignores_website_when_canonical_fields_filled():
    """With name/industry/company_size present, missing list is empty even if website is NULL.

    This is the core guarantee of Task #819: the demo tenant deliberately
    leaves `website` NULL, and that should NOT trigger
    `incomplete_company_profile`. Website has its own dedicated hint
    (`company_website_missing`).
    """
    from app.orchestrator.guards.precondition_checker import PreConditionChecker

    # Canonical row: name + industry + company_size all set; website NULL.
    fake_row = ("[DEMO] WeDo Talent", "Recursos Humanos / Tecnologia", "Medium")
    fake_result = MagicMock()
    fake_result.first = MagicMock(return_value=fake_row)
    fake_session = AsyncMock()
    fake_session.execute = AsyncMock(return_value=fake_result)
    fake_session.__aenter__ = AsyncMock(return_value=fake_session)
    fake_session.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "lia_config.database.AsyncSessionLocal",
        return_value=fake_session,
    ):
        checker = PreConditionChecker()
        missing = await checker._check_company_profile_completeness(DEMO_COMPANY_UUID)

    assert missing == [], (
        "Demo tenant has name/industry/company_size filled. The completeness "
        "check must return an empty list (website is covered by the separate "
        "company_website_missing hint, not by this check)."
    )


@pytest.mark.asyncio
async def test_completeness_check_still_flags_truly_missing_canonical_fields():
    """Negative test: when canonical fields are actually empty, they are reported."""
    from app.orchestrator.guards.precondition_checker import PreConditionChecker

    fake_row = (None, "", None)  # all 3 canonical fields blank
    fake_result = MagicMock()
    fake_result.first = MagicMock(return_value=fake_row)
    fake_session = AsyncMock()
    fake_session.execute = AsyncMock(return_value=fake_result)
    fake_session.__aenter__ = AsyncMock(return_value=fake_session)
    fake_session.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "lia_config.database.AsyncSessionLocal",
        return_value=fake_session,
    ):
        checker = PreConditionChecker()
        missing = await checker._check_company_profile_completeness("any-tenant")

    assert "nome" in missing
    assert "setor" in missing
    assert "tamanho" in missing
    assert "website" not in missing, (
        "Website must NOT appear in incomplete_company_profile output — "
        "it has its own dedicated hint (company_website_missing)."
    )


@pytest.mark.asyncio
async def test_completeness_check_sql_does_not_select_website():
    """SQL of the completeness check must not even SELECT website — defense in depth."""
    from app.orchestrator.guards.precondition_checker import PreConditionChecker

    captured: dict[str, str] = {}

    fake_result = MagicMock()
    fake_result.first = MagicMock(return_value=("x", "y", "z"))

    async def _fake_execute(stmt, params=None):
        captured["sql"] = str(getattr(stmt, "text", stmt))
        return fake_result

    fake_session = AsyncMock()
    fake_session.execute = _fake_execute
    fake_session.__aenter__ = AsyncMock(return_value=fake_session)
    fake_session.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "lia_config.database.AsyncSessionLocal",
        return_value=fake_session,
    ):
        checker = PreConditionChecker()
        await checker._check_company_profile_completeness("any-tenant")

    sql = captured.get("sql", "").lower()
    assert "select" in sql
    assert "name" in sql and "industry" in sql and "company_size" in sql
    assert "website" not in sql, (
        "Website was removed from the completeness query — re-adding it would "
        "regress Task #819 by surfacing the same gap twice."
    )
