"""Coverage tests for app/schemas/audit_logs.py — enums and Pydantic models."""
import pytest
from datetime import datetime
from app.schemas.audit_logs import (
    ActionCategoryEnum,
    AuditStatusEnum,
    AuditLogCreate,
    AuditLogResponse,
    AuditLogListResponse,
    AuditLogFilter,
    AuditStatsResponse,
    AuditRetentionPolicyResponse,
)


class TestActionCategoryEnum:
    def test_authentication(self):
        assert ActionCategoryEnum.AUTHENTICATION == "authentication"

    def test_data_access(self):
        assert ActionCategoryEnum.DATA_ACCESS == "data_access"

    def test_configuration(self):
        assert ActionCategoryEnum.CONFIGURATION == "configuration"

    def test_ai_decision(self):
        assert ActionCategoryEnum.AI_DECISION == "ai_decision"

    def test_financial(self):
        assert ActionCategoryEnum.FINANCIAL == "financial"

    def test_all_are_strings(self):
        for v in ActionCategoryEnum:
            assert isinstance(v.value, str)


class TestAuditStatusEnum:
    def test_has_values(self):
        values = list(AuditStatusEnum)
        assert len(values) > 0

    def test_success_exists(self):
        vals = [e.value for e in AuditStatusEnum]
        assert any("success" in v for v in vals)


class TestAuditLogCreate:
    def test_basic(self):
        m = AuditLogCreate(
            action="user_login",
            action_category=ActionCategoryEnum.AUTHENTICATION,
        )
        assert m.action == "user_login"
        assert m.action_category == "authentication"

    def test_ai_decision(self):
        m = AuditLogCreate(
            action="candidate_screening",
            action_category=ActionCategoryEnum.AI_DECISION,
            user_id="user-001",
            client_id="co-001",
            resource_type="candidate",
            resource_id="cand-001",
        )
        assert m.action_category == "ai_decision"
        assert m.resource_type == "candidate"

    def test_data_access(self):
        m = AuditLogCreate(
            action="export_candidate_data",
            action_category=ActionCategoryEnum.DATA_ACCESS,
            client_id="co-001",
        )
        assert m.action == "export_candidate_data"

    def test_with_details(self):
        m = AuditLogCreate(
            action="config_change",
            action_category=ActionCategoryEnum.CONFIGURATION,
            details={"old_value": "low", "new_value": "high"},
            ip_address="10.0.0.1",
        )
        assert m.details["old_value"] == "low"
        assert m.ip_address == "10.0.0.1"

    def test_defaults(self):
        m = AuditLogCreate(
            action="api_call",
            action_category=ActionCategoryEnum.DATA_ACCESS,
        )
        assert m.user_id is None
        assert m.client_id is None
        assert m.ip_address is None


class TestAuditLogResponse:
    def test_basic(self):
        m = AuditLogResponse(
            id="log-001",
            action="user_login",
            action_category=ActionCategoryEnum.AUTHENTICATION.value,
            status="success",
        )
        assert m.id == "log-001"
        assert m.action == "user_login"
        assert m.status == "success"

    def test_optional_fields(self):
        m = AuditLogResponse(
            id="log-002",
            action="bulk_export",
            action_category=ActionCategoryEnum.DATA_ACCESS.value,
            status="success",
        )
        assert m.user_id is None
        assert m.client_id is None
        assert m.resource_id is None

    def test_failed_action(self):
        m = AuditLogResponse(
            id="log-003",
            action="unauthorized_access",
            action_category=ActionCategoryEnum.AUTHENTICATION.value,
            status="failed",
        )
        assert m.status == "failed"


class TestAuditLogListResponse:
    def test_empty(self):
        m = AuditLogListResponse(logs=[], total=0, limit=20, offset=0)
        assert m.logs == []
        assert m.total == 0

    def test_with_items(self):
        log = AuditLogResponse(
            id="log-001", action="login",
            action_category="authentication", status="success",
        )
        m = AuditLogListResponse(
            logs=[log],
            total=1,
            limit=20,
            offset=0,
        )
        assert m.total == 1
        assert len(m.logs) == 1


class TestAuditLogFilter:
    def test_empty_filter(self):
        m = AuditLogFilter()
        assert m.action_category is None
        assert m.user_id is None
        assert m.client_id is None

    def test_with_category(self):
        m = AuditLogFilter(
            action_category=ActionCategoryEnum.AI_DECISION,
            client_id="co-001",
        )
        assert m.action_category == "ai_decision"
        assert m.client_id == "co-001"

    def test_with_date_range(self):
        m = AuditLogFilter(
            date_from=datetime(2024, 1, 1),
            date_to=datetime(2024, 12, 31),
        )
        assert m.date_from is not None
        assert m.date_to is not None

    def test_by_resource(self):
        m = AuditLogFilter(
            resource_type="candidate",
            action="screening",
        )
        assert m.resource_type == "candidate"


class TestAuditStatsResponse:
    def test_basic(self):
        m = AuditStatsResponse(
            total_logs=1000,
            failed_actions_count=15,
            ai_decisions_count=200,
            unique_users=50,
            unique_clients=10,
        )
        assert m.total_logs == 1000
        assert m.failed_actions_count == 15
        assert m.ai_decisions_count == 200
        assert m.unique_users == 50
        assert m.unique_clients == 10

    def test_zero_events(self):
        m = AuditStatsResponse(
            total_logs=0,
            failed_actions_count=0,
            ai_decisions_count=0,
            unique_users=0,
            unique_clients=0,
        )
        assert m.total_logs == 0


class TestAuditRetentionPolicyResponse:
    def test_basic(self):
        m = AuditRetentionPolicyResponse(
            id="ret-001",
            category="authentication",
            retention_months=12,
        )
        assert m.id == "ret-001"
        assert m.retention_months == 12
        assert m.is_active is True  # default

    def test_sox_required(self):
        m = AuditRetentionPolicyResponse(
            id="ret-002",
            category="financial",
            retention_months=84,
            is_sox_required=True,
            legal_basis="SOX Section 802",
        )
        assert m.is_sox_required is True
        assert m.retention_months == 84

    def test_inactive(self):
        m = AuditRetentionPolicyResponse(
            id="ret-003",
            category="data_access",
            retention_months=36,
            is_active=False,
        )
        assert m.is_active is False
