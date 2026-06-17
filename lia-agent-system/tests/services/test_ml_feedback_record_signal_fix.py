"""Sprint 7B-3b Part 1 Fase B — MLFeedback canonical migration + silent fix.

Tests pra:
1. orchestrator importa de `app.shared.services.ml_feedback_service` (canonical Paulo locked)
2. Exception em record_signal NÃO silencia — logger.error com exc_info chamado
"""
import logging
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

pytestmark = pytest.mark.asyncio


async def test_orchestrator_imports_canonical_shared_path():
    """Source de orchestrator usa from app.shared.services.ml_feedback_service."""
    from pathlib import Path
    src = Path("app/services/sourcing_agent_orchestrator.py").read_text()
    assert "from app.shared.services.ml_feedback_service import" in src, \
        "orchestrator deve importar de canonical shared path (Paulo locked 2026-05-26)"
    assert "from app.domains.analytics.services.ml_feedback_service import MLFeedbackService" not in src, \
        "orchestrator NÃO deve importar via domains.analytics path direto (use shared shim canonical)"


async def test_record_signal_failure_logs_error_not_silent(caplog):
    """Exception em record_signal → logger.error(exc_info=True), não logger.debug silent."""
    from app.services.sourcing_agent_orchestrator import SourcingAgentOrchestrator
    from sqlalchemy import or_, select

    orch = SourcingAgentOrchestrator()

    # Mock agent lookup retornando agent canonical
    fake_agent = MagicMock()
    fake_agent.id = "uuid-1"
    fake_agent.company_id = "comp-1"
    fake_agent.name = "Agent X"
    fake_agent.search_strategy = {}
    fake_agent.runtime_metrics = {}
    fake_agent.preferences = {}

    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()

    exec_result = MagicMock()
    exec_result.scalar_one = MagicMock(return_value=fake_agent)
    exec_result.scalar_one_or_none = MagicMock(return_value=fake_agent)
    # Para count query do final
    exec_count = MagicMock()
    exec_count.scalar_one = MagicMock(return_value=10)
    exec_count.scalar = MagicMock(return_value=10)

    db.execute = AsyncMock(side_effect=[exec_result, exec_count, exec_count, exec_count])

    # Mock MLFeedbackService.record_signal pra lançar exceção
    failing_record = AsyncMock(side_effect=RuntimeError("ML pipeline down"))
    fake_ml_cls = MagicMock()
    fake_ml_instance = MagicMock()
    fake_ml_instance.record_signal = failing_record
    fake_ml_cls.return_value = fake_ml_instance

    # Mock _extract_criteria & audit
    with patch.object(orch, "_extract_criteria", new=AsyncMock(return_value=["py"])):
        with patch("app.shared.services.ml_feedback_service.MLFeedbackService", fake_ml_cls):
            with patch("app.shared.compliance.audit_service.AuditService") as mock_audit:
                mock_audit_inst = MagicMock()
                mock_audit_inst.log_decision = AsyncMock()
                mock_audit.return_value = mock_audit_inst

                with caplog.at_level(logging.ERROR, logger="app.services.sourcing_agent_orchestrator"):
                    try:
                        await orch.process_feedback(
                            agent_id="uuid-1",
                            candidate_id="cand-1",
                            signal_type="positive",
                            reason="good fit",
                            db=db,
                        )
                    except Exception:
                        pass  # process_feedback may continue or raise downstream

    # ASSERT: logger.error chamado com mensagem que contém indicador de ML feedback failure
    error_records = [r for r in caplog.records if r.levelno >= logging.ERROR]
    ml_errors = [r for r in error_records if "ML feedback" in r.getMessage() or "ml_feedback" in r.getMessage().lower() or "MLFeedback" in r.getMessage()]
    assert ml_errors, \
        f"Esperado logger.error pra ML failure. Records: {[r.getMessage() for r in caplog.records]}"
    # exc_info presente → logger.error com exc_info=True
    assert any(r.exc_info for r in ml_errors), \
        "logger.error deve ter exc_info=True (Option A canonical Paulo)"
