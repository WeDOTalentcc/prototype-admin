"""
PR-B — test_offer_service.py

Unit tests for OfferService pure functions (no DB required).
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal


class TestPrefillFromSnapshots:

    def test_salary_midpoint_from_range(self):
        """Sprint F.4 #42 canonical-remap: prefill keys use canonical column
        names (``salary``, ``benefits``, ``start_date``, ``currency``)."""
        from app.domains.offer.services.offer_service import prefill_from_snapshots
        job = {"salary_range": {"min": 8000, "max": 12000, "currency": "BRL"}, "benefits": []}
        candidate = {}
        fields = prefill_from_snapshots(job, candidate)
        assert fields["salary"] == Decimal("10000.0")

    def test_salary_from_candidate_desired_when_no_range(self):
        from app.domains.offer.services.offer_service import prefill_from_snapshots
        job = {"benefits": []}
        candidate = {"desired_salary_min": 9000}
        fields = prefill_from_snapshots(job, candidate)
        assert fields["salary"] == Decimal("9000")

    def test_benefits_copied_from_job(self):
        from app.domains.offer.services.offer_service import prefill_from_snapshots
        job = {"salary_range": {}, "benefits": ["VT", "VR", "Plano de saude"]}
        candidate = {}
        fields = prefill_from_snapshots(job, candidate)
        assert fields["benefits"] == [{"name": "VT"}, {"name": "VR"}, {"name": "Plano de saude"}]

    def test_default_start_date_is_future(self):
        from app.domains.offer.services.offer_service import prefill_from_snapshots
        job = {}
        candidate = {}
        fields = prefill_from_snapshots(job, candidate)
        assert fields["start_date"] > date.today()

    def test_currency_from_range(self):
        from app.domains.offer.services.offer_service import prefill_from_snapshots
        job = {"salary_range": {"currency": "USD", "min": 5000, "max": 8000}}
        candidate = {}
        fields = prefill_from_snapshots(job, candidate)
        assert fields["currency"] == "USD"


class TestSalaryWarnings:

    def test_above_max_gives_warning(self):
        from app.domains.offer.services.offer_service import check_salary_warnings
        warnings = check_salary_warnings(
            Decimal("15000"),
            {"salary_range": {"min": 8000, "max": 12000}},
        )
        assert any(w["level"] == "warning" for w in warnings)

    def test_below_min_gives_info(self):
        from app.domains.offer.services.offer_service import check_salary_warnings
        warnings = check_salary_warnings(
            Decimal("5000"),
            {"salary_range": {"min": 8000, "max": 12000}},
        )
        assert any(w["level"] == "info" for w in warnings)

    def test_in_range_no_warnings(self):
        from app.domains.offer.services.offer_service import check_salary_warnings
        warnings = check_salary_warnings(
            Decimal("10000"),
            {"salary_range": {"min": 8000, "max": 12000}},
        )
        assert warnings == []

    def test_none_salary_no_warnings(self):
        from app.domains.offer.services.offer_service import check_salary_warnings
        warnings = check_salary_warnings(None, {"salary_range": {"min": 8000}})
        assert warnings == []


class TestComputeDefaultStartDate:

    def test_returns_date_in_future(self):
        from app.domains.offer.services.offer_service import compute_default_start_date
        start = compute_default_start_date()
        assert start > date.today()
        assert start <= date.today() + timedelta(days=45)
