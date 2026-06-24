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

# Identificador de SESSÃO para endpoints de chat/SSE. String OPACA, NÃO é UUID:
# o FE gera ids como "lia-<timestamp>-<rand>". Aceita UUID, bigint E o formato
# lia-*. Bounded (1-128) + charset seguro (sem '/', '.', evita path traversal).
SESSION_ID_PATH_PATTERN = r"^[A-Za-z0-9_:-]{1,128}$"

def reorder_collection_before_item(router) -> None:
    """In-place reorder ``router.routes`` so every collection-scoped
    APIRoute (no ``{`` in its path) comes before any item-scoped
    APIRoute (at least one ``{`` in its path).

    This is the lightweight, single-file equivalent of the partition that
    ``app.api.v1.job_vacancies.__init__`` does across its sub-routers
    (Task #455). Call it once at the bottom of a single-file router
    module so source-order regressions cannot reintroduce the
    routing-shadowing bug. Combined with
    ``Path(pattern=DUAL_ID_PATH_PATTERN)`` on every ``{*_id}`` parameter,
    this is the same blindagem applied to ``/job-vacancies`` (Task #458).

    Non-APIRoute entries (websockets, mounts) are left in their original
    relative position by being treated as collection-scoped — they never
    capture path parameters anyway.
    """
    from fastapi.routing import APIRoute

    collection = []
    item = []
    for route in router.routes:
        path = getattr(route, "path", "")
        if isinstance(route, APIRoute) and "{" in path:
            item.append(route)
        else:
            collection.append(route)
    router.routes = collection + item

__all__ = [
    "DUAL_ID_PATH_PATTERN",
    "reorder_collection_before_item",
]

# Candidato com id LOCAL (UUID/bigint) OU id externo de sourcing
# (ex.: pearch slug "paul-criswell-7583691"). Para rotas que aceitam
# candidatos GLOBAIS nao-persistidos (ex.: experience-highlights), onde
# DUAL_ID_PATH_PATTERN rejeitaria o slug com 422. A precedencia sobre rotas
# estaticas irmas (/generate, /batch-generate) e garantida por
# reorder_collection_before_item, NAO por este pattern.
CANDIDATE_OR_SOURCING_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$"
