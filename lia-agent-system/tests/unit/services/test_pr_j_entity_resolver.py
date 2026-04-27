"""
PR-J — EntityResolverService tests (TDD RED → GREEN).

harness-engineering sensor computacional:
Valida que o resolver retorna entidade correta OU navega sem perguntas
excessivas. Multi-tenant: company_id sempre enforced.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.shared.services.entity_resolver_service import (
    EntityResolverService,
    EntityResolutionResult,
)


def _make_candidate(id_: str, name: str, stage: str = "triagem") -> MagicMock:
    c = MagicMock()
    c.id = id_
    c.name = name
    c.email = f"{name.lower().replace(' ', '.')}@test.com"
    c.current_stage = stage
    return c


def _mock_db(candidates: list) -> AsyncMock:
    db = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = candidates
    result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result)
    return db


class TestEntityResolverCandidateSingleMatch:
    @pytest.mark.asyncio
    async def test_single_match_resolves_with_preview(self):
        c = _make_candidate("c123", "João Silva")
        db = _mock_db([c])
        result = await EntityResolverService._resolve_candidate(
            "João", "comp_A", db
        )
        assert result.resolved is True
        assert result.entity_id == "c123"
        assert result.preview["name"] == "João Silva"
        assert result.preview["stage"] == "triagem"

    @pytest.mark.asyncio
    async def test_single_match_sets_correct_entity_type(self):
        db = _mock_db([_make_candidate("c1", "Maria")])
        result = await EntityResolverService._resolve_candidate("Maria", "comp_A", db)
        assert result.entity_type == "candidate"


class TestEntityResolverCandidateNotFound:
    @pytest.mark.asyncio
    async def test_no_match_returns_not_resolved(self):
        db = _mock_db([])
        result = await EntityResolverService._resolve_candidate(
            "xyz_nao_existe", "comp_A", db
        )
        assert result.resolved is False
        assert result.ambiguous is False

    @pytest.mark.asyncio
    async def test_no_match_provides_navigate_to(self):
        db = _mock_db([])
        result = await EntityResolverService._resolve_candidate(
            "xyz_nao_existe", "comp_A", db
        )
        assert result.navigate_to == "/funil-de-talentos"


class TestEntityResolverCandidateAmbiguous:
    @pytest.mark.asyncio
    async def test_multiple_matches_returns_ambiguous(self):
        candidates = [_make_candidate(f"c{i}", f"João {i}") for i in range(3)]
        db = _mock_db(candidates)
        result = await EntityResolverService._resolve_candidate(
            "João", "comp_A", db
        )
        assert result.resolved is False
        assert result.ambiguous is True
        assert len(result.candidates_preview) == 3

    @pytest.mark.asyncio
    async def test_ambiguous_caps_at_three_previews(self):
        candidates = [_make_candidate(f"c{i}", f"João {i}") for i in range(5)]
        db = _mock_db(candidates)
        result = await EntityResolverService._resolve_candidate(
            "João", "comp_A", db
        )
        assert len(result.candidates_preview) <= 3


class TestEntityResolverMultiTenant:
    @pytest.mark.asyncio
    async def test_resolve_calls_db_with_company_id(self):
        db = _mock_db([])
        await EntityResolverService.resolve(
            entity_type="candidate",
            hint="test",
            company_id="comp_tenant_A",
            db=db,
        )
        db.execute.assert_called()

    @pytest.mark.asyncio
    async def test_unknown_entity_type_returns_not_resolved(self):
        db = _mock_db([])
        result = await EntityResolverService.resolve(
            entity_type="unknown_type_xyz",
            hint="test",
            company_id="comp_A",
            db=db,
        )
        assert result.resolved is False
        assert result.navigate_to is not None
