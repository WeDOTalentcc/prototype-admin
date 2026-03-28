"""
E2E Tests — JobWizardGraph (LangGraph-style state machine).

Cobre:
- invoke() decorado com @_traceable e chamável
- _execute_node emite node_start / node_end / node_error nos logs
- Erro em nó propaga corretamente no estado
- Grafo singleton importável
"""
import pytest
import logging
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Section 1: Importação e estrutura
# ---------------------------------------------------------------------------

class TestJobWizardGraphImport:

    def test_graph_importable(self):
        from app.domains.job_management.agents.job_wizard_graph import JobWizardGraph
        g = JobWizardGraph()
        assert g is not None

    def test_singleton_importable(self):
        from app.domains.job_management.agents.job_wizard_graph import job_wizard_graph
        assert job_wizard_graph is not None

    def test_invoke_callable(self):
        from app.domains.job_management.agents.job_wizard_graph import JobWizardGraph
        import asyncio
        g = JobWizardGraph()
        assert callable(g.invoke)
        assert asyncio.iscoroutinefunction(g.invoke)

    def test_execute_node_callable(self):
        from app.domains.job_management.agents.job_wizard_graph import JobWizardGraph
        import asyncio
        g = JobWizardGraph()
        assert callable(g._execute_node)
        assert asyncio.iscoroutinefunction(g._execute_node)


# ---------------------------------------------------------------------------
# Section 2: Logging estruturado em _execute_node
# ---------------------------------------------------------------------------

class TestJobWizardGraphNodeLogging:

    @pytest.mark.asyncio
    async def test_execute_node_logs_node_start_and_end(self):
        """_execute_node deve emitir node_start e node_end nos logs."""
        from app.domains.job_management.agents.job_wizard_graph import JobWizardGraph
        from app.agents.nodes import JobWizardNodes

        fresh_nodes = JobWizardNodes()
        g = JobWizardGraph(nodes=fresh_nodes)
        log_records = []

        class _Capture(logging.Handler):
            def emit(self, record):
                log_records.append(record.getMessage())

        handler = _Capture()
        log_inst = logging.getLogger("JobWizardGraph")
        log_inst.addHandler(handler)
        log_inst.setLevel(logging.DEBUG)

        state = {
            "session_id": "wiz-e2e-1",
            "company_id": "tenant-wiz",
            "current_stage": "input_evaluation",
        }

        async def mock_node(s):
            return s

        fresh_nodes.get_node = lambda name: mock_node

        await g._execute_node("__test_node__", state)
        log_inst.removeHandler(handler)

        assert any("node_start" in m for m in log_records), f"node_start not found in: {log_records}"
        assert any("node_end" in m for m in log_records), f"node_end not found in: {log_records}"

    @pytest.mark.asyncio
    async def test_execute_node_logs_node_error_on_exception(self):
        """_execute_node em exceção deve emitir node_error e registrar erro no estado."""
        from app.domains.job_management.agents.job_wizard_graph import JobWizardGraph
        from app.agents.nodes import JobWizardNodes

        fresh_nodes = JobWizardNodes()
        g = JobWizardGraph(nodes=fresh_nodes)
        log_records = []

        class _Capture(logging.Handler):
            def emit(self, record):
                log_records.append(record.getMessage())

        handler = _Capture()
        log_inst = logging.getLogger("JobWizardGraph")
        log_inst.addHandler(handler)
        log_inst.setLevel(logging.DEBUG)

        state = {
            "session_id": "wiz-e2e-err",
            "company_id": "tenant-wiz",
            "current_stage": "input_evaluation",
        }

        async def failing_node(s):
            raise RuntimeError("simulated wizard node failure")

        fresh_nodes.get_node = lambda name: failing_node

        result_state, elapsed = await g._execute_node("__fail_node__", state)
        log_inst.removeHandler(handler)

        assert any("node_error" in m for m in log_records), f"node_error not found in: {log_records}"
        assert "error" in result_state

    @pytest.mark.asyncio
    async def test_execute_node_returns_elapsed_ms(self):
        """_execute_node deve retornar (state, elapsed_ms) onde elapsed >= 0."""
        from app.domains.job_management.agents.job_wizard_graph import JobWizardGraph
        from app.agents.nodes import JobWizardNodes

        fresh_nodes = JobWizardNodes()
        g = JobWizardGraph(nodes=fresh_nodes)
        state = {"session_id": "wiz-e2e-2", "current_stage": "input_evaluation"}

        async def noop(s):
            return s

        fresh_nodes.get_node = lambda name: noop
        result_state, elapsed = await g._execute_node("__noop__", state)
        assert elapsed >= 0

    @pytest.mark.asyncio
    async def test_execute_node_returns_error_state_for_unknown_node(self):
        """Nó desconhecido deve retornar estado com erro sem levantar exceção."""
        from app.domains.job_management.agents.job_wizard_graph import JobWizardGraph
        from app.agents.nodes import JobWizardNodes

        # Fresh nodes instance to avoid singleton state pollution from other tests
        fresh_nodes = JobWizardNodes()
        g = JobWizardGraph(nodes=fresh_nodes)  # Inject isolated nodes

        state = {"session_id": "wiz-e2e-3", "current_stage": "input_evaluation"}

        result_state, elapsed = await g._execute_node("__nonexistent_node__", state)
        assert "error" in result_state
        assert elapsed == 0.0


# ---------------------------------------------------------------------------
# Section 3: Traceable decorator aplicado
# ---------------------------------------------------------------------------

class TestJobWizardGraphTracing:

    def test_invoke_has_traceable_or_is_callable(self):
        """invoke() deve ser chamável (decorator @_traceable não quebra a assinatura)."""
        from app.domains.job_management.agents.job_wizard_graph import JobWizardGraph
        g = JobWizardGraph()
        assert callable(g.invoke)
