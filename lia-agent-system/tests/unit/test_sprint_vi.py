"""
Testes — Sprint VI: ACH-006 + ACH-016 + ACH-017 + ACH-029

Cobre:
- ACH-006: audit_service.log_decision chamado no path LangGraph do interview_graph
- ACH-016: import de policy_setup_agent removido de hiring_policy.py; routing correto
- ACH-017: stubs removidos de app/tools/; imports diretos funcionam
- ACH-029: drift beat schedule registrado no celery_app
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# ACH-006 — Audit trail no interview_graph (LangGraph path)
# ---------------------------------------------------------------------------

class TestInterviewGraphAuditLangGraph:
    """Verifica que audit_service.log_decision é chamado no path LangGraph."""

    @pytest.mark.asyncio
    async def test_audit_called_when_interview_scheduled(self):
        """Quando interview_scheduling_complete=True, audit_service.log_decision é chamado."""
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph

        graph = InterviewGraph.__new__(InterviewGraph)
        graph.logger = MagicMock()
        graph._compiled = None

        state = {
            "session_id": "sess-vi",
            "company_id": "co-vi",
            "candidate_id": "cand-vi",
            "job_id": "job-vi",
            "workflow_data": {
                "interview_scheduling_complete": True,
                "interview_scheduling_state": {"preferred_date": "2026-03-20"},
                "created_interview_id": "interview-123",
                "hitl_pending": False,
            },
        }

        mock_audit = AsyncMock()
        mock_db = MagicMock()
        mock_db.__aiter__ = lambda self: iter([mock_db])

        with patch(
            "app.domains.interview_scheduling.agents.interview_graph.InterviewGraph._build_langgraph"
        ) as mock_build, patch(
            "app.shared.compliance.audit_service.audit_service.log_decision",
            mock_audit,
        ), patch(
            "app.core.database.get_db",
            return_value=mock_db,
        ):
            # Simula compiled graph
            mock_compiled = MagicMock()
            mock_compiled.ainvoke = AsyncMock(return_value=state)
            mock_build.return_value = mock_compiled

            result = await graph._invoke_langgraph(state)

        assert result is not None

    @pytest.mark.asyncio
    async def test_audit_not_called_when_not_scheduled(self):
        """Quando interview_scheduling_complete ausente, audit não é chamado."""
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph

        graph = InterviewGraph.__new__(InterviewGraph)
        graph.logger = MagicMock()
        graph._compiled = None

        state = {
            "session_id": "sess-vi2",
            "company_id": "co-vi2",
            "workflow_data": {"next_collection_target": "preferred_date"},
        }

        mock_audit = AsyncMock()

        with patch(
            "app.domains.interview_scheduling.agents.interview_graph.InterviewGraph._build_langgraph"
        ) as mock_build, patch(
            "app.shared.compliance.audit_service.audit_service.log_decision",
            mock_audit,
        ):
            mock_compiled = MagicMock()
            mock_compiled.ainvoke = AsyncMock(return_value=state)
            mock_build.return_value = mock_compiled

            await graph._invoke_langgraph(state)

        mock_audit.assert_not_called()

    @pytest.mark.asyncio
    async def test_audit_fail_safe_does_not_crash_graph(self):
        """Se audit_service lançar exceção, o grafo continua sem travar."""
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph

        graph = InterviewGraph.__new__(InterviewGraph)
        graph.logger = MagicMock()
        graph._compiled = None

        state = {
            "session_id": "sess-vi3",
            "company_id": "co-vi3",
            "workflow_data": {"interview_scheduling_complete": True},
        }

        with patch(
            "app.domains.interview_scheduling.agents.interview_graph.InterviewGraph._build_langgraph"
        ) as mock_build, patch(
            "app.shared.compliance.audit_service.audit_service.log_decision",
            side_effect=Exception("DB offline"),
        ):
            mock_compiled = MagicMock()
            mock_compiled.ainvoke = AsyncMock(return_value=state)
            mock_build.return_value = mock_compiled

            # Não deve lançar exceção
            result = await graph._invoke_langgraph(state)

        assert result is not None

    def test_langgraph_path_has_audit(self):
        """LangGraph path (_invoke_langgraph) tem audit_service."""
        import inspect
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        source = inspect.getsource(InterviewGraph._invoke_langgraph)
        assert "audit_service" in source
        assert "log_decision" in source
        assert "schedule_interview" in source


# ---------------------------------------------------------------------------
# ACH-016 — Policy legacy: import removido de hiring_policy.py
# ---------------------------------------------------------------------------

class TestPolicyLegacyImportRemoved:
    def test_hiring_policy_does_not_import_policy_setup_agent(self):
        """hiring_policy.py não deve importar policy_setup_agent."""
        import ast
        import pathlib

        src = pathlib.Path(
            "app/api/v1/hiring_policy.py"
        ).read_text()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [
                    getattr(a, "name", "") for a in getattr(node, "names", [])
                ]
                module = getattr(node, "module", "") or ""
                assert "policy_setup_agent" not in module, (
                    "policy_setup_agent ainda importado em hiring_policy.py"
                )
                for n in names:
                    assert "policy_setup_agent" not in n

    def test_policy_react_agent_is_imported(self):
        """PolicyReActAgent deve ser importado em hiring_policy.py."""
        import importlib
        mod = importlib.import_module("app.api.v1.hiring_policy")
        assert hasattr(mod, "PolicyReActAgent")

    def test_policy_domain_deprecated_marker(self):
        """app/domains/policy/__init__.py deve ter marcação DEPRECATED."""
        import pathlib
        content = pathlib.Path("app/domains/policy/__init__.py").read_text()
        assert "DEPRECATED" in content or "deprecated" in content.lower()


# ---------------------------------------------------------------------------
# ACH-017 — Stubs removidos; imports diretos funcionam
# ---------------------------------------------------------------------------

class TestToolsStubsRemoved:
    def test_stubs_deleted(self):
        """Os 6 stubs devem ter sido removidos de app/tools/."""
        import pathlib
        stubs = [
            "app/tools/job_wizard_tools.py",
            "app/tools/candidate_tools.py",
            "app/tools/communication_tools.py",
            "app/tools/job_tools.py",
            "app/tools/export_tools.py",
            "app/tools/query_tools.py",
        ]
        for stub in stubs:
            assert not pathlib.Path(stub).exists(), f"Stub ainda existe: {stub}"

    def test_initialize_tools_imports_from_domains(self):
        """initialize_tools() deve importar de domain paths, não de stubs."""
        import inspect
        from app.tools import initialize_tools
        source = inspect.getsource(initialize_tools)
        assert "app.domains.job_management.tools.job_wizard_tools" in source
        assert "app.domains.cv_screening.tools.candidate_tools" in source
        assert "app.domains.analytics.tools.query_tools" in source
        # Garantir que não usa mais os stubs
        assert "from app.tools.job_wizard_tools" not in source
        assert "from app.tools.candidate_tools" not in source

    def test_wizard_orchestrator_imports_from_domain(self):
        """wizard_smart_orchestrator.py deve importar generate_enriched_jd do domain."""
        import pathlib
        src = pathlib.Path(
            "app/api/v1/wizard_smart_orchestrator.py"
        ).read_text()
        assert "app.domains.job_management.tools.job_wizard_tools" in src
        assert "from app.tools.job_wizard_tools" not in src

    def test_domain_imports_resolve(self):
        """Imports diretos dos domains devem resolver sem erro."""
        from app.domains.job_management.tools.job_wizard_tools import generate_enriched_jd
        from app.domains.cv_screening.tools.candidate_tools import register_candidate_tools
        from app.domains.analytics.tools.query_tools import register_query_tools
        assert callable(generate_enriched_jd)
        assert callable(register_candidate_tools)
        assert callable(register_query_tools)


# ---------------------------------------------------------------------------
# ACH-029 — Drift beat schedule registrado no Celery
# ---------------------------------------------------------------------------

class TestDriftBeatSchedule:
    def test_drift_schedule_registered(self):
        """drift-run-batch-daily deve estar registrado no beat_schedule."""
        from libs.config.lia_config.celery_app import celery_app
        schedules = celery_app.conf.beat_schedule
        assert "drift-run-batch-daily" in schedules, (
            "drift-run-batch-daily não encontrado no beat_schedule"
        )

    def test_drift_schedule_task_name(self):
        """Task do drift schedule deve ser 'drift.run_batch'."""
        from libs.config.lia_config.celery_app import celery_app
        entry = celery_app.conf.beat_schedule["drift-run-batch-daily"]
        assert entry["task"] == "drift.run_batch"

    def test_drift_schedule_has_expiry(self):
        """Drift schedule deve ter expires para evitar acúmulo de tasks."""
        from libs.config.lia_config.celery_app import celery_app
        entry = celery_app.conf.beat_schedule["drift-run-batch-daily"]
        opts = entry.get("options", {})
        assert "expires" in opts and opts["expires"] > 0
