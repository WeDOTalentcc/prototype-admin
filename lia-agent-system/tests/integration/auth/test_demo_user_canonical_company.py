"""Regression: demo user must be created with canonical Demo Company UUID.

Task #1043. Before this fix, ``app/auth/dependencies.py`` created the
demo user with ``company_id="demo_company"`` (string literal), which
does not match any row in the ``companies`` table (the canonical
seed uses UUID ``00000000-0000-4000-a000-000000000001``). The
``TenantContextService`` then resolved an empty/generic context, and
the LIA Wizard ended up asking the recruiter for company name/sector
in the chat — the T-E anti-pattern.

This test asserts:

1. The legacy literal ``"demo_company"`` is gone from the demo-user
   creation paths in ``app/auth/dependencies.py``.
2. ``CANONICAL_DEMO_UUID`` is referenced in those paths.
3. The Alembic heal migration ``129_heal_demo_user_company_id`` exists
   and references both the legacy id and the canonical UUID.
"""
from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
DEPENDENCIES_PY = REPO / "app" / "auth" / "dependencies.py"
HEAL_MIGRATION = REPO / "alembic" / "versions" / "129_heal_demo_user_company_id.py"


def test_dependencies_does_not_hardcode_legacy_demo_company_string() -> None:
    src = DEPENDENCIES_PY.read_text(encoding="utf-8")
    assert 'company_id="demo_company"' not in src, (
        "Found legacy 'company_id=\"demo_company\"' literal in "
        "app/auth/dependencies.py. Use scripts.seeds.demo_company.CANONICAL_DEMO_UUID "
        "instead so TenantContextService can resolve the demo tenant. "
        "See Task #1043 (T-E regression)."
    )
    assert "CANONICAL_DEMO_UUID" in src, (
        "app/auth/dependencies.py must import CANONICAL_DEMO_UUID from "
        "scripts.seeds.demo_company when creating the demo user."
    )


def test_heal_migration_present_and_correct() -> None:
    assert HEAL_MIGRATION.exists(), (
        "Missing Alembic migration 129_heal_demo_user_company_id. "
        "Existing demo users with company_id='demo_company' need a "
        "data heal to point at the canonical UUID."
    )
    src = HEAL_MIGRATION.read_text(encoding="utf-8")
    assert "demo_company" in src
    assert "00000000-0000-4000-a000-000000000001" in src
    assert 'down_revision = "128_company_profile_is_default_not_null"' in src


def test_canonical_demo_uuid_constant_is_stable() -> None:
    """If the canonical UUID ever changes, the heal migration must change too."""
    from scripts.seeds.demo_company import CANONICAL_DEMO_UUID
    assert CANONICAL_DEMO_UUID == "00000000-0000-4000-a000-000000000001"
