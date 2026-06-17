"""
ADR-001 Wave C-2 Agent D — TDD: passive_pipeline_tool_registry migration.

Tests:
  1. No unmarked SQL in passive_pipeline_tool_registry.py
  2. PassiveCandidateRepository exists on disk
  3. _require_company_id raises ValueError on empty company_id
  4. lgpd_cutoff is required (raises ValueError if None)
"""
from pathlib import Path
import asyncio
import pytest


BASE = Path("app/domains/sourcing")
TEXT_TRIPLE = 'text("""'
_LOOKBACK = 5  # lines to scan back for ADR-001-EXEMPT marker


def test_passive_no_unmarked_sql():
    """Every text() call in passive_pipeline_tool_registry must be covered by ADR-001-EXEMPT."""
    content = (BASE / "agents/passive_pipeline_tool_registry.py").read_text()
    lines = content.split("\n")
    unmarked = []
    for i, line in enumerate(lines):
        if TEXT_TRIPLE in line:
            window = [lines[i - k].strip() for k in range(1, _LOOKBACK + 1) if i - k >= 0]
            if not any("ADR-001-EXEMPT" in w for w in window):
                unmarked.append(f"Line {i + 1}: {line.strip()}")
    assert not unmarked, (
        "Unmarked SQL inline found in passive_pipeline_tool_registry:\n"
        + "\n".join(unmarked)
    )


def test_passive_candidate_repository_exists():
    """PassiveCandidateRepository file must exist."""
    repo_path = BASE / "repositories/passive_candidate_repository.py"
    assert repo_path.exists(), f"File not found: {repo_path}"


def test_passive_repo_require_company_id():
    """PassiveCandidateRepository.get_with_lgpd_check raises ValueError on empty company_id."""
    from app.domains.sourcing.repositories.passive_candidate_repository import (
        PassiveCandidateRepository,
    )
    from datetime import date

    repo = PassiveCandidateRepository(db=None)
    with pytest.raises(ValueError, match="company_id is required"):
        asyncio.get_event_loop().run_until_complete(
            repo.get_with_lgpd_check("some-id", "", date.today())
        )


def test_passive_repo_lgpd_cutoff_required():
    """PassiveCandidateRepository.get_with_lgpd_check raises ValueError if lgpd_cutoff is None."""
    from app.domains.sourcing.repositories.passive_candidate_repository import (
        PassiveCandidateRepository,
    )

    repo = PassiveCandidateRepository(db=None)
    with pytest.raises(ValueError, match="lgpd_cutoff is required"):
        asyncio.get_event_loop().run_until_complete(
            repo.get_with_lgpd_check("cid-123", "company-123", None)
        )


def test_passive_repo_static_require_company_id():
    """PassiveCandidateRepository._require_company_id raises on blank string."""
    from app.domains.sourcing.repositories.passive_candidate_repository import (
        PassiveCandidateRepository,
    )

    with pytest.raises(ValueError):
        PassiveCandidateRepository._require_company_id("")
