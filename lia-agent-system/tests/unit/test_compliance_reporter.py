"""UC-P1-12: ComplianceReporter aggregates all compliance signals."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date


@pytest.mark.asyncio
async def test_report_has_required_sections():
    from app.domains.compliance.services.compliance_reporter import ComplianceReporter
    reporter = ComplianceReporter.__new__(ComplianceReporter)
    with patch.object(reporter, "_get_bias_summary", new=AsyncMock(return_value={"adverse_impact": []})),          patch.object(reporter, "_get_fairness_summary", new=AsyncMock(return_value={"violations": 0})),          patch.object(reporter, "_get_audit_log_count", new=AsyncMock(return_value=142)),          patch.object(reporter, "_get_consent_summary", new=AsyncMock(return_value={"active": 10})),          patch.object(reporter, "_get_retention_status", new=AsyncMock(return_value={"pending_deletion": 0})):
        report = await reporter.generate_report("company_123", date(2026, 1, 1), date(2026, 5, 2))
    assert "bias_summary" in report
    assert "fairness_summary" in report
    assert "audit_log_count" in report
    assert "consent_summary" in report
    assert "retention_status" in report
    assert "generated_at" in report
    assert "company_id" in report


@pytest.mark.asyncio
async def test_report_includes_company_id():
    from app.domains.compliance.services.compliance_reporter import ComplianceReporter
    reporter = ComplianceReporter.__new__(ComplianceReporter)
    with patch.object(reporter, "_get_bias_summary", new=AsyncMock(return_value={})),          patch.object(reporter, "_get_fairness_summary", new=AsyncMock(return_value={})),          patch.object(reporter, "_get_audit_log_count", new=AsyncMock(return_value=0)),          patch.object(reporter, "_get_consent_summary", new=AsyncMock(return_value={})),          patch.object(reporter, "_get_retention_status", new=AsyncMock(return_value={})):
        report = await reporter.generate_report("company_XYZ", date(2026, 1, 1), date(2026, 5, 2))
    assert report["company_id"] == "company_XYZ"
