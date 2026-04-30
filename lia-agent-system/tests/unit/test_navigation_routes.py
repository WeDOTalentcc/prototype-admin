"""
Sensor: navigate_to whitelist prevents dead-route emissions.

Post-mortem 2026-04-29 wizard UAT — Bug 4. Guards against regression
of route validation so backend producers never emit
`ui_action: navigate_to` with paths that don't exist in the Next.js
app (e.g. the deleted `/funil-de-talentos`).

Skill canônica: harness-engineering [sensor computacional].
"""
import pytest

from app.shared.navigation_routes import (
    VALID_ROUTES,
    safe_navigate_route,
    validate_navigate_route,
)


class TestValidateNavigateRoute:
    """Behavior contract for validate_navigate_route."""

    def test_known_route_passes(self):
        assert (
            validate_navigate_route("/teams-tab/candidatos")
            == "/teams-tab/candidatos"
        )

    def test_route_with_locale_passes(self):
        assert (
            validate_navigate_route("/pt/teams-tab/candidatos")
            == "/pt/teams-tab/candidatos"
        )

    def test_orphan_route_funil_de_talentos_rejected(self):
        """The exact bug case from post-mortem."""
        assert validate_navigate_route("/funil-de-talentos") is None

    def test_orphan_route_jobs_rejected(self):
        """Another route deleted in App Router migration."""
        assert validate_navigate_route("/jobs/abc-123") is None
        assert validate_navigate_route("/jobs") is None

    def test_dynamic_vagas_passes(self):
        """Dynamic /vagas/[slug] is allowed."""
        assert (
            validate_navigate_route("/vagas/dev-python-senior")
            == "/vagas/dev-python-senior"
        )

    def test_dynamic_with_locale_passes(self):
        assert (
            validate_navigate_route("/pt/vagas/python-jr")
            == "/pt/vagas/python-jr"
        )

    def test_query_string_ignored(self):
        assert (
            validate_navigate_route("/teams-tab/candidatos?filter=active")
            == "/teams-tab/candidatos?filter=active"
        )

    def test_hash_ignored(self):
        assert (
            validate_navigate_route("/configuracoes#benefits")
            == "/configuracoes#benefits"
        )

    def test_none_returns_none(self):
        assert validate_navigate_route(None) is None

    def test_empty_returns_none(self):
        assert validate_navigate_route("") is None

    def test_whitespace_returns_none(self):
        assert validate_navigate_route("   ") is None

    def test_random_path_rejected(self):
        assert validate_navigate_route("/random-not-a-route") is None


class TestSafeNavigateRoute:
    """Behavior contract for safe_navigate_route."""

    def test_valid_candidate_returned(self):
        assert (
            safe_navigate_route("/teams-tab/candidatos")
            == "/teams-tab/candidatos"
        )

    def test_invalid_candidate_uses_fallback(self):
        # The exact bug case: producer hardcoded /funil-de-talentos.
        assert safe_navigate_route("/funil-de-talentos") == "/"

    def test_custom_fallback_used_when_valid(self):
        assert (
            safe_navigate_route("/dead-route", fallback="/chat")
            == "/chat"
        )

    def test_invalid_fallback_falls_to_root(self):
        """Defense-in-depth: even the fallback is validated."""
        assert (
            safe_navigate_route("/dead", fallback="/another-dead")
            == "/"
        )


class TestRouteListIntegrity:
    """Sanity checks on the VALID_ROUTES set itself."""

    def test_dashboard_routes_present(self):
        """Routes in (dashboard) group must be in the whitelist."""
        for r in (
            "/agent-studio",
            "/configuracoes",
            "/chat",
            "/teams-tab/candidatos",
            "/teams-tab/vagas",
            "/biblioteca-lia",
        ):
            assert r in VALID_ROUTES, f"{r} missing from VALID_ROUTES"

    def test_orphan_routes_absent(self):
        """Routes deleted in 2026 App Router migration must NOT be here."""
        for orphan in (
            "/funil-de-talentos",
            "/jobs",
            "/jobs/new",
        ):
            assert orphan not in VALID_ROUTES, (
                f"{orphan} is an orphan route — remove from VALID_ROUTES"
            )
