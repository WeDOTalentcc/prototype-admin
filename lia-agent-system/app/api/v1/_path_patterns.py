"""
Shared path-parameter regex patterns for FastAPI route declarations
under ``/api/v1``.

Why this module exists
----------------------
ADR 003 (`docs/adr/003-id-strategy-lia-vs-rails.md`) formalises that several
LIA entities are *dual-ID* — their primary key on the API surface can be
either a UUID v4 (rows authored locally) or a decimal integer (Rails bigint,
when the row was authored on the legacy Rails side and re-exposed via the
`RailsAdapter`). Job vacancies, candidates, applications/candidacies, and
interview/recruitment stages all fall in this bucket.

For routes that take such an ID as a path parameter, the parameter MUST be
constrained to one of these two shapes. Without the constraint, FastAPI
treats the segment as an unbounded ``str`` and a sibling static route
(e.g. ``/candidates/search``) can be silently captured by an item handler
(e.g. ``GET /candidates/{candidate_id}``) — the exact bug from Task #455.

Constraining ``{*_id}`` here serves two purposes:
  1. Static collection-scoped routes registered alongside the item route
     can never be silently shadowed if router ordering regresses — the
     regex simply does not match a string like ``"search"``.
  2. Garbage IDs receive a 422 from FastAPI before the handler runs,
     instead of a misleading 404 raised by ``UUID("garbage")`` inside.

Use ``DUAL_ID_PATH_PATTERN`` as ``Path(..., pattern=DUAL_ID_PATH_PATTERN)``
on every dual-ID path parameter. The structural test
``tests/api/test_dual_id_route_shadowing.py`` fails the build if any new
``{*_id}`` parameter on a dual-ID router is left as unconstrained ``str``.
"""

# UUID v4 OR decimal integer (Rails bigint). Anchored on both ends so the
# whole path segment must conform — partial matches are rejected.
DUAL_ID_PATH_PATTERN = (
    r"^([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}|\d+)$"
)

__all__ = ["DUAL_ID_PATH_PATTERN"]
