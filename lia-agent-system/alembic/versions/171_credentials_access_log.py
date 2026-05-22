"""WT Camada 3 Item 1: credentials_access_logs (LGPD Art. 37 audit trail).

Revision ID: 171_credentials_access_log
Revises: 170_alert_canonical_consolidation, 170_approver_department_amount
Create Date: 2026-05-22

Contexto (Wave 3 Camada 3 backlog 2026-05-22)
---------------------------------------------
Commit `b5c560513` (migration 168) introduziu Fernet encryption para
`IntegrationConnection.credentials_encrypted`. Mas **toda chamada a
`get_decrypted_credentials` ate hoje e sem audit trail** — LGPD Art. 37
recomenda registro de TODO acesso a dados sensiveis. Credenciais de
integracoes sao secret material critico (API keys de HRIS, OAuth tokens,
webhook secrets) — auditoria post-incident exige saber QUEM acessou,
QUANDO, em que CONTEXTO.

Esta migration cria a tabela canonical onde toda decryption deixa
trilha:

  - `id` UUID primary key
  - `company_id` UUID NOT NULL FK -> company_profiles (multi-tenancy)
  - `integration_connection_id` UUID FK -> integration_connections
  - `accessed_at` timestamptz NOT NULL DEFAULT now()
  - `accessor_user_id` UUID FK -> users (nullable for system/celery)
  - `accessor_type` VARCHAR(50) NOT NULL — 'human_user' | 'system' |
    'agent' | 'celery_task'
  - `access_purpose` VARCHAR(200) NOT NULL — REQUIRED (sensor forca
    caller a documentar)
  - `client_ip` VARCHAR(45) NULL — IPv4/IPv6
  - `request_id` VARCHAR(100) NULL INDEX — corr cross-system

Indexes:
  - `(company_id, accessed_at)` composto — forensic query
  - `(integration_connection_id)` — trace por conexao
  - `(request_id)` — corr cross-system

Idempotente via `IF NOT EXISTS`. Reversivel via `op.drop_table`.

REGRA 4 (CLAUDE.md): tabela append-only. UPDATE/DELETE programaticos
seriam violacao de integridade de audit trail — enforce via app layer
(repository so expoe insert + read).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "171_credentials_access_log"
down_revision: Union[str, Sequence[str], None] = (
    "170_alert_canonical_consolidation",
    "170_approver_department_amount",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Idempotent: skip creation if table already exists from partial prior run
    conn = op.get_bind()
    exists = conn.execute(sa.text(
        "SELECT 1 FROM pg_tables WHERE tablename = 'credentials_access_logs'"
    )).scalar()
    if exists:
        print(
            "[171] credentials_access_logs already exists — skipping CREATE "
            "(idempotent recovery from partial prior run)."
        )
        return
    op.create_table(
        "credentials_access_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("company_profiles.id"),
            nullable=False,
        ),
        sa.Column(
            "integration_connection_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("integration_connections.id"),
            nullable=True,
        ),
        sa.Column(
            "accessed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "accessor_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("accessor_type", sa.String(length=50), nullable=False),
        sa.Column("access_purpose", sa.String(length=200), nullable=False),
        sa.Column("client_ip", sa.String(length=45), nullable=True),
        sa.Column("request_id", sa.String(length=100), nullable=True),
    )

    # Indexes
    op.create_index(
        "ix_credentials_access_logs_company_id",
        "credentials_access_logs",
        ["company_id"],
    )
    op.create_index(
        "ix_credentials_access_logs_integration_connection_id",
        "credentials_access_logs",
        ["integration_connection_id"],
    )
    op.create_index(
        "ix_credentials_access_logs_accessed_at",
        "credentials_access_logs",
        ["accessed_at"],
    )
    op.create_index(
        "ix_credentials_access_logs_request_id",
        "credentials_access_logs",
        ["request_id"],
    )
    # Composite — forensic query "all decryptions on tenant X in time window"
    op.create_index(
        "ix_credentials_access_company_time",
        "credentials_access_logs",
        ["company_id", "accessed_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_credentials_access_company_time",
        table_name="credentials_access_logs",
    )
    op.drop_index(
        "ix_credentials_access_logs_request_id",
        table_name="credentials_access_logs",
    )
    op.drop_index(
        "ix_credentials_access_logs_accessed_at",
        table_name="credentials_access_logs",
    )
    op.drop_index(
        "ix_credentials_access_logs_integration_connection_id",
        table_name="credentials_access_logs",
    )
    op.drop_index(
        "ix_credentials_access_logs_company_id",
        table_name="credentials_access_logs",
    )
    op.drop_table("credentials_access_logs")
