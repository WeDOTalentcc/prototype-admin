"""Unit tests for `candidate_search_service` (Task #727).

Cobre os 4 cenários do done-criteria:
  (a) tenant com vacancy_candidates retornando local
  (b) tenant vazio caindo no global (fellback_to_global=True)
  (c) busca explícita scope=global
  (d) query inválida retornando erro estruturado
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.ai.services import candidate_search_service as svc


def _row(**overrides):
    base = {
        "id": "11111111-1111-1111-1111-111111111111",
        "name": "Alice",
        "current_title": "Eng",
        "current_company": "Acme",
        "location_city": "SP",
        "location_state": "SP",
        "seniority_level": "Senior",
        "technical_skills": ["python"],
        "years_of_experience": 5,
        "lia_score": 90.0,
        "skills_match_percentage": 80.0,
        "status": "active",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


class _FakeSession:
    """Simula AsyncSessionLocal context manager + execute().fetchall()."""

    def __init__(self, results: list[list]):
        self._results = list(results)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def execute(self, *_args, **_kwargs):
        rows = self._results.pop(0) if self._results else []
        result = MagicMock()
        result.fetchall = MagicMock(return_value=rows)
        return result


@pytest.mark.asyncio
async def test_local_scope_returns_results_for_tenant_with_vacancy_candidates():
    rows_local = [_row(name="Bruno")]
    fake = _FakeSession([rows_local])
    with patch.object(svc, "AsyncSessionLocal", return_value=fake):
        out = await svc.search_candidates(
            query="python", company_id="co-1", scope="local", limit=10
        )
    assert out["status"] == "ok"
    assert out["scope_used"] == "local"
    assert out["fellback_to_global"] is False
    assert out["total"] == 1
    assert out["candidates"][0]["name"] == "Bruno"


@pytest.mark.asyncio
async def test_both_falls_back_to_global_when_local_empty():
    fake = _FakeSession([[], [_row(name="Carlos")]])  # local vazio, global tem 1
    with patch.object(svc, "AsyncSessionLocal", return_value=fake):
        out = await svc.search_candidates(
            query="python", company_id="co-1", scope="both", limit=10
        )
    assert out["status"] == "ok"
    assert out["scope_used"] == "global"
    assert out["fellback_to_global"] is True
    assert out["total"] == 1
    assert out["candidates"][0]["name"] == "Carlos"


@pytest.mark.asyncio
async def test_explicit_global_scope_skips_local_query():
    fake = _FakeSession([[_row(name="Diana")]])
    with patch.object(svc, "AsyncSessionLocal", return_value=fake):
        out = await svc.search_candidates(
            query="python", company_id=None, scope="global", limit=5
        )
    assert out["status"] == "ok"
    assert out["scope_used"] == "global"
    assert out["fellback_to_global"] is False
    assert out["total"] == 1


@pytest.mark.asyncio
async def test_empty_query_returns_structured_error():
    out = await svc.search_candidates(
        query="   ", company_id="co-1", scope="both", limit=10
    )
    assert out["status"] == "error"
    assert out["candidates"] == []
    assert "vazia" in out["error"]


@pytest.mark.asyncio
async def test_invalid_scope_returns_structured_error():
    out = await svc.search_candidates(
        query="x", company_id="co-1", scope="weird", limit=10  # type: ignore[arg-type]
    )
    assert out["status"] == "error"
    assert "scope" in out["error"]


@pytest.mark.asyncio
async def test_local_without_company_id_returns_error():
    out = await svc.search_candidates(
        query="x", company_id=None, scope="local", limit=10
    )
    assert out["status"] == "error"
    assert "company_id" in out["error"]


@pytest.mark.asyncio
async def test_both_returns_local_results_without_falling_back():
    rows_local = [_row(name="Eva"), _row(name="Fábio")]
    fake = _FakeSession([rows_local])  # só uma chamada — global não acionado
    with patch.object(svc, "AsyncSessionLocal", return_value=fake):
        out = await svc.search_candidates(
            query="python", company_id="co-1", scope="both", limit=10
        )
    assert out["scope_used"] == "local"
    assert out["fellback_to_global"] is False
    assert out["total"] == 2
