"""
Tests for LGPD Compliance - Consent Management and Data Subject Requests.
Verifies API structure and endpoint availability.
"""
import pytest


class TestConsentManagementStructure:
    def test_consent_module_importable(self):
        from app.api.v1 import consent_management
        assert hasattr(consent_management, 'router')

    def test_consent_router_has_endpoints(self):
        from app.api.v1.consent_management import router
        routes = [r.path for r in router.routes]
        assert len(routes) > 0


class TestDataSubjectRequestsStructure:
    def test_dsr_module_importable(self):
        from app.api.v1 import data_subject_requests
        assert hasattr(data_subject_requests, 'router')

    def test_dsr_router_has_endpoints(self):
        from app.api.v1.data_subject_requests import router
        routes = [r.path for r in router.routes]
        assert len(routes) > 0


class TestLGPDComplianceStructure:
    def test_lgpd_module_importable(self):
        from app.api.v1 import lgpd_compliance
        assert hasattr(lgpd_compliance, 'router')

    def test_lgpd_router_has_endpoints(self):
        from app.api.v1.lgpd_compliance import router
        routes = [r.path for r in router.routes]
        assert len(routes) > 0
