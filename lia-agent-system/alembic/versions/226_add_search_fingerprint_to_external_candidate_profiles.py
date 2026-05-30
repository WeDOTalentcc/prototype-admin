"""Add search_fingerprint to external_candidate_profiles (Fase 4 — snapshot Pearch).

Revision ID: 226
Revises: 225
Create Date: 2026-05-30

Habilita o resgate congelado de resultados Pearch sem re-rodar a busca (sem
crédito). Cada perfil Pearch pesquisado é upsertado em external_candidate_profiles
com o search_fingerprint da busca que o trouxe. O endpoint GET /snapshot?fingerprint=fp
retorna os perfis daquele snapshot sem chamar a API Pearch.

LGPD Art. 7 IX (interesse legítimo recrutamento): armazenamento é restrito à
empresa recrutadora (company_id, RLS já ativo com 4 policies). TTL e erasure
cascade adicionados em lgpd_cleanup_service.py (180 dias não-engajados) e
data_subject_repository.py (Art. 18 VI cascade por email).

Coluna nullable (sem backfill: perfis importados antes desta migration ficam sem
fingerprint, o que é correto — foram descobertos fora do contexto de busca).
Index para lookup por (company_id, search_fingerprint) no snapshot endpoint.

NOTA numeração: down_revision=225 (head confirmado via `alembic heads`).
"""
from alembic import op
import sqlalchemy as sa

revision = "226"
down_revision = "225"
branch_labels = None
depends_on = None

TABLE = "external_candidate_profiles"


def upgrade() -> None:
    op.add_column(TABLE, sa.Column("search_fingerprint", sa.String(64), nullable=True))
    op.create_index(
        "ix_external_candidate_profiles_search_fingerprint",
        TABLE,
        ["search_fingerprint"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_external_candidate_profiles_search_fingerprint", table_name=TABLE
    )
    op.drop_column(TABLE, "search_fingerprint")
