"""Promote candidate_experience_highlights to canonical alembic-managed table.

Revision ID: 138_candidate_experience_highlights_canonical
Revises: 137_wsi_sessions_agent_id
Create Date: 2026-05-20

SMOKE-#4+#5 fix (audit 2026-05-20 — E2E vaga creation):
- ``ExperienceHighlightRepository.ensure_table()`` rodava ``CREATE TABLE IF NOT EXISTS``
  em todo request, sob role ``lia_app`` (sem ``CREATE`` em schema public — by design).
- Resultado: ``InsufficientPrivilegeError: permission denied for schema public`` em
  GET /api/v1/experience-highlights/{candidate_id} e DELETE equivalente.
- Fix em código: ``ensure_table()`` swallows permission denied (tabela é canonical-managed
  agora). Esta migration garante o schema definitivo via role ``postgres`` (com CREATE).

Idempotente — tabela já existe runtime-criada em ambientes de dev.
Não dá CREATE ao lia_app (anti-pattern — viola fail-closed do RLS).
Apenas DML grants (SELECT/INSERT/UPDATE/DELETE) + RLS canonical.

asyncpg não aceita statements múltiplos em prepared statement — cada DDL precisa
de op.execute() próprio.
"""
from alembic import op


revision = "138_candidate_experience_highlights_canonical"
down_revision = "137_wsi_sessions_agent_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS candidate_experience_highlights (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            candidate_id VARCHAR(255) NOT NULL,
            company_id VARCHAR(255) NOT NULL,
            highlight_text TEXT NOT NULL,
            model_used VARCHAR(100) NOT NULL DEFAULT 'claude-sonnet-4-6',
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT uq_candidate_highlight UNIQUE (candidate_id, company_id)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_exp_highlights_candidate ON candidate_experience_highlights(candidate_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_exp_highlights_expires ON candidate_experience_highlights(expires_at)")

    # DML grants pro role do app (RLS continua bloqueando cross-tenant)
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON candidate_experience_highlights TO lia_app")

    # RLS canonical (idempotente — pode já estar habilitado por 068)
    op.execute("ALTER TABLE candidate_experience_highlights ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE candidate_experience_highlights FORCE ROW LEVEL SECURITY")

    # Tenant policies idempotentes (4 policies separadas em DO blocks individuais)
    for policy_name, op_kind, extra in [
        ("candidate_experience_highlights_tenant_select", "SELECT",
         "USING (company_id::text = current_setting('app.company_id', true))"),
        ("candidate_experience_highlights_tenant_insert", "INSERT",
         "WITH CHECK (company_id::text = current_setting('app.company_id', true))"),
        ("candidate_experience_highlights_tenant_update", "UPDATE",
         "USING (company_id::text = current_setting('app.company_id', true)) WITH CHECK (company_id::text = current_setting('app.company_id', true))"),
        ("candidate_experience_highlights_tenant_delete", "DELETE",
         "USING (company_id::text = current_setting('app.company_id', true))"),
    ]:
        op.execute(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_policies
                    WHERE schemaname='public' AND tablename='candidate_experience_highlights'
                      AND policyname='{policy_name}'
                ) THEN
                    CREATE POLICY {policy_name}
                      ON candidate_experience_highlights FOR {op_kind} TO lia_app
                      {extra};
                END IF;
            END $$
        """)


def downgrade() -> None:
    # No-op: tabela é cache regenerável; sem perda de dado relevante mantendo-a.
    pass
