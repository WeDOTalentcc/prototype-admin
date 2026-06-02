import pytest
from datetime import datetime, timedelta

from app.shared.execution.execution_plan import (
    ExecutionPlan, AgentTask, TaskStatus, PlanStatus
)
from app.shared.execution.plan_detector import PlanDetector, PLAN_PATTERNS
from app.shared.execution.plan_executor import PlanExecutor
from app.domains.base import DomainResponse


class TestAgentTask:
    def test_create_task(self):
        task = AgentTask(task_id="t1", domain_id="sourcing", action_id="search")
        assert task.task_id == "t1"
        assert task.domain_id == "sourcing"
        assert task.action_id == "search"
        assert task.status == TaskStatus.PENDING

    def test_is_done_completed(self):
        task = AgentTask(task_id="t1", domain_id="d", action_id="a", status=TaskStatus.COMPLETED)
        assert task.is_done is True

    def test_is_done_failed(self):
        task = AgentTask(task_id="t1", domain_id="d", action_id="a", status=TaskStatus.FAILED)
        assert task.is_done is True

    def test_is_done_skipped(self):
        task = AgentTask(task_id="t1", domain_id="d", action_id="a", status=TaskStatus.SKIPPED)
        assert task.is_done is True

    def test_is_done_pending(self):
        task = AgentTask(task_id="t1", domain_id="d", action_id="a", status=TaskStatus.PENDING)
        assert task.is_done is False

    def test_is_done_running(self):
        task = AgentTask(task_id="t1", domain_id="d", action_id="a", status=TaskStatus.RUNNING)
        assert task.is_done is False

    def test_duration_ms(self):
        now = datetime.utcnow()
        task = AgentTask(
            task_id="t1", domain_id="d", action_id="a",
            started_at=now, completed_at=now + timedelta(milliseconds=500)
        )
        assert task.duration_ms is not None
        assert abs(task.duration_ms - 500) < 10

    def test_duration_ms_none(self):
        task = AgentTask(task_id="t1", domain_id="d", action_id="a")
        assert task.duration_ms is None

    def test_to_dict(self):
        task = AgentTask(task_id="t1", domain_id="sourcing", action_id="search",
                         depends_on=["t0"], is_critical=True)
        d = task.to_dict()
        assert d["task_id"] == "t1"
        assert d["domain_id"] == "sourcing"
        assert d["action_id"] == "search"
        assert d["depends_on"] == ["t0"]
        assert d["status"] == "pending"
        assert d["is_critical"] is True


class TestExecutionPlan:
    def test_create_empty_plan(self):
        plan = ExecutionPlan()
        assert len(plan.tasks) == 0
        assert plan.status == PlanStatus.PENDING

    def test_create_plan_with_id(self):
        plan = ExecutionPlan(plan_id="test123")
        assert plan.plan_id == "test123"

    def test_add_task(self):
        plan = ExecutionPlan()
        task = AgentTask(task_id="t0", domain_id="sourcing", action_id="search")
        plan.add_task(task)
        assert len(plan.tasks) == 1

    def test_get_task(self):
        plan = ExecutionPlan()
        task = AgentTask(task_id="t0", domain_id="sourcing", action_id="search")
        plan.add_task(task)
        found = plan.get_task("t0")
        assert found is not None
        assert found.task_id == "t0"

    def test_get_task_not_found(self):
        plan = ExecutionPlan()
        assert plan.get_task("nonexistent") is None

    def test_get_next_tasks_no_deps(self):
        plan = ExecutionPlan()
        t0 = AgentTask(task_id="t0", domain_id="d", action_id="a")
        t1 = AgentTask(task_id="t1", domain_id="d", action_id="b")
        plan.add_task(t0)
        plan.add_task(t1)
        ready = plan.get_next_tasks()
        assert len(ready) == 2

    def test_get_next_tasks_with_deps(self):
        plan = ExecutionPlan()
        t0 = AgentTask(task_id="t0", domain_id="d", action_id="a")
        t1 = AgentTask(task_id="t1", domain_id="d", action_id="b", depends_on=["t0"])
        plan.add_task(t0)
        plan.add_task(t1)
        ready = plan.get_next_tasks()
        assert len(ready) == 1
        assert ready[0].task_id == "t0"

    def test_get_next_tasks_after_completion(self):
        plan = ExecutionPlan()
        t0 = AgentTask(task_id="t0", domain_id="d", action_id="a", status=TaskStatus.COMPLETED)
        t1 = AgentTask(task_id="t1", domain_id="d", action_id="b", depends_on=["t0"])
        plan.add_task(t0)
        plan.add_task(t1)
        ready = plan.get_next_tasks()
        assert len(ready) == 1
        assert ready[0].task_id == "t1"

    def test_get_next_tasks_blocked(self):
        plan = ExecutionPlan()
        t0 = AgentTask(task_id="t0", domain_id="d", action_id="a", status=TaskStatus.FAILED)
        t1 = AgentTask(task_id="t1", domain_id="d", action_id="b", depends_on=["t0"])
        plan.add_task(t0)
        plan.add_task(t1)
        ready = plan.get_next_tasks()
        assert len(ready) == 0

    def test_update_task_result_success(self):
        plan = ExecutionPlan()
        task = AgentTask(task_id="t0", domain_id="d", action_id="a")
        plan.add_task(task)
        plan.update_task_result("t0", result={"data": "ok"}, success=True)
        assert task.status == TaskStatus.COMPLETED
        assert task.result == {"data": "ok"}

    def test_update_task_result_failure(self):
        plan = ExecutionPlan()
        task = AgentTask(task_id="t0", domain_id="d", action_id="a")
        plan.add_task(task)
        plan.update_task_result("t0", result=None, success=False, error="boom")
        assert task.status == TaskStatus.FAILED
        assert task.error == "boom"

    def test_inject_and_get_context(self):
        plan = ExecutionPlan()
        plan.inject_context("task_0.candidate_ids", [1, 2, 3])
        assert plan.get_context("task_0.candidate_ids") == [1, 2, 3]

    def test_get_context_default(self):
        plan = ExecutionPlan()
        assert plan.get_context("missing", "default") == "default"

    def test_is_complete_false(self):
        plan = ExecutionPlan()
        plan.add_task(AgentTask(task_id="t0", domain_id="d", action_id="a"))
        assert plan.is_complete is False

    def test_is_complete_true(self):
        plan = ExecutionPlan()
        plan.add_task(AgentTask(task_id="t0", domain_id="d", action_id="a", status=TaskStatus.COMPLETED))
        assert plan.is_complete is True

    def test_has_failures(self):
        plan = ExecutionPlan()
        plan.add_task(AgentTask(task_id="t0", domain_id="d", action_id="a", status=TaskStatus.FAILED))
        assert plan.has_failures is True

    def test_no_failures(self):
        plan = ExecutionPlan()
        plan.add_task(AgentTask(task_id="t0", domain_id="d", action_id="a", status=TaskStatus.COMPLETED))
        assert plan.has_failures is False

    def test_all_succeeded(self):
        plan = ExecutionPlan()
        plan.add_task(AgentTask(task_id="t0", domain_id="d", action_id="a", status=TaskStatus.COMPLETED))
        plan.add_task(AgentTask(task_id="t1", domain_id="d", action_id="b", status=TaskStatus.SKIPPED))
        assert plan.all_succeeded is True

    def test_all_succeeded_false(self):
        plan = ExecutionPlan()
        plan.add_task(AgentTask(task_id="t0", domain_id="d", action_id="a", status=TaskStatus.COMPLETED))
        plan.add_task(AgentTask(task_id="t1", domain_id="d", action_id="b", status=TaskStatus.FAILED))
        assert plan.all_succeeded is False

    def test_get_summary(self):
        plan = ExecutionPlan(plan_id="s1")
        plan.detected_pattern = "test"
        plan.add_task(AgentTask(task_id="t0", domain_id="d", action_id="a", status=TaskStatus.COMPLETED))
        plan.add_task(AgentTask(task_id="t1", domain_id="d", action_id="b", status=TaskStatus.FAILED))
        summary = plan.get_summary()
        assert summary["plan_id"] == "s1"
        assert summary["total_tasks"] == 2
        assert summary["completed"] == 1
        assert summary["failed"] == 1
        assert summary["detected_pattern"] == "test"

    def test_repr(self):
        plan = ExecutionPlan(plan_id="abc")
        assert "abc" in repr(plan)
        assert "pending" in repr(plan)


class TestPlanDetector:
    def setup_method(self):
        self.detector = PlanDetector()

    def test_buscar_e_comparar(self):
        plan = self.detector.detect("buscar candidatos python e comparar")
        assert plan is not None
        assert plan.detected_pattern == "buscar_e_comparar"
        assert len(plan.tasks) == 2

    def test_encontrar_e_comparar(self):
        plan = self.detector.detect("encontrar desenvolvedores e comparar")
        assert plan is not None
        assert plan.detected_pattern == "buscar_e_comparar"

    def test_pesquisar_e_comparar(self):
        plan = self.detector.detect("pesquisar candidatos react e comparar")
        assert plan is not None
        assert plan.detected_pattern == "buscar_e_comparar"

    def test_buscar_top_e_detalhar(self):
        plan = self.detector.detect("top 5 candidatos python e detalhar")
        assert plan is not None
        assert plan.detected_pattern == "buscar_top_e_detalhar"

    def test_gerar_jd_e_avaliar(self):
        plan = self.detector.detect("gerar a JD e avaliar candidatos")
        assert plan is not None
        assert plan.detected_pattern == "gerar_jd_e_avaliar"

    def test_gerar_descricao_e_triar(self):
        plan = self.detector.detect("gerar a descrição e triar candidatos")
        assert plan is not None
        assert plan.detected_pattern == "gerar_jd_e_avaliar"

    def test_triagem_e_agendar(self):
        plan = self.detector.detect("triar candidatos e agendar entrevista")
        assert plan is not None
        assert plan.detected_pattern == "triagem_e_agendar"

    def test_avaliar_e_notificar(self):
        plan = self.detector.detect("avaliar candidato e notificar resultado")
        assert plan is not None
        assert plan.detected_pattern == "avaliar_e_notificar"

    def test_filtrar_e_reportar(self):
        plan = self.detector.detect("filtrar candidatos e gerar relatório")
        assert plan is not None
        assert plan.detected_pattern == "filtrar_e_reportar"

    def test_criar_vaga_e_publicar_NUNCA_vira_plano(self):
        """Task #1211 (INVIOLÁVEL): criação de vaga é SEMPRE e SÓ o wizard
        canônico. O padrão `criar_vaga_e_publicar` (que tinha um step
        `create_job` proibido) foi removido — uma frase composta de criação
        NÃO pode produzir um ExecutionPlan, senão o Plan & Execute criaria a
        vaga fora do wizard. A continuidade pós-wizard é tratada pelo
        orchestrator (offer + confirmação), não por um plano de criação.
        """
        plan = self.detector.detect("criar vaga e publicar no ATS")
        assert plan is None, (
            "criação de vaga jamais pode virar plano — deve cair no wizard"
        )

    def test_analisar_e_planejar(self):
        plan = self.detector.detect("analisar funil e planejar ações")
        assert plan is not None
        assert plan.detected_pattern == "analisar_e_planejar"

    def test_agendar_e_lembrar(self):
        plan = self.detector.detect("agendar entrevista e enviar lembrete")
        assert plan is not None
        assert plan.detected_pattern == "agendar_e_lembrar"

    def test_mover_e_notificar(self):
        plan = self.detector.detect("mover candidato e notificar recrutador")
        assert plan is not None
        assert plan.detected_pattern == "mover_e_notificar"

    def test_buscar_e_triar(self):
        plan = self.detector.detect("buscar candidatos java e triar")
        assert plan is not None
        assert plan.detected_pattern == "buscar_e_triar"

    def test_relatorio_e_exportar(self):
        plan = self.detector.detect("gerar relatório e exportar em PDF")
        assert plan is not None
        assert plan.detected_pattern == "relatorio_e_exportar"

    def test_no_match_simple_query(self):
        plan = self.detector.detect("buscar candidatos python")
        assert plan is None

    def test_no_match_greeting(self):
        plan = self.detector.detect("olá, como vai?")
        assert plan is None

    def test_no_match_single_action(self):
        plan = self.detector.detect("criar uma vaga de desenvolvedor")
        assert plan is None

    def test_plan_has_correct_tasks(self):
        plan = self.detector.detect("buscar candidatos e comparar")
        assert plan is not None
        assert plan.tasks[0].domain_id == "sourcing"
        assert plan.tasks[0].action_id == "search_candidates"
        assert plan.tasks[1].domain_id == "sourcing"
        assert plan.tasks[1].action_id == "compare_candidates"

    def test_plan_has_dependencies(self):
        plan = self.detector.detect("buscar candidatos e comparar")
        assert plan is not None
        assert plan.tasks[0].depends_on == []
        assert plan.tasks[1].depends_on == ["task_0"]

    def test_plan_has_context_mappings(self):
        plan = self.detector.detect("buscar candidatos e comparar")
        assert plan is not None
        assert "candidate_ids" in plan.tasks[1].context_mappings

    def test_plan_original_query(self):
        query = "buscar candidatos e comparar"
        plan = self.detector.detect(query)
        assert plan is not None
        assert plan.original_query == query

    def test_stats_initial(self):
        stats = self.detector.get_stats()
        assert stats["total_detections"] == 0
        assert stats["total_matches"] == 0

    def test_stats_after_detections(self):
        self.detector.detect("buscar candidatos python e comparar")
        self.detector.detect("olá")
        stats = self.detector.get_stats()
        assert stats["total_detections"] == 2
        assert stats["total_matches"] == 1

    def test_list_patterns(self):
        # Task #1211: the catalog grows over time, so assert meaningful
        # properties instead of a brittle hard count.
        from app.shared.execution.plan_detector import PLAN_PATTERNS

        patterns = self.detector.list_patterns()
        assert len(patterns) == len(PLAN_PATTERNS)
        assert all("name" in p and "description" in p for p in patterns)
        names = [p["name"] for p in patterns]
        assert len(names) == len(set(names)), "pattern names must be unique"

    def test_no_plan_pattern_creates_a_job(self):
        """INVIOLABLE (Task #1211): Plan & Execute must NEVER create a job.

        Job creation is exclusively the canonical wizard. The removed
        'criar_vaga_e_publicar' pattern (step create_job) must not return.
        """
        from app.shared.execution.plan_detector import (
            JOB_CREATION_ACTION_IDS,
            PLAN_PATTERNS,
        )

        offenders = [
            f"{p.name} -> {s.domain_id}.{s.action_id}"
            for p in PLAN_PATTERNS
            for s in p.pipeline
            if s.action_id in JOB_CREATION_ACTION_IDS
        ]
        assert offenders == [], (
            "No plan pattern may create a job; found: " + "; ".join(offenders)
        )
        assert "criar_vaga_e_publicar" not in [p.name for p in PLAN_PATTERNS]

    def test_creation_guard_raises_on_forbidden_step(self):
        from app.shared.execution.plan_detector import (
            JobCreationInPlanError,
            PipelineStep,
            PlanPattern,
            _assert_no_creation_steps,
        )

        bad = [
            PlanPattern(
                name="bad",
                patterns=[r"x"],
                pipeline=[PipelineStep(domain_id="job_management", action_id="create_job")],
            )
        ]
        with pytest.raises(JobCreationInPlanError):
            _assert_no_creation_steps(bad)

    def test_case_insensitive(self):
        plan = self.detector.detect("BUSCAR candidatos Python E COMPARAR")
        assert plan is not None


class TestPlanExecutor:
    @pytest.fixture
    def executor(self):
        return PlanExecutor()

    @pytest.mark.asyncio
    async def test_execute_simple_plan(self, executor):
        plan = ExecutionPlan(plan_id="test1")
        plan.add_task(AgentTask(task_id="task_0", domain_id="sourcing", action_id="search"))
        plan.add_task(AgentTask(task_id="task_1", domain_id="sourcing", action_id="compare",
                                depends_on=["task_0"]))
        result = await executor.execute(plan)
        assert result.status in (PlanStatus.COMPLETED, PlanStatus.PARTIAL)
        assert result.is_complete

    @pytest.mark.asyncio
    async def test_execute_plan_all_complete(self, executor):
        plan = ExecutionPlan(plan_id="test2")
        plan.add_task(AgentTask(task_id="task_0", domain_id="d", action_id="a"))
        result = await executor.execute(plan)
        assert result.status == PlanStatus.COMPLETED
        assert result.all_succeeded

    @pytest.mark.asyncio
    async def test_execute_records_timing(self, executor):
        plan = ExecutionPlan()
        plan.add_task(AgentTask(task_id="task_0", domain_id="d", action_id="a"))
        result = await executor.execute(plan)
        assert result.completed_at is not None
        assert result.tasks[0].started_at is not None
        assert result.tasks[0].completed_at is not None

    @pytest.mark.asyncio
    async def test_execute_without_registry_uses_mock(self, executor):
        plan = ExecutionPlan()
        plan.add_task(AgentTask(task_id="task_0", domain_id="d", action_id="a"))
        result = await executor.execute(plan)
        assert result.tasks[0].status == TaskStatus.COMPLETED
        assert isinstance(result.tasks[0].result, DomainResponse)

    def test_build_consolidated_response_success(self, executor):
        plan = ExecutionPlan(plan_id="test")
        plan.detected_pattern = "buscar_e_comparar"
        plan.status = PlanStatus.COMPLETED
        t = AgentTask(task_id="t0", domain_id="sourcing", action_id="search",
                      status=TaskStatus.COMPLETED)
        t.result = DomainResponse.success_response(message="Found 5 candidates")
        plan.add_task(t)
        response = executor.build_consolidated_response(plan)
        assert response.success is True
        assert "buscar_e_comparar" in response.message

    def test_build_consolidated_response_failure(self, executor):
        plan = ExecutionPlan()
        plan.detected_pattern = "test"
        plan.status = PlanStatus.FAILED
        t = AgentTask(task_id="t0", domain_id="d", action_id="a",
                      status=TaskStatus.FAILED, error="something broke")
        plan.add_task(t)
        response = executor.build_consolidated_response(plan)
        assert response.success is False

    def test_resolve_context_path_from_context_data(self, executor):
        plan = ExecutionPlan()
        plan.inject_context("task_0.candidate_ids", [1, 2, 3])
        value = executor._resolve_context_path("task_0.candidate_ids", plan)
        assert value == [1, 2, 3]

    def test_resolve_context_path_from_task_result(self, executor):
        plan = ExecutionPlan()
        task = AgentTask(task_id="task_0", domain_id="d", action_id="a",
                         status=TaskStatus.COMPLETED)
        task.result = DomainResponse.success_response(
            message="ok", data={"candidate_ids": [10, 20]}
        )
        plan.add_task(task)
        value = executor._resolve_context_path("task_0.candidate_ids", plan)
        assert value == [10, 20]

    def test_resolve_context_path_not_found(self, executor):
        plan = ExecutionPlan()
        value = executor._resolve_context_path("task_99.missing", plan)
        assert value is None

    def test_build_task_query(self, executor):
        task = AgentTask(task_id="t0", domain_id="sourcing", action_id="search_candidates")
        query = executor._build_task_query(task, {"skill": "python", "limit": 5})
        assert "search candidates" in query
        assert "python" in query

    def test_build_task_query_large_list(self, executor):
        task = AgentTask(task_id="t0", domain_id="d", action_id="test")
        query = executor._build_task_query(task, {"ids": [1, 2, 3, 4, 5]})
        assert "5 itens" in query

    def test_mark_remaining_as_blocked_critical(self, executor):
        plan = ExecutionPlan()
        t0 = AgentTask(task_id="t0", domain_id="d", action_id="a", status=TaskStatus.FAILED)
        t1 = AgentTask(task_id="t1", domain_id="d", action_id="b", depends_on=["t0"], is_critical=True)
        plan.add_task(t0)
        plan.add_task(t1)
        executor._mark_remaining_as_blocked(plan, "t0")
        assert t1.status == TaskStatus.FAILED

    def test_mark_remaining_as_blocked_non_critical(self, executor):
        plan = ExecutionPlan()
        t0 = AgentTask(task_id="t0", domain_id="d", action_id="a", status=TaskStatus.FAILED)
        t1 = AgentTask(task_id="t1", domain_id="d", action_id="b", depends_on=["t0"], is_critical=False)
        plan.add_task(t0)
        plan.add_task(t1)
        executor._mark_remaining_as_blocked(plan, "t0")
        assert t1.status == TaskStatus.SKIPPED

    @pytest.mark.asyncio
    async def test_plan_summary_after_execution(self, executor):
        plan = ExecutionPlan(plan_id="sum_test")
        plan.detected_pattern = "test_pattern"
        plan.add_task(AgentTask(task_id="task_0", domain_id="d", action_id="a"))
        plan.add_task(AgentTask(task_id="task_1", domain_id="d", action_id="b",
                                depends_on=["task_0"]))
        result = await executor.execute(plan)
        summary = result.get_summary()
        assert summary["total_tasks"] == 2
        assert summary["completed"] == 2
        assert summary["detected_pattern"] == "test_pattern"
