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


import os as _os


@pytest.mark.asyncio
@pytest.mark.skipif(not _os.environ.get("DATABASE_URL"), reason="integração: precisa de DB")
async def test_list_jobs_ordena_ativas_primeiro():
    """Fix P1 (2026-06-06): list_jobs ordenava por priority/created_at -> as
    Ativa espalhavam e só 2 caíam na 1ª página (a IA listava 2 mas contava 6).
    Agora ordena por status (Ativa primeiro) -> ordem monotônica não-decrescente."""
    from app.core.database import AsyncSessionLocal
    from app.domains.job_management.repositories.job_vacancy_crud_repository import (
        JobVacancyCRUDRepository,
    )
    PRIO = {"Ativa": 1, "Aprovada": 2, "Rascunho": 3, "Concluída": 4, "Arquivada": 5}
    async with AsyncSessionLocal() as db:
        r = await JobVacancyCRUDRepository(db).list_jobs_with_candidate_count(
            company_id="00000000-0000-4000-a000-000000000001", status="all", limit=30
        )
        prios = [PRIO.get(j["status"], 6) for j in r["jobs"]]
        assert prios == sorted(prios), f"ordem de status quebrada: {[j['status'] for j in r['jobs']]}"
