"""W2-009-B · idempotency_keys cache table (Stripe-style)

Revision ID: 181_idempotency_keys
Revises: 180_audit_append_only_triggers
Create Date: 2026-05-23

W2-009-B do MASTER_PLAN.md de remediação enterprise.
Tests: tests/integration/test_idempotency_middleware.py
Sensor: scripts/check_idempotency_middleware_wired.py
Middleware: app/middleware/idempotency.py

Cache table para enforcement Stripe-style de Idempotency-Key em mutations
FastAPI (POST/PUT/PATCH/DELETE).

Comportamento canonical:
- Header `Idempotency-Key` opcional em qualquer mutation.
- Se ausente: passthrough normal (back-compat).
- Se presente E nova: middleware executa request, cacheia (key, company_id,
  method, path, request_hash, response_status, response_body), retorna response.
- Se presente E replay com mesmo body hash: middleware retorna cached response
  (não reexecuta).
- Se presente E replay com body DIFERENTE: middleware retorna 409 Conflict
  (Stripe behavior — proteção contra key reuse).

TTL: 24h via column `created_at` + job cleanup periódico (não incluso neste
commit — out of scope, próxima sprint).

Multi-tenancy: PK composta (idempotency_key, company_id) — isola por tenant
fail-closed. Mesmo key em 2 tenants diferentes = 2 entries independentes.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = "181_idempotency_keys"
down_revision = "180_audit_append_only_triggers"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "idempotency_keys",
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("method", sa.String(length=10), nullable=False),
        sa.Column("path", sa.String(length=1024), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("response_status", sa.Integer, nullable=False),
        sa.Column("response_body", sa.LargeBinary, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "idempotency_key", "company_id", name="pk_idempotency_keys"
        ),
    )
    # Index para purge job (drop entries > 24h)
    op.create_index(
        "ix_idempotency_keys_created_at",
        "idempotency_keys",
        ["created_at"],
    )


def downgrade():
    op.drop_index("ix_idempotency_keys_created_at", table_name="idempotency_keys")
    op.drop_table("idempotency_keys")
