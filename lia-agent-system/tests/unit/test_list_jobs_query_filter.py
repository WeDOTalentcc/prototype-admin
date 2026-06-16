"""
Tests for list_jobs title_query filter (2026-06-09).
Verifies: query param accepted, passed to repo, schema includes query field.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_list_jobs_accepts_query_param():
    """_wrap_list_jobs reads kwargs.query and passes to repo as title_query."""
    mock_repo = AsyncMock()
    mock_repo.list_jobs_with_candidate_count.return_value = {
        "jobs": [{"id": "abc", "title": "Diretor Juridico", "status": "Ativa",
                  "priority": "alta", "department": "Legal", "location": "SP",
                  "candidate_count": 24, "days_open": 60, "deadline": None}],
        "total": 1,
    }
    mock_repo.count_by_status.return_value = {}

    with patch("app.domains.recruiter_assistant.agents.jobs_mgmt_tool_registry.AsyncSessionLocal") as mock_ctx:
        mock_session = AsyncMock()
        mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.return_value.__aexit__ = AsyncMock(return_value=None)
        with patch(
            "app.domains.recruiter_assistant.agents.jobs_mgmt_tool_registry.JobVacancyCrudRepository",
            return_value=mock_repo,
        ):
            from app.domains.recruiter_assistant.agents.jobs_mgmt_tool_registry import _wrap_list_jobs

            await _wrap_list_jobs(
                company_id="co-1",
                query="Diretor Juridico",
            )

    mock_repo.list_jobs_with_candidate_count.assert_called_once()
    call_kwargs = mock_repo.list_jobs_with_candidate_count.call_args[1]
    assert call_kwargs.get("title_query") == "Diretor Juridico"


@pytest.mark.asyncio
async def test_list_jobs_no_query_uses_default():
    """Without query param, title_query=None passed (no filter)."""
    mock_repo = AsyncMock()
    mock_repo.list_jobs_with_candidate_count.return_value = {"jobs": [], "total": 0}
    mock_repo.count_by_status.return_value = {}

    with patch("app.domains.recruiter_assistant.agents.jobs_mgmt_tool_registry.AsyncSessionLocal") as mock_ctx:
        mock_session = AsyncMock()
        mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.return_value.__aexit__ = AsyncMock(return_value=None)
        with patch(
            "app.domains.recruiter_assistant.agents.jobs_mgmt_tool_registry.JobVacancyCrudRepository",
            return_value=mock_repo,
        ):
            from app.domains.recruiter_assistant.agents.jobs_mgmt_tool_registry import _wrap_list_jobs

            await _wrap_list_jobs(company_id="co-1")

    call_kwargs = mock_repo.list_jobs_with_candidate_count.call_args[1]
    assert call_kwargs.get("title_query") is None


def test_list_jobs_schema_has_query_param():
    """Tool schema must declare query parameter so LLM can use it."""
    from app.domains.recruiter_assistant.agents.jobs_mgmt_tool_registry import TOOL_DEFINITIONS as TOOL_REGISTRY
    tool_def = next((t for t in TOOL_REGISTRY if t.name == "list_jobs"), None)
    assert tool_def is not None, "list_jobs not in TOOL_REGISTRY"
    props = tool_def.parameters.get("properties", {})
    assert "query" in props, f"query param missing from schema, got: {list(props.keys())}"
    assert "titulo" in props["query"]["description"].lower() or "title" in props["query"]["description"].lower()


def test_list_jobs_description_mentions_query():
    """Tool description should tell LLM to use query for vaga name searches."""
    from app.domains.recruiter_assistant.agents.jobs_mgmt_tool_registry import TOOL_DEFINITIONS as TOOL_REGISTRY
    tool_def = next((t for t in TOOL_REGISTRY if t.name == "list_jobs"), None)
    desc = tool_def.description if isinstance(tool_def.description, str) else " ".join(tool_def.description)
    assert "query" in desc.lower(), "description does not mention query param"
