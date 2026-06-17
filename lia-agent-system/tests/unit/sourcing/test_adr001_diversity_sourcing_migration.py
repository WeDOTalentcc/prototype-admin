"""
TDD: ADR-001 Wave C-1 Agent A — diversity + sourcing EXEMPT markers + SourcingCandidateRepository.

Tests:
1. diversity_tool_registry has EXEMPT markers on all SQL inline blocks
2. sourcing_tool_registry has EXEMPT markers on all SQL inline blocks (no unmarked text() calls)
3. SourcingCandidateRepository file exists
4. SourcingCandidateRepository._require_company_id raises on empty company_id
"""
import asyncio
from pathlib import Path
import pytest


def test_diversity_no_unmarked_sql():
    """Todos os blocos session.execute(text(...)) em diversity_tool_registry têm EXEMPT marker."""
    content = Path(
        "app/domains/sourcing/agents/diversity_tool_registry.py"
    ).read_text()
    lines = content.split("\n")

    # The sensor catches: session.execute(text( on same line
    for i, line in enumerate(lines):
        stripped = line.strip()
        if "session.execute(text(" in stripped and "session.execute(text(" in line:
            # Check 10 lines above for an ADR-001-EXEMPT marker
            window = lines[max(0, i - 10) : i]
            has_exempt = any("ADR-001-EXEMPT" in prev for prev in window)
            assert has_exempt, (
                f"diversity_tool_registry.py line {i+1}: "
                f"session.execute(text() without ADR-001-EXEMPT marker in preceding 10 lines.\n"
                f"Line: {stripped}"
            )


def test_sourcing_no_unmarked_sql():
    """Todos os blocos session.execute(text(...)) em sourcing_tool_registry têm EXEMPT marker."""
    content = Path(
        "app/domains/sourcing/agents/sourcing_tool_registry.py"
    ).read_text()
    lines = content.split("\n")

    for i, line in enumerate(lines):
        stripped = line.strip()
        if "session.execute(text(" in stripped:
            window = lines[max(0, i - 10) : i]
            has_exempt = any("ADR-001-EXEMPT" in prev for prev in window)
            assert has_exempt, (
                f"sourcing_tool_registry.py line {i+1}: "
                f"session.execute(text() without ADR-001-EXEMPT marker in preceding 10 lines.\n"
                f"Line: {stripped}"
            )


def test_sourcing_candidate_repository_exists():
    """SourcingCandidateRepository file exists in canonical repositories/ location."""
    repo_path = Path(
        "app/domains/sourcing/repositories/sourcing_candidate_repository.py"
    )
    assert repo_path.exists(), (
        f"SourcingCandidateRepository not found at {repo_path}. "
        "ADR-001 MIGRATE requires a repo class for count_active."
    )


def test_sourcing_candidate_repo_require_company_id():
    """SourcingCandidateRepository._require_company_id raises ValueError on empty company_id."""
    from app.domains.sourcing.repositories.sourcing_candidate_repository import (
        SourcingCandidateRepository,
    )

    repo = SourcingCandidateRepository(db=None)

    # Empty string
    with pytest.raises(ValueError, match="company_id is required"):
        repo._require_company_id("")

    # None (coerced to falsy)
    with pytest.raises(ValueError, match="company_id is required"):
        repo._require_company_id(None)  # type: ignore[arg-type]
