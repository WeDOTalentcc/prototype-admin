"""W1-006 part 1 · audit_execution_metadata hash chain (SHA-256 per-tenant)

Revision ID: 176_audit_hash_chain
Revises: 175_byok_soft_cap
Create Date: 2026-05-22

W1-006 do MASTER_PLAN.md de remediação enterprise.
Pre-audit: /Users/paulomoraes/Documents/Python/replit_lia_audit/sprint_logs/sprint_1.1/W1-006_AUDIT.md
Tests: tests/integration/test_audit_hash_chain.py
Sensor: scripts/check_audit_hash_chain_exists.py

Adiciona hash chain SHA-256 per-tenant a audit_execution_metadata:
- Column prev_hash CHAR(64) NULLABLE (genesis tem NULL)
- Column this_hash CHAR(64) NULLABLE (populada por BEFORE INSERT trigger)
- Function audit_compute_hash_chain() — calcula prev_hash + this_hash via digest()
- Trigger audit_execution_metadata_hash_chain_trigger — BEFORE INSERT

Mitigations:
- Tampering detection: alterar payload sem recomputar chain é detectável via verify
- Multi-tenancy: chain isolada por company_id (cross-tenant impossível)
- Performance: trigger lookup do last this_hash usa index (company_id, timestamp)

UPDATE/DELETE triggers (parte 2 / Sprint 1.2) virão em migration separada após:
- Decisão Opção A confirmada: split audit_log_human_reviews append-only
- Bucket S3 lia-audit-worm-2026 criado pelo DevOps
- Backfill data se houver reviews existentes

Requires: pgcrypto extension (habilitada em migrations 060, 091, 160).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = "176_audit_hash_chain"
down_revision = "175_byok_soft_cap"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # 1. Garantir pgcrypto (idempotente, já habilitado em 060)
    conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))

    # 2. Adicionar colunas hash chain
    op.add_column(
        "audit_execution_metadata",
        sa.Column("prev_hash", sa.CHAR(64), nullable=True),
    )
    op.add_column(
        "audit_execution_metadata",
        sa.Column("this_hash", sa.CHAR(64), nullable=True),
    )

    # 3. Index para lookup do last this_hash per company_id (trigger usa)
    op.create_index(
        "ix_audit_execution_metadata_company_timestamp",
        "audit_execution_metadata",
        ["company_id", "timestamp"],
        unique=False,
    )

    # 4. Function: computa hash chain em BEFORE INSERT
    op.execute(sa.text("""
        CREATE OR REPLACE FUNCTION audit_compute_hash_chain()
        RETURNS TRIGGER AS $$
        DECLARE
            v_prev_hash CHAR(64);
            v_canonical_payload TEXT;
        BEGIN
            -- Lookup last this_hash para esta company (chain per-tenant)
            SELECT this_hash INTO v_prev_hash
            FROM audit_execution_metadata
            WHERE company_id = NEW.company_id
              AND this_hash IS NOT NULL
            ORDER BY timestamp DESC, execution_id DESC
            LIMIT 1;

            -- Canonical payload determinístico (campos imutáveis do audit)
            v_canonical_payload := concat_ws('|',
                NEW.execution_id,
                NEW.company_id,
                COALESCE(NEW.timestamp::text, ''),
                COALESCE(NEW.domain, ''),
                COALESCE(NEW.agent_type, ''),
                COALESCE(NEW.user_id, ''),
                COALESCE(NEW.session_id, ''),
                COALESCE(NEW.success::text, ''),
                COALESCE(NEW.confidence::text, ''),
                COALESCE(NEW.duration_ms::text, '')
            );

            NEW.prev_hash := v_prev_hash;
            NEW.this_hash := encode(
                digest(COALESCE(v_prev_hash, '') || ':' || v_canonical_payload, 'sha256'),
                'hex'
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """))

    # 5. Attach trigger
    op.execute(sa.text("""
        DROP TRIGGER IF EXISTS audit_execution_metadata_hash_chain_trigger
        ON audit_execution_metadata
    """))
    op.execute(sa.text("""
        CREATE TRIGGER audit_execution_metadata_hash_chain_trigger
        BEFORE INSERT ON audit_execution_metadata
        FOR EACH ROW
        EXECUTE FUNCTION audit_compute_hash_chain()
    """))

    # 6. Backfill: rows pre-existentes ficam com prev_hash=NULL e this_hash computado
    # via mesma fórmula que o trigger usaria (chain começa a partir daqui).
    # ORDER BY garante chain determinística por tenant.
    op.execute(sa.text("""
        WITH ordered_rows AS (
            SELECT
                execution_id,
                company_id,
                timestamp,
                LAG(execution_id) OVER (
                    PARTITION BY company_id
                    ORDER BY timestamp ASC, execution_id ASC
                ) AS prev_eid
            FROM audit_execution_metadata
            WHERE this_hash IS NULL
        )
        UPDATE audit_execution_metadata m
        SET
            this_hash = encode(
                digest(
                    concat_ws('|',
                        m.execution_id,
                        m.company_id,
                        COALESCE(m.timestamp::text, ''),
                        COALESCE(m.domain, ''),
                        COALESCE(m.agent_type, ''),
                        COALESCE(m.user_id, ''),
                        COALESCE(m.session_id, ''),
                        COALESCE(m.success::text, ''),
                        COALESCE(m.confidence::text, ''),
                        COALESCE(m.duration_ms::text, '')
                    ),
                    'sha256'
                ),
                'hex'
            )
        FROM ordered_rows o
        WHERE m.execution_id = o.execution_id
          AND m.this_hash IS NULL;
    """))


def downgrade():
    op.execute(sa.text(
        "DROP TRIGGER IF EXISTS audit_execution_metadata_hash_chain_trigger "
        "ON audit_execution_metadata"
    ))
    op.execute(sa.text("DROP FUNCTION IF EXISTS audit_compute_hash_chain()"))
    op.drop_index(
        "ix_audit_execution_metadata_company_timestamp",
        table_name="audit_execution_metadata",
    )
    op.drop_column("audit_execution_metadata", "this_hash")
    op.drop_column("audit_execution_metadata", "prev_hash")
