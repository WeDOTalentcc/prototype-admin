"""Fix #3 (2026-06-06): count_by_status dá contagem ACURADA por status.
Bug live: a IA contava 'ativas' da lista truncada (2) em vez do total real (6)."""
import pytest

from app.domains.job_management.repositories.job_vacancy_crud_repository import (
    JobVacancyCRUDRepository,
)


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _FakeDB:
    def __init__(self, rows):
        self._rows = rows

    async def execute(self, stmt):
        return _FakeResult(self._rows)


@pytest.mark.asyncio
async def test_count_by_status_mapeia_breakdown():
    repo = JobVacancyCRUDRepository(
        _FakeDB([("Ativa", 6), ("Aprovada", 12), ("Concluída", 55)])
    )
    out = await repo.count_by_status("co1")
    assert out == {"Ativa": 6, "Aprovada": 12, "Concluída": 55}


@pytest.mark.asyncio
async def test_count_by_status_sem_company_retorna_vazio():
    repo = JobVacancyCRUDRepository(_FakeDB([("Ativa", 6)]))
    assert await repo.count_by_status("") == {}


@pytest.mark.asyncio
async def test_count_by_status_ignora_status_none():
    repo = JobVacancyCRUDRepository(_FakeDB([("Ativa", 6), (None, 3)]))
    out = await repo.count_by_status("co1")
    assert out == {"Ativa": 6}
