"""add legal_basis_id and consent_version_id to candidates (LGPD Art.18)

Revision ID: 5880556c6d91
Revises: a3f91c2e8b4d
Create Date: 2026-05-02

UC-P0-14: LGPD Art.18 requires recording legal basis for data processing.
Creates lgpd_legal_bases and lgpd_consent_versions lookup tables.
Adds FK columns to candidates table (nullable -- backfill via separate data task).
Inserts default legal basis records for common LGPD Art.7 scenarios.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '5880556c6d91'
down_revision = 'a3f91c2e8b4d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create lookup tables
    op.create_table(
        'lgpd_legal_bases',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('code', sa.String(100), nullable=False),
        sa.Column('description_pt', sa.Text(), nullable=False),
        sa.Column('lgpd_article', sa.String(50), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
    )

    op.create_table(
        'lgpd_consent_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=True),
        sa.Column('changes_summary', sa.Text(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('version'),
    )

    # 2. Add FK columns to candidates (nullable -- no NOT NULL to avoid breaking existing inserts)
    op.add_column('candidates', sa.Column(
        'legal_basis_id',
        postgresql.UUID(as_uuid=True),
        nullable=True,
        comment='LGPD Art.7: legal basis authorizing data processing',
    ))
    op.add_column('candidates', sa.Column(
        'consent_version_id',
        postgresql.UUID(as_uuid=True),
        nullable=True,
        comment='Version of consent form (required when legal_basis=consent)',
    ))

    # 3. Create FKs explicitly (safer than ForeignKey in add_column)
    op.create_foreign_key(
        'fk_candidates_legal_basis_id',
        'candidates', 'lgpd_legal_bases',
        ['legal_basis_id'], ['id'],
    )
    op.create_foreign_key(
        'fk_candidates_consent_version_id',
        'candidates', 'lgpd_consent_versions',
        ['consent_version_id'], ['id'],
    )

    # 4. Indexes
    op.create_index('ix_candidates_legal_basis_id', 'candidates', ['legal_basis_id'])
    op.create_index('ix_candidates_consent_version_id', 'candidates', ['consent_version_id'])

    # 5. Seed default legal bases (LGPD Art.7 grounds)
    op.execute("""
        INSERT INTO lgpd_legal_bases (id, code, description_pt, lgpd_article) VALUES
        (gen_random_uuid(), 'consent', 'Consentimento do titular (candidato)', 'Art. 7, inciso I'),
        (gen_random_uuid(), 'legitimate_interest', 'Legitimo interesse do controlador (plataforma de recrutamento)', 'Art. 7, inciso IX'),
        (gen_random_uuid(), 'contract', 'Execucao de contrato ou procedimentos pre-contratuais', 'Art. 7, inciso V'),
        (gen_random_uuid(), 'legal_obligation', 'Cumprimento de obrigacao legal ou regulatoria', 'Art. 7, inciso II')
    """)


def downgrade() -> None:
    op.drop_index('ix_candidates_consent_version_id', 'candidates')
    op.drop_index('ix_candidates_legal_basis_id', 'candidates')
    op.drop_constraint('fk_candidates_consent_version_id', 'candidates', type_='foreignkey')
    op.drop_constraint('fk_candidates_legal_basis_id', 'candidates', type_='foreignkey')
    op.drop_column('candidates', 'consent_version_id')
    op.drop_column('candidates', 'legal_basis_id')
    op.drop_table('lgpd_consent_versions')
    op.drop_table('lgpd_legal_bases')
