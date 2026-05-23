"""
ADR-001 Wave C-2 Agent D — TDD: company_tool_registry migration.

Tests:
  1. No unmarked SQL in company_tool_registry.py
  2. CompanyProfileRepository exists on disk
  3. CompanyProfileRepository._require_company_id raises on empty company_id
  4. CompanyProfileRepository.get_full_profile raises on empty company_id
  5. CompanyProfileRepository.get_culture_profile raises on empty company_id
  6. CompanyProfileRepository.upsert_workforce_plan raises on empty company_id
"""
from pathlib import Path
import asyncio
import pytest


BASE = Path("app/domains/company_settings")
TEXT_TRIPLE = 'text("""'


def test_company_no_unmarked_sql():
    """Every text() call in company_tool_registry must be preceded by ADR-001-EXEMPT."""
    content = (BASE / "agents/company_tool_registry.py").read_text()
    lines = content.split("\n")
    unmarked = []
    for i, line in enumerate(lines):
        if TEXT_TRIPLE in line:
            prev = lines[i - 1].strip() if i > 0 else ""
            prev2 = lines[i - 2].strip() if i > 1 else ""
            prev3 = lines[i - 3].strip() if i > 2 else ""
            # Some EXEMPT markers span multiple comment lines — check up to 3 lines back
            has_exempt = any(
                "ADR-001-EXEMPT" in x for x in [prev, prev2, prev3]
            )
            if not has_exempt:
                unmarked.append(f"Line {i + 1}: {line.strip()}")
    assert not unmarked, (
        "Unmarked SQL inline found in company_tool_registry:\n"
        + "\n".join(unmarked)
    )


def test_company_profile_repository_exists():
    """CompanyProfileRepository file must exist."""
    repo_path = BASE / "repositories/company_profile_repository.py"
    assert repo_path.exists(), f"File not found: {repo_path}"


def test_company_repo_require_company_id():
    """CompanyProfileRepository._require_company_id raises on blank string."""
    from app.domains.company_settings.repositories.company_profile_repository import (
        CompanyProfileRepository,
    )

    with pytest.raises(ValueError, match="company_id is required"):
        CompanyProfileRepository._require_company_id("")


def test_company_repo_get_full_profile_raises_empty():
    """CompanyProfileRepository.get_full_profile raises ValueError on empty company_id."""
    from app.domains.company_settings.repositories.company_profile_repository import (
        CompanyProfileRepository,
    )

    repo = CompanyProfileRepository(db=None)
    with pytest.raises(ValueError, match="company_id is required"):
        asyncio.get_event_loop().run_until_complete(repo.get_full_profile(""))


def test_company_repo_get_culture_profile_raises_empty():
    """CompanyProfileRepository.get_culture_profile raises ValueError on empty company_id."""
    from app.domains.company_settings.repositories.company_profile_repository import (
        CompanyProfileRepository,
    )

    repo = CompanyProfileRepository(db=None)
    with pytest.raises(ValueError, match="company_id is required"):
        asyncio.get_event_loop().run_until_complete(repo.get_culture_profile(""))


def test_company_repo_upsert_workforce_plan_raises_empty():
    """CompanyProfileRepository.upsert_workforce_plan raises ValueError on empty company_id."""
    from app.domains.company_settings.repositories.company_profile_repository import (
        CompanyProfileRepository,
    )

    repo = CompanyProfileRepository(db=None)
    with pytest.raises(ValueError, match="company_id is required"):
        asyncio.get_event_loop().run_until_complete(
            repo.upsert_workforce_plan("", "[]")
        )
