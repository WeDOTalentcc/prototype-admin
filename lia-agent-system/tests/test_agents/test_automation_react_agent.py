"""
Tests for AutomationReActAgent and CVScreeningBatchService (Sprint 5).

Covers:
- AutomationReActAgent instantiation and metadata
- Tool registry: all tools callable
- decompose_task and prioritize_tasks direct methods (API shim)
- CVScreeningBatchService.run_batch happy path and empty/error cases
"""
import pytest
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


# ---------------------------------------------------------------------------
# Section 1: AutomationReActAgent structure
# ---------------------------------------------------------------------------

class TestAutomationReActAgentStructure:

    def test_agent_importable(self):
        from app.domains.automation.agents.automation_react_agent import AutomationReActAgent
        assert AutomationReActAgent is not None

    def test_agent_instantiates(self):
        from app.domains.automation.agents.automation_react_agent import AutomationReActAgent
        agent = AutomationReActAgent()
        assert agent.domain_name == "automation"

    def test_agent_has_all_tools(self):
        from app.domains.automation.agents.automation_react_agent import AutomationReActAgent
        agent = AutomationReActAgent()
        expected = {
            "decompose_task",
            "prioritize_tasks",
            "get_execution_plan",
            "build_dag",
            "check_dependencies",
            "get_next_tasks",
        }
        assert expected.issubset(set(agent.available_tools))

    def test_agent_has_decompose_method(self):
        from app.domains.automation.agents.automation_react_agent import AutomationReActAgent
        agent = AutomationReActAgent()
        assert callable(agent.decompose_task)

    def test_agent_has_prioritize_method(self):
        from app.domains.automation.agents.automation_react_agent import AutomationReActAgent
        agent = AutomationReActAgent()
        assert callable(agent.prioritize_tasks)


# ---------------------------------------------------------------------------
# Section 2: Tool registry
# ---------------------------------------------------------------------------

class TestAutomationToolRegistry:

    def test_get_automation_tools_returns_six(self):
        from app.domains.automation.agents.automation_tool_registry import get_automation_tools
        tools = get_automation_tools()
        assert len(tools) == 6

    def test_all_tool_functions_are_callable(self):
        from app.domains.automation.agents.automation_tool_registry import get_automation_tools
        for tool in get_automation_tools():
            assert callable(tool.function), f"Tool '{tool.name}' function is not callable"

    def test_tool_names_are_unique(self):
        from app.domains.automation.agents.automation_tool_registry import get_automation_tools
        names = [t.name for t in get_automation_tools()]
        assert len(names) == len(set(names))

    def test_get_stage_tools_decompose(self):
        from app.domains.automation.agents.automation_tool_registry import get_stage_tools
        tools = get_stage_tools("decompose")
        names = {t.name for t in tools}
        assert "decompose_task" in names

    def test_get_stage_tools_plan(self):
        from app.domains.automation.agents.automation_tool_registry import get_stage_tools
        tools = get_stage_tools("plan")
        names = {t.name for t in tools}
        assert "get_execution_plan" in names
        assert "build_dag" in names


# ---------------------------------------------------------------------------
# Section 3: Stage context
# ---------------------------------------------------------------------------

class TestAutomationStageContext:

    def test_all_stages_defined(self):
        from app.domains.automation.agents.automation_stage_context import STAGE_DEFINITIONS
        assert "decompose" in STAGE_DEFINITIONS
        assert "prioritize" in STAGE_DEFINITIONS
        assert "plan" in STAGE_DEFINITIONS
        assert "execute" in STAGE_DEFINITIONS

    def test_get_stage_context_returns_dict(self):
        from app.domains.automation.agents.automation_stage_context import get_stage_context
        ctx = get_stage_context("decompose")
        assert "description" in ctx
        assert "tools" in ctx

    def test_get_stage_tools_returns_list(self):
        from app.domains.automation.agents.automation_stage_context import get_stage_tools
        tools = get_stage_tools("plan")
        assert isinstance(tools, list)
        assert len(tools) > 0

    def test_get_transition_prompt_returns_string(self):
        from app.domains.automation.agents.automation_stage_context import get_transition_prompt
        prompt = get_transition_prompt("decompose", "prioritize")
        assert isinstance(prompt, str)
        assert len(prompt) > 0


# ---------------------------------------------------------------------------
# Section 4: decompose_task shim (mocked LLM + DB)
# ---------------------------------------------------------------------------

class TestAutomationDecomposeShim:

    @pytest.mark.asyncio
    async def test_decompose_task_missing_description_returns_error(self):
        from app.domains.automation.agents.automation_react_agent import AutomationReActAgent
        agent = AutomationReActAgent()
        result = await agent.decompose_task(task_description="")
        assert result["success"] is False
        assert "task_description" in result["message"].lower() or "obrigatório" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_decompose_task_calls_wrap_function(self):
        from app.domains.automation.agents.automation_react_agent import AutomationReActAgent

        mock_result = {
            "success": True,
            "subtasks_created": 3,
            "subtasks": [],
            "dag": {},
            "parallel_opportunities": [],
        }

        # _wrap_decompose_task is lazy-imported inside the method body; patch its source module
        with patch(
            "app.domains.automation.agents.automation_tool_registry._wrap_decompose_task",
            AsyncMock(return_value=mock_result),
        ):
            agent = AutomationReActAgent()
            result = await agent.decompose_task(
                task_description="Recrutar 5 engenheiros sênior",
                company_id="company-1",
            )

        assert result["success"] is True
        assert result["subtasks_created"] == 3


# ---------------------------------------------------------------------------
# Section 5: prioritize_tasks shim (mocked DB)
# ---------------------------------------------------------------------------

class TestAutomationPrioritizeShim:

    @pytest.mark.asyncio
    async def test_prioritize_tasks_no_ids_returns_error(self):
        """No task_ids and no goal_id → _wrap_prioritize_tasks returns error dict."""
        from app.domains.automation.agents.automation_tool_registry import _wrap_prioritize_tasks

        # Both PlannedTaskService and AsyncSessionLocal are lazy-imported inside the function.
        # Patch them at their source modules so the function can import them.
        mock_db_ctx = MagicMock()
        mock_db_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_db_ctx.__aexit__ = AsyncMock(return_value=False)

        mock_svc = MagicMock()
        mock_svc.get_tasks_by_goal = AsyncMock(return_value=[])

        with patch("app.domains.automation.services.planned_task_service.PlannedTaskService", return_value=mock_svc), \
             patch("app.core.database.AsyncSessionLocal", return_value=mock_db_ctx):
            result = await _wrap_prioritize_tasks(task_ids=[], goal_id=None)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_prioritize_tasks_calls_service(self):
        from app.domains.automation.agents.automation_react_agent import AutomationReActAgent

        mock_result = {
            "success": True,
            "prioritized_count": 2,
            "tasks": [
                {"id": "t1", "title": "Task 1", "priority": "high", "priority_score": 0.9, "status": "pending"},
                {"id": "t2", "title": "Task 2", "priority": "medium", "priority_score": 0.6, "status": "pending"},
            ],
        }

        # _wrap_prioritize_tasks is lazy-imported inside prioritize_tasks(); patch the source
        with patch(
            "app.domains.automation.agents.automation_tool_registry._wrap_prioritize_tasks",
            AsyncMock(return_value=mock_result),
        ):
            agent = AutomationReActAgent()
            result = await agent.prioritize_tasks(task_ids=["t1", "t2"])

        assert result["success"] is True
        assert result["prioritized_count"] == 2


# ---------------------------------------------------------------------------
# Section 6: CVScreeningBatchService
# ---------------------------------------------------------------------------

class TestCVScreeningBatchService:

    def test_service_importable(self):
        from app.domains.cv_screening.services.cv_screening_batch_service import run_batch
        assert callable(run_batch)

    @pytest.mark.asyncio
    async def test_run_batch_no_requirements_returns_empty(self):
        """When no job requirements exist, return empty result without crashing."""
        from app.domains.cv_screening.services.cv_screening_batch_service import run_batch

        with patch(
            "app.domains.cv_screening.services.cv_screening_batch_service._get_job_requirements",
            AsyncMock(return_value=[]),
        ):
            result = await run_batch(
                candidate_ids=["c1", "c2"],
                job_id="job-1",
                company_id="company-1",
            )

        assert result["processed"] == 0
        assert result["approved"] == 0
        assert result["ranking"] == []

    @pytest.mark.asyncio
    async def test_run_batch_no_candidates_found_returns_empty(self):
        """When all candidate_ids are invalid, return empty result."""
        from app.domains.cv_screening.services.cv_screening_batch_service import run_batch
        from app.schemas.rubric import JobRequirementCreate, RequirementPriorityEnum

        fake_req = MagicMock(spec=JobRequirementCreate)

        with patch(
            "app.domains.cv_screening.services.cv_screening_batch_service._get_job_requirements",
            AsyncMock(return_value=[fake_req]),
        ), patch(
            "app.domains.cv_screening.services.cv_screening_batch_service._get_job_title",
            AsyncMock(return_value="Engenheiro"),
        ), patch(
            "app.domains.cv_screening.services.cv_screening_batch_service._get_candidate_data",
            AsyncMock(return_value=None),
        ):
            result = await run_batch(
                candidate_ids=["bad-id"],
                job_id="job-1",
                company_id="company-1",
            )

        assert result["processed"] == 0

    @pytest.mark.asyncio
    async def test_run_batch_happy_path_returns_ranking(self):
        """Full happy path: 2 candidates evaluated and ranked."""
        from app.domains.cv_screening.services.cv_screening_batch_service import run_batch
        from app.schemas.rubric import JobRequirementCreate, RequirementPriorityEnum

        fake_req = MagicMock(spec=JobRequirementCreate)

        candidate_a = {"id": "c1", "name": "Alice", "technical_skills": ["Python"]}
        candidate_b = {"id": "c2", "name": "Bob", "technical_skills": ["Java"]}

        eval_result_a = MagicMock()
        eval_result_a.score = 80.0
        eval_result_a.strengths = ["Python forte"]
        eval_result_a.concerns = []

        eval_result_b = MagicMock()
        eval_result_b.score = 55.0
        eval_result_b.strengths = ["Experiência Java"]
        eval_result_b.concerns = ["Sem Python"]

        with patch(
            "app.domains.cv_screening.services.cv_screening_batch_service._get_job_requirements",
            AsyncMock(return_value=[fake_req]),
        ), patch(
            "app.domains.cv_screening.services.cv_screening_batch_service._get_job_title",
            AsyncMock(return_value="Dev Backend"),
        ), patch(
            "app.domains.cv_screening.services.cv_screening_batch_service._get_candidate_data",
            AsyncMock(side_effect=lambda cid, db: candidate_a if cid == "c1" else candidate_b),
        ), patch(
            "app.domains.cv_screening.services.cv_screening_batch_service.rubric_evaluation_service.evaluate_candidate",
            AsyncMock(side_effect=lambda candidate_data, requirements: eval_result_a if candidate_data["id"] == "c1" else eval_result_b),
        ):
            result = await run_batch(
                candidate_ids=["c1", "c2"],
                job_id="job-1",
                company_id="company-1",
            )

        assert result["processed"] == 2
        assert result["approved"] == 1   # Alice: 80 >= 75
        assert result["review"] == 1     # Bob: 55 >= 55
        assert result["rejected"] == 0
        assert result["ranking"][0]["candidate_id"] == "c1"  # Alice ranked first
        assert result["ranking"][0]["rank"] == 1
        assert result["ranking"][0]["status"] == "Aprovado"
        assert result["ranking"][1]["status"] == "Revisão"

    @pytest.mark.asyncio
    async def test_run_batch_partial_failure_handled(self):
        """When one candidate evaluation fails, others still succeed."""
        from app.domains.cv_screening.services.cv_screening_batch_service import run_batch

        fake_req = MagicMock()
        candidate_a = {"id": "c1", "name": "Alice"}
        candidate_b = {"id": "c2", "name": "Bob"}

        eval_ok = MagicMock()
        eval_ok.score = 90.0
        eval_ok.strengths = []
        eval_ok.concerns = []

        async def mock_evaluate(candidate_data, requirements):
            if candidate_data["id"] == "c1":
                return eval_ok
            raise RuntimeError("Evaluation service unavailable")

        with patch(
            "app.domains.cv_screening.services.cv_screening_batch_service._get_job_requirements",
            AsyncMock(return_value=[fake_req]),
        ), patch(
            "app.domains.cv_screening.services.cv_screening_batch_service._get_job_title",
            AsyncMock(return_value="Vaga"),
        ), patch(
            "app.domains.cv_screening.services.cv_screening_batch_service._get_candidate_data",
            AsyncMock(side_effect=lambda cid, db: candidate_a if cid == "c1" else candidate_b),
        ), patch(
            "app.domains.cv_screening.services.cv_screening_batch_service.rubric_evaluation_service.evaluate_candidate",
            AsyncMock(side_effect=mock_evaluate),
        ):
            result = await run_batch(
                candidate_ids=["c1", "c2"],
                job_id="job-1",
                company_id="company-1",
            )

        assert result["processed"] == 1  # Only c1 succeeded
        assert result["failed"] == 1
        assert result["ranking"][0]["candidate_id"] == "c1"
