"""Task #672 / Fase 2C P0-2 — silent-fallback observability for resolve_domain.

When the LLM at Tier 5 emits an agent-type that is not in
``AGENT_TYPE_TO_DOMAIN``, ``resolve_domain`` must:
1. still return ``DEFAULT_DOMAIN`` (behaviour preserved),
2. emit a structured WARNING log with ``agent_type_received``,
   ``fallback_domain``, ``tenant_id``, ``user_id``, ``conversation_id``,
3. increment the in-process fallback counter exposed via
   ``get_fallback_stats()``.

The warning is the only signal the team has to detect a Tier 5 prompt
regression in production — without it the chat silently routes to
``recruiter_assistant`` and produces off-context answers.
"""
from __future__ import annotations

import logging

import pytest


@pytest.fixture(autouse=True)
def _reset_state():
    import app.domains  # noqa: F401  — ensure registry populated
    from app.orchestrator.domain_mappings import (
        reset_fallback_stats,
        reset_mapping_cache,
    )
    reset_mapping_cache()
    reset_fallback_stats()
    yield
    reset_mapping_cache()
    reset_fallback_stats()


def test_known_agent_type_does_not_warn(caplog):
    from app.orchestrator.domain_mappings import resolve_domain

    with caplog.at_level(logging.WARNING, logger="app.orchestrator.domain_mappings"):
        assert resolve_domain("sourcing") == "sourcing"

    assert not [
        r for r in caplog.records
        if "DEFAULT_DOMAIN" in r.getMessage()
    ], "Known agent-type must not trigger fallback warning"


def test_unknown_agent_type_returns_default_and_warns(caplog):
    from app.orchestrator.domain_mappings import (
        DEFAULT_DOMAIN,
        get_fallback_stats,
        resolve_domain,
    )

    with caplog.at_level(logging.WARNING, logger="app.orchestrator.domain_mappings"):
        result = resolve_domain(
            "totally_unknown_agent_xyz",
            tenant_id="tenant-42",
            user_id="user-7",
            conversation_id="conv-99",
        )

    assert result == DEFAULT_DOMAIN

    matching = [
        r for r in caplog.records
        if r.levelno == logging.WARNING and "DEFAULT_DOMAIN" in r.getMessage()
    ]
    assert matching, f"Expected fallback warning, got: {[r.getMessage() for r in caplog.records]}"
    record = matching[-1]
    assert record.agent_type_received == "totally_unknown_agent_xyz"
    assert record.fallback_domain == DEFAULT_DOMAIN
    assert record.tenant_id == "tenant-42"
    assert record.user_id == "user-7"
    assert record.conversation_id == "conv-99"

    stats = get_fallback_stats()
    assert stats["total"] == 1
    assert stats["by_intent"]["totally_unknown_agent_xyz"] == 1
    # Identifiers must NOT leak into the stats payload — they live in the log only.
    assert "recent" not in stats
    for forbidden in ("tenant_id", "user_id", "conversation_id"):
        assert forbidden not in stats, (
            f"{forbidden} must not be exposed by get_fallback_stats() — "
            "it would leak through /api/v1/orchestrator/health"
        )


def test_fallback_counter_aggregates_across_calls(caplog):
    from app.orchestrator.domain_mappings import (
        get_fallback_stats,
        resolve_domain,
    )

    with caplog.at_level(logging.WARNING, logger="app.orchestrator.domain_mappings"):
        resolve_domain("ghost_agent_a")
        resolve_domain("ghost_agent_a")
        resolve_domain("ghost_agent_b")

    stats = get_fallback_stats()
    assert stats["total"] == 3
    assert stats["by_intent"]["ghost_agent_a"] == 2
    assert stats["by_intent"]["ghost_agent_b"] == 1
