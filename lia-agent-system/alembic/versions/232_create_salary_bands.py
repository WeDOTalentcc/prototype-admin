"""create salary_bands (faixa salarial canonica por nivel) + backfill do PRV

Revision ID: 232
Revises: 231
Create Date: 2026-06-01

Promove a faixa salarial por nivel a entidade de primeira classe (fonte unica),
saindo de compensation_policies.salary_bands (JSONB policy-centric). Faz backfill
das bandas existentes: por empresa, prefere a policy is_default; dedupe por nivel.

Idempotente: o dev server do Replit pode ter auto-criado a tabela via
Base.metadata.create_all no hot-reload. Por isso checamos o inspector antes de
criar (skip se ja existe) e o backfill usa ON CONFLICT DO NOTHING.
"""
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "232"
down_revision = "231"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "salary_bands" not in existing_tables:
        op.create_table(
            "salary_bands",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("company_id", sa.String(255), nullable=False),
            sa.Column("level", sa.String(50), nullable=False),
            sa.Column("label", sa.String(100), nullable=True),
            sa.Column("min", sa.Float, nullable=True),
            sa.Column("mid", sa.Float, nullable=True),
            sa.Column("max", sa.Float, nullable=True),
            sa.Column("currency", sa.String(10), server_default="BRL"),
            sa.Column("effective_from", sa.Date, nullable=True),
            sa.Column("effective_until", sa.Date, nullable=True),
            sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
            sa.Column("order", sa.Integer, server_default="0"),
            sa.Column("created_at", sa.DateTime, server_default=sa.text("NOW()")),
            sa.Column("updated_at", sa.DateTime, server_default=sa.text("NOW()")),
            sa.UniqueConstraint("company_id", "level", name="uq_salary_bands_company_level"),
        )
        existing_indexes = set()
    else:
        print("[232] salary_bands ja existe (create_all race) — skip create_table")
        existing_indexes = {ix["name"] for ix in inspector.get_indexes("salary_bands")}

    if "ix_salary_bands_company_id" not in existing_indexes:
        try:
            op.create_index("ix_salary_bands_company_id", "salary_bands", ["company_id"])
        except Exception as exc:
            print(f"[232] index ix_salary_bands_company_id skip: {exc}")

    _backfill_from_policies()


def _backfill_from_policies() -> None:
    """Popula salary_bands a partir de compensation_policies.salary_bands.
    Por empresa, prefere a policy is_default (senao a primeira ativa); dedupe nivel."""
    conn = op.get_bind()
    try:
        rows = conn.execute(
            sa.text(
                "SELECT company_id, salary_bands, "
                "COALESCE(is_default, false) AS is_default "
                "FROM compensation_policies "
                "WHERE salary_bands IS NOT NULL"
            )
        ).fetchall()
    except Exception as exc:  # tabela/coluna ausente em algum ambiente
        print(f"[232 backfill] skip (compensation_policies indisponivel): {exc}")
        return

    # company_id -> {level: {min,mid,max,currency}}; policy is_default tem prioridade
    chosen: dict[str, dict] = {}
    default_seen: set[str] = set()
    for company_id, bands, is_default in rows:
        if not company_id or not bands:
            continue
        cid = str(company_id)
        if cid in default_seen and not is_default:
            continue
        if is_default:
            chosen[cid] = {}
            default_seen.add(cid)
        elif cid in chosen:
            continue
        else:
            chosen.setdefault(cid, {})
        target = chosen[cid]
        for b in bands:
            if not isinstance(b, dict):
                continue
            level = (b.get("level") or "").strip()
            if not level:
                continue
            target[level] = {
                "min": b.get("min"),
                "mid": b.get("mid"),
                "max": b.get("max"),
                "currency": b.get("currency") or "BRL",
            }

    inserted = 0
    for cid, levels in chosen.items():
        for order_idx, (level, vals) in enumerate(levels.items()):
            conn.execute(
                sa.text(
                    "INSERT INTO salary_bands "
                    "(id, company_id, level, min, mid, max, currency, is_active, \"order\") "
                    "VALUES (:id, :company_id, :level, :min, :mid, :max, :currency, true, :order) "
                    "ON CONFLICT (company_id, level) DO NOTHING"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "company_id": cid,
                    "level": level,
                    "min": vals["min"],
                    "mid": vals["mid"],
                    "max": vals["max"],
                    "currency": vals["currency"],
                    "order": order_idx,
                },
            )
            inserted += 1
    print(f"[232 backfill] salary_bands inseridas (tentativas): {inserted} (empresas: {len(chosen)})")


def downgrade() -> None:
    try:
        op.drop_index("ix_salary_bands_company_id", table_name="salary_bands")
    except Exception:
        pass
    op.drop_table("salary_bands")
