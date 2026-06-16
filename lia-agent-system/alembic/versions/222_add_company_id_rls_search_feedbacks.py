"""Add company_id + RLS to search_feedbacks (Onda A.2 — fecha gap LGPD de isolamento).

Revision ID: 222
Revises: 221
Create Date: 2026-05-29

search_feedbacks nunca teve company_id nem RLS — isolamento entre empresas era
inexistente (o comentario "Postgres RLS (Task #1143)" em app/api/v1/search_feedback.py
era aspiracional: a tabela tem relrowsecurity=False e zero policies). A Onda B
(re-ranker lendo feedback no scoring de busca) exige isolamento real ANTES de
prosseguir, senao feedback de uma empresa influenciaria ranking de outra.

- Adiciona company_id (varchar; casa com app_current_company_id()::text e com o
  padrao de candidates.company_id, que tambem e varchar).
- Remove os feedbacks orfaos pre-RLS (sem user->company resolvivel nem job_id,
  nao atribuiveis a nenhum tenant — eram 9 linhas de teste em 2026-05-29).
- company_id NOT NULL apos limpeza + index.
- ENABLE + FORCE RLS + 4 policies tenant_{select,insert,update,delete}
  (espelha 118_rls_candidates verbatim).
- GRANT lia_app.

Reversivel (downgrade remove policies + coluna). Policies idempotentes (DROP IF EXISTS).

Pre-requisito de deploy: o codigo atualizado (modelo SearchFeedback.company_id NOT NULL +
producer search_feedback.py gravando company_id) assume esta migration aplicada.
Rodar `alembic upgrade head` antes de servir trafego com o codigo novo.
"""
from alembic import op
import sqlalchemy as sa

revision = "222"
down_revision = "221"
branch_labels = None
depends_on = None

TABLE = "search_feedbacks"


def upgrade() -> None:
    # 1. Adiciona company_id (nullable primeiro, pra permitir limpeza dos orfaos)
    op.add_column(TABLE, sa.Column("company_id", sa.String(), nullable=True))

    # 2. Remove orfaos pre-RLS: toda linha existente tem company_id NULL agora
    #    (coluna recem-criada) e nenhuma era atribuivel a um tenant. Deletar.
    op.execute(f"DELETE FROM {TABLE} WHERE company_id IS NULL;")

    # 3. NOT NULL + index
    op.alter_column(TABLE, "company_id", existing_type=sa.String(), nullable=False)
    op.create_index("ix_search_feedbacks_company_id", TABLE, ["company_id"])

    # 4. RLS deny-by-default (mirror 118_rls_candidates)
    op.execute(f"ALTER TABLE {TABLE} ENABLE ROW LEVEL SECURITY;")
    op.execute(f"ALTER TABLE {TABLE} FORCE ROW LEVEL SECURITY;")
    for op_kind in ("select", "insert", "update", "delete"):
        op.execute(f"DROP POLICY IF EXISTS {TABLE}_tenant_{op_kind} ON {TABLE};")
    op.execute(f"""
        CREATE POLICY {TABLE}_tenant_select ON {TABLE}
            FOR SELECT USING (company_id = app_current_company_id());
    """)
    op.execute(f"""
        CREATE POLICY {TABLE}_tenant_insert ON {TABLE}
            FOR INSERT WITH CHECK (company_id = app_current_company_id());
    """)
    op.execute(f"""
        CREATE POLICY {TABLE}_tenant_update ON {TABLE}
            FOR UPDATE USING (company_id = app_current_company_id());
    """)
    op.execute(f"""
        CREATE POLICY {TABLE}_tenant_delete ON {TABLE}
            FOR DELETE USING (company_id = app_current_company_id());
    """)
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {TABLE} TO lia_app;")


def downgrade() -> None:
    for op_kind in ("delete", "update", "insert", "select"):
        op.execute(f"DROP POLICY IF EXISTS {TABLE}_tenant_{op_kind} ON {TABLE};")
    op.execute(f"ALTER TABLE {TABLE} NO FORCE ROW LEVEL SECURITY;")
    op.execute(f"ALTER TABLE {TABLE} DISABLE ROW LEVEL SECURITY;")
    op.drop_index("ix_search_feedbacks_company_id", table_name=TABLE)
    op.drop_column(TABLE, "company_id")
