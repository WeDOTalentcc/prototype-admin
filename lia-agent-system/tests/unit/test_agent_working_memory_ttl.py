"""Tests for AgentWorkingMemory TTL (UC-P2-02)."""
import pytest


def test_working_memory_has_expires_at():
    """AgentWorkingMemory model has expires_at field (migration 112)."""
    from lia_agents_core.working_memory import AgentWorkingMemory
    cols = [c.name for c in AgentWorkingMemory.__table__.columns]
    assert "expires_at" in cols, "expires_at column missing from AgentWorkingMemory"


def test_cleanup_task_is_registered():
    """agent_working_memory.cleanup Celery task is importable."""
    from app.jobs.tasks.compliance import cleanup_expired_working_memory
    assert callable(cleanup_expired_working_memory)
    assert cleanup_expired_working_memory.name == "agent_working_memory.cleanup"
