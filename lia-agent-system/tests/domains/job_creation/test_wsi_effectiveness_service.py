"""Unit tests for WsiEffectivenessService - Sprint B Phase 3."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest


@pytest.fixture
def fake_company() -> str:
    return f"co-{uuid4()}"


@pytest.mark.asyncio
async def test_select_priority_skills_requires_company_id():
    from app.domains.job_creation.services.wsi_effectiveness_service import (
        WsiEffectivenessService,
    )
    svc = WsiEffectivenessService(db=AsyncMock())
    with pytest.raises(ValueError, match="company_id"):
        await svc.select_priority_skills(
            company_id="",
            parent_ids=["communication_collaboration"],
        )


@pytest.mark.asyncio
async def test_select_priority_skills_unknown_parent_returns_empty(fake_company):
    from app.domains.job_creation.services.wsi_effectiveness_service import (
        WsiEffectivenessService,
    )
    svc = WsiEffectivenessService(db=AsyncMock())
    # Mock repo to return empty
    svc.repo = MagicMock()
    svc.repo.get_by_skills = AsyncMock(return_value={})

    result = await svc.select_priority_skills(
        company_id=fake_company,
        parent_ids=["nonexistent_parent"],
    )
    assert result == []


@pytest.mark.asyncio
async def test_select_priority_skills_no_data_returns_default_skills(fake_company):
    """Sem dados em effectiveness, retorna skills do parent com source=default."""
    from app.domains.job_creation.services.wsi_effectiveness_service import (
        WsiEffectivenessService,
    )
    svc = WsiEffectivenessService(db=AsyncMock())
    svc.repo = MagicMock()
    svc.repo.get_by_skills = AsyncMock(return_value={})

    result = await svc.select_priority_skills(
        company_id=fake_company,
        parent_ids=["communication_collaboration"],
        top_n_per_parent=3,
    )
    assert len(result) == 3
    assert all(item["source"] == "default" for item in result)
    assert all(item["parent_id"] == "communication_collaboration" for item in result)


@pytest.mark.asyncio
async def test_select_priority_skills_excludes_fairness_blocked(fake_company):
    """Skills com fairness_blocked=1 nao aparecem."""
    from app.domains.job_creation.services.wsi_effectiveness_service import (
        WsiEffectivenessService,
    )
    blocked_eff = MagicMock()
    blocked_eff.fairness_blocked = 1
    blocked_eff.times_used = 50
    blocked_eff.discrimination_score = 0.9

    svc = WsiEffectivenessService(db=AsyncMock())
    svc.repo = MagicMock()
    svc.repo.get_by_skills = AsyncMock(return_value={
        "active_listening": blocked_eff,
    })

    result = await svc.select_priority_skills(
        company_id=fake_company,
        parent_ids=["communication_collaboration"],
        top_n_per_parent=10,
    )
    skill_ids = {item["skill_id"] for item in result}
    assert "active_listening" not in skill_ids


@pytest.mark.asyncio
async def test_record_outcome_unknown_skill_skipped(fake_company):
    """Skill nao existe na taxonomia - skip silencioso."""
    from app.domains.job_creation.services.wsi_effectiveness_service import (
        WsiEffectivenessService,
    )
    svc = WsiEffectivenessService(db=AsyncMock())
    svc.repo = MagicMock()
    svc.repo.record_outcome = AsyncMock()

    await svc.record_question_outcome(
        company_id=fake_company,
        skill_probed="totally_invalid_skill",
        outcome="hired",
        score=80.0,
    )
    svc.repo.record_outcome.assert_not_called()


@pytest.mark.asyncio
async def test_record_outcome_resolves_parent_automatically(fake_company):
    """parent_id eh resolvido automaticamente da taxonomia."""
    from app.domains.job_creation.services.wsi_effectiveness_service import (
        WsiEffectivenessService,
    )
    svc = WsiEffectivenessService(db=AsyncMock())
    svc.repo = MagicMock()
    svc.repo.record_outcome = AsyncMock()

    await svc.record_question_outcome(
        company_id=fake_company,
        skill_probed="active_listening",
        outcome="hired",
        score=80.0,
        department="eng",
        seniority_level="sr",
    )
    svc.repo.record_outcome.assert_called_once()
    kwargs = svc.repo.record_outcome.call_args.kwargs
    assert kwargs["parent_id"] == "communication_collaboration"
    assert kwargs["company_id"] == fake_company


@pytest.mark.asyncio
async def test_record_outcome_fail_soft_on_repo_error(fake_company):
    """Erro no repo nao raise - log warning + continue."""
    from app.domains.job_creation.services.wsi_effectiveness_service import (
        WsiEffectivenessService,
    )
    svc = WsiEffectivenessService(db=AsyncMock())
    svc.repo = MagicMock()
    svc.repo.record_outcome = AsyncMock(side_effect=RuntimeError("DB down"))

    # Should NOT raise
    await svc.record_question_outcome(
        company_id=fake_company,
        skill_probed="active_listening",
        outcome="hired",
        score=80.0,
    )
