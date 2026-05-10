"""Coverage tests for pearch_service.py — pure/simple methods."""
import pytest
from unittest.mock import patch

from lia_models.pearch import PearchSearchRequest, SearchType


@pytest.fixture
def svc():
    with patch.dict("os.environ", {"PEARCH_API_KEY": "test-key-123"}):
        from app.domains.sourcing.services.pearch_service import PearchService
        return PearchService()


@pytest.fixture
def svc_unconfigured():
    with patch.dict("os.environ", {}, clear=False):
        import os
        os.environ.pop("PEARCH_API_KEY", None)
        from app.domains.sourcing.services.pearch_service import PearchService
        return PearchService()


@pytest.fixture
def basic_request():
    return PearchSearchRequest(
        query="Python developer senior",
        type=SearchType.FAST,
        limit=10,
        insights=False,
        profile_scoring=False,
        high_freshness=False,
    )


class TestIsConfigured:
    def test_configured_when_api_key_present(self, svc):
        assert svc.is_configured is True

    def test_not_configured_when_no_api_key(self, svc_unconfigured):
        assert svc_unconfigured.is_configured is False


class TestGetHeaders:
    def test_headers_include_auth(self, svc):
        headers = svc._get_headers()
        assert "Authorization" in headers
        assert "Bearer" in headers["Authorization"]

    def test_headers_include_content_type(self, svc):
        headers = svc._get_headers()
        assert headers["content-type"] == "application/json"


class TestEstimateCredits:
    def test_basic_fast_search_1_credit_per_candidate(self, svc, basic_request):
        estimate = svc.estimate_credits(basic_request)
        assert estimate.base_cost == 1
        assert estimate.total_per_candidate == 1
        assert estimate.estimated_candidates == 10
        assert estimate.total_estimated == 10

    def test_with_insights_adds_cost(self, svc):
        request = PearchSearchRequest(
            query="Dev", type=SearchType.FAST, limit=5, insights=True
        )
        estimate = svc.estimate_credits(request)
        assert estimate.insights_cost >= 1
        assert estimate.total_per_candidate >= 2

    def test_with_profile_scoring_adds_cost(self, svc):
        request = PearchSearchRequest(
            query="Dev", type=SearchType.FAST, limit=5, profile_scoring=True
        )
        estimate = svc.estimate_credits(request)
        assert estimate.total_per_candidate >= 2

    def test_with_high_freshness_adds_2(self, svc):
        request = PearchSearchRequest(
            query="Dev", type=SearchType.FAST, limit=5, high_freshness=True
        )
        estimate = svc.estimate_credits(request)
        assert estimate.freshness_cost == 2
        assert estimate.total_per_candidate >= 3

    def test_all_features_combined(self, svc):
        request = PearchSearchRequest(
            query="Dev", type=SearchType.FAST, limit=10,
            insights=True, profile_scoring=True, high_freshness=True
        )
        estimate = svc.estimate_credits(request)
        # 1 base + 2 insights/scoring + 2 freshness = 5
        assert estimate.total_per_candidate == 5
        assert estimate.total_estimated == 50

    def test_zero_cost_fields_default(self, svc, basic_request):
        estimate = svc.estimate_credits(basic_request)
        assert estimate.email_cost == 0
        assert estimate.phone_cost == 0

    def test_estimated_candidates_equals_limit(self, svc, basic_request):
        estimate = svc.estimate_credits(basic_request)
        assert estimate.estimated_candidates == basic_request.limit

    def test_total_is_per_candidate_times_limit(self, svc, basic_request):
        estimate = svc.estimate_credits(basic_request)
        assert estimate.total_estimated == estimate.total_per_candidate * estimate.estimated_candidates


class TestCreateConfirmationMessage:
    def test_returns_search_confirmation(self, svc, basic_request):
        confirmation = svc.create_confirmation_message(basic_request)
        assert confirmation.query == basic_request.query
        assert confirmation.requires_confirmation is True

    def test_message_contains_query(self, svc, basic_request):
        confirmation = svc.create_confirmation_message(basic_request)
        assert basic_request.query in confirmation.confirmation_message

    def test_message_contains_total_estimate(self, svc, basic_request):
        confirmation = svc.create_confirmation_message(basic_request)
        assert "TOTAL ESTIMADO" in confirmation.confirmation_message

    def test_estimated_results_equals_limit(self, svc, basic_request):
        confirmation = svc.create_confirmation_message(basic_request)
        assert confirmation.estimated_results == basic_request.limit

    def test_credit_estimate_is_populated(self, svc, basic_request):
        confirmation = svc.create_confirmation_message(basic_request)
        assert confirmation.credit_estimate is not None
        assert confirmation.credit_estimate.total_estimated >= 1

    def test_message_mentions_fast(self, svc, basic_request):
        confirmation = svc.create_confirmation_message(basic_request)
        assert "FAST" in confirmation.confirmation_message


class TestParseCompanyLocation:
    def test_explicit_fields(self, svc):
        data = {"hq_city": "São Paulo", "hq_state": "SP", "hq_country": "Brasil"}
        city, state, country = svc._parse_company_location(data)
        assert city == "São Paulo"
        assert state == "SP"
        assert country == "Brasil"

    def test_empty_explicit_fallback_to_short_address(self, svc):
        data = {"short_address": "Rio de Janeiro, RJ, Brasil"}
        city, state, country = svc._parse_company_location(data)
        assert city == "Rio de Janeiro"
        assert country == "Brasil"

    def test_two_part_address(self, svc):
        data = {"short_address": "São Paulo, Brasil"}
        city, state, country = svc._parse_company_location(data)
        assert city == "São Paulo"
        assert country == "Brasil"

    def test_empty_data_returns_nones(self, svc):
        city, state, country = svc._parse_company_location({})
        assert city is None and state is None and country is None

    def test_partial_explicit_city_only(self, svc):
        data = {"hq_city": "Curitiba"}
        city, state, country = svc._parse_company_location(data)
        assert city == "Curitiba"
        assert state is None

    def test_fallback_to_locations_list(self, svc):
        data = {"locations": ["São Paulo, Brasil"]}
        city, state, country = svc._parse_company_location(data)
        assert country == "Brasil"


class TestParseInstitutionLocation:
    def test_explicit_fields(self, svc):
        data = {"institution_city": "Campinas", "institution_state": "SP", "institution_country": "Brasil"}
        city, state, country = svc._parse_institution_location(data)
        assert city == "Campinas"
        assert state == "SP"

    def test_city_state_field_fallback(self, svc):
        data = {"city": "Recife", "state": "PE", "country": "Brasil"}
        city, state, country = svc._parse_institution_location(data)
        assert city == "Recife"

    def test_location_string_fallback(self, svc):
        data = {"location": "Belo Horizonte, MG, Brasil"}
        city, state, country = svc._parse_institution_location(data)
        assert city == "Belo Horizonte"
        assert state == "MG"
        assert country == "Brasil"

    def test_empty_data_returns_nones(self, svc):
        city, state, country = svc._parse_institution_location({})
        assert city is None and state is None and country is None

    def test_two_part_location_string(self, svc):
        data = {"location": "Porto Alegre, Brasil"}
        city, state, country = svc._parse_institution_location(data)
        assert city == "Porto Alegre"
        assert country == "Brasil"
