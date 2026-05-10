"""Enrich companies schema with sector/plan/timezone/persona + id-format check.

Revision ID: 127_enrich_companies_schema
Revises: 30c0e47d1f56
Create Date: 2026-05-10

Background
----------
Task #969 (T-C canonica). The ``companies`` table historically held only
``id, name, display_name, is_active, is_demo, created_at, updated_at``.
``TenantContextService.get_context()`` therefore always fell back to
``sector="geral"``, ``plan="standard"``, ``timezone="America/Sao_Paulo"``
even for real tenants — making the LIA prompt snippet generic regardless
of who the tenant actually is.

This migration adds the columns required by ``TenantContext`` so the
snippet can be populated from the database instead of from defaults:

- ``sector`` — high-level industry label (e.g. ``"Tecnologia"``)
- ``industry_segment`` — narrower segment (e.g. ``"HRTech"``)
- ``plan`` — commercial tier (``"standard" | "professional" | "enterprise"``)
- ``timezone`` — IANA TZ string for tenant-local time formatting
- ``lia_persona_override`` — optional tenant-specific persona text
- ``headcount_range`` — coarse sizing label (``"50-200"``)

It also installs a CHECK constraint that mirrors
``app.shared.value_objects.CompanyId.parse()`` (T-A): ``id`` must be a
UUID v4 OR a ``[a-z][a-z0-9_-]{2,63}`` slug. This makes the database
fail for the same reason the application VO fails — no more ``""``,
``"default"``, ``"null"``, or whitespace ids slipping in via raw SQL.

Slugs remain valid for legacy compat (``demo_company``,
``test_tenant``, etc.); aposentadoria de slug e' assunto separado.
"""
from alembic import op
import sqlalchemy as sa


revision = "127_enrich_companies_schema"
# Merges the two open heads at the time of writing:
#   - 126_rls_t8_other_misc (RLS chain — the actual deployed head)
#   - 30c0e47d1f56          (merge of sox079_lgpd108_wsi117)
# so this single revision becomes the new sole head.
down_revision = ("126_rls_t8_other_misc", "30c0e47d1f56")
branch_labels = None
depends_on = None


# Mirrors CompanyId.parse() in app/shared/value_objects/company_id.py.
# UUID v4: lower-case hex, version nibble 4, variant nibble 8/9/a/b.
_UUID_V4_REGEX = (
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
# Slug: starts lowercase letter, 3-64 chars total, [a-z0-9_-].
_SLUG_REGEX = r"^[a-z][a-z0-9_-]{2,63}$"

# Reserved literals that look like valid slugs but are forbidden as
# tenant identifiers — must stay in lock-step with the
# ``_RESERVED_SLUG_LITERALS`` set in
# ``app/shared/value_objects/company_id.py``. These are blocked because
# they are historically used as "no tenant resolved" sentinels and any
# row carrying them would silently degrade tenant isolation.
# Must be EXACTLY equal to ``_FORBIDDEN_LITERALS`` in
# ``app/shared/value_objects/company_id.py`` so DB and value object
# fail "pelo mesmo motivo" for these reserved sentinels (Task #969
# acceptance criterion).
#
# Defense-in-depth note: ``CompanyId.parse()`` performs ``strip().lower()``
# *before* validating, so it normalises e.g. ``"  Demo_Company  "`` into
# ``"demo_company"`` and accepts it. The CHECK below intentionally does
# NOT normalise — it is a *canonical-only* floor and rejects raw
# whitespace/uppercase that would only arrive in the table if some code
# path bypassed the value object. This asymmetry is deliberate: the VO
# is the front gate, the constraint is the last line of defense.
_RESERVED_SLUG_LITERALS = (
    "default", "none", "null", "undefined", "system", "anonymous",
)

ID_FORMAT_CHECK = "ck_companies_id_format_canonical"


def _column_exists(conn, table: str, column: str) -> bool:
    return bool(conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name=:t AND column_name=:c)"
    ), {"t": table, "c": column}).scalar())


def _constraint_exists(conn, table: str, constraint: str) -> bool:
    return bool(conn.execute(sa.text(
        "SELECT EXISTS ("
        " SELECT 1 FROM pg_constraint c "
        " JOIN pg_class cl ON cl.oid = c.conrelid "
        " JOIN pg_namespace n ON n.oid = cl.relnamespace "
        " WHERE n.nspname='public' AND cl.relname=:t AND c.conname=:c)"
    ), {"t": table, "c": constraint}).scalar())


def _table_exists(conn, table: str) -> bool:
    return bool(conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
        "WHERE table_schema='public' AND table_name=:t)"
    ), {"t": table}).scalar())


def upgrade() -> None:
    conn = op.get_bind()

    if not _table_exists(conn, "companies"):
        # Fresh schema — bootstrap will create with the enriched layout
        # via the SQLAlchemy model (out of scope here).
        return

    # ---- Add columns (idempotent via IF NOT EXISTS) ----
    new_columns = [
        ("sector", "VARCHAR(100)", None),
        ("industry_segment", "VARCHAR(100)", None),
        ("plan", "VARCHAR(50)", "'standard'"),
        ("timezone", "VARCHAR(64)", "'America/Sao_Paulo'"),
        ("lia_persona_override", "TEXT", None),
        ("headcount_range", "VARCHAR(50)", None),
    ]
    for col_name, col_type, default in new_columns:
        if _column_exists(conn, "companies", col_name):
            continue
        default_clause = f" DEFAULT {default}" if default else ""
        conn.execute(sa.text(
            f"ALTER TABLE companies ADD COLUMN {col_name} {col_type}{default_clause}"
        ))

    # ---- CHECK constraint mirroring CompanyId.parse() ----
    # Drop any prior version (older migration may have installed the
    # regex-only variant) so the deny-list rebuild is idempotent.
    reserved_in_sql = ", ".join(f"'{lit}'" for lit in _RESERVED_SLUG_LITERALS)
    bad_ids = conn.execute(sa.text(
        "SELECT id FROM companies "
        "WHERE (id !~ :uuid AND id !~ :slug) "
        f"   OR id IN ({reserved_in_sql})"
    ), {"uuid": _UUID_V4_REGEX, "slug": _SLUG_REGEX}).fetchall()
    if bad_ids:
        # pii-logs ok: company id is a tenant identifier (per LGPD
        # Art.5 V it is not data of a natural person).
        raise RuntimeError(
            f"[127] Cannot install id-format check — {len(bad_ids)} "
            f"row(s) violate canonical pattern: "
            f"{', '.join(str(r[0]) for r in bad_ids[:5])}"
            f"{' ...' if len(bad_ids) > 5 else ''}. "
            "Reconcile via scripts/migrate_demo_company_consolidation.py "
            "or manual cleanup, then retry the migration."
        )
    if _constraint_exists(conn, "companies", ID_FORMAT_CHECK):
        conn.execute(sa.text(
            f"ALTER TABLE companies DROP CONSTRAINT {ID_FORMAT_CHECK}"
        ))
    conn.execute(sa.text(
        f"ALTER TABLE companies ADD CONSTRAINT {ID_FORMAT_CHECK} "
        f"CHECK ("
        f"  (id ~ '{_UUID_V4_REGEX}' OR id ~ '{_SLUG_REGEX}') "
        f"  AND id NOT IN ({reserved_in_sql})"
        f")"
    ))


def downgrade() -> None:
    conn = op.get_bind()
    if not _table_exists(conn, "companies"):
        return

    if _constraint_exists(conn, "companies", ID_FORMAT_CHECK):
        conn.execute(sa.text(
            f"ALTER TABLE companies DROP CONSTRAINT {ID_FORMAT_CHECK}"
        ))

    for col_name in (
        "headcount_range",
        "lia_persona_override",
        "timezone",
        "plan",
        "industry_segment",
        "sector",
    ):
        if _column_exists(conn, "companies", col_name):
            conn.execute(sa.text(
                f"ALTER TABLE companies DROP COLUMN {col_name}"
            ))
