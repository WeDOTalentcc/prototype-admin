"""
Canonical whitelist of valid frontend routes.

Post-mortem 2026-04-29 wizard UAT — Bug 4: backend code suggested
navigation to `/funil-de-talentos`, a route that does not exist in
the Next.js app. The frontend rendered the link / triggered the
navigate_to action and the user landed on a 404 page.

Why this happens: backend producers (capability checks, intent
mappers, notification services) hardcode route paths. When the
frontend route is renamed/removed, those producers point to dead
URLs — but the producers don't know.

Fix: every navigation path must pass through `validate_navigate_route`
before being emitted in a `ui_action: navigate_to` response. Invalid
paths return None — caller must decide whether to fall back to a sane
default (e.g. dashboard root) or omit the navigation action entirely.

Skill canônica: harness-engineering [guide computacional] +
canonical-fix (single source of truth for valid routes).

When the frontend adds/removes a route, update VALID_ROUTES below.
A future improvement is to auto-generate this list from
plataforma-lia/src/app/**/page.tsx at build time.
"""
from __future__ import annotations

import re
from typing import Optional

# Canonical list of valid frontend routes (locale-stripped).
# Paths starting with "/" are matched literally.
# Paths with "{}" placeholders (e.g. "/vagas/{slug}") match dynamic segments.
VALID_ROUTES: frozenset[str] = frozenset({
    "/",
    "/agent-studio",
    "/ajuda",
    "/bancos-de-talentos",
    "/biblioteca-lia",
    "/central-comunicacao",
    "/chat",
    "/configuracoes",
    "/configuracoes/ai-credits",
    "/design-system",
    "/forgot-password",
    "/login",
    "/login/welcome",
    "/privacidade",
    "/register",
    "/reset-password",
    "/teams-tab",
    "/teams-tab/candidatos",
    "/teams-tab/dashboard",
    "/teams-tab/pipeline",
    "/teams-tab/vagas",
    "/triagem/preview",
    "/triagem/preview/chat",
    "/triagem/preview/email",
    "/triagem/preview/email-reminder",
    "/triagem/preview/welcome",
    "/triagem/preview/whatsapp",
    "/recrutar",
    "/trust",
})

# Dynamic route patterns (regex). Each must anchor with ^ and $.
_DYNAMIC_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^/vagas/[^/]+$"),
    re.compile(r"^/triagem/[^/]+$"),
    re.compile(r"^/shared/[^/]+$"),
    re.compile(r"^/portal/data-request/[^/]+$"),
)

_LOCALE_PREFIX = re.compile(r"^/[a-z]{2}(?=/|$)")


def _strip_locale(path: str) -> str:
    """Remove `/<2-letter-locale>` prefix if present."""
    return _LOCALE_PREFIX.sub("", path) or "/"


def _strip_query_and_hash(path: str) -> str:
    """Drop `?query` and `#hash` for matching."""
    return path.split("?", 1)[0].split("#", 1)[0]


def validate_navigate_route(path: Optional[str]) -> Optional[str]:
    """Return the canonical path if it maps to an existing frontend route.

    Behavior:
      - None / empty / whitespace-only → None
      - Path that matches `VALID_ROUTES` (after stripping locale + query)
        → returns the original path (locale preserved if user supplied it)
      - Path matching a dynamic route pattern → returns the original path
      - Anything else → None (caller should NOT emit navigate_to)

    Examples:
        >>> validate_navigate_route("/teams-tab/candidatos")
        '/teams-tab/candidatos'
        >>> validate_navigate_route("/pt/teams-tab/candidatos")
        '/pt/teams-tab/candidatos'
        >>> validate_navigate_route("/funil-de-talentos") is None
        True
        >>> validate_navigate_route("/jobs/abc123") is None
        True
        >>> validate_navigate_route("/vagas/dev-python-senior")
        '/vagas/dev-python-senior'
        >>> validate_navigate_route(None) is None
        True
        >>> validate_navigate_route("") is None
        True
    """
    if not path or not path.strip():
        return None
    cleaned = _strip_query_and_hash(path.strip())
    # Try with and without locale prefix
    locale_stripped = _strip_locale(cleaned)
    if locale_stripped in VALID_ROUTES:
        return path
    # Dynamic patterns
    for pattern in _DYNAMIC_PATTERNS:
        if pattern.match(locale_stripped):
            return path
    return None


# Default fallback when caller wants navigation but their candidate
# route is invalid. Picks a safe page that always exists. The dashboard
# root (`/`) is the safest because it works for every authenticated
# user regardless of feature flags.
DEFAULT_FALLBACK_ROUTE: str = "/"


def safe_navigate_route(
    candidate: Optional[str],
    fallback: str = DEFAULT_FALLBACK_ROUTE,
) -> str:
    """Return `candidate` if valid, otherwise `fallback`.

    Use this in producer call-sites that ALWAYS want a navigation. If
    the producer can also choose to omit the navigation, prefer
    `validate_navigate_route` directly.
    """
    validated = validate_navigate_route(candidate)
    if validated is not None:
        return validated
    # Validate fallback too, so callers can't introduce a new dead route.
    fb_validated = validate_navigate_route(fallback)
    if fb_validated is not None:
        return fb_validated
    return DEFAULT_FALLBACK_ROUTE
