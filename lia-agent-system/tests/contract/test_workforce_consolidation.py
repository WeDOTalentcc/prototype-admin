"""
Test Workforce consolidation — Sistema C -> B redirect.
P2 Audit 2026-05-24: _import_workforce_plan_impl deve criar PlannedHeadcount
em Sistema B alem de escrever em additional_data (Sistema C).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_import_workforce_plan_creates_planned_headcounts():
    """Ao receber plan_data, criar PlannedHeadcount records no Sistema B."""
    mock_wf_repo = MagicMock()
    mock_wf_repo.list_hiring_plans = AsyncMock(return_value=[])
    mock_plan = MagicMock()
    mock_plan.id = "plan-uuid-123"
    mock_wf_repo.create_hiring_plan = AsyncMock(return_value=mock_plan)
    mock_wf_repo.create_headcount = AsyncMock(return_value=MagicMock())

    mock_cp_repo = MagicMock()
    mock_cp_repo.get_workforce_plan = AsyncMock(return_value=None)
    mock_cp_repo.upsert_workforce_plan = AsyncMock()

    plan_data = [
        {"department": "Engenharia", "role": "Dev Backend", "quantity": 2, "deadline": "2026-09-01", "seniority": "Pleno"},
        {"department": "Produto", "role": "Product Manager", "quantity": 1},
    ]

    with patch(
        "app.domains.company_settings.agents.company_tool_registry.WorkforceRepository",
        return_value=mock_wf_repo,
    ), patch(
        "app.domains.company_settings.agents.company_tool_registry.CompanyProfileRepository",
        return_value=mock_cp_repo,
    ):
        from app.domains.company_settings.agents.company_tool_registry import _import_workforce_plan_impl
        result = await _import_workforce_plan_impl(
            session=AsyncMock(),
            company_id="test-company-uuid",
            plan_data=plan_data,
        )

    assert result["success"] is True
    # create_headcount called once per item
    assert mock_wf_repo.create_headcount.call_count == 2
    # Sistema C also preserved
    assert mock_cp_repo.upsert_workforce_plan.called
    # create_hiring_plan called because list returned empty
    assert mock_wf_repo.create_hiring_plan.called


@pytest.mark.asyncio
async def test_import_workforce_plan_uses_existing_hiring_plan():
    """Se ja existe HiringPlan para o ano, reutilizar em vez de criar novo."""
    mock_wf_repo = MagicMock()
    existing_plan = MagicMock()
    existing_plan.id = "existing-plan-uuid"
    mock_wf_repo.list_hiring_plans = AsyncMock(return_value=[existing_plan])
    mock_wf_repo.create_hiring_plan = AsyncMock()
    mock_wf_repo.create_headcount = AsyncMock(return_value=MagicMock())

    mock_cp_repo = MagicMock()
    mock_cp_repo.get_workforce_plan = AsyncMock(return_value=None)
    mock_cp_repo.upsert_workforce_plan = AsyncMock()

    with patch(
        "app.domains.company_settings.agents.company_tool_registry.WorkforceRepository",
        return_value=mock_wf_repo,
    ), patch(
        "app.domains.company_settings.agents.company_tool_registry.CompanyProfileRepository",
        return_value=mock_cp_repo,
    ):
        from app.domains.company_settings.agents.company_tool_registry import _import_workforce_plan_impl
        await _import_workforce_plan_impl(
            session=AsyncMock(),
            company_id="test-company-uuid",
            plan_data=[{"role": "Dev", "quantity": 1}],
        )

    # Must NOT create new plan when one already exists
    mock_wf_repo.create_hiring_plan.assert_not_called()
    # Must use existing plan
    mock_wf_repo.create_headcount.assert_called_once()
    # Verify the headcount_data passed includes the correct hiring_plan_id
    call_kwargs = mock_wf_repo.create_headcount.call_args
    headcount_data = call_kwargs.kwargs.get("headcount_data") or call_kwargs[1].get("headcount_data") or call_kwargs[0][0]
    assert headcount_data["hiring_plan_id"] == "existing-plan-uuid"


@pytest.mark.asyncio
async def test_import_workforce_plan_empty_data_returns_error():
    """plan_data vazio retorna success=False sem criar records."""
    with patch(
        "app.domains.company_settings.agents.company_tool_registry.WorkforceRepository",
    ) as mock_wf_class, patch(
        "app.domains.company_settings.agents.company_tool_registry.CompanyProfileRepository",
    ):
        from app.domains.company_settings.agents.company_tool_registry import _import_workforce_plan_impl
        result = await _import_workforce_plan_impl(
            session=AsyncMock(),
            company_id="test-company-uuid",
            plan_data=[],
        )

    assert result["success"] is False
    mock_wf_class.return_value.create_headcount.assert_not_called()


@pytest.mark.asyncio
async def test_import_workforce_plan_deadline_parsed_to_month_year():
    """deadline ISO string e mapeado corretamente para target_month/target_year."""
    mock_wf_repo = MagicMock()
    existing_plan = MagicMock()
    existing_plan.id = "plan-uuid"
    mock_wf_repo.list_hiring_plans = AsyncMock(return_value=[existing_plan])
    mock_wf_repo.create_headcount = AsyncMock(return_value=MagicMock())

    mock_cp_repo = MagicMock()
    mock_cp_repo.get_workforce_plan = AsyncMock(return_value=None)
    mock_cp_repo.upsert_workforce_plan = AsyncMock()

    with patch(
        "app.domains.company_settings.agents.company_tool_registry.WorkforceRepository",
        return_value=mock_wf_repo,
    ), patch(
        "app.domains.company_settings.agents.company_tool_registry.CompanyProfileRepository",
        return_value=mock_cp_repo,
    ):
        from app.domains.company_settings.agents.company_tool_registry import _import_workforce_plan_impl
        await _import_workforce_plan_impl(
            session=AsyncMock(),
            company_id="test-company-uuid",
            plan_data=[{"role": "Dev", "quantity": 1, "deadline": "2027-03-15"}],
        )

    call_kwargs = mock_wf_repo.create_headcount.call_args
    hc_data = call_kwargs.kwargs.get("headcount_data") or call_kwargs[1].get("headcount_data") or call_kwargs[0][0]
    assert hc_data["target_month"] == 3
    assert hc_data["target_year"] == 2027


@pytest.mark.asyncio
async def test_import_workforce_plan_sistema_b_failure_does_not_break_result():
    """Falha no Sistema B nao propaga erro — resultado ainda e success=True."""
    mock_wf_repo = MagicMock()
    mock_wf_repo.list_hiring_plans = AsyncMock(side_effect=Exception("DB connection error"))

    mock_cp_repo = MagicMock()
    mock_cp_repo.get_workforce_plan = AsyncMock(return_value=None)
    mock_cp_repo.upsert_workforce_plan = AsyncMock()

    with patch(
        "app.domains.company_settings.agents.company_tool_registry.WorkforceRepository",
        return_value=mock_wf_repo,
    ), patch(
        "app.domains.company_settings.agents.company_tool_registry.CompanyProfileRepository",
        return_value=mock_cp_repo,
    ):
        from app.domains.company_settings.agents.company_tool_registry import _import_workforce_plan_impl
        result = await _import_workforce_plan_impl(
            session=AsyncMock(),
            company_id="test-company-uuid",
            plan_data=[{"role": "Dev", "quantity": 1}],
        )

    # Sistema C committed OK, success should be True despite Sistema B failure
    assert result["success"] is True
    assert mock_cp_repo.upsert_workforce_plan.called
