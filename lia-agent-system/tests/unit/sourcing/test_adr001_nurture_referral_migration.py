"""
TDD ADR-001: nurture + referral tool_registries migração para repos sourcing.

Valida:
- SQL inline removido dos dois tool_registries
- 3 novos repos existem em disco
- _require_company_id fail-closed em cada repo
"""
import asyncio
import re
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Structural tests — sem DB, só filesystem
# ---------------------------------------------------------------------------

def test_nurture_registry_no_sql_inline():
    """Nenhum bloco text(\"\"\" deve existir no tool_registry pós-migração."""
    content = Path("app/domains/sourcing/agents/nurture_sequence_tool_registry.py").read_text()
    blocks = re.findall(r'text\("""', content)
    assert len(blocks) == 0, f"Ainda há {len(blocks)} bloco(s) SQL inline em nurture_sequence_tool_registry.py"


def test_referral_registry_no_sql_inline():
    """Nenhum bloco text(\"\"\" deve existir no tool_registry pós-migração."""
    content = Path("app/domains/sourcing/agents/referral_tool_registry.py").read_text()
    blocks = re.findall(r'text\("""', content)
    assert len(blocks) == 0, f"Ainda há {len(blocks)} bloco(s) SQL inline em referral_tool_registry.py"


def test_nurture_sequence_repository_exists():
    assert Path(
        "app/domains/sourcing/repositories/nurture_sequence_repository.py"
    ).exists(), "NurtureSequenceRepository não encontrado"


def test_communication_matrix_repository_exists():
    assert Path(
        "app/domains/sourcing/repositories/communication_matrix_repository.py"
    ).exists(), "CommunicationMatrixRepository não encontrado"


def test_referral_repository_exists():
    assert Path(
        "app/domains/sourcing/repositories/referral_repository.py"
    ).exists(), "ReferralRepository não encontrado"


def test_repositories_init_exists():
    assert Path(
        "app/domains/sourcing/repositories/__init__.py"
    ).exists(), "repositories/__init__.py não encontrado"


# ---------------------------------------------------------------------------
# Import + _require_company_id tests
# ---------------------------------------------------------------------------

def test_nurture_repo_require_company_id():
    """NurtureSequenceRepository.create deve levantar ValueError com company_id vazio."""
    from app.domains.sourcing.repositories.nurture_sequence_repository import (
        NurtureSequenceRepository,
    )
    repo = NurtureSequenceRepository(db=None)
    with pytest.raises(ValueError, match="company_id is required"):
        asyncio.get_event_loop().run_until_complete(repo.create("cand-1", "", []))


def test_nurture_repo_get_by_id_require_company_id():
    """NurtureSequenceRepository.get_by_id deve levantar ValueError com company_id vazio."""
    from app.domains.sourcing.repositories.nurture_sequence_repository import (
        NurtureSequenceRepository,
    )
    repo = NurtureSequenceRepository(db=None)
    with pytest.raises(ValueError, match="company_id is required"):
        asyncio.get_event_loop().run_until_complete(repo.get_by_id("seq-1", ""))


def test_referral_repo_require_company_id():
    """ReferralRepository.get_hired_connectors deve levantar ValueError com company_id vazio."""
    from app.domains.sourcing.repositories.referral_repository import ReferralRepository
    repo = ReferralRepository(db=None)
    with pytest.raises(ValueError, match="company_id is required"):
        asyncio.get_event_loop().run_until_complete(repo.get_hired_connectors(""))


def test_comm_matrix_repo_require_company_id():
    """CommunicationMatrixRepository.get_channel_policy deve levantar ValueError com company_id vazio."""
    from app.domains.sourcing.repositories.communication_matrix_repository import (
        CommunicationMatrixRepository,
    )
    repo = CommunicationMatrixRepository(db=None)
    with pytest.raises(ValueError, match="company_id is required"):
        asyncio.get_event_loop().run_until_complete(repo.get_channel_policy("", "email"))
