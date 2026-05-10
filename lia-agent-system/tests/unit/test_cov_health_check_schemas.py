"""Coverage tests for app/schemas/health_check.py — enums and Pydantic models."""
import pytest
from app.schemas.health_check import (
    ComplianceFrameworkEnum,
    HealthCheckStatusEnum,
    ReviewFrequencyEnum,
    PriorityEnum,
    HealthCheckItemCreate,
    HealthCheckItemResponse,
    HealthCheckItemListResponse,
)


class TestComplianceFrameworkEnum:
    def test_sox(self):
        assert ComplianceFrameworkEnum.SOX == "SOX"

    def test_soc2(self):
        assert ComplianceFrameworkEnum.SOC2 == "SOC2"

    def test_iso27001(self):
        assert ComplianceFrameworkEnum.ISO27001 == "ISO27001"

    def test_lgpd(self):
        assert ComplianceFrameworkEnum.LGPD == "LGPD"

    def test_bcb498(self):
        assert ComplianceFrameworkEnum.BCB498 == "BCB498"


class TestHealthCheckStatusEnum:
    def test_implemented(self):
        assert HealthCheckStatusEnum.IMPLEMENTED == "implemented"

    def test_partial(self):
        assert HealthCheckStatusEnum.PARTIAL == "partial"

    def test_pending(self):
        assert HealthCheckStatusEnum.PENDING == "pending"

    def test_not_applicable(self):
        assert HealthCheckStatusEnum.NOT_APPLICABLE == "not_applicable"

    def test_not_checked(self):
        assert HealthCheckStatusEnum.NOT_CHECKED == "not_checked"


class TestReviewFrequencyEnum:
    def test_weekly(self):
        assert ReviewFrequencyEnum.WEEKLY == "weekly"

    def test_monthly(self):
        assert ReviewFrequencyEnum.MONTHLY == "monthly"

    def test_quarterly(self):
        assert ReviewFrequencyEnum.QUARTERLY == "quarterly"

    def test_annual(self):
        assert ReviewFrequencyEnum.ANNUAL == "annual"


class TestPriorityEnum:
    def test_critical(self):
        assert PriorityEnum.CRITICAL == "critical"

    def test_high(self):
        assert PriorityEnum.HIGH == "high"

    def test_medium(self):
        assert PriorityEnum.MEDIUM == "medium"

    def test_low(self):
        assert PriorityEnum.LOW == "low"


class TestHealthCheckItemCreate:
    def test_basic(self):
        m = HealthCheckItemCreate(
            framework=ComplianceFrameworkEnum.LGPD,
            category="Data Protection",
            req_id="LGPD-001",
            requirement="Nomear DPO (Encarregado de Dados)",
        )
        assert m.framework == "LGPD"
        assert m.req_id == "LGPD-001"

    def test_sox_item(self):
        m = HealthCheckItemCreate(
            framework=ComplianceFrameworkEnum.SOX,
            category="Financial Controls",
            req_id="SOX-302",
            requirement="CEO/CFO Certification of financial statements",
        )
        assert m.framework == "SOX"
        assert m.category == "Financial Controls"

    def test_with_optional(self):
        m = HealthCheckItemCreate(
            framework=ComplianceFrameworkEnum.ISO27001,
            category="Access Control",
            req_id="ISO-A9",
            requirement="Access control policy must be documented",
            status=HealthCheckStatusEnum.PARTIAL,
            priority=PriorityEnum.HIGH,
            review_frequency=ReviewFrequencyEnum.ANNUAL,
        )
        assert m.status == "partial"
        assert m.priority == "high"
        assert m.review_frequency == "annual"

    def test_defaults(self):
        m = HealthCheckItemCreate(
            framework=ComplianceFrameworkEnum.SOC2,
            category="Security",
            req_id="CC1.1",
            requirement="Demonstrate commitment to integrity",
        )
        assert m.evidence is None


class TestHealthCheckItemResponse:
    def test_basic(self):
        m = HealthCheckItemResponse(
            id="hc-001",
            framework=ComplianceFrameworkEnum.LGPD.value,
            category="Data Protection",
            req_id="LGPD-001",
            requirement="Nomear DPO",
            status=HealthCheckStatusEnum.IMPLEMENTED.value,
            review_frequency=ReviewFrequencyEnum.ANNUAL.value,
            priority=PriorityEnum.HIGH.value,
        )
        assert m.id == "hc-001"
        assert m.status == "implemented"
        assert m.priority == "high"

    def test_partial(self):
        m = HealthCheckItemResponse(
            id="hc-002",
            framework="SOX",
            category="Financial",
            req_id="SOX-404",
            requirement="Internal controls assessment",
            status=HealthCheckStatusEnum.PARTIAL.value,
            review_frequency=ReviewFrequencyEnum.QUARTERLY.value,
            priority=PriorityEnum.CRITICAL.value,
        )
        assert m.status == "partial"
        assert m.priority == "critical"

    def test_optional_fields_none(self):
        m = HealthCheckItemResponse(
            id="hc-003",
            framework="BCB498",
            category="Banking",
            req_id="BCB-001",
            requirement="Banking regulation",
            status=HealthCheckStatusEnum.NOT_APPLICABLE.value,
            review_frequency=ReviewFrequencyEnum.ANNUAL.value,
            priority=PriorityEnum.LOW.value,
        )
        assert m.evidence is None
        assert m.evidence_details is None
        assert m.gap_observation is None


class TestHealthCheckItemListResponse:
    def test_empty(self):
        m = HealthCheckItemListResponse(items=[], total=0, limit=20, offset=0)
        assert m.items == []
        assert m.total == 0

    def test_with_items(self):
        item = HealthCheckItemResponse(
            id="hc-001", framework="LGPD", category="Data",
            req_id="L1", requirement="Req",
            status="implemented", review_frequency="annual", priority="high",
        )
        m = HealthCheckItemListResponse(items=[item], total=1, limit=20, offset=0)
        assert m.total == 1
        assert len(m.items) == 1

    def test_pagination(self):
        m = HealthCheckItemListResponse(
            items=[],
            total=50,
            limit=10,
            offset=20,
        )
        assert m.total == 50
        assert m.offset == 20
