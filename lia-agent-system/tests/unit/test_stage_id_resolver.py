"""Task #1306: resolve_recruitment_stage_id maps a stage name to its id.

Every non-canonical path that writes ``VacancyCandidate.stage`` directly now
also records ``recruitment_stage_id`` via this resolver, so the SLA detector can
join by id instead of fragile name matching. The resolver mirrors the canonical
service (exact ``name``) and adds case-insensitive name / display_name
fallbacks, and is fail-soft (returns ``None`` on no-match or error).
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.shared.services.stage_id_resolver import resolve_recruitment_stage_id


def _fake_db(rows):
    res = MagicMock()
    res.all = lambda: rows
    db = MagicMock()
    db.execute = AsyncMock(return_value=res)
    return db


@pytest.mark.asyncio
async def test_exact_name_match():
    stage_id = uuid.uuid4()
    db = _fake_db([(stage_id, "Triagem", "Triagem")])
    assert await resolve_recruitment_stage_id(db, "c1", "Triagem") == stage_id


@pytest.mark.asyncio
async def test_case_insensitive_name_match():
    stage_id = uuid.uuid4()
    db = _fake_db([(stage_id, "Entrevista Técnica", "Entrevista Técnica")])
    # divergent casing/accent text still resolves to the id
    assert (
        await resolve_recruitment_stage_id(db, "c1", "entrevista técnica") == stage_id
    )


@pytest.mark.asyncio
async def test_display_name_match():
    stage_id = uuid.uuid4()
    db = _fake_db([(stage_id, "screening", "Triagem")])
    assert await resolve_recruitment_stage_id(db, "c1", "triagem") == stage_id


@pytest.mark.asyncio
async def test_no_match_returns_none():
    db = _fake_db([(uuid.uuid4(), "Triagem", "Triagem")])
    assert await resolve_recruitment_stage_id(db, "c1", "Proposta") is None


@pytest.mark.asyncio
async def test_missing_inputs_return_none():
    db = _fake_db([(uuid.uuid4(), "Triagem", "Triagem")])
    assert await resolve_recruitment_stage_id(db, None, "Triagem") is None
    assert await resolve_recruitment_stage_id(db, "c1", None) is None


@pytest.mark.asyncio
async def test_query_error_is_fail_soft():
    db = MagicMock()
    db.execute = AsyncMock(side_effect=RuntimeError("db down"))
    assert await resolve_recruitment_stage_id(db, "c1", "Triagem") is None
