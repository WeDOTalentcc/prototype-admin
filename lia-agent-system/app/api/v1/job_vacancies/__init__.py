"""
job_vacancies package — aggregates all sub-routers into a single `router`
and re-exports `router_public` for unauthenticated candidate flows.

Sub-modules:
  _shared    — shared imports, helpers, Pydantic schemas
  crud       — GET/POST/PUT/DELETE/PATCH + finalize/search/duplicate/clone (14 routes)
  lifecycle  — publish, confirm-global-search, sourcing-status, bulk ops, close (15 routes)
  analytics  — metrics, analytics, history, stats/overview, job report (6 routes)
  screening  — screening-config GET/PUT, screening-status PUT (3 routes)
  public     — generate-public-link, share-link (auth) + /p/{slug} GET/POST (4 routes)
  export     — PDF/Excel export (2 routes)

─── Routing invariant (Task #455) ──────────────────────────────────────────────
Within the `/job-vacancies` URL prefix, *static* collection routes
(`/job-vacancies/lifecycle-overview`, `/job-vacancies/stats/overview`,
`/job-vacancies/finalize`, `/job-vacancies/search`, `/job-vacancies/archetypes`,
`/job-vacancies/find-by-identifier`, `/job-vacancies/bulk/...`) MUST be
registered before any *item* route that captures `{job_vacancy_id}` /
`{job_id}` / `{vacancy_id}`. Otherwise the item handler silently shadows
the static segment and returns a misleading 404 when it tries to parse
the static name as a UUID.

This module enforces the invariant by partitioning every sub-router into
a collection-scoped half (no `{` in the path) and an item-scoped half
(at least one `{` in the path), then including ALL collection halves
before ANY item half. The regression test
`tests/api/test_job_vacancies_route_shadowing.py` documents the rule
and breaks the build if a future change reintroduces shadowing.

A second line of defense lives in the path-parameter contract itself:
`{job_vacancy_id}` is constrained by `JOB_ID_PATH_PATTERN` (UUID or
decimal integer) so a static segment like `lifecycle-overview` cannot
match the item handler's pattern even if ordering regresses.
"""

from fastapi import APIRouter
from fastapi.routing import APIRoute

from .analytics import router as _analytics_router, get_job_report  # noqa: F401
from .analytics import get_user_company_id  # noqa: F401
from .crud import router as _crud_router
from .export import router as _export_router
from .lifecycle import router as _lifecycle_router
from .public import router as _public_router
from .public import router_public
from .screening import router as _screening_router


def _split_collection_vs_item(src: APIRouter) -> tuple[APIRouter, APIRouter]:
    """Partition a router into (collection, item) routers.

    A route is "item-scoped" if its path contains at least one `{` —
    i.e. it captures a path parameter. Everything else is "collection-
    scoped" (operates on the resource collection, not a single row).

    Non-APIRoute entries (websockets, mounts) are conservatively bucketed
    as collection so they keep their original relative ordering.
    """
    coll = APIRouter()
    item = APIRouter()
    for route in src.routes:
        path = getattr(route, "path", "")
        if isinstance(route, APIRoute) and "{" in path:
            item.routes.append(route)
        else:
            coll.routes.append(route)
    # Preserve any router-level dependencies (e.g. crud.py's deprecation guard)
    # so endpoints behave identically after the split.
    coll.dependencies = list(src.dependencies)
    item.dependencies = list(src.dependencies)
    return coll, item


_crud_collection, _crud_item = _split_collection_vs_item(_crud_router)
_lifecycle_collection, _lifecycle_item = _split_collection_vs_item(_lifecycle_router)
_analytics_collection, _analytics_item = _split_collection_vs_item(_analytics_router)
_screening_collection, _screening_item = _split_collection_vs_item(_screening_router)
_public_collection, _public_item = _split_collection_vs_item(_public_router)
_export_collection, _export_item = _split_collection_vs_item(_export_router)


# Main aggregated router — collection routes first, item routes second.
# This ordering is the routing invariant guarded by the shadowing test.
router = APIRouter()

# 1) All collection-scoped routes across every sub-module.
router.include_router(_crud_collection)
router.include_router(_lifecycle_collection)
router.include_router(_analytics_collection)
router.include_router(_screening_collection)
router.include_router(_public_collection)
router.include_router(_export_collection)

# 2) All item-scoped routes (paths with `{...}` segments).
router.include_router(_crud_item)
router.include_router(_lifecycle_item)
router.include_router(_analytics_item)
router.include_router(_screening_item)
router.include_router(_public_item)
router.include_router(_export_item)

# router_public is already exported above — used as:
#   app.include_router(job_vacancies.router_public, prefix="/api/v1/public-vacancies", ...)

__all__ = ["router", "router_public", "get_job_report"]
