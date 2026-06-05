"""
Sensores da persistência de parecer (Fase 2).

Pinam (sem DB real, mock de sessão):
- create_parecer_opinion é fail-closed em company_id (multi-tenancy)
- exige candidate_id
- executa 2 statements (archive + insert atômico) e retorna um id
- contrato do SQL: opinion_type='general' + versão atômica COALESCE(MAX)+1
"""
from unittest.mock import AsyncMock

import pytest

from app.domains.opinions.repositories.opinions_repository import OpinionsRepository


def _repo() -> OpinionsRepository:
    db = AsyncMock()
    db.execute = AsyncMock(return_value=None)
    return OpinionsRepository(db)


COMMON = dict(
    candidate_id="cand-1",
    job_vacancy_id="job-1",
    score=8.5,
    recommendation="RECOMMENDED",
    summary="resumo",
    score_breakdown={"qualification_matrix": {"mode": "grouped"}},
    strengths=["a"],
    concerns=[],
    gaps=[],
    matched_skills=["Python"],
    missing_skills=["Go"],
    next_steps=["entrevista"],
)


class TestTenantSafety:
    @pytest.mark.asyncio
    async def test_empty_company_id_fails_closed(self):
        repo = _repo()
        with pytest.raises(Exception):
            await repo.create_parecer_opinion(company_id="", **COMMON)

    @pytest.mark.asyncio
    async def test_requires_candidate_id(self):
        repo = _repo()
        args = {**COMMON, "candidate_id": ""}
        with pytest.raises(ValueError):
            await repo.create_parecer_opinion(company_id="comp-1", **args)


class TestAtomicWrite:
    @pytest.mark.asyncio
    async def test_archives_then_inserts_and_returns_id(self):
        repo = _repo()
        opinion_id = await repo.create_parecer_opinion(company_id="comp-1", **COMMON)
        assert isinstance(opinion_id, str) and len(opinion_id) > 10
        # 2 statements: archive + insert atômico
        assert repo.db.execute.await_count == 2

    def test_sql_contract_general_and_atomic_version(self):
        sql = OpinionsRepository._INSERT_PARECER_OPINION_ATOMIC_SQL
        assert "'general'" in sql
        assert "MAX(version)" in sql
        assert "COALESCE" in sql
        archive = OpinionsRepository._ARCHIVE_PARECER_OPINIONS_SQL
        assert "is_current = false" in archive
        assert "opinion_type = 'general'" in archive
