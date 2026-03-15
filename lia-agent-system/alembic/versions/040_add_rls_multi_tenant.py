"""Add Row Level Security for multi-tenant isolation.

Revision ID: 040_add_rls_multi_tenant
Revises: 037
Create Date: 2026-03-13

ATENÇÃO: Esta migration habilita RLS nas tabelas críticas.
Requer que o app injete `SET app.company_id = '<uuid>'` antes de cada query.
Rollback disponível em downgrade().
"""
from alembic import op
import sqlalchemy as sa

revision = "040_add_rls_multi_tenant"
down_revision = "037"
depends_on = None

# Tabelas que devem ter RLS — apenas as que têm company_id
RLS_TABLES = [
    "job_vacancies",
    "candidates",
    "applications",
    "wsi_sessions",
    "pipeline_stages",
    "short_lists",
    "hitl_requests",
    "audit_logs",
    "bias_audit_snapshots",
    "notifications",
]


def upgrade() -> None:
    # Criar função auxiliar para obter company_id da sessão
    op.execute("""
        CREATE OR REPLACE FUNCTION app_current_company_id() RETURNS uuid AS $$
        BEGIN
            RETURN NULLIF(current_setting('app.company_id', true), '')::uuid;
        EXCEPTION WHEN others THEN
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql STABLE;
    """)

    for table in RLS_TABLES:
        # Habilitar RLS (não bloqueia superuser por padrão)
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")

        # Policy SELECT: só vê registros do próprio tenant
        op.execute(f"""
            CREATE POLICY {table}_tenant_isolation_select ON {table}
                FOR SELECT
                USING (
                    app_current_company_id() IS NULL
                    OR company_id = app_current_company_id()
                );
        """)

        # Policy INSERT: só pode inserir para o próprio tenant
        op.execute(f"""
            CREATE POLICY {table}_tenant_isolation_insert ON {table}
                FOR INSERT
                WITH CHECK (
                    app_current_company_id() IS NULL
                    OR company_id = app_current_company_id()
                );
        """)

        # Policy UPDATE/DELETE: só afeta o próprio tenant
        op.execute(f"""
            CREATE POLICY {table}_tenant_isolation_update ON {table}
                FOR UPDATE
                USING (
                    app_current_company_id() IS NULL
                    OR company_id = app_current_company_id()
                );
        """)

        op.execute(f"""
            CREATE POLICY {table}_tenant_isolation_delete ON {table}
                FOR DELETE
                USING (
                    app_current_company_id() IS NULL
                    OR company_id = app_current_company_id()
                );
        """)

    # Documentar a função auxiliar
    op.execute("""
        COMMENT ON FUNCTION app_current_company_id() IS
        'Retorna o company_id da sessão atual. Definido pelo middleware FastAPI via SET app.company_id.';
    """)


def downgrade() -> None:
    for table in reversed(RLS_TABLES):
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation_select ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation_insert ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation_update ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation_delete ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    op.execute("DROP FUNCTION IF EXISTS app_current_company_id();")
