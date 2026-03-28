import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestPipelineMonitor:

    def test_pipeline_event_type_enum(self):
        from app.domains.automation.services.pipeline_monitor import PipelineEventType
        assert PipelineEventType.CANDIDATE_STAGNANT == "candidate_stagnant"
        assert PipelineEventType.HIGH_SCORE_NO_ACTION == "high_score_no_action"
        assert PipelineEventType.DEADLINE_APPROACHING == "deadline_approaching"
        assert PipelineEventType.INTERVIEW_NO_FEEDBACK == "interview_no_feedback"
        assert PipelineEventType.REJECTION_PENDING_FEEDBACK == "rejection_pending_feedback"
        assert PipelineEventType.FUNNEL_WEAK == "funnel_weak"

    def test_pipeline_event_dataclass(self):
        from app.domains.automation.services.pipeline_monitor import PipelineEvent, PipelineEventType
        event = PipelineEvent(
            event_type=PipelineEventType.CANDIDATE_STAGNANT,
            company_id="comp-1",
            title="Test Event",
            message="Test message",
            severity="warning",
            data={"days": 10},
            suggested_action="advance_candidate",
            action_label="Avançar",
            candidate_id="cand-1",
            vacancy_id="vac-1",
        )
        assert event.event_type == PipelineEventType.CANDIDATE_STAGNANT
        assert event.company_id == "comp-1"
        assert event.severity == "warning"
        assert event.data["days"] == 10

    def test_pipeline_event_optional_fields(self):
        from app.domains.automation.services.pipeline_monitor import PipelineEvent, PipelineEventType
        event = PipelineEvent(
            event_type=PipelineEventType.FUNNEL_WEAK,
            company_id="comp-2",
            title="Weak Funnel",
            message="Only 1 candidate in advanced stages",
            severity="info",
            data={"advanced_count": 1},
            suggested_action="expand_sourcing",
            action_label="Ampliar Sourcing",
        )
        assert event.candidate_id is None
        assert event.vacancy_id is None
        assert event.created_at is not None

    def test_pipeline_monitor_init(self):
        from app.domains.automation.services.pipeline_monitor import PipelineMonitor
        monitor = PipelineMonitor()
        assert monitor is not None

    def test_pipeline_event_type_values_unique(self):
        from app.domains.automation.services.pipeline_monitor import PipelineEventType
        values = [e.value for e in PipelineEventType]
        assert len(values) == len(set(values))
        assert len(values) == 6


class TestRetryPolicy:
    def test_exponential_backoff_delays(self):
        from app.shared.execution.action_planner import RetryPolicy
        policy = RetryPolicy(max_retries=3, backoff_type="exponential", base_delay_seconds=1.0)
        assert policy.get_delay(1) == 1.0
        assert policy.get_delay(2) == 2.0
        assert policy.get_delay(3) == 4.0

    def test_linear_backoff_delays(self):
        from app.shared.execution.action_planner import RetryPolicy
        policy = RetryPolicy(max_retries=3, backoff_type="linear", base_delay_seconds=2.0)
        assert policy.get_delay(1) == 2.0
        assert policy.get_delay(2) == 4.0
        assert policy.get_delay(3) == 6.0

    def test_fixed_backoff_delays(self):
        from app.shared.execution.action_planner import RetryPolicy
        policy = RetryPolicy(max_retries=3, backoff_type="fixed", base_delay_seconds=5.0)
        assert policy.get_delay(1) == 5.0
        assert policy.get_delay(2) == 5.0

    def test_max_delay_cap(self):
        from app.shared.execution.action_planner import RetryPolicy
        policy = RetryPolicy(max_retries=10, backoff_type="exponential", base_delay_seconds=1.0, max_delay_seconds=10.0)
        assert policy.get_delay(10) == 10.0

    def test_default_values(self):
        from app.shared.execution.action_planner import RetryPolicy
        policy = RetryPolicy()
        assert policy.max_retries == 2
        assert policy.backoff_type == "exponential"
        assert policy.base_delay_seconds == 1.0
        assert policy.max_delay_seconds == 30.0


class TestActionPlanner:
    def test_action_planner_init(self):
        from app.shared.execution.action_planner import ActionPlanner
        planner = ActionPlanner()
        assert planner is not None
        assert planner.retry_policy.max_retries == 2

    def test_set_retry_policy(self):
        from app.shared.execution.action_planner import ActionPlanner, RetryPolicy
        planner = ActionPlanner()
        policy = RetryPolicy(max_retries=5, backoff_type="linear")
        planner.set_retry_policy(policy)
        assert planner.retry_policy.max_retries == 5

    def test_add_rollback_hook(self):
        from app.shared.execution.action_planner import ActionPlanner, RollbackHook
        planner = ActionPlanner()
        hook = RollbackHook(task_id="task-1", action_id="undo-1", domain_id="test", description="Rollback test")
        planner.add_rollback_hook(hook)
        assert "task-1" in planner.rollback_hooks

    def test_multiple_rollback_hooks(self):
        from app.shared.execution.action_planner import ActionPlanner, RollbackHook
        planner = ActionPlanner()
        hook1 = RollbackHook(task_id="task-1", action_id="undo-1", domain_id="test", description="Rollback 1")
        hook2 = RollbackHook(task_id="task-2", action_id="undo-2", domain_id="test", description="Rollback 2")
        planner.add_rollback_hook(hook1)
        planner.add_rollback_hook(hook2)
        assert len(planner.rollback_hooks) == 2

    def test_rollback_hook_dataclass(self):
        from app.shared.execution.action_planner import RollbackHook
        hook = RollbackHook(task_id="t1", action_id="a1", domain_id="d1", description="desc")
        assert hook.task_id == "t1"
        assert hook.action_id == "a1"
        assert hook.domain_id == "d1"
        assert hook.description == "desc"
        assert hook.params == {}

    def test_init_with_empty_rollbacks(self):
        from app.shared.execution.action_planner import ActionPlanner
        planner = ActionPlanner()
        assert len(planner.rollback_hooks) == 0
        assert len(planner._executed_rollbacks) == 0


class TestPlanTemplateRegistry:
    def test_list_templates(self):
        from app.shared.execution.plan_templates import PlanTemplateRegistry
        names = PlanTemplateRegistry.get_template_names()
        assert "schedule_interviews_batch" in names
        assert "batch_rejection_feedback" in names
        assert "advance_top_candidates" in names
        assert "sourcing_expansion" in names

    def test_get_template(self):
        from app.shared.execution.plan_templates import PlanTemplateRegistry
        template = PlanTemplateRegistry.get_template("schedule_interviews_batch")
        assert template is not None
        assert "steps" in template
        assert "retry_policy" in template
        assert template["name"] == "Agendar Entrevistas em Lote"

    def test_build_plan(self):
        from app.shared.execution.plan_templates import PlanTemplateRegistry
        plan = PlanTemplateRegistry.build_plan("batch_rejection_feedback", params={"company_id": "test"})
        assert plan is not None
        assert len(plan.tasks) == 4

    def test_build_planner(self):
        from app.shared.execution.plan_templates import PlanTemplateRegistry
        planner = PlanTemplateRegistry.build_planner("advance_top_candidates")
        assert planner is not None
        assert planner.retry_policy.max_retries == 1
        assert planner.retry_policy.backoff_type == "fixed"

    def test_invalid_template(self):
        from app.shared.execution.plan_templates import PlanTemplateRegistry
        result = PlanTemplateRegistry.build_plan("nonexistent")
        assert result is None

    def test_invalid_planner(self):
        from app.shared.execution.plan_templates import PlanTemplateRegistry
        result = PlanTemplateRegistry.build_planner("nonexistent")
        assert result is None

    def test_template_count(self):
        from app.shared.execution.plan_templates import PlanTemplateRegistry
        names = PlanTemplateRegistry.get_template_names()
        assert len(names) == 4

    def test_build_plan_with_params(self):
        from app.shared.execution.plan_templates import PlanTemplateRegistry
        plan = PlanTemplateRegistry.build_plan("sourcing_expansion", params={"company_id": "comp-x", "vacancy_id": "vac-1"})
        assert plan is not None
        for task in plan.tasks:
            assert task.params["company_id"] == "comp-x"
            assert task.params["vacancy_id"] == "vac-1"

    def test_build_plan_dependencies(self):
        from app.shared.execution.plan_templates import PlanTemplateRegistry
        plan = PlanTemplateRegistry.build_plan("schedule_interviews_batch", params={})
        assert plan is not None
        task_map = {t.task_id: t for t in plan.tasks}
        assert task_map["find_candidates"].depends_on == []
        assert "find_candidates" in task_map["check_availability"].depends_on
        assert "check_availability" in task_map["create_events"].depends_on


class TestPredictionActionBridge:
    def test_init(self):
        from app.domains.automation.services.prediction_action_bridge import PredictionActionBridge
        bridge = PredictionActionBridge()
        assert bridge is not None
        assert bridge.THRESHOLDS["high_success_score"] == 0.8

    def test_thresholds(self):
        from app.domains.automation.services.prediction_action_bridge import PredictionActionBridge
        bridge = PredictionActionBridge()
        assert bridge.THRESHOLDS["dropout_risk_score"] == 0.7
        assert bridge.THRESHOLDS["time_to_fill_risk_percent"] == 120
        assert bridge.THRESHOLDS["salary_mismatch_percent"] == 20

    def test_lazy_loading_none(self):
        from app.domains.automation.services.prediction_action_bridge import PredictionActionBridge
        bridge = PredictionActionBridge()
        assert bridge._outcome_predictor is None
        assert bridge._autonomous_service is None

    def test_threshold_keys(self):
        from app.domains.automation.services.prediction_action_bridge import PredictionActionBridge
        bridge = PredictionActionBridge()
        expected_keys = {"high_success_score", "dropout_risk_score", "time_to_fill_risk_percent", "salary_mismatch_percent"}
        assert set(bridge.THRESHOLDS.keys()) == expected_keys


class TestEventActionConnector:
    def test_init(self):
        from app.domains.automation.services.event_action_connector import EventActionConnector
        connector = EventActionConnector()
        assert connector is not None

    @pytest.mark.asyncio
    async def test_process_empty_events(self):
        from app.domains.automation.services.event_action_connector import EventActionConnector
        connector = EventActionConnector()
        stats = await connector.process_events([])
        assert stats["actions_created"] == 0
        assert stats["notifications_sent"] == 0
        assert stats["errors"] == 0

    def test_lazy_services_none(self):
        from app.domains.automation.services.event_action_connector import EventActionConnector
        connector = EventActionConnector()
        assert connector._alert_service is None
        assert connector._autonomous_service is None
        assert connector._notification_service is None

    def test_module_level_instance(self):
        from app.domains.automation.services.event_action_connector import event_action_connector
        assert event_action_connector is not None


class TestPhase3Integration:
    def test_imports(self):
        from app.domains.automation.services.pipeline_monitor import PipelineMonitor, PipelineEvent, PipelineEventType
        from app.shared.execution.action_planner import ActionPlanner, RetryPolicy, RollbackHook
        from app.shared.execution.plan_templates import PlanTemplateRegistry
        from app.domains.automation.services.prediction_action_bridge import PredictionActionBridge
        from app.domains.automation.services.event_action_connector import EventActionConnector
        assert True

    def test_event_to_action_mapping(self):
        from app.domains.automation.services.pipeline_monitor import PipelineEvent, PipelineEventType
        event = PipelineEvent(
            event_type=PipelineEventType.HIGH_SCORE_NO_ACTION,
            company_id="comp-1",
            title="Candidato com Score Alto",
            message="João tem score WSI 92 e está parado há 72h",
            severity="warning",
            data={"candidate_name": "João", "wsi_score": 92, "hours_stagnant": 72},
            suggested_action="schedule_interview",
            action_label="Agendar Entrevista",
            candidate_id="cand-1",
            vacancy_id="vac-1",
        )
        assert event.suggested_action == "schedule_interview"
        assert event.data["wsi_score"] == 92

    def test_plan_template_builds_valid_plan(self):
        from app.shared.execution.plan_templates import PlanTemplateRegistry
        from app.shared.execution.execution_plan import ExecutionPlan
        for name in PlanTemplateRegistry.get_template_names():
            plan = PlanTemplateRegistry.build_plan(name, params={"company_id": "test-comp"})
            assert plan is not None
            assert isinstance(plan, ExecutionPlan)
            assert len(plan.tasks) > 0
            for task in plan.tasks:
                assert task.domain_id != ""
                assert task.action_id != ""

    def test_all_plan_templates_have_retry_policies(self):
        from app.shared.execution.plan_templates import PlanTemplateRegistry
        for name in PlanTemplateRegistry.get_template_names():
            template = PlanTemplateRegistry.get_template(name)
            assert "retry_policy" in template
            assert "max_retries" in template["retry_policy"]

    def test_scheduler_has_pipeline_monitor_job(self):
        from app.domains.automation.services.automation_scheduler import AutomationScheduler
        scheduler = AutomationScheduler()
        assert hasattr(scheduler, 'run_pipeline_monitor')
        assert hasattr(scheduler, '_get_pipeline_monitor')

    def test_pipeline_event_all_severities(self):
        from app.domains.automation.services.pipeline_monitor import PipelineEvent, PipelineEventType
        for severity in ["urgent", "warning", "info"]:
            event = PipelineEvent(
                event_type=PipelineEventType.CANDIDATE_STAGNANT,
                company_id="comp-1",
                title="Test",
                message="Test",
                severity=severity,
                data={},
                suggested_action="test",
                action_label="Test",
            )
            assert event.severity == severity

    def test_planner_inherits_plan_executor(self):
        from app.shared.execution.action_planner import ActionPlanner
        from app.shared.execution.plan_executor import PlanExecutor
        planner = ActionPlanner()
        assert isinstance(planner, PlanExecutor)

    def test_bridge_module_singleton(self):
        from app.domains.automation.services.prediction_action_bridge import prediction_action_bridge
        assert prediction_action_bridge is not None
