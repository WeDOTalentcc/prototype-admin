"""Sentinel test for T2/#994 — culture endpoints relocated from
``app/api/v1/company.py`` to ``app/api/v1/company_culture.py``.

Guarantees:
1. The 4 public paths remain registered on the FastAPI app under the
   exact same URLs (the frontend must not break).
2. The handler functions live in ``company_culture`` (not in
   ``company``), enforcing the module-cohesion invariant going forward.
"""
from __future__ import annotations

import ast
import importlib
import inspect
import textwrap

import pytest


CULTURE_PATHS_AND_METHODS = [
    ("/api/v1/company/enrich", "POST"),
    ("/api/v1/company/auto-enrich/{profile_id}", "POST"),
    ("/api/v1/company/profile/{profile_id}/generate-evp", "POST"),
    ("/api/v1/company/analyze-culture", "POST"),
]


@pytest.fixture(scope="module")
def app():
    from app.main import app as fastapi_app  # noqa: WPS433 — lazy import for test

    return fastapi_app


def _route_index(app):
    """Map (path, method) → endpoint module so we can assert location."""
    index: dict[tuple[str, str], str] = {}
    for route in app.routes:
        path = getattr(route, "path", None)
        endpoint = getattr(route, "endpoint", None)
        methods = getattr(route, "methods", None) or set()
        if not path or endpoint is None:
            continue
        module = getattr(endpoint, "__module__", "")
        for method in methods:
            index[(path, method)] = module
    return index


def test_all_relocated_culture_paths_remain_registered(app):
    """The 4 legacy paths MUST still be served (no frontend breakage)."""
    index = _route_index(app)
    missing = [
        (path, method)
        for path, method in CULTURE_PATHS_AND_METHODS
        if (path, method) not in index
    ]
    assert not missing, f"Relocated culture endpoints missing from app: {missing}"


def test_relocated_culture_handlers_live_in_company_culture_module(app):
    """The handlers must be served from ``company_culture``, not ``company``.

    This is the cohesion guarantee — if someone re-adds these handlers
    to ``app.api.v1.company`` in the future, this test fails loudly.
    """
    index = _route_index(app)
    misplaced: list[tuple[str, str, str]] = []
    for path, method in CULTURE_PATHS_AND_METHODS:
        module = index.get((path, method), "")
        if not module.endswith(".company_culture"):
            misplaced.append((path, method, module))
    assert not misplaced, (
        "Culture handlers must live in app.api.v1.company_culture; found: "
        f"{misplaced}"
    )


def test_legacy_router_exported_from_company_culture():
    """The second router used in ``routes.py`` must exist on the module."""
    mod = importlib.import_module("app.api.v1.company_culture")
    assert hasattr(mod, "legacy_router"), (
        "company_culture.legacy_router missing — routes.py registration "
        "would fail."
    )
    legacy = mod.legacy_router
    # FastAPI APIRouter exposes ``.prefix`` and ``.routes``.
    assert legacy.prefix == "/company"
    legacy_paths = {getattr(r, "path", None) for r in legacy.routes}
    expected = {
        "/company/enrich",
        "/company/auto-enrich/{profile_id}",
        "/company/profile/{profile_id}/generate-evp",
        "/company/analyze-culture",
    }
    assert expected.issubset(legacy_paths), (
        f"legacy_router missing expected paths: {expected - legacy_paths}"
    )


# Task #1029 — explicit tenant gate sentinel for the relocated legacy
# endpoints. Each handler MUST accept ``current_user`` and invoke an
# explicit ``_require_company_id`` / ``_require_profile_in_tenant``
# helper. Without this gate the four endpoints rely on JWT + Postgres
# RLS only, which is one bug away from cross-tenant data exposure.
LEGACY_HANDLER_GATES = {
    "/company/enrich": ("enrich_company_profile", "_require_company_id"),
    "/company/auto-enrich/{profile_id}": (
        "auto_enrich_company",
        "_require_profile_in_tenant",
    ),
    "/company/profile/{profile_id}/generate-evp": (
        "generate_evp",
        "_require_profile_in_tenant",
    ),
    "/company/analyze-culture": ("analyze_company_culture", "_require_company_id"),
}


@pytest.fixture(scope="module")
def company_culture_module():
    return importlib.import_module("app.api.v1.company_culture")


def test_legacy_router_handlers_accept_current_user(company_culture_module):
    """Every legacy handler must depend on ``current_user`` (Task #1029).

    A handler missing the dependency cannot enforce a tenant gate at
    all — anonymous traffic would slip through to the protected work
    (paid Apify/LLM calls, profile mutations).
    """
    legacy_router = company_culture_module.legacy_router
    routes_by_path = {
        getattr(r, "path", None): getattr(r, "endpoint", None)
        for r in legacy_router.routes
    }
    missing: list[tuple[str, str]] = []
    for path, (expected_name, _gate) in LEGACY_HANDLER_GATES.items():
        endpoint = routes_by_path.get(path)
        assert endpoint is not None, f"legacy_router missing handler for {path}"
        assert endpoint.__name__ == expected_name, (
            f"unexpected handler bound to {path}: got {endpoint.__name__}"
        )
        sig = inspect.signature(endpoint)
        if "current_user" not in sig.parameters:
            missing.append((path, expected_name))
    assert not missing, (
        "Legacy culture handlers without `current_user` dependency "
        f"(Task #1029 tenant gate missing): {missing}"
    )


def _called_function_names(func) -> set[str]:
    """Collect every callable name invoked anywhere inside ``func`` body.

    AST-based — immune to false positives from docstrings, comments, or
    string literals (a substring match on ``inspect.getsource`` is not).
    """
    source = textwrap.dedent(inspect.getsource(func))
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Name):
                names.add(target.id)
            elif isinstance(target, ast.Attribute):
                names.add(target.attr)
    return names


def test_legacy_router_handlers_invoke_tenant_gate(company_culture_module):
    """Every legacy handler body must actually CALL the explicit gate helper.

    AST-based check (not substring): the gate must appear as an
    ``ast.Call`` target inside the handler body. Catches the regression
    of someone adding ``current_user`` to the signature, or naming the
    helper only in a docstring/comment, without actually invoking it.
    """
    legacy_router = company_culture_module.legacy_router
    routes_by_path = {
        getattr(r, "path", None): getattr(r, "endpoint", None)
        for r in legacy_router.routes
    }
    failures: list[tuple[str, str, set[str]]] = []
    for path, (expected_name, gate_name) in LEGACY_HANDLER_GATES.items():
        endpoint = routes_by_path.get(path)
        called = _called_function_names(endpoint)
        if gate_name not in called:
            failures.append((path, gate_name, called))
    assert not failures, (
        "Legacy culture handlers missing explicit tenant gate CALL "
        f"(Task #1029): {failures}"
    )


def test_require_company_id_helper_rejects_unauthenticated(company_culture_module):
    """``_require_company_id`` must 401 on missing user, 403 on missing claim."""
    from fastapi import HTTPException

    helper = company_culture_module._require_company_id

    with pytest.raises(HTTPException) as missing_user:
        helper(None)
    assert missing_user.value.status_code == 401

    class _UserNoCompany:
        company_id = None

    with pytest.raises(HTTPException) as missing_claim:
        helper(_UserNoCompany())
    assert missing_claim.value.status_code == 403

    class _UserOk:
        company_id = "00000000-0000-4000-a000-000000000001"

    assert helper(_UserOk()) == "00000000-0000-4000-a000-000000000001"
