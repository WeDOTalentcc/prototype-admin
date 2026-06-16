"""
P1-7 regression sensor (audit 2026-05-21): the recruiter-facing endpoint that
creates self-scheduling links MUST refuse when the company policy
``scheduling_rules.self_scheduling_enabled`` is OFF.

Ghost-gate context: the toggle was already propagated to the frontend via
``scheduling_service.py:94`` but no write-path endpoint actually blocked
creation. Recruiter could disable the feature in Configurações and still
create links through the API (and through any LLM tool that wraps it).

Strategy: unit-test the canonical helper ``_is_self_scheduling_enabled``
directly. We do NOT spin up FastAPI's TestClient — the gate logic lives
in a pure async function that can be exercised in isolation. A separate
integration test (out of scope for this contract suite) can later exercise
the full HTTP path.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.v1.self_scheduling_public import _is_self_scheduling_enabled


def _make_db_with_policy(*, scheduling_rules: dict | None) -> MagicMock:
    """Build a MagicMock db whose HiringPolicyRepository returns a policy
    with the given scheduling_rules.

    Passing ``scheduling_rules=None`` simulates a cold-start tenant with no
    policy row at all (helper should return False — opt-in semantics).
    """
    db = MagicMock()
    policy = MagicMock() if scheduling_rules is not None else None
    if policy is not None:
        policy.scheduling_rules = scheduling_rules

    repo = MagicMock()
    repo.get_by_company = AsyncMock(return_value=policy)

    # Patch the canonical repository factory the helper uses. NOTE the
    # helper imports HiringPolicyRepository locally (intentional — it is
    # not a hot path so the late import keeps the dependency surface
    # narrow); we patch at the source module so the local import resolves
    # to our mock.
    import app.domains.hiring_policy.repositories.hiring_policy_repository as repo_mod
    repo_mod.HiringPolicyRepository = MagicMock(return_value=repo)
    return db


@pytest.mark.asyncio
async def test_self_scheduling_disabled_when_toggle_off():
    db = _make_db_with_policy(scheduling_rules={"self_scheduling_enabled": False})
    assert await _is_self_scheduling_enabled("co-1", db) is False


@pytest.mark.asyncio
async def test_self_scheduling_enabled_when_toggle_on():
    db = _make_db_with_policy(scheduling_rules={"self_scheduling_enabled": True})
    assert await _is_self_scheduling_enabled("co-1", db) is True


@pytest.mark.asyncio
async def test_self_scheduling_disabled_by_default_for_cold_start_tenant():
    """No policy row yet → return False. Opt-in matches the schema default
    in SchedulingRulesIn (Field(default=False))."""
    db = _make_db_with_policy(scheduling_rules=None)
    assert await _is_self_scheduling_enabled("co-1", db) is False


@pytest.mark.asyncio
async def test_self_scheduling_disabled_when_scheduling_rules_missing_key():
    """Policy exists but the scheduling_rules dict does not have the key.
    Match the .get(_, False) fallback — explicit opt-in."""
    db = _make_db_with_policy(scheduling_rules={"some_other_setting": True})
    assert await _is_self_scheduling_enabled("co-1", db) is False


@pytest.mark.asyncio
async def test_self_scheduling_fails_safe_on_db_error():
    """DB outage MUST return False (fail-safe). For self-scheduling the
    safe default is OFF because enabling it without recruiter intent could
    leak draft slots to candidates."""
    db = MagicMock()

    repo = MagicMock()
    repo.get_by_company = AsyncMock(side_effect=RuntimeError("simulated outage"))
    import app.domains.hiring_policy.repositories.hiring_policy_repository as repo_mod
    repo_mod.HiringPolicyRepository = MagicMock(return_value=repo)

    assert await _is_self_scheduling_enabled("co-1", db) is False
