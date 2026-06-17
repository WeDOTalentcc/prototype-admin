"""Contract: Context Center approval gate (Fase 5.1, 2026-06-04).

Auto-generated culture profiles (scrape+LLM, source='auto') MUST NOT feed agent
prompts until a human approves them (LGPD/bias — ghost-context gate). Human-authored
profiles (source != 'auto': manual / onboarding / rest_put_inline_edit) always pass.

The single gate lives in CultureProfileRepository.get_for_agent_context(); UI/approval
flows keep using get_for_company() (which sees pending profiles). These are pure unit
tests over the gate logic (get_for_company mocked) — no DB.
"""
import pytest
from unittest.mock import AsyncMock

from app.domains.company.repositories.culture_profile_repository import (
    CultureProfileRepository,
)


class _Profile:
    def __init__(self, source, is_approved):
        self.source = source
        self.is_approved = is_approved


def _repo(profile):
    repo = CultureProfileRepository(AsyncMock())
    repo.get_for_company = AsyncMock(return_value=profile)
    return repo


@pytest.mark.asyncio
async def test_auto_pending_is_withheld_from_agents():
    repo = _repo(_Profile("auto", False))
    assert await repo.get_for_agent_context("c1") is None


@pytest.mark.asyncio
async def test_auto_approved_is_served():
    repo = _repo(_Profile("auto", True))
    p = await repo.get_for_agent_context("c1")
    assert p is not None and p.source == "auto"


@pytest.mark.asyncio
async def test_human_authored_always_served_even_if_not_approved():
    # source != 'auto' bypasses the gate (human already in the loop).
    for src in ("manual", "onboarding", "rest_put_inline_edit"):
        repo = _repo(_Profile(src, False))
        assert await repo.get_for_agent_context("c1") is not None, src


@pytest.mark.asyncio
async def test_none_passthrough():
    repo = _repo(None)
    assert await repo.get_for_agent_context("c1") is None
