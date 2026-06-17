"""
Task #455 — Routing invariant test for /api/v1/job-vacancies.

Background
----------
The aba "Vagas" of the Visão do Pipeline page calls
``GET /api/v1/job-vacancies/lifecycle-overview``. That endpoint used to
return 404 because it was registered AFTER ``GET /job-vacancies/{job_vacancy_id}``,
whose path parameter was typed ``str`` with no constraint. FastAPI happily
matched ``lifecycle-overview`` against ``{job_vacancy_id}``, then the
handler tried ``UUID("lifecycle-overview")``, raised ``ValueError``, and
returned the 404 from the ``except`` branch.

Two layers of defense protect against the bug coming back, and this test
documents both as executable specification:

1. *Path-parameter contract* — every ``{job_vacancy_id}`` / ``{job_id}`` /
   ``{vacancy_id}`` path parameter must reject anything that is not a UUID
   or a decimal integer. This means a static collection segment like
   ``lifecycle-overview`` cannot match an item route's pattern even if
   ordering regresses.

2. *Router ordering* — within ``/job-vacancies``, every collection-scoped
   static route is registered before any item-scoped route in the
   aggregated ``router`` exposed by ``app.api.v1.job_vacancies``.

If a future change reintroduces shadowing (e.g. by adding a new static
collection route inside ``crud.py`` after the item handler, or by
relaxing the path-parameter pattern), the assertions below break the
build and point straight at the regression.
"""
from __future__ import annotations

import pytest
from fastapi.routing import APIRoute

from app.api.v1.job_vacancies import router as job_vacancies_router


# All static collection-scoped paths under /job-vacancies that the
# product depends on. Each one must be served by the static handler,
# never silently captured by an item handler.
STATIC_COLLECTION_PATHS: list[str] = [
    "/job-vacancies",
    "/job-vacancies/lifecycle-overview",
    "/job-vacancies/stats/overview",
    "/job-vacancies/search",
    "/job-vacancies/archetypes",
    "/job-vacancies/find-by-identifier",
    "/job-vacancies/finalize",
    "/job-vacancies/bulk/pause",
    "/job-vacancies/bulk/resume",
    "/job-vacancies/bulk/archive",
    "/job-vacancies/bulk/assign-recruiter",
    "/job-vacancies/bulk/change-status",
]


def _api_routes() -> list[APIRoute]:
    return [r for r in job_vacancies_router.routes if isinstance(r, APIRoute)]


# Map each static collection path to the handler function that MUST receive
# the request. Resolving the route through FastAPI's own matching machinery
# is the closest we can get to an HTTP-level test without booting the full
# app (which requires the database, auth, and Rails adapter).
EXPECTED_HANDLERS: dict[tuple[str, str], str] = {
    ("GET", "/job-vacancies"): "list_job_vacancies",
    ("GET", "/job-vacancies/lifecycle-overview"): "get_job_lifecycle_overview",
    ("GET", "/job-vacancies/stats/overview"): "get_job_vacancies_stats_overview",
    ("GET", "/job-vacancies/search"): "search_job_vacancies",
    ("GET", "/job-vacancies/archetypes"): "get_archetypes",
    ("POST", "/job-vacancies/find-by-identifier"): "find_job_by_identifier",
    ("POST", "/job-vacancies/finalize"): "finalize_job_vacancy",
    ("POST", "/job-vacancies/bulk/pause"): "bulk_pause_job_vacancies",
    ("POST", "/job-vacancies/bulk/resume"): "bulk_resume_job_vacancies",
    ("POST", "/job-vacancies/bulk/archive"): "bulk_archive_job_vacancies",
    ("POST", "/job-vacancies/bulk/assign-recruiter"): "bulk_assign_recruiter",
    ("POST", "/job-vacancies/bulk/change-status"): "bulk_change_status",
}


@pytest.mark.parametrize("static_path", STATIC_COLLECTION_PATHS)
def test_static_collection_route_is_registered(static_path: str) -> None:
    """Each static collection path must be present as a literal route.

    A regression where the static handler is removed (and only an item
    handler with `{...}` is left to "match") would silently break the
    UI; making the literal presence an assertion catches that case.
    """
    paths = {r.path for r in _api_routes()}
    assert static_path in paths, (
        f"Static collection route {static_path!r} is not registered. "
        f"The Visão do Pipeline 'Vagas' tab and other features that rely "
        f"on this URL will return 404."
    )


@pytest.mark.parametrize("static_path", STATIC_COLLECTION_PATHS)
def test_static_collection_route_precedes_item_routes(static_path: str) -> None:
    """The static handler must be registered before any item route that
    captures the same prefix segment.

    FastAPI uses first-match routing, so the order of ``router.routes``
    is the source of truth. We compute the index of the static route
    and require it to be smaller than the index of any item route whose
    pattern would otherwise capture the same path.
    """
    routes = _api_routes()
    indices_by_path: dict[str, int] = {}
    for idx, r in enumerate(routes):
        # Keep the FIRST occurrence — that's what FastAPI matches.
        indices_by_path.setdefault(r.path, idx)

    static_idx = indices_by_path.get(static_path)
    assert static_idx is not None, (
        f"{static_path!r} not in router; cannot evaluate ordering."
    )

    # Find item routes whose path-regex would also match `static_path`.
    # We approximate this by checking item routes that share the same
    # parent prefix (e.g. /job-vacancies/{...} vs /job-vacancies/foo).
    parent_prefix = static_path.rsplit("/", 1)[0] + "/"
    for idx, r in enumerate(routes):
        if "{" not in r.path:
            continue
        if not r.path.startswith(parent_prefix):
            continue
        # Skip item routes that go deeper than the static path
        # (those can't possibly capture it).
        item_segments = r.path.count("/")
        static_segments = static_path.count("/")
        if item_segments != static_segments:
            continue
        assert static_idx < idx, (
            f"Item route {r.path!r} (index {idx}) is registered before "
            f"static collection route {static_path!r} (index {static_idx}). "
            f"This will cause {static_path!r} to be shadowed and return a "
            f"misleading 404. Register collection routes before item routes "
            f"in app/api/v1/job_vacancies/__init__.py."
        )


@pytest.mark.parametrize(
    ("verb", "route_path", "expected_handler_name"),
    [(verb, path, handler) for (verb, path), handler in sorted(EXPECTED_HANDLERS.items())],
)
def test_static_collection_route_dispatches_to_static_handler(
    verb: str, route_path: str, expected_handler_name: str
) -> None:
    """Run an actual request through FastAPI's matching machinery and
    assert that the static collection handler — not the item handler —
    is the one that ends up dispatched.

    This is the closest we can get to an end-to-end HTTP smoke test
    without booting the full backend (which requires DB, auth, and the
    Rails adapter). Each route's ``matches`` method is called in the
    same order FastAPI would in production, and the FIRST match wins.
    A regression where ``/job-vacancies/{job_vacancy_id}`` is registered
    before ``/job-vacancies/lifecycle-overview`` would surface here as
    the wrong handler name being returned.
    """
    scope = {
        "type": "http",
        "method": verb,
        "path": route_path,
        "headers": [],
        "query_string": b"",
        "path_params": {},
        "root_path": "",
    }

    matched_route = None
    for route in _api_routes():
        match, _child_scope = route.matches(scope)
        if match.name == "FULL":
            matched_route = route
            break

    assert matched_route is not None, (
        f"No route matched {verb} {route_path!r}; "
        f"the static collection handler is missing or unreachable."
    )
    handler_name = getattr(matched_route.endpoint, "__name__", "<unknown>")
    assert handler_name == expected_handler_name, (
        f"{verb} {route_path!r} dispatched to {handler_name!r} instead of "
        f"the expected static handler {expected_handler_name!r}. "
        f"This is the routing-shadowing bug from Task #455 — a static "
        f"collection route is being captured by an item handler. Verify "
        f"that collection routers are registered before item routers in "
        f"`app/api/v1/job_vacancies/__init__.py` and that "
        f"`{{job_vacancy_id}}` is constrained by `JOB_ID_PATH_PATTERN`."
    )


def test_close_vacancy_route_lives_under_job_vacancies_prefix() -> None:
    """Task #459 regression — ``POST /{vacancy_id}/close`` used to be
    registered without the ``/job-vacancies`` prefix, which mounted it
    as a top-level catch-all under ``/api/v1`` (any first segment would
    be parsed as ``vacancy_id``). Ensure it stays inside the proper
    namespace so future single-segment POSTs cannot be silently
    shadowed.

    Two assertions:
    1. The canonical path is registered and dispatches to ``close_vacancy``.
    2. The orphan top-level path ``/{vacancy_id}/close`` is NOT registered.
    """
    routes = _api_routes()

    # 1) canonical path exists and routes to close_vacancy
    canonical_scope = {
        "type": "http",
        "method": "POST",
        "path": "/job-vacancies/550e8400-e29b-41d4-a716-446655440000/close",
        "headers": [],
        "query_string": b"",
        "path_params": {},
        "root_path": "",
    }
    matched = None
    for route in routes:
        match, _ = route.matches(canonical_scope)
        if match.name == "FULL":
            matched = route
            break
    assert matched is not None, (
        "POST /job-vacancies/{uuid}/close did not match any registered route. "
        "Task #459 expected the close endpoint under the /job-vacancies prefix."
    )
    handler_name = getattr(matched.endpoint, "__name__", "<unknown>")
    assert handler_name == "close_vacancy", (
        f"POST /job-vacancies/{{uuid}}/close dispatched to {handler_name!r} "
        "instead of close_vacancy."
    )

    # 2) orphan top-level path must not exist as a registered route
    paths = {r.path for r in routes}
    assert "/{vacancy_id}/close" not in paths, (
        "Orphan top-level route /{vacancy_id}/close is still registered. "
        "Move it under the /job-vacancies prefix (Task #459)."
    )


def test_item_path_parameters_are_uuid_or_int_constrained() -> None:
    """Every ``{job_vacancy_id}`` / ``{job_id}`` / ``{vacancy_id}`` path
    parameter under ``/job-vacancies`` must reject non-UUID, non-digit
    segments.

    Without this constraint, a sibling static route added in the future
    (e.g. ``/job-vacancies/foo``) could be silently captured by an item
    handler and return 404 instead of being routed to its real handler.

    The check is structural: the parameter must either be typed as
    ``UUID`` (FastAPI auto-validates) OR have an explicit ``pattern``
    that does not accept arbitrary strings.
    """
    from uuid import UUID

    item_param_names = {"job_vacancy_id", "job_id", "vacancy_id"}
    offenders: list[str] = []

    for r in _api_routes():
        if not r.path.startswith("/job-vacancies/"):
            continue
        if "{" not in r.path:
            continue
        for param in r.dependant.path_params:
            if param.name not in item_param_names:
                continue
            annotation = getattr(param, "type_", None)
            # UUID-typed params are safe — FastAPI validates the format.
            if annotation is UUID:
                continue
            # str-typed params must have an explicit pattern constraint.
            # Pydantic v2 attaches the regex via field_info.metadata as a
            # `_PydanticGeneralMetadata(pattern=...)` entry rather than as
            # a top-level attribute on FieldInfo.
            field_info = getattr(param, "field_info", None)
            pattern = None
            if field_info is not None:
                pattern = getattr(field_info, "pattern", None)
                if not pattern:
                    for meta in getattr(field_info, "metadata", None) or []:
                        meta_pattern = getattr(meta, "pattern", None)
                        if meta_pattern:
                            pattern = meta_pattern
                            break
            if not pattern:
                offenders.append(f"{r.path}:{param.name}")

    assert not offenders, (
        "The following item-route path parameters under /job-vacancies "
        "are unconstrained `str` and would silently shadow any new "
        "static sibling route:\n  - "
        + "\n  - ".join(offenders)
        + "\nConstrain them with `Path(..., pattern=JOB_ID_PATH_PATTERN)` "
        "from `app.api.v1.job_vacancies._shared`."
    )
