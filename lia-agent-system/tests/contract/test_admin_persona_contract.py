"""
Contract sensor para ``/api/v1/admin/persona/contract-version``.

Registrado 2026-05-21 (C5+C6 — Admin WeDOTalent Integration Contract).

Garante que o endpoint que time admin WeDOTalent vai chamar como
health-check + version probe:

1. Existe e tem signature canonical (`async def get_contract_version`).
2. Está gated por ``require_wedotalent_admin``.
3. Versão segue semver válido.
4. Lista de ``surfaces`` contém os identifiers canonical esperados.
5. Schema do response (``AdminPersonaContractVersionResponse``) tem os
   campos pinados — renomear força major bump.

Bumping ``ADMIN_PERSONA_CONTRACT_VERSION`` MAJOR sem coordenação com time
admin é quebra de contrato; este sensor é o gate canonical.
"""
from __future__ import annotations

import inspect
import re

import pytest

from app.api.v1 import admin_persona
from app.api.v1.admin_persona import (
    ADMIN_PERSONA_CONTRACT_VERSION,
    AdminPersonaContractVersionResponse,
    get_contract_version,
)


SEMVER_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:[-.][A-Za-z0-9.-]+)?$")


# ----------------------------------------------------------------------------
# Version string itself
# ----------------------------------------------------------------------------

def test_contract_version_is_valid_semver():
    assert SEMVER_PATTERN.match(ADMIN_PERSONA_CONTRACT_VERSION), (
        f"ADMIN_PERSONA_CONTRACT_VERSION '{ADMIN_PERSONA_CONTRACT_VERSION}' "
        f"is not valid semver."
    )


def test_contract_version_starts_at_least_at_1_0_0():
    """Pre-1.0 versions imply 'still moving' — admin WeDOTalent should
    not pin against anything below 1.0.0. Bump to 0.x.y only with explicit
    review."""
    major = int(ADMIN_PERSONA_CONTRACT_VERSION.split(".")[0])
    assert major >= 1, f"Major must be >=1; got {major}"


# ----------------------------------------------------------------------------
# Endpoint signature + gate
# ----------------------------------------------------------------------------

def test_endpoint_function_is_async_and_named_canonical():
    """get_contract_version is part of the wire contract — renaming it
    forces an admin-side code change."""
    assert inspect.iscoroutinefunction(get_contract_version)
    assert get_contract_version.__name__ == "get_contract_version"


def test_endpoint_requires_wedotalent_admin():
    """Same canonical gate as the rest of the admin surface. A 403 for
    customer-end roles is the wire contract."""
    src = inspect.getsource(get_contract_version)
    assert "require_wedotalent_admin" in src, (
        "get_contract_version must declare Depends(require_wedotalent_admin). "
        "Removing the gate exposes the contract version to customer-end "
        "roles — defense-in-depth posture broken."
    )


def test_endpoint_is_registered_under_admin_persona_prefix():
    """Router prefix is part of the URL contract. Renaming /admin/persona
    breaks the admin UI's hard-coded paths."""
    assert admin_persona.router.prefix == "/admin/persona"


# ----------------------------------------------------------------------------
# Response schema stability
# ----------------------------------------------------------------------------

EXPECTED_RESPONSE_FIELDS = {
    "contract_version", "major", "minor", "patch",
    "surfaces", "docs_url_relative",
}


def test_response_schema_has_canonical_fields():
    """Each field rename / removal = major bump. Pin them so a careless
    Pydantic refactor doesn't ship a breaking change silently."""
    fields = set(AdminPersonaContractVersionResponse.model_fields.keys())
    missing = EXPECTED_RESPONSE_FIELDS - fields
    assert not missing, (
        f"Missing canonical fields in response schema: {missing}. "
        f"Removing/renaming requires major bump of ADMIN_PERSONA_CONTRACT_VERSION."
    )


def test_response_schema_forbids_extra_fields():
    """Forbid extra fields so admin UI gets deterministic schema (no
    drift via accidental kwargs)."""
    config = AdminPersonaContractVersionResponse.model_config
    assert config.get("extra") == "forbid", (
        "AdminPersonaContractVersionResponse must use extra='forbid' to "
        "guarantee deterministic schema for admin WeDOTalent consumers."
    )


# ----------------------------------------------------------------------------
# Surfaces list (feature flags)
# ----------------------------------------------------------------------------

EXPECTED_SURFACES_BASELINE = {
    "tenant_overrides_crud",
    "ethics_invariants_validation",
    "audit_trail_per_change",
}


@pytest.mark.asyncio
async def test_endpoint_returns_baseline_surfaces():
    """Calling the function directly (bypassing FastAPI machinery) is the
    fastest possible smoke. Admin UI iterates ``surfaces`` to decide which
    features to render — removing a surface here is a contract break."""
    from unittest.mock import MagicMock
    user = MagicMock()
    user.role = "wedotalent_admin"
    user.is_active = True
    resp = await get_contract_version(current_user=user)
    surfaces = set(resp.surfaces)
    missing = EXPECTED_SURFACES_BASELINE - surfaces
    assert not missing, (
        f"Baseline surfaces missing from contract response: {missing}. "
        f"Removing a surface forces a major bump."
    )
