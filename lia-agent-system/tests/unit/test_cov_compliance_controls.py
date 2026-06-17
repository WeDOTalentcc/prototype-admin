"""Coverage tests for app/schemas/compliance_controls.py — enums and Pydantic models."""
import pytest
from datetime import date, datetime
from app.schemas.compliance_controls import (
    ComplianceFrameworkTypeEnum,
    CompanyControlStatusEnum,
    AuditResultTypeEnum,
    AuditTypeEnum,
    SOXSectionEnum,
    SOXTestResultEnum,
    SOXControlFrequencyEnum,
    ControlLibraryResponse,
    ControlLibraryListResponse,
    ControlLibraryCreate,
    EvidenceFile,
    CompanyControlResponse,
    CompanyControlListResponse,
    CompanyControlCreate,
    CompanyControlUpdate,
    EvidenceUpload,
    ComplianceAuditResponse,
    ComplianceAuditListResponse,
    ComplianceAuditCreate,
    ComplianceAuditUpdate,
    SOXControlResponse,
    SOXControlListResponse,
    SOXControlCreate,
    SOXControlUpdate,
    FrameworkStats,
    ComplianceDashboardResponse,
    SeedDataResponse,
)


class TestComplianceFrameworkTypeEnum:
    def test_iso_27001(self):
        assert ComplianceFrameworkTypeEnum.ISO_27001 == "ISO_27001"

    def test_soc2_type_i(self):
        assert ComplianceFrameworkTypeEnum.SOC_2_TYPE_I == "SOC_2_TYPE_I"

    def test_sox(self):
        assert ComplianceFrameworkTypeEnum.SOX == "SOX"

    def test_lgpd(self):
        assert ComplianceFrameworkTypeEnum.LGPD == "LGPD"

    def test_gdpr(self):
        assert ComplianceFrameworkTypeEnum.GDPR == "GDPR"

    def test_pci_dss(self):
        assert ComplianceFrameworkTypeEnum.PCI_DSS == "PCI_DSS"


class TestCompanyControlStatusEnum:
    def test_not_started(self):
        assert CompanyControlStatusEnum.NOT_STARTED == "not_started"

    def test_in_progress(self):
        assert CompanyControlStatusEnum.IN_PROGRESS == "in_progress"

    def test_implemented(self):
        assert CompanyControlStatusEnum.IMPLEMENTED == "implemented"

    def test_verified(self):
        assert CompanyControlStatusEnum.VERIFIED == "verified"

    def test_not_applicable(self):
        assert CompanyControlStatusEnum.NOT_APPLICABLE == "not_applicable"


class TestAuditResultTypeEnum:
    def test_pass(self):
        assert AuditResultTypeEnum.PASS == "pass"

    def test_conditional_pass(self):
        assert AuditResultTypeEnum.CONDITIONAL_PASS == "conditional_pass"

    def test_fail(self):
        assert AuditResultTypeEnum.FAIL == "fail"


class TestAuditTypeEnum:
    def test_internal(self):
        assert AuditTypeEnum.INTERNAL == "internal"

    def test_external(self):
        assert AuditTypeEnum.EXTERNAL == "external"

    def test_certification(self):
        assert AuditTypeEnum.CERTIFICATION == "certification"


class TestSOXSectionEnum:
    def test_section_302(self):
        assert SOXSectionEnum.SECTION_302 == "302"

    def test_section_404(self):
        assert SOXSectionEnum.SECTION_404 == "404"

    def test_section_409(self):
        assert SOXSectionEnum.SECTION_409 == "409"

    def test_section_802(self):
        assert SOXSectionEnum.SECTION_802 == "802"


class TestSOXTestResultEnum:
    def test_effective(self):
        assert SOXTestResultEnum.EFFECTIVE == "effective"

    def test_ineffective(self):
        assert SOXTestResultEnum.INEFFECTIVE == "ineffective"

    def test_not_tested(self):
        assert SOXTestResultEnum.NOT_TESTED == "not_tested"


class TestSOXControlFrequencyEnum:
    def test_daily(self):
        assert SOXControlFrequencyEnum.DAILY == "daily"

    def test_monthly(self):
        assert SOXControlFrequencyEnum.MONTHLY == "monthly"

    def test_quarterly(self):
        assert SOXControlFrequencyEnum.QUARTERLY == "quarterly"

    def test_annual(self):
        assert SOXControlFrequencyEnum.ANNUAL == "annual"


class TestControlLibraryResponse:
    def test_basic(self):
        m = ControlLibraryResponse(
            id="ctrl-001",
            framework="ISO_27001",
            control_id="A.5.1",
            control_name="Information security policies",
        )
        assert m.id == "ctrl-001"
        assert m.framework == "ISO_27001"
        assert m.is_mandatory is True
        assert m.evidence_requirements == []

    def test_optional_fields(self):
        m = ControlLibraryResponse(
            id="ctrl-002",
            framework="LGPD",
            control_id="Art.46",
            control_name="Security measures",
            control_description="Technical and administrative measures",
            domain="Data Protection",
        )
        assert m.control_description == "Technical and administrative measures"
        assert m.domain == "Data Protection"
        assert m.created_at is None


class TestControlLibraryListResponse:
    def test_empty(self):
        m = ControlLibraryListResponse(controls=[], total=0, limit=20, offset=0)
        assert m.controls == []
        assert m.total == 0

    def test_with_items(self):
        ctrl = ControlLibraryResponse(
            id="c1", framework="SOC_2_TYPE_I",
            control_id="CC1.1", control_name="Control 1",
        )
        m = ControlLibraryListResponse(controls=[ctrl], total=1, limit=50, offset=0)
        assert len(m.controls) == 1
        assert m.total == 1


class TestControlLibraryCreate:
    def test_basic(self):
        m = ControlLibraryCreate(
            framework="ISO_27001",
            control_id="A.9.1",
            control_name="Access Control Policy",
        )
        assert m.framework == "ISO_27001"
        assert m.control_id == "A.9.1"

    def test_with_guidance(self):
        m = ControlLibraryCreate(
            framework="SOX",
            control_id="302-01",
            control_name="CEO Certification",
            implementation_guidance="CEO must sign quarterly",
            is_mandatory=True,
        )
        assert m.implementation_guidance == "CEO must sign quarterly"
        assert m.is_mandatory is True


class TestEvidenceFile:
    def test_basic(self):
        m = EvidenceFile(
            filename="policy.pdf",
            url="https://s3.example.com/policy.pdf",
            uploaded_at="2024-05-01T10:00:00Z",
        )
        assert m.filename == "policy.pdf"
        assert m.url == "https://s3.example.com/policy.pdf"

    def test_different_file(self):
        m = EvidenceFile(
            filename="audit.xlsx",
            url="https://s3.example.com/audit.xlsx",
            uploaded_at="2024-06-01T00:00:00Z",
        )
        assert m.filename == "audit.xlsx"


class TestCompanyControlCreate:
    def test_basic(self):
        m = CompanyControlCreate(
            control_library_id="ctrl-001",
            status=CompanyControlStatusEnum.IN_PROGRESS,
        )
        assert m.control_library_id == "ctrl-001"
        assert m.status == "in_progress"

    def test_with_owner(self):
        m = CompanyControlCreate(
            control_library_id="ctrl-002",
            status=CompanyControlStatusEnum.IMPLEMENTED,
            owner_name="João Silva",
            owner_email="joao@company.com",
            notes="Implemented via security policy v3",
        )
        assert m.owner_name == "João Silva"
        assert m.notes == "Implemented via security policy v3"


class TestCompanyControlUpdate:
    def test_all_optional(self):
        m = CompanyControlUpdate()
        assert m.status is None
        assert m.owner_name is None

    def test_update_status(self):
        m = CompanyControlUpdate(status=CompanyControlStatusEnum.VERIFIED)
        assert m.status == "verified"


class TestComplianceAuditCreate:
    def test_basic(self):
        m = ComplianceAuditCreate(
            framework="ISO_27001",
            audit_type="internal",
        )
        assert m.framework == "ISO_27001"
        assert m.audit_type == "internal"

    def test_with_dates(self):
        m = ComplianceAuditCreate(
            framework="SOC_2_TYPE_II",
            audit_type="external",
            auditor_organization="KPMG",
            audit_start_date=date(2024, 6, 1),
            audit_end_date=date(2024, 6, 30),
        )
        assert m.auditor_organization == "KPMG"
        assert m.audit_start_date == date(2024, 6, 1)


class TestComplianceAuditUpdate:
    def test_all_optional(self):
        m = ComplianceAuditUpdate()
        assert m.auditor_name is None
        assert m.findings_count is None

    def test_update_findings(self):
        m = ComplianceAuditUpdate(
            findings_count=5,
            critical_findings=1,
            high_findings=2,
        )
        assert m.findings_count == 5
        assert m.critical_findings == 1


class TestSOXControlCreate:
    def test_basic(self):
        m = SOXControlCreate(
            section="302",
            control_id="302-01",
            control_name="CEO Quarterly Certification",
        )
        assert m.section == "302"
        assert m.control_id == "302-01"

    def test_with_frequency(self):
        m = SOXControlCreate(
            section="404",
            control_id="404-10",
            control_name="Internal Control Assessment",
            frequency="quarterly",
            key_control=True,
            control_owner="CFO",
        )
        assert m.frequency == "quarterly"
        assert m.key_control is True

    def test_defaults(self):
        m = SOXControlCreate(
            section="802",
            control_id="802-01",
            control_name="Record Retention",
        )
        assert m.key_control is False


class TestSOXControlUpdate:
    def test_all_optional(self):
        m = SOXControlUpdate()
        assert m.key_control is None
        assert m.frequency is None

    def test_update_key_control(self):
        m = SOXControlUpdate(key_control=True, frequency="monthly")
        assert m.key_control is True
        assert m.frequency == "monthly"


class TestFrameworkStats:
    def test_basic(self):
        m = FrameworkStats(
            total_controls=100,
            implemented=60,
            in_progress=20,
            not_started=20,
            not_applicable=0,
            compliance_percentage=60.0,
        )
        assert m.total_controls == 100
        assert m.compliance_percentage == pytest.approx(60.0)

    def test_defaults_to_zero(self):
        m = FrameworkStats()
        assert m.total_controls == 0
        assert m.compliance_percentage == pytest.approx(0.0)

    def test_full_compliance(self):
        m = FrameworkStats(
            total_controls=50,
            implemented=50,
            in_progress=0,
            not_started=0,
            not_applicable=0,
            compliance_percentage=100.0,
        )
        assert m.compliance_percentage == pytest.approx(100.0)


class TestSeedDataResponse:
    def test_basic(self):
        m = SeedDataResponse(message="Seeded successfully")
        assert m.message == "Seeded successfully"

    def test_with_count(self):
        m = SeedDataResponse(
            message="Done",
            iso_27001_controls=114,
            soc_2_controls=64,
            sox_controls=20,
            total_controls=198,
        )
        assert m.iso_27001_controls == 114
        assert m.total_controls == 198
