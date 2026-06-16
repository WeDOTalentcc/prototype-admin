"""Coverage tests for navigation_routes.py and ocean_constants.py"""
import pytest


# ===========================================================================
# app/shared/ocean_constants.py
# ===========================================================================
from app.shared.ocean_constants import ALLOWED_TRAITS


class TestOceanConstants:
    def test_allowed_traits_is_frozenset(self):
        assert isinstance(ALLOWED_TRAITS, frozenset)

    def test_has_five_traits(self):
        assert len(ALLOWED_TRAITS) == 5

    def test_contains_openness(self):
        assert "openness" in ALLOWED_TRAITS

    def test_contains_conscientiousness(self):
        assert "conscientiousness" in ALLOWED_TRAITS

    def test_contains_extraversion(self):
        assert "extraversion" in ALLOWED_TRAITS

    def test_contains_agreeableness(self):
        assert "agreeableness" in ALLOWED_TRAITS

    def test_contains_stability(self):
        # Note: stability (not neuroticism) per canonical
        assert "stability" in ALLOWED_TRAITS

    def test_immutable(self):
        with pytest.raises(AttributeError):
            ALLOWED_TRAITS.add("new_trait")  # type: ignore[attr-defined]


# ===========================================================================
# app/shared/navigation_routes.py
# ===========================================================================
from app.shared.navigation_routes import (
    VALID_ROUTES,
    DEFAULT_FALLBACK_ROUTE,
    validate_navigate_route,
    safe_navigate_route,
    _strip_locale,
    _strip_query_and_hash,
)


class TestValidRoutes:
    def test_is_frozenset(self):
        assert isinstance(VALID_ROUTES, frozenset)

    def test_has_entries(self):
        assert len(VALID_ROUTES) > 5

    def test_contains_root(self):
        assert "/" in VALID_ROUTES

    def test_contains_login(self):
        assert "/login" in VALID_ROUTES

    def test_contains_configuracoes(self):
        assert "/configuracoes" in VALID_ROUTES

    def test_default_fallback(self):
        assert DEFAULT_FALLBACK_ROUTE == "/"


class TestStripHelpers:
    def test_strip_locale_en(self):
        result = _strip_locale("/en/login")
        assert result == "/login"

    def test_strip_locale_pt(self):
        result = _strip_locale("/pt/configuracoes")
        assert result == "/configuracoes"

    def test_strip_locale_no_prefix(self):
        result = _strip_locale("/login")
        assert result == "/login"

    def test_strip_query(self):
        result = _strip_query_and_hash("/login?redirect=/jobs")
        assert result == "/login"
        assert "?" not in result

    def test_strip_hash(self):
        result = _strip_query_and_hash("/login#section")
        assert result == "/login"

    def test_strip_both(self):
        result = _strip_query_and_hash("/page?q=1#anchor")
        assert result == "/page"


class TestValidateNavigateRoute:
    def test_valid_route(self):
        result = validate_navigate_route("/login")
        assert result == "/login"

    def test_valid_route_root(self):
        result = validate_navigate_route("/")
        assert result == "/"

    def test_valid_route_configuracoes(self):
        result = validate_navigate_route("/configuracoes")
        assert result == "/configuracoes"

    def test_none_returns_none(self):
        assert validate_navigate_route(None) is None

    def test_empty_returns_none(self):
        assert validate_navigate_route("") is None

    def test_whitespace_returns_none(self):
        assert validate_navigate_route("   ") is None

    def test_invalid_route_returns_none(self):
        assert validate_navigate_route("/funil-de-talentos") is None

    def test_invalid_random_returns_none(self):
        assert validate_navigate_route("/totally-fake-route-xyz") is None

    def test_locale_prefix_preserved(self):
        result = validate_navigate_route("/pt/login")
        assert result == "/pt/login"

    def test_with_query_string_valid(self):
        result = validate_navigate_route("/login?redirect=/jobs")
        # Original path returned if base is valid
        assert result == "/login?redirect=/jobs"

    def test_dynamic_route_vagas(self):
        # /vagas/{slug} is a dynamic route pattern
        result = validate_navigate_route("/vagas/dev-python-senior")
        assert result == "/vagas/dev-python-senior"

    def test_teams_tab_pipeline(self):
        result = validate_navigate_route("/teams-tab/pipeline")
        assert result == "/teams-tab/pipeline"


class TestSafeNavigateRoute:
    def test_valid_candidate(self):
        result = safe_navigate_route("/login")
        assert result == "/login"

    def test_invalid_candidate_uses_fallback(self):
        result = safe_navigate_route("/invalid-xyz-route")
        assert result == "/"

    def test_custom_valid_fallback(self):
        result = safe_navigate_route("/invalid-route", fallback="/configuracoes")
        assert result == "/configuracoes"

    def test_invalid_fallback_uses_default(self):
        result = safe_navigate_route("/invalid", fallback="/also-invalid")
        assert result == DEFAULT_FALLBACK_ROUTE

    def test_none_candidate(self):
        result = safe_navigate_route(None)
        assert result == DEFAULT_FALLBACK_ROUTE

    def test_returns_string(self):
        result = safe_navigate_route("/login")
        assert isinstance(result, str)
