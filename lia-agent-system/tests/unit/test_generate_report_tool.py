"""
P3-B — Testes: generate_report em todos os agentes

Cobre:
1. talent — retorna success=True com summary de applications
2. sourcing — retorna success=True com shortlisted/contacted
3. wizard — retorna success=True com drafts/published de job_vacancies
4. pipeline — retorna success=True com screening/interview/offer/hired
5. DB error → ainda retorna success=True com summary vazio
6. period inválido → defaults para 30 dias (month)
7. report_id único a cada chamada
8. STAGE_TOOLS: generate_report presente nos stages corretos
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ────────────────────────────── helpers ──────────────────────────────

def _make_db_row(data: dict):
    row = MagicMock()
    row.mappings.return_value.first.return_value = data
    return row


# ────────────────────────────── talent ──────────────────────────────

@pytest.mark.asyncio
async def test_talent_generate_report_success():
    from app.domains.recruiter_assistant.agents.talent_tool_registry import _wrap_generate_report

    mock_row = _make_db_row({"total": 100, "approved": 40, "rejected": 20})
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_row)
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch("app.domains.recruiter_assistant.agents.talent_tool_registry.AsyncSessionLocal", return_value=mock_ctx):
        result = await _wrap_generate_report(report_type="summary", period="month", company_id="c1")

    assert result["success"] is True
    assert result["data"]["summary"]["total_applications"] == 100
    assert result["data"]["summary"]["approved"] == 40
    assert "report_id" in result["data"]


@pytest.mark.asyncio
async def test_talent_generate_report_db_error_still_success():
    from app.domains.recruiter_assistant.agents.talent_tool_registry import _wrap_generate_report

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(side_effect=Exception("DB connection failed"))
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch("app.domains.recruiter_assistant.agents.talent_tool_registry.AsyncSessionLocal", return_value=mock_ctx):
        result = await _wrap_generate_report(company_id="c1")

    assert result["success"] is True
    assert result["data"]["summary"] == {}


# ────────────────────────────── sourcing ──────────────────────────────

@pytest.mark.asyncio
async def test_sourcing_generate_report_success():
    from app.domains.sourcing.agents.sourcing_tool_registry import _wrap_generate_report

    mock_row = _make_db_row({"total": 50, "shortlisted": 15, "contacted": 30})
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_row)
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch("app.domains.sourcing.agents.sourcing_tool_registry.AsyncSessionLocal", return_value=mock_ctx):
        result = await _wrap_generate_report(report_type="funnel", period="week", company_id="c2")

    assert result["success"] is True
    assert result["data"]["summary"]["shortlisted"] == 15
    assert result["data"]["period"] == "week"


# ────────────────────────────── wizard ──────────────────────────────

@pytest.mark.asyncio
async def test_wizard_generate_report_success():
    from app.domains.job_management.agents.wizard_tool_registry import _wrap_generate_report

    mock_row = _make_db_row({"total": 20, "drafts": 5, "published": 15})
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_row)
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch("app.domains.job_management.agents.wizard_tool_registry.AsyncSessionLocal", return_value=mock_ctx):
        result = await _wrap_generate_report(report_type="summary", period="quarter", company_id="c3")

    assert result["success"] is True
    assert result["data"]["summary"]["published"] == 15
    assert result["data"]["summary"]["drafts"] == 5


# ────────────────────────────── pipeline ──────────────────────────────

@pytest.mark.asyncio
async def test_pipeline_generate_report_success():
    from app.domains.cv_screening.agents.pipeline_tool_registry import _wrap_generate_report

    mock_row = _make_db_row({"total": 80, "screening": 30, "interview": 20, "offer": 10, "hired": 5})
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_row)
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch("app.domains.cv_screening.agents.pipeline_tool_registry.AsyncSessionLocal", return_value=mock_ctx):
        result = await _wrap_generate_report(report_type="funnel", period="month", company_id="c4")

    assert result["success"] is True
    assert result["data"]["summary"]["hired"] == 5
    assert result["data"]["summary"]["interview"] == 20


# ────────────────────────────── edge cases ──────────────────────────────

@pytest.mark.asyncio
async def test_invalid_period_defaults_to_30_days():
    """Período inválido usa 30 dias (month default)."""
    from app.domains.recruiter_assistant.agents.talent_tool_registry import _wrap_generate_report

    captured_params = {}

    async def fake_execute(query, params):
        captured_params.update(params)
        return _make_db_row({})

    mock_session = AsyncMock()
    mock_session.execute = fake_execute
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch("app.domains.recruiter_assistant.agents.talent_tool_registry.AsyncSessionLocal", return_value=mock_ctx):
        await _wrap_generate_report(period="invalid_period", company_id="c1")

    assert captured_params.get("days") == 30


@pytest.mark.asyncio
async def test_report_id_unique_per_call():
    """Cada chamada gera um report_id diferente."""
    from app.domains.recruiter_assistant.agents.talent_tool_registry import _wrap_generate_report

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=_make_db_row({}))
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch("app.domains.recruiter_assistant.agents.talent_tool_registry.AsyncSessionLocal", return_value=mock_ctx):
        r1 = await _wrap_generate_report(company_id="c1")
        r2 = await _wrap_generate_report(company_id="c1")

    assert r1["data"]["report_id"] != r2["data"]["report_id"]


# ────────────────────────────── STAGE_TOOLS ──────────────────────────────

def test_stage_tools_include_generate_report():
    """generate_report presente nos stages corretos de cada agente."""
    from app.domains.recruiter_assistant.agents.talent_tool_registry import STAGE_TOOLS as talent_stages
    from app.domains.sourcing.agents.sourcing_tool_registry import STAGE_TOOLS as sourcing_stages
    from app.domains.job_management.agents.wizard_tool_registry import STAGE_TOOLS as wizard_stages
    from app.domains.cv_screening.agents.pipeline_tool_registry import STAGE_TOOLS as pipeline_stages

    assert "generate_report" in talent_stages.get("action_planning", [])
    assert "generate_report" in sourcing_stages.get("shortlist-creation", [])
    assert "generate_report" in wizard_stages.get("review", [])
    assert "generate_report" in wizard_stages.get("publish", [])
    assert "generate_report" in pipeline_stages.get("offer", [])
    assert "generate_report" in pipeline_stages.get("hired", [])
