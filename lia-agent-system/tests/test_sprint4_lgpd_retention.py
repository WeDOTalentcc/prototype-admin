"""
Tests for Sprint 4 — LGPD retention policy on AiConsumption records.

Verifies that:
- AiConsumption model has scheduled_deletion_at field
- token_tracking_service sets scheduled_deletion_at = now + 365 days
- lgpd_cleanup_service includes AiConsumption in cleanup scope
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock


class TestAiConsumptionRetentionField:
    """Verifica que o modelo AiConsumption tem o campo de retenção."""

    def test_model_has_scheduled_deletion_at(self):
        from app.models.ai_consumption import AiConsumption
        assert hasattr(AiConsumption, "scheduled_deletion_at"), (
            "AiConsumption deve ter campo 'scheduled_deletion_at' (LGPD L6)"
        )

    def test_scheduled_deletion_at_is_nullable(self):
        from app.models.ai_consumption import AiConsumption
        col = AiConsumption.__table__.columns.get("scheduled_deletion_at")
        assert col is not None, "Coluna 'scheduled_deletion_at' não encontrada na tabela"
        assert col.nullable is True, "scheduled_deletion_at deve ser nullable"


class TestTokenTrackingSetsRetention:
    """Verifica que record_usage() define scheduled_deletion_at = now + 365 dias."""

    @pytest.mark.asyncio
    async def test_record_usage_sets_scheduled_deletion_365_days(self):
        from app.shared.services.token_tracking_service import TokenTrackingService

        fake_db = AsyncMock()
        fake_db.add = MagicMock()
        fake_db.commit = AsyncMock()
        service = TokenTrackingService(db=fake_db)

        captured = {}

        def capture_add(record):
            captured["record"] = record

        fake_db.add.side_effect = capture_add

        before = datetime.utcnow()
        await service.record_usage(
            user_id="550e8400-e29b-41d4-a716-446655440001",
            company_id="550e8400-e29b-41d4-a716-446655440000",
            agent_type="screening",
            intent="test",
            input_tokens=100,
            output_tokens=50,
            model="claude-sonnet-4-6",
            latency_ms=200.0,
        )
        after = datetime.utcnow()

        record = captured.get("record")
        assert record is not None, "record_usage() deve chamar db.add() com um objeto AiConsumption"
        assert hasattr(record, "scheduled_deletion_at"), (
            "AiConsumption criado deve ter scheduled_deletion_at"
        )
        assert record.scheduled_deletion_at is not None, (
            "scheduled_deletion_at não deve ser None após record_usage()"
        )

        expected_min = before + timedelta(days=364)
        expected_max = after + timedelta(days=366)
        assert expected_min <= record.scheduled_deletion_at <= expected_max, (
            f"scheduled_deletion_at={record.scheduled_deletion_at} deve ser ~now+365d"
        )


class TestLgpdCleanupIncludesAiLogs:
    """Verifica que lgpd_cleanup_service processa AiConsumption expirados."""

    def test_cleanup_service_has_ai_consumption_scope(self):
        import inspect
        from app.services import lgpd_cleanup_service as module
        source = inspect.getsource(module)
        assert "AiConsumption" in source, (
            "lgpd_cleanup_service deve referenciar AiConsumption no cleanup"
        )

    def test_retention_constant_is_365_days(self):
        import inspect
        from app.services import lgpd_cleanup_service as module
        source = inspect.getsource(module)
        assert "365" in source, (
            "lgpd_cleanup_service deve usar retenção de 365 dias para ai_logs"
        )
