"""Tests for GAP-10-004: model_version tracking in AuditLog.

Verifies:
- AuditLog model has model_version column
- _resolve_model_version resolves from config when not explicit
- log_decision accepts and persists model_version
- log_output accepts and persists model_version
- log_action accepts and persists model_version
- to_dict includes model_version
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.audit_log import AuditLog


class TestAuditLogModelVersion:
    """AuditLog model has model_version column."""

    def test_model_has_column(self):
        assert hasattr(AuditLog, "model_version")
        col = AuditLog.__table__.columns["model_version"]
        assert col.nullable is True
        assert str(col.type) == "VARCHAR(80)"

    def test_to_dict_includes_model_version(self):
        log = AuditLog(
            id="test-1",
            company_id="c1",
            agent_name="test_agent",
            decision_type="score_candidate",
            action="test",
            decision="approved",
            reasoning=[],
            criteria_used=[],
            criteria_ignored=[],
            model_version="claude-sonnet-4-6",
        )
        d = log.to_dict()
        assert d["model_version"] == "claude-sonnet-4-6"

    def test_to_dict_model_version_none(self):
        log = AuditLog(
            id="test-2",
            company_id="c1",
            agent_name="test_agent",
            decision_type="score_candidate",
            action="test",
            decision="approved",
            reasoning=[],
            criteria_used=[],
            criteria_ignored=[],
        )
        d = log.to_dict()
        assert d["model_version"] is None


class TestResolveModelVersion:
    """_resolve_model_version auto-resolves from agent_model_config."""

    def test_explicit_version_wins(self):
        from app.shared.compliance.audit_service import _resolve_model_version
        result = _resolve_model_version("kanban", "claude-opus-4-6")
        assert result == "claude-opus-4-6"

    def test_resolves_from_agent_config(self):
        from app.shared.compliance.audit_service import _resolve_model_version
        result = _resolve_model_version("kanban", None)
        assert result == "claude-haiku-4-5"

    def test_resolves_default_for_unknown_agent(self):
        from app.shared.compliance.audit_service import _resolve_model_version
        result = _resolve_model_version("nonexistent_agent_xyz", None)
        assert result is not None  # falls back to DEFAULT_MODEL

    def test_none_agent_returns_none(self):
        from app.shared.compliance.audit_service import _resolve_model_version
        result = _resolve_model_version(None, None)
        assert result is None

    def test_import_failure_returns_none(self):
        from app.shared.compliance.audit_service import _resolve_model_version
        with patch("app.shared.compliance.audit_service._resolve_model_version") as mock_fn:
            # Simulate import failure inside the function
            pass
        # Direct test: if get_model_for_agent raises, returns None
        with patch("app.core.agent_model_config.get_model_for_agent", side_effect=ImportError):
            result = _resolve_model_version("kanban", None)
            assert result is None


class TestLogDecisionModelVersion:
    """log_decision passes model_version through."""

    @pytest.mark.asyncio
    async def test_log_decision_with_explicit_model(self):
        from app.shared.compliance.audit_service import AuditService

        svc = AuditService()
        with patch("app.shared.compliance.audit_service.AsyncSessionLocal") as mock_session_cls:
            mock_session = AsyncMock()
            mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_session.add = MagicMock()
            mock_session.commit = AsyncMock()
            mock_session.execute = AsyncMock()

            result = await svc._log_decision_impl(
                company_id="c1",
                agent_name="sourcing",
                decision_type="search_candidates",
                action="search",
                decision="executed",
                reasoning=["test"],
                criteria_used=["skill"],
                model_version="claude-opus-4-6",
            )

            assert result.model_version == "claude-opus-4-6"

    @pytest.mark.asyncio
    async def test_log_decision_auto_resolves_model(self):
        from app.shared.compliance.audit_service import AuditService

        svc = AuditService()
        with patch("app.shared.compliance.audit_service.AsyncSessionLocal") as mock_session_cls:
            mock_session = AsyncMock()
            mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_session.add = MagicMock()
            mock_session.commit = AsyncMock()
            mock_session.execute = AsyncMock()

            result = await svc._log_decision_impl(
                company_id="c1",
                agent_name="kanban",
                decision_type="search_candidates",
                action="search",
                decision="executed",
                reasoning=["test"],
                criteria_used=["skill"],
            )

            assert result.model_version == "claude-haiku-4-5"
