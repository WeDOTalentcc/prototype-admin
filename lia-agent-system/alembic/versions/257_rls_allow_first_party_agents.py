"""rls: allow first_party agents (company_id IS NULL) on custom_agents SELECT policy

Revision ID: 257
Revises: 256
Create Date: 2026-06-09

Problema: a policy `custom_agents_tenant_select` usa
  USING ((company_id)::text = app_current_company_id())
Quando company_id IS NULL (agentes first_party globais da WeDo), a expressão
NULL = 'qualquer_valor' avalia para NULL (não TRUE), portanto o PostgreSQL
BLOQUEIA essas linhas via RLS. O frontend recebia array vazio na seção
"Agentes WeDo" mesmo após seed correto.

Fix: adicionar cláusula `OR company_id IS NULL` na policy SELECT para que
agentes globais sejam visíveis a qualquer tenant autenticado.
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "257"
down_revision = "256"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP POLICY IF EXISTS custom_agents_tenant_select ON custom_agents;")
    op.execute(
        """
        CREATE POLICY custom_agents_tenant_select ON custom_agents
            FOR SELECT
            USING (
                (company_id)::text = app_current_company_id()
                OR company_id IS NULL
            );
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS custom_agents_tenant_select ON custom_agents;")
    op.execute(
        """
        CREATE POLICY custom_agents_tenant_select ON custom_agents
            FOR SELECT
            USING ((company_id)::text = app_current_company_id());
        """
    )
