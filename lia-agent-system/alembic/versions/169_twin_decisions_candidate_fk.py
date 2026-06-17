"""twin_decisions add candidate_id FK SET NULL (Wave 3 #17 LGPD Art. 18 erasure)

Revision ID: 169_twin_decisions_candidate_fk
Revises: 168_encrypt_integration_credentials
Create Date: 2026-05-22 00:00:00.000000

Wave 3 #17 audit 2026-05-22: P0-4 chunk 1 (commit 3a8492d02) substituiu nome cru
por candidate_id no candidate_snapshot JSONB. Esta migration formaliza a FK e
implementa erasure cascade via SET NULL (LGPD Art. 18).

Estratégia ON DELETE SET NULL (não CASCADE):
  - Preserva embeddings vetoriais (valor de treinamento agregado anonimizado)
  - Anonimiza referência ao candidato individual quando exclusão é solicitada
  - Trade-off vs CASCADE: histórico de decisões do SME sobrevive a erasure
    de candidato individual; só perde a referência que permitiria re-identificação
  - Justificativa: ADR-LGPD-001 (agregados destrutivos N≥10 = anonimização)

Idempotent: usa op.execute com IF NOT EXISTS pattern.

Audit ref: ~/Documents/wedotalent_audit_2026-05-21/DIAGNOSTICO_ESTUDIO_AGENTES_2026-05-21.md
Sec. 7 Twin LGPD reality check + P0-4 chunk 2.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "169_twin_decisions_candidate_fk"
down_revision = "168_encrypt_integration_credentials"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add candidate_id column + FK SET NULL + back-fill from JSONB snapshot."""
    conn = op.get_bind()

    # 1. Add column if not exists
    conn.execute(sa.text("""
        ALTER TABLE twin_decisions
        ADD COLUMN IF NOT EXISTS candidate_id UUID
    """))

    # 2. Back-fill from existing candidate_snapshot->>'candidate_id' (P0-4 chunk 1)
    # Only updates rows where candidate_snapshot has the new schema
    conn.execute(sa.text("""
        UPDATE twin_decisions
        SET candidate_id = (candidate_snapshot->>'candidate_id')::uuid
        WHERE candidate_id IS NULL
          AND candidate_snapshot IS NOT NULL
          AND candidate_snapshot ? 'candidate_id'
          AND candidate_snapshot->>'candidate_id' ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    """))

    # 3. Add FK constraint with ON DELETE SET NULL (LGPD Art. 18)
    # Drop existing constraint first if any (idempotency)
    conn.execute(sa.text("""
        ALTER TABLE twin_decisions
        DROP CONSTRAINT IF EXISTS twin_decisions_candidate_id_fkey
    """))

    conn.execute(sa.text("""
        ALTER TABLE twin_decisions
        ADD CONSTRAINT twin_decisions_candidate_id_fkey
        FOREIGN KEY (candidate_id) REFERENCES candidates(id)
        ON DELETE SET NULL
    """))

    # 4. Index for performance (lookup by candidate_id when candidate is deleted)
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_twin_decisions_candidate_id
        ON twin_decisions(candidate_id)
        WHERE candidate_id IS NOT NULL
    """))


def downgrade() -> None:
    """Remove FK + column."""
    conn = op.get_bind()
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_twin_decisions_candidate_id"))
    conn.execute(sa.text("""
        ALTER TABLE twin_decisions
        DROP CONSTRAINT IF EXISTS twin_decisions_candidate_id_fkey
    """))
    conn.execute(sa.text("ALTER TABLE twin_decisions DROP COLUMN IF EXISTS candidate_id"))
