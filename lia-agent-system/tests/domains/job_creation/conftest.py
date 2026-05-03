"""Pytest fixtures for job_creation domain tests (Sprint B Phase 1).

Convenções:
- Mocks de DB seguem o padrão de `tests/test_agents/conftest.py` (mock_db_session)
- Multi-tenancy: cada teste declara company_id explícito
"""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def db_session() -> MagicMock:
    """Mock async DB session.

    Stores `add()` calls in `db_session.added` and `commit()` calls in `db_session.commits`
    para asserts. Override `execute` em testes específicos quando precisar simular query results.
    """
    mock = MagicMock()
    mock.added: list[Any] = []
    mock.commits: int = 0

    def _add(obj):
        mock.added.append(obj)

    async def _commit():
        mock.commits += 1

    async def _refresh(obj):
        # Simulate ID assignment after commit (real session behavior)
        if not getattr(obj, "id", None):
            from uuid import uuid4
            obj.id = uuid4()

    mock.add = _add
    mock.commit = AsyncMock(side_effect=_commit)
    mock.rollback = AsyncMock()
    mock.refresh = AsyncMock(side_effect=_refresh)
    mock.execute = AsyncMock()
    mock.flush = AsyncMock()
    return mock


@pytest.fixture
def fake_uuid_str() -> str:
    from uuid import uuid4
    return str(uuid4())
