"""Coverage tests for app/schemas/consent_management.py — enums and Pydantic models."""
import pytest
from datetime import date, datetime
from app.schemas.consent_management import (
    ConsentEventTypeEnum,
    ConsentChannelEnum,
    ConsentVersionCreate,
    ConsentVersionResponse,
    ConsentVersionListResponse,
    ConsentEventCreate,
    ConsentEventResponse,
    ConsentEventListResponse,
)


class TestConsentEventTypeEnum:
    def test_granted(self):
        assert ConsentEventTypeEnum.GRANTED == "granted"

    def test_revoked(self):
        assert ConsentEventTypeEnum.REVOKED == "revoked"

    def test_renewed(self):
        assert ConsentEventTypeEnum.RENEWED == "renewed"

    def test_expired(self):
        assert ConsentEventTypeEnum.EXPIRED == "expired"


class TestConsentChannelEnum:
    def test_web(self):
        assert ConsentChannelEnum.WEB == "web"

    def test_whatsapp(self):
        assert ConsentChannelEnum.WHATSAPP == "whatsapp"

    def test_email(self):
        assert ConsentChannelEnum.EMAIL == "email"

    def test_api(self):
        assert ConsentChannelEnum.API == "api"

    def test_portal(self):
        assert ConsentChannelEnum.PORTAL == "portal"


class TestConsentVersionCreate:
    def test_basic(self):
        m = ConsentVersionCreate(
            consent_type="terms_of_service",
            version="1.0",
            title="Terms of Service",
            content_html="<p>Full terms here</p>",
            content_text="Full terms here",
            effective_from=date(2024, 1, 1),
        )
        assert m.consent_type == "terms_of_service"
        assert m.version == "1.0"
        assert m.effective_from is not None

    def test_privacy_policy(self):
        m = ConsentVersionCreate(
            consent_type="privacy_policy",
            version="2.1",
            title="Privacy Policy v2.1",
            content_html="<h1>Privacy Policy</h1><p>We take your privacy seriously.</p>",
            content_text="Privacy Policy. We take your privacy seriously.",
            effective_from=date(2024, 5, 10),
        )
        assert m.version == "2.1"

    def test_lgpd_consent(self):
        m = ConsentVersionCreate(
            consent_type="lgpd_data_processing",
            version="1.2",
            title="LGPD Data Processing Consent",
            content_html="<p>LGPD terms</p>",
            content_text="LGPD terms",
            effective_from=date(2024, 3, 1),
        )
        assert m.consent_type == "lgpd_data_processing"


class TestConsentVersionResponse:
    def test_basic(self):
        m = ConsentVersionResponse(
            id="cv-001",
            company_id="co-001",
            consent_type="terms_of_service",
            version="1.0",
            title="Terms",
            content_html="<p>Terms</p>",
            content_text="Terms",
            hash="sha256abc123",
            is_current=True,
        )
        assert m.id == "cv-001"
        assert m.is_current is True
        assert m.hash == "sha256abc123"

    def test_not_current(self):
        m = ConsentVersionResponse(
            id="cv-002",
            company_id="co-001",
            consent_type="privacy_policy",
            version="1.0",
            title="Old Privacy Policy",
            content_html="<p>Old</p>",
            content_text="Old",
            hash="sha256old",
            is_current=False,
        )
        assert m.is_current is False


class TestConsentVersionListResponse:
    def test_empty(self):
        m = ConsentVersionListResponse(versions=[], total=0, limit=20, offset=0)
        assert m.versions == []
        assert m.total == 0

    def test_with_items(self):
        v = ConsentVersionResponse(
            id="cv-001", company_id="co-001", consent_type="terms",
            version="1.0", title="Terms", content_html="<p>T</p>",
            content_text="T", hash="h1",
        )
        m = ConsentVersionListResponse(versions=[v], total=1, limit=20, offset=0)
        assert m.total == 1


class TestConsentEventCreate:
    def test_granted(self):
        m = ConsentEventCreate(
            consent_version_id="cv-001",
            subject_email="user@example.com",
            subject_identifier="user-001",
            event_type=ConsentEventTypeEnum.GRANTED,
            consent_given=True,
        )
        assert m.consent_version_id == "cv-001"
        assert m.consent_given is True
        assert m.event_type == "granted"

    def test_revoked(self):
        m = ConsentEventCreate(
            consent_version_id="cv-001",
            subject_email="user@example.com",
            subject_identifier="user-001",
            event_type=ConsentEventTypeEnum.REVOKED,
            consent_given=False,
        )
        assert m.consent_given is False
        assert m.event_type == "revoked"

    def test_with_channel_and_ip(self):
        m = ConsentEventCreate(
            consent_version_id="cv-002",
            subject_email="candidate@test.com",
            subject_identifier="cand-001",
            event_type=ConsentEventTypeEnum.GRANTED,
            consent_given=True,
            channel=ConsentChannelEnum.WEB,
            ip_address="192.168.1.1",
        )
        assert m.channel == "web"
        assert m.ip_address == "192.168.1.1"

    def test_defaults(self):
        m = ConsentEventCreate(
            consent_version_id="cv-003",
            subject_email="test@test.com",
            subject_identifier="test-001",
            event_type=ConsentEventTypeEnum.GRANTED,
            consent_given=True,
        )
        assert m.channel == ConsentChannelEnum.WEB  # default is web
        assert m.ip_address is None


class TestConsentEventResponse:
    def test_basic(self):
        m = ConsentEventResponse(
            id="ce-001",
            company_id="co-001",
            consent_version_id="cv-001",
            subject_email="user@example.com",
            subject_identifier="user-001",
            event_type=ConsentEventTypeEnum.GRANTED.value,
            consent_given=True,
            channel=ConsentChannelEnum.WEB.value,
            proof_hash="sha256proof",
        )
        assert m.id == "ce-001"
        assert m.consent_given is True
        assert m.proof_hash == "sha256proof"

    def test_optional_fields(self):
        m = ConsentEventResponse(
            id="ce-002",
            company_id="co-001",
            consent_version_id="cv-002",
            subject_email="user2@example.com",
            subject_identifier="user-002",
            event_type="revoked",
            consent_given=False,
            channel="email",
            proof_hash="hash2",
        )
        assert m.location_country is None
        assert m.expires_at is None


class TestConsentEventListResponse:
    def test_empty(self):
        m = ConsentEventListResponse(events=[], total=0, limit=20, offset=0)
        assert m.events == []
        assert m.total == 0
