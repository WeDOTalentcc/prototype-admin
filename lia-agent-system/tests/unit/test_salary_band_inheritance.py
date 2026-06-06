"""Sensor TDD — heranca live da faixa salarial (read-time enrichment).

Audit 2026-06-06 (Paulo): a faixa salarial da vaga deve ser HERDADA da empresa
(Configuracoes -> Faixas Salariais por Nivel) em TODO lugar (lista + detalhe),
nao so quando o recrutador edita+salva. Cobre:
  - match_from_bands: matching PURO sobre bandas ja carregadas (sem N+1).
  - resolve_inherited_salary_ranges: preenche salary_range das vagas SEM faixa;
    respeita faixa explicita; marca source=company_salary_band + inherited=True.
"""
import types
from unittest.mock import AsyncMock, patch

import pytest


class _Band:
    def __init__(self, level, min_, max_, *, departments=None, contract_types=None, order=0, currency="BRL"):
        self.level = level
        self.min = min_
        self.max = max_
        self.departments = departments
        self.contract_types = contract_types
        self.subsidiaries = None
        self.order = order
        self.currency = currency


def _vaga(**kw):
    base = {"seniority_level": "junior", "department": None, "employment_type": None, "salary_range": None}
    base.update(kw)
    return types.SimpleNamespace(**base)


class TestMatchFromBands:
    def _repo(self):
        from app.domains.company.repositories.salary_band_repository import SalaryBandRepository
        return SalaryBandRepository(db=None)

    def test_matches_by_level(self):
        repo = self._repo()
        bands = [_Band("junior", 4000, 8000), _Band("senior", 11000, 17000)]
        b = repo.match_from_bands(bands, seniority_level="junior")
        assert b is not None and b.min == 4000

    def test_no_match_returns_none(self):
        repo = self._repo()
        bands = [_Band("senior", 11000, 17000)]
        assert repo.match_from_bands(bands, seniority_level="junior") is None

    def test_department_specific_band_preferred(self):
        repo = self._repo()
        generic = _Band("pleno", 7000, 12000, order=0)
        tech = _Band("pleno", 9000, 14000, departments={"tecnologia": True}, order=1)
        b = repo.match_from_bands([generic, tech], seniority_level="pleno", department="Tecnologia")
        assert b.min == 9000, "banda especifica do departamento deve vencer a generica"


class TestResolveInheritedSalaryRanges:
    async def _call(self, vacancies, bands, company_id="cid-1"):
        from app.api.v1.job_vacancies._shared import resolve_inherited_salary_ranges
        with patch(
            "app.domains.company.repositories.salary_band_repository.SalaryBandRepository.list_for_company",
            new=AsyncMock(return_value=bands),
        ):
            await resolve_inherited_salary_ranges(db=None, company_id=company_id, vacancies=vacancies)

    @pytest.mark.asyncio
    async def test_fills_empty_salary_from_band(self):
        v = _vaga(seniority_level="junior", salary_range=None)
        await self._call([v], [_Band("junior", 4000, 8000)])
        assert v.salary_range["min"] == 4000
        assert v.salary_range["max"] == 8000
        assert v.salary_range["source"] == "company_salary_band"
        assert v.salary_range["inherited"] is True

    @pytest.mark.asyncio
    async def test_explicit_salary_is_preserved(self):
        v = _vaga(seniority_level="junior", salary_range={"min": 5000, "max": 9000})
        await self._call([v], [_Band("junior", 4000, 8000)])
        assert v.salary_range == {"min": 5000, "max": 9000}, "faixa explicita da vaga nao pode ser sobrescrita"

    @pytest.mark.asyncio
    async def test_no_matching_band_leaves_empty(self):
        v = _vaga(seniority_level="director", salary_range=None)
        await self._call([v], [_Band("junior", 4000, 8000)])
        assert _salary_empty(v.salary_range)


def _salary_empty(sr):
    return not sr or (not sr.get("min") and not sr.get("max"))


class TestUndisclosedSalary:
    """'A combinar' (undisclosed) vence a heranca da empresa — nao herda banda."""

    @pytest.mark.asyncio
    async def test_undisclosed_salary_not_overwritten_by_band(self):
        from unittest.mock import AsyncMock, patch

        from app.api.v1.job_vacancies._shared import resolve_inherited_salary_ranges

        v = _vaga(seniority_level="junior", salary_range={"undisclosed": True, "min": None, "max": None})
        with patch(
            "app.domains.company.repositories.salary_band_repository.SalaryBandRepository.list_for_company",
            new=AsyncMock(return_value=[_Band("junior", 4000, 8000)]),
        ):
            await resolve_inherited_salary_ranges(db=None, company_id="cid-1", vacancies=[v])
        assert v.salary_range.get("undisclosed") is True
        assert not v.salary_range.get("min"), "'A combinar' nao pode herdar a banda da empresa"
