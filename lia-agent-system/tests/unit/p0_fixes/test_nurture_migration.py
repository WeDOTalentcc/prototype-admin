"""Tests verifying nurture sequence tooling is wired (migration 290 enables tables)."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


def test_nurture_tool_registry_importable():
    """Registry and tools must import without error."""
    from app.domains.sourcing.agents.nurture_sequence_tool_registry import (
        get_nurture_sequence_tools,
        _NURTURE_TOOL_DEFINITIONS,
    )
    tools = get_nurture_sequence_tools()
    assert isinstance(tools, list)
    assert len(tools) >= 5, "Expected at least 5 nurture tools"


def test_nurture_tool_names():
    """All 5 canonical tools must be present."""
    from app.domains.sourcing.agents.nurture_sequence_tool_registry import get_nurture_sequence_tools
    tool_names = {t.name for t in get_nurture_sequence_tools()}
    expected = {
        "nurture_create_sequence",
        "nurture_get_sequence_status",
        "nurture_approve_step",
        "nurture_execute_step",
        "nurture_expire_sequence",
    }
    missing = expected - tool_names
    assert not missing, f"Missing nurture tools: {missing}"


def test_nurture_sequence_repository_importable():
    """Repository must be importable."""
    from app.domains.sourcing.repositories.nurture_sequence_repository import (
        NurtureSequenceRepository,
    )
    assert NurtureSequenceRepository is not None


def test_migration_290_exists():
    """Migration file must exist on disk."""
    import os
    migration_path = "alembic/versions/290_nurture_sequence_tables.py"
    assert os.path.exists(migration_path), f"Migration not found: {migration_path}"


def test_nurture_invalid_candidate_returns_error():
    """nurture_create_sequence with empty candidate_id must return error, not crash."""
    from app.domains.sourcing.agents.nurture_sequence_tool_registry import (
        _wrap_nurture_create_sequence,
    )
    result = asyncio.get_event_loop().run_until_complete(
        _wrap_nurture_create_sequence(candidate_id="", company_id="co-test", steps=[])
    )
    assert result.get("success") is False
    assert "candidate_id" in result.get("message", "").lower()
