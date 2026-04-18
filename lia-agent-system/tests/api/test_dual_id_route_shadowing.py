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
from app.api.v1.recruitment_stages import (
    router as recruitment_stages_router,
    screening_questions_router,
)


# Each entry: (router, scope_label).
#
# The check auto-discovers any path parameter whose name ends in ``_id``
# rather than relying on a hardcoded allow-list — this is what makes the
# guard "generalised": a future ``{interview_id}`` or ``{note_id}`` added
# to one of these routers is automatically protected without anyone
# needing to remember to update this test.
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


def test_job_id_path_pattern_alias_still_exported() -> None:
    """``JOB_ID_PATH_PATTERN`` is kept as an alias of
    ``DUAL_ID_PATH_PATTERN`` for backward compatibility with existing
    job-vacancy handlers. Removing the alias would silently drop the
    constraint everywhere it's still imported by name.
    """
    from app.api.v1.job_vacancies._shared import JOB_ID_PATH_PATTERN

    assert JOB_ID_PATH_PATTERN == DUAL_ID_PATH_PATTERN
