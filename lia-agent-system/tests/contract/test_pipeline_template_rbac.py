"""Contract tests: RBAC gates for Pipeline Templates endpoints.

Sprint Pipeline Templates Afya 2026-05-26 — Fase 4.1 (TDD canonical green).

Garante (via router-introspection canonical pattern, ref test_admin_persona_contract.py):

1. Mutations (POST/PUT/DELETE/archive/clone/seed-defaults) gateadas por
   require_pipeline_template_admin (admin + wedotalent_admin).
2. Reads (GET /, GET /{id}, GET /suggest, POST /{id}/increment-usage) abertos
   para qualquer role autenticada (recruiter incluído).
3. require_pipeline_template_admin canonical aceita exatamente {admin, wedotalent_admin}.
4. Apply endpoint (/vacancies/{id}/apply-pipeline-template) aberto a qualquer
   role autenticada — recrutador pode aplicar via wizard.
"""
from __future__ import annotations

import inspect

import pytest
from fastapi import Depends

from app.api.v1 import pipeline_templates as pt_module
from app.api.v1.pipeline_templates import (
    require_pipeline_template_admin,
    router,
    vacancy_apply_router,
)
from app.auth.models import UserRole


# ---------------------------------------------------------------------------
# require_pipeline_template_admin gate composition
# ---------------------------------------------------------------------------


def test_require_pipeline_template_admin_allowed_roles_canonical():
    """Gate canonical: {admin, wedotalent_admin} EXATAMENTE. Adicionar role nova
    sem atualizar este teste = quebra de contrato RBAC."""
    # require_role retorna um closure; o source revela a allowlist
    src = inspect.getsource(pt_module)
    assert "require_pipeline_template_admin = require_role([UserRole.admin, UserRole.wedotalent_admin])" in src, (
        "RBAC gate canonical drift — expected: "
        "require_pipeline_template_admin = require_role([UserRole.admin, UserRole.wedotalent_admin])"
    )


def test_require_pipeline_template_admin_is_callable():
    """Gate é uma dependency function utilizável em Depends()."""
    assert callable(require_pipeline_template_admin)


# ---------------------------------------------------------------------------
# Mutation endpoints gated
# ---------------------------------------------------------------------------


def _route_by_path_and_method(routes, path_suffix: str, method: str):
    matches = [
        r for r in routes
        if path_suffix in r.path and method.upper() in r.methods
    ]
    return matches[0] if matches else None


def _has_admin_gate(route) -> bool:
    """Inspect a route's dependant tree for require_pipeline_template_admin."""
    # FastAPI stores Depends in route.dependant.dependencies
    deps = route.dependant.dependencies
    for d in deps:
        # require_pipeline_template_admin é closure de require_role
        call = d.call
        if call is require_pipeline_template_admin:
            return True
        # Algumas versões resolvem para inner role_checker — checar nome qualificado
        if getattr(call, "__qualname__", "").startswith("require_role."):
            # Inspect closure cells for the allowed list
            closure = getattr(call, "__closure__", None) or ()
            for cell in closure:
                val = cell.cell_contents
                if isinstance(val, list) and UserRole.admin in val and UserRole.wedotalent_admin in val:
                    return True
    return False


MUTATION_ROUTES = [
    ("/company/pipeline-templates/", "POST"),                   # create
    ("/{template_id}", "PUT"),                                  # update
    ("/{template_id}", "DELETE"),                               # delete (legacy soft-delete)
    ("/{template_id}/archive", "POST"),                         # archive
    ("/{template_id}/clone", "POST"),                           # clone
    ("/seed-defaults", "POST"),                                 # seed
]


@pytest.mark.parametrize("path_suffix, method", MUTATION_ROUTES)
def test_mutation_endpoints_gated_by_admin(path_suffix, method):
    route = _route_by_path_and_method(router.routes, path_suffix, method)
    assert route is not None, (
        f"Mutation route {method} {path_suffix} not registered on router"
    )
    assert _has_admin_gate(route), (
        f"Mutation {method} {path_suffix} MUST be gated by require_pipeline_template_admin. "
        "Removing the gate exposes templates to recruiter/viewer roles."
    )


# ---------------------------------------------------------------------------
# Read endpoints NOT gated by admin
# ---------------------------------------------------------------------------


READ_ROUTES = [
    ("/company/pipeline-templates/", "GET"),       # list
    ("/{template_id}", "GET"),                     # get single
    ("/suggest", "GET"),                           # suggest
    ("/{template_id}/increment-usage", "POST"),    # increment-usage (legacy frontend)
]


@pytest.mark.parametrize("path_suffix, method", READ_ROUTES)
def test_read_endpoints_open_to_authenticated_users(path_suffix, method):
    route = _route_by_path_and_method(router.routes, path_suffix, method)
    assert route is not None, (
        f"Read route {method} {path_suffix} not registered on router"
    )
    assert not _has_admin_gate(route), (
        f"Read {method} {path_suffix} MUST NOT have admin gate. Recruiter/viewer should "
        "be able to view templates and apply usage telemetry."
    )


# ---------------------------------------------------------------------------
# Apply endpoint — vacancy_apply_router
# ---------------------------------------------------------------------------


def test_apply_endpoint_open_to_authenticated_users():
    """Apply é canonical no fluxo do wizard — recrutador chama via chat LIA."""
    routes = vacancy_apply_router.routes
    apply_route = _route_by_path_and_method(
        routes, "/apply-pipeline-template", "POST"
    )
    assert apply_route is not None
    assert not _has_admin_gate(apply_route), (
        "Apply endpoint MUST be open to recruiter/manager — wizard usage canonical"
    )


def test_apply_endpoint_registered():
    paths = [r.path for r in vacancy_apply_router.routes]
    assert any("/apply-pipeline-template" in p for p in paths), (
        f"apply-pipeline-template endpoint missing. Paths: {paths}"
    )


# ---------------------------------------------------------------------------
# UserRole canonical contract — pin enum members used by the gate
# ---------------------------------------------------------------------------


def test_userrole_admin_and_wedotalent_admin_exist():
    """Pin UserRole enum members. Renaming forces RBAC gate update."""
    assert UserRole.admin.value == "admin"
    assert UserRole.wedotalent_admin.value == "wedotalent_admin"
    assert UserRole.recruiter.value == "recruiter"
    assert UserRole.viewer.value == "viewer"


def test_recruiter_and_viewer_not_in_admin_gate():
    """Canonical: recruiter + viewer SÃO NEGADOS no gate de admin."""
    # Inspect the closure of require_pipeline_template_admin (an instance of role_checker)
    closure = require_pipeline_template_admin.__closure__ or ()
    allowed_lists = [
        c.cell_contents for c in closure
        if isinstance(c.cell_contents, list)
        and all(isinstance(x, UserRole) for x in c.cell_contents)
    ]
    assert allowed_lists, "could not extract allowed_roles from gate closure"
    allowed = allowed_lists[0]
    assert UserRole.admin in allowed
    assert UserRole.wedotalent_admin in allowed
    assert UserRole.recruiter not in allowed, "recruiter MUST be denied"
    assert UserRole.viewer not in allowed, "viewer MUST be denied"
    assert UserRole.manager not in allowed, "manager MUST be denied (Paulo decisão 2026-05-26)"
