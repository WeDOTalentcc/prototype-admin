"""299 index integration catalog is master template query.

Revision ID: 299_index_integration_catalog_is_master
Revises: 298_add_company_id_to_calibration_feedback

PERF-299: A query list_for_company executa:
  WHERE (is_master_template = TRUE OR company_id = :cid) AND deleted_at IS NULL

O indice individual em is_master_template (criado pelo ORM via index=True)
nao e otimizado para o pattern OR — o planner do Postgres prefere um indice
parcial dedicado para as linhas master_template ativas (deleted_at IS NULL).
Esse indice permite index scan para a branch is_master_template=TRUE sem
full-table scan quando a tabela cresce.

Indice existente ix_integration_catalog_active (deleted_at, is_master_template)
cobre o filtro deleted_at mas o Postgres ainda precisa escanear todas as linhas
nao-deletadas para encontrar as master. O novo indice parcial e mais seletivo.
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "299_index_integration_catalog_is_master"
down_revision = "298_add_company_id_to_calibration_feedback"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Indice parcial para o pattern: is_master_template=TRUE AND deleted_at IS NULL
    # Usado pela branch OR da query list_for_company (selecao dos master templates ativos).
    # CONCURRENTLY evita lock exclusivo em producao.
    op.execute(
        """
        CREATE INDEX CONCURRENTLY IF NOT EXISTS
            ix_integration_catalog_master_active
        ON integration_catalog_entries (is_master_template)
        WHERE is_master_template = TRUE AND deleted_at IS NULL
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP INDEX CONCURRENTLY IF EXISTS ix_integration_catalog_master_active"
    )
