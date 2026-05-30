"""
TDD — ADR-001 Wave C-2 Agent E: talent_pool migration.

Valida que:
1. talent_pool_tool_registry.py não tem select(Talent*) inline
2. Repos existem em disco
3. _require_company_id fail-closed em ambos os repos
"""
import asyncio
from pathlib import Path

import pytest

BASE = Path("app/domains/talent_pool")
REGISTRY = BASE / "agents/talent_pool_tool_registry.py"


# ─── Structural tests ────────────────────────────────────────────────────────

def test_talent_pool_registry_no_select_inline():
    """Nenhum select(Talent*) direto no tool_registry (ADR-001)."""
    import re
    content = REGISTRY.read_text()
    selects = re.findall(r'\bselect\(Talent', content)
    assert len(selects) == 0, f"Remaining inline select() calls: {selects}"


def test_talent_pool_repository_exists():
    """TalentPoolRepository existe em disco."""
    assert (BASE / "repositories/talent_pool_repository.py").exists()


def test_talent_pool_candidate_repository_exists():
    """TalentPoolCandidateRepository existe em disco."""
    assert (BASE / "repositories/talent_pool_candidate_repository.py").exists()


def test_repositories_init_exists():
    """__init__.py do pacote repositories existe."""
    assert (BASE / "repositories/__init__.py").exists()


def test_registry_imports_repos():
    """tool_registry importa os dois repositórios."""
    content = REGISTRY.read_text()
    assert "TalentPoolRepository" in content
    assert "TalentPoolCandidateRepository" in content


def test_registry_preserves_lia_config_import():
    """tool_registry preserva import lia_config.database (padrão do domínio)."""
    content = REGISTRY.read_text()
    assert "lia_config.database" in content


# ─── Multi-tenancy fail-closed tests ─────────────────────────────────────────

def test_talent_pool_repo_require_company_id_empty_string():
    """TalentPoolRepository.list_pools levanta ValueError com company_id vazio."""
    from app.domains.talent_pool.repositories.talent_pool_repository import TalentPoolRepository
    repo = TalentPoolRepository(db=None)

    async def _run():
        return await repo.list_pools("")

    with pytest.raises(ValueError, match="company_id is required"):
        asyncio.run(_run())


def test_talent_pool_repo_require_company_id_none():
    """TalentPoolRepository.get_by_id levanta ValueError com company_id None."""
    from app.domains.talent_pool.repositories.talent_pool_repository import TalentPoolRepository
    repo = TalentPoolRepository(db=None)

    async def _run():
        return await repo.get_by_id("some-pool-id", None)

    with pytest.raises(ValueError, match="company_id is required"):
        asyncio.run(_run())


def test_talent_pool_candidate_repo_require_company_id_list():
    """TalentPoolCandidateRepository.list_by_pool levanta ValueError com company_id vazio."""
    from app.domains.talent_pool.repositories.talent_pool_candidate_repository import TalentPoolCandidateRepository
    repo = TalentPoolCandidateRepository(db=None)

    async def _run():
        return await repo.list_by_pool("pool-id", "")

    with pytest.raises(ValueError, match="company_id is required"):
        asyncio.run(_run())


def test_talent_pool_candidate_repo_require_company_id_move():
    """TalentPoolCandidateRepository.move_candidates_to_vacancy levanta ValueError com company_id None."""
    from app.domains.talent_pool.repositories.talent_pool_candidate_repository import TalentPoolCandidateRepository
    repo = TalentPoolCandidateRepository(db=None)

    async def _run():
        return await repo.move_candidates_to_vacancy(
            candidate_ids=["cid"],
            job_id="vid",
            company_id=None,
            source_pool_id="pool",
        )

    with pytest.raises(ValueError, match="company_id is required"):
        asyncio.run(_run())


def test_talent_pool_candidate_repo_require_company_id_move_empty():
    """TalentPoolCandidateRepository.move_candidates_to_vacancy levanta ValueError com company_id string vazia."""
    from app.domains.talent_pool.repositories.talent_pool_candidate_repository import TalentPoolCandidateRepository
    repo = TalentPoolCandidateRepository(db=None)

    async def _run():
        return await repo.move_candidates_to_vacancy(
            candidate_ids=["cid"],
            job_id="vid",
            company_id="",
            source_pool_id="pool",
        )

    with pytest.raises(ValueError, match="company_id is required"):
        asyncio.run(_run())
