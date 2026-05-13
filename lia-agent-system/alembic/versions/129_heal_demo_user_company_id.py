"""Heal users.company_id='demo_company' -> canonical UUID.

Revision ID: 129_heal_demo_user_company_id
Revises: 128_company_profile_is_default_not_null
Create Date: 2026-05-13

Background
----------
Task #1043 / PR-A. ``app/auth/dependencies.py`` (auto-login fallback at
``ensure_demo_user`` and ``get_current_user_or_demo``) historically
created the demo user with ``company_id="demo_company"`` (string literal),
while the canonical ``Demo Company`` row in ``companies`` lives under
UUID ``00000000-0000-4000-a000-000000000001`` (Task #966 seed).

Effect: ``TenantContextService.resolve_for_company(...)`` looked up
``companies WHERE id='demo_company'`` -> 0 rows -> empty/generic
``TenantContext`` -> the LIA Wizard prompted the recruiter for company
name/sector/plan in the chat (anti-pattern T-B/T-E from ``replit.md``).

Fix: re-point legacy demo users to the canonical UUID so existing
sessions / DBs heal automatically on deploy. The code-path that created
the bad rows is fixed in ``app/auth/dependencies.py`` (same PR);
this migration cleans up the historical residue.

Idempotent: re-running is a no-op once converged.
"""
from alembic import op
import sqlalchemy as sa


revision = "129_heal_demo_user_company_id"
down_revision = "128_company_profile_is_default_not_null"
branch_labels = None
depends_on = None


LEGACY_DEMO_ID = "demo_company"
CANONICAL_DEMO_UUID = "00000000-0000-4000-a000-000000000001"


def _table_exists(conn, table: str) -> bool:
    return bool(conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
        "WHERE table_schema='public' AND table_name=:t)"
    ), {"t": table}).scalar())


def upgrade() -> None:
    conn = op.get_bind()

    if not _table_exists(conn, "users"):
        return

    legacy_count = conn.execute(
        sa.text("SELECT COUNT(*) FROM users WHERE company_id = :legacy"),
        {"legacy": LEGACY_DEMO_ID},
    ).scalar() or 0

    if legacy_count == 0:
        return

    conn.execute(
        sa.text(
            "UPDATE users SET company_id = :canonical "
            "WHERE company_id = :legacy"
        ),
        {"canonical": CANONICAL_DEMO_UUID, "legacy": LEGACY_DEMO_ID},
    )


def downgrade() -> None:
    # Intentionally a no-op: reverting would re-introduce the bug.
    # The legacy string ``demo_company`` is not a valid FK to companies.id.
    pass
