"""
Contract tests for build_operational_config_context (Phase C 2026-06-22).

Validates that offer_rules and screening_config_defaults from
CompanyHiringPolicy are correctly formatted into the agent prompt fragment.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass, field
from datetime import datetime


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def mock_policy():
    p = MagicMock()
    p.offer_rules = {
        "allowed_start_day_of_month": [1, 15],
        "min_notice_days": 30,
        "negotiation_enabled": True,
        "salary_flex_pct_max": 15,
        "counter_proposal_max_rounds": 3,
        "negotiation_hitl_threshold_pct": 20,
    }
    p.screening_config_defaults = {
        "settings": {
            "min_score": 70,
            "response_timeout_hours": 48,
            "auto_approval_limit": 5,
        },
        "channels": {
            "whatsapp": {"enabled": True},
            "email": {"enabled": False},
            "sms": {"enabled": True},
        },
        "scheduling": {
            "auto_enabled": True,
            "min_score_for_auto": 80,
        },
    }
    return p


MOCK_REPO_PATH = "app.domains.hiring_policy.repositories.hiring_policy_repository.HiringPolicyRepository"


@pytest.mark.asyncio
async def test_returns_empty_when_no_company_id(mock_db):
    from app.shared.services.lia_agent_context_builder import build_operational_config_context
    result = await build_operational_config_context("", mock_db)
    assert result == ""


@pytest.mark.asyncio
async def test_returns_empty_when_no_policy(mock_db):
    with patch(MOCK_REPO_PATH) as MockRepo:
        MockRepo.return_value.get_by_company = AsyncMock(return_value=None)
        from app.shared.services.lia_agent_context_builder import build_operational_config_context
        result = await build_operational_config_context("comp-123", mock_db)
    assert result == ""


@pytest.mark.asyncio
async def test_includes_offer_rules_fields(mock_db, mock_policy):
    with patch(MOCK_REPO_PATH) as MockRepo:
        MockRepo.return_value.get_by_company = AsyncMock(return_value=mock_policy)
        from app.shared.services.lia_agent_context_builder import build_operational_config_context
        result = await build_operational_config_context("comp-123", mock_db)

    assert "Regras de Contratação" in result
    assert "[1, 15]" in result
    assert "30 dias" in result
    assert "habilitada" in result
    assert "15%" in result


@pytest.mark.asyncio
async def test_includes_screening_defaults_fields(mock_db, mock_policy):
    with patch(MOCK_REPO_PATH) as MockRepo:
        MockRepo.return_value.get_by_company = AsyncMock(return_value=mock_policy)
        from app.shared.services.lia_agent_context_builder import build_operational_config_context
        result = await build_operational_config_context("comp-123", mock_db)

    assert "Configuração Padrão de Triagem" in result
    assert "70" in result
    assert "48h" in result
    assert "whatsapp" in result
    assert "sms" in result
    assert "sim" in result
    assert "80" in result


@pytest.mark.asyncio
async def test_empty_offer_rules_no_section(mock_db, mock_policy):
    mock_policy.offer_rules = {}
    mock_policy.screening_config_defaults = {}
    with patch(MOCK_REPO_PATH) as MockRepo:
        MockRepo.return_value.get_by_company = AsyncMock(return_value=mock_policy)
        from app.shared.services.lia_agent_context_builder import build_operational_config_context
        result = await build_operational_config_context("comp-123", mock_db)

    assert "Regras de Contratação" not in result
    assert "Configuração Padrão de Triagem" not in result


@pytest.mark.asyncio
async def test_negotiation_disabled_text(mock_db, mock_policy):
    mock_policy.offer_rules["negotiation_enabled"] = False
    with patch(MOCK_REPO_PATH) as MockRepo:
        MockRepo.return_value.get_by_company = AsyncMock(return_value=mock_policy)
        from app.shared.services.lia_agent_context_builder import build_operational_config_context
        result = await build_operational_config_context("comp-123", mock_db)

    assert "desabilitada" in result


@pytest.mark.asyncio
async def test_fail_open_on_exception(mock_db):
    with patch(MOCK_REPO_PATH) as MockRepo:
        MockRepo.return_value.get_by_company = AsyncMock(side_effect=Exception("DB down"))
        from app.shared.services.lia_agent_context_builder import build_operational_config_context
        result = await build_operational_config_context("comp-123", mock_db)

    assert result == ""


@pytest.mark.asyncio
async def test_aggregated_context_includes_operational_config():
    """Validate AggregatedContext.to_prompt_context appends operational_config_prompt."""
    from app.domains.ai.services.context_aggregator_service import (
        AggregatedContext, CompanyContext, HistoricalContext, SessionContext,
    )

    ctx = AggregatedContext(
        company=CompanyContext(id="c1", name="Test Corp"),
        historical=HistoricalContext(),
        session=SessionContext(session_id="test-session"),
        operational_config_prompt="## Regras de Contratacao\n- Aviso previo: 30 dias",
    )
    prompt = ctx.to_prompt_context()
    assert "Regras de Contratacao" in prompt
    assert "30 dias" in prompt
