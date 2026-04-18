"""
Task #470 — Generalised routing invariant for dual-ID entities.

Background
----------
Task #455 fixed a shadowing bug on ``/job-vacancies/{job_vacancy_id}``: a
``str``-typed item parameter silently captured the static sibling segment
``lifecycle-overview`` and the handler returned a misleading 404. The fix
combined router ordering with a regex-constrained path parameter
(``JOB_ID_PATH_PATTERN``).

ADR 003 (`docs/adr/003-id-strategy-lia-vs-rails.md`) extended the rule:
the *same* shape of route exists for **candidates**, **applications**, and
**interview/recruitment stages**, all of which are dual-ID entities (UUID
*or* Rails bigint). Today none of the static sibling routes on those
families have actually collided with item routes, but the trap is open —
adding ``/candidates/search`` next to ``GET /candidates/{candidate_id}``
without the regex would reproduce Task #455 verbatim.

This test fails the build whenever any new ``{*_id}`` path parameter on
those dual-ID routers is left as unconstrained ``str``. It complements
the original ``test_item_path_parameters_are_uuid_or_int_constrained``
which still guards ``/job-vacancies`` specifically.
"""
from __future__ import annotations

from uuid import UUID

import pytest
from fastapi.routing import APIRoute

from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN
from app.api.v1.applications import router as applications_router
from app.api.v1.candidates import router as candidates_router
from app.api.v1.lgpd_compliance import router as lgpd_compliance_router
from app.api.v1.policy_engine import router as policy_engine_router
from app.api.v1.proactive_actions import router as proactive_actions_router
from app.api.v1.recruitment_stages import (
    router as recruitment_stages_router,
    screening_questions_router,
)
from app.api.v1.wizard_analytics import router as wizard_analytics_router


# Each entry: (router, scope_label).
#
# The check auto-discovers any path parameter whose name ends in ``_id``
# rather than relying on a hardcoded allow-list — this is what makes the
# guard "generalised": a future ``{interview_id}`` or ``{note_id}`` added
# to one of these routers is automatically protected without anyone
# needing to remember to update this test.
#
# Task #458 extends the coverage to the remaining single-file ``/api/v1``
# routers that previously had unconstrained ``{*_id}: str`` path
# parameters: proactive-actions, wizard-analytics, lgpd, policy-engine.
DUAL_ID_ROUTERS = [
    pytest.param(candidates_router, "candidates", id="candidates"),
    pytest.param(applications_router, "applications", id="applications"),
    pytest.param(
        recruitment_stages_router, "recruitment-stages", id="recruitment-stages"
    ),
    pytest.param(
        screening_questions_router,
        "screening-questions",
        id="screening-questions",
    ),
    pytest.param(
        proactive_actions_router, "proactive-actions", id="proactive-actions"
    ),
    pytest.param(
        wizard_analytics_router, "wizard-analytics", id="wizard-analytics"
    ),
    pytest.param(lgpd_compliance_router, "lgpd", id="lgpd"),
    pytest.param(policy_engine_router, "policy-engine", id="policy-engine"),
]


# Task #458 — Routers where collection-before-item ordering is enforced
# in-module via ``reorder_collection_before_item``. The structural test
# below asserts that within each router every collection-scoped APIRoute
# (no ``{`` in path) is registered before any item-scoped APIRoute, so a
# future static sibling cannot be silently shadowed.
COLLECTION_BEFORE_ITEM_ROUTERS = [
    pytest.param(
        proactive_actions_router, "proactive-actions", id="proactive-actions"
    ),
    pytest.param(
        wizard_analytics_router, "wizard-analytics", id="wizard-analytics"
    ),
    pytest.param(lgpd_compliance_router, "lgpd", id="lgpd"),
    pytest.param(policy_engine_router, "policy-engine", id="policy-engine"),
]


def _api_routes(router) -> list[APIRoute]:
    return [r for r in router.routes if isinstance(r, APIRoute)]


def _param_pattern(param) -> str | None:
    """Pull the ``pattern=`` regex off a Pydantic v2 path parameter.

    Pydantic v2 attaches the regex via ``field_info.metadata`` as a
    ``_PydanticGeneralMetadata(pattern=...)`` entry rather than as a
    top-level attribute on FieldInfo, so we have to walk both shapes.
    """
    field_info = getattr(param, "field_info", None)
    if field_info is None:
        return None
    pattern = getattr(field_info, "pattern", None)
    if pattern:
        return pattern
    for meta in getattr(field_info, "metadata", None) or []:
        meta_pattern = getattr(meta, "pattern", None)
        if meta_pattern:
            return meta_pattern
    return None


@pytest.mark.parametrize(("router", "scope_label"), DUAL_ID_ROUTERS)
def test_dual_id_path_parameters_are_constrained(
    router, scope_label: str
) -> None:
    """Every ``{*_id}`` path parameter on a dual-ID router must reject
    anything that is not a UUID or a decimal integer.

    Without this constraint, a sibling static route added in the future
    (e.g. ``/candidates/search``) could be silently captured by an item
    handler and return 404 instead of being routed to its real handler —
    the exact failure mode of Task #455.

    The check is structural and self-updating: it auto-discovers any
    path parameter whose name ends in ``_id``, so a new ``{interview_id}``
    or ``{note_id}`` added to one of these routers is automatically
    protected without anyone needing to remember to update this test.
    The parameter must either be typed as ``UUID`` (FastAPI
    auto-validates) OR carry an explicit ``pattern`` attached via
    ``Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)]``.
    """
    offenders: list[str] = []

    for r in _api_routes(router):
        if "{" not in r.path:
            continue
        for param in r.dependant.path_params:
            if not param.name.endswith("_id"):
                continue
            annotation = getattr(param, "type_", None)
            if annotation is UUID:
                continue
            pattern = _param_pattern(param)
            if not pattern:
                offenders.append(f"{r.path}:{param.name}")

    assert not offenders, (
        f"The following item-route path parameters in the {scope_label!r} "
        f"router are unconstrained `str` and would silently shadow any "
        f"new static sibling route (Task #455-class bug):\n  - "
        + "\n  - ".join(offenders)
        + "\nConstrain them with "
        "`Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)]` from "
        "`app.api.v1._path_patterns`."
    )


@pytest.mark.parametrize(
    ("router", "scope_label"), COLLECTION_BEFORE_ITEM_ROUTERS
)
def test_collection_routes_precede_item_routes(router, scope_label: str) -> None:
    """Within each single-file router that opted into the Task #458
    blindagem, every collection-scoped ``APIRoute`` must be registered
    before any item-scoped ``APIRoute``.

    FastAPI uses first-match routing, so the position of a route in
    ``router.routes`` is the source of truth. The
    ``reorder_collection_before_item`` helper is invoked at the bottom
    of each opted-in module to guarantee this; this test breaks the
    build if either the helper call is removed or new routes are
    appended after it without re-running it.
    """
    routes = _api_routes(router)
    # Index of the LAST collection-scoped route, then the FIRST item-
    # scoped route. The first must come before the second.
    last_collection_idx = -1
    first_item_idx = None
    for idx, r in enumerate(routes):
        if "{" in r.path:
            if first_item_idx is None:
                first_item_idx = idx
        else:
            last_collection_idx = idx

    if first_item_idx is None or last_collection_idx == -1:
        # Router has only one kind of route — invariant trivially holds.
        return

    assert last_collection_idx < first_item_idx, (
        f"In the {scope_label!r} router, a collection-scoped route at "
        f"index {last_collection_idx} is registered AFTER an item-scoped "
        f"route at index {first_item_idx}. This reintroduces the Task "
        f"#455 routing-shadowing bug — the static collection segment "
        f"will be silently captured by the item handler. Make sure "
        f"``reorder_collection_before_item(router)`` runs at the bottom "
        f"of the module after all routes are declared."
    )


def test_dual_id_path_pattern_accepts_uuid_and_bigint() -> None:
    """Sanity-check the regex itself: it must accept UUIDs and decimal
    integers, and reject anything else (so static sibling segments stay
    safe from item-route capture).
    """
    import re

    rx = re.compile(DUAL_ID_PATH_PATTERN)
    # accept
    assert rx.match("550e8400-e29b-41d4-a716-446655440000")
    assert rx.match("12345")
    assert rx.match("1")
    # reject — these are the segments most at risk of shadowing
    assert not rx.match("search")
    assert not rx.match("lifecycle-overview")
    assert not rx.match("favorites")
    assert not rx.match("hidden")
    assert not rx.match("viewed")
    assert not rx.match("health")
    assert not rx.match("12345abc")
    assert not rx.match("")


# =============================================
# Task #476 — Whole-app structural guard
# =============================================
#
# The router-by-router check above is precise but it relies on someone
# remembering to add a new dual-ID router to ``DUAL_ID_ROUTERS`` whenever
# one is created. That's exactly the human-memory step that burned us in
# Tasks #455, #459, and #468 (a new endpoint shipped that skipped the ID
# safety rule, and nobody noticed until production).
#
# The test below does NOT rely on that allow-list. It imports the real
# FastAPI app, walks every registered route, and fails the build the
# moment a route under one of the dual-ID URL spaces declared in ADR 003
# (``/api/v1/job-vacancies``, ``/api/v1/public-vacancies``,
# ``/api/v1/candidates``, ``/api/v1/applications``,
# ``/api/v1/recruitment-stages``) carries an item-route path parameter
# whose name ends in ``_id`` and is typed as bare ``str`` (no UUID
# annotation, no ``pattern=DUAL_ID_PATH_PATTERN``).
#
# This is the "structural test that fails the build when somebody adds a
# new ``{*_id}: str`` path parameter on a dual-ID resource without the
# dual-ID regex" called for by the ID Boundary Policy
# (`docs/architecture/id-boundary-policy.md`, §3 and §8).

# Every URL-space that ADR 003 designates as dual-ID. Adding a new
# dual-ID resource here is a one-line opt-in; the rest of the check is
# automatic. The list intentionally lives next to the test rather than
# next to the routers themselves so this file remains the single source
# of truth — the policy check shouldn't be silently disabled by editing
# the router being checked.
DUAL_ID_URL_PREFIXES: tuple[str, ...] = (
    "/api/v1/job-vacancies",
    "/api/v1/public-vacancies",
    "/api/v1/candidates",
    "/api/v1/applications",
    "/api/v1/recruitment-stages",
)


def test_every_dual_id_route_constrains_id_path_params() -> None:
    """Walk every route registered on the real FastAPI app and fail if
    any path parameter ending in ``_id`` on a dual-ID resource is typed
    as bare ``str`` without the dual-ID regex.

    This is the *generalised* version of
    ``test_item_path_parameters_are_uuid_or_int_constrained`` (which
    covers ``/job-vacancies`` only) and the per-router parametrised
    check above (which covers a hand-maintained list of routers).

    Why a third check? Because both of the existing checks rely on a
    human remembering to extend an allow-list. This one does not — it
    starts from the real ``app.routes`` and only asks whether each route
    falls under a dual-ID URL space (per ADR 003, see
    ``DUAL_ID_URL_PREFIXES`` above). A new endpoint added under any of
    those spaces is policed automatically; if it skips the safety rule,
    the build fails with a message that points at the policy.
    """
    from app.main import app  # noqa: PLC0415 — heavy import, kept lazy

    offenders: list[str] = []

    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        path = route.path
        if not any(path.startswith(prefix) for prefix in DUAL_ID_URL_PREFIXES):
            continue
        if "{" not in path:
            continue
        for param in route.dependant.path_params:
            if not param.name.endswith("_id"):
                continue
            annotation = getattr(param, "type_", None)
            if annotation is UUID:
                continue
            pattern = _param_pattern(param)
            # The contract is the dual-ID regex specifically — any other
            # regex (e.g. a tighter UUID-only one, or a free-form match)
            # would either be too narrow to accept Rails bigints or too
            # loose to reject sibling static segments. Require equality
            # so the policy can't be silently weakened.
            if pattern == DUAL_ID_PATH_PATTERN:
                continue
            methods = ",".join(sorted(route.methods or {"?"}))
            suffix = f" (current pattern: {pattern!r})" if pattern else ""
            offenders.append(f"{methods} {path}:{param.name}{suffix}")

    assert not offenders, (
        "The following routes live under a dual-ID URL space (per ADR "
        "003) but declare a `{*_id}` path parameter as unconstrained "
        "`str`. This is a Task #455-class bug: a sibling static segment "
        "(e.g. `/candidates/search`) can be silently captured by the "
        "item handler and surface as a misleading 404.\n  - "
        + "\n  - ".join(sorted(offenders))
        + "\n\nFix: type the parameter as `UUID`, OR declare it as "
        "`Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)]` from "
        "`app.api.v1._path_patterns`. See the ID Boundary Policy: "
        "`docs/architecture/id-boundary-policy.md` §3 and the checklist "
        "in §8."
    )


def test_job_id_path_pattern_alias_still_exported() -> None:
    """``JOB_ID_PATH_PATTERN`` is kept as an alias of
    ``DUAL_ID_PATH_PATTERN`` for backward compatibility with existing
    job-vacancy handlers. Removing the alias would silently drop the
    constraint everywhere it's still imported by name.
    """
    from app.api.v1.job_vacancies._shared import JOB_ID_PATH_PATTERN

    assert JOB_ID_PATH_PATTERN == DUAL_ID_PATH_PATTERN
