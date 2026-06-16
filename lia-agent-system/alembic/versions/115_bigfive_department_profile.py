"""Sprint B Phase 2 - Create bigfive_department_profiles table.

Armazena medias correntes de Big Five por (empresa, departamento, senioridade).
Stability semantics alinhada com CompanyCultureProfile (alto = estavel/bom).
Usado como Layer 4 na formula hibrida do WSIQuestionGenerator quando:
  - sample_count >= 10
  - toggle bigfive_department_history = True

Multi-tenancy: company_id NOT NULL com indice unico composto.
LGPD: sem PII - apenas scores agregados (nenhum dado individual de candidato).
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "115_bigfive_department_profile"
# Renamed from "102_bigfive_department_profile" during import from agent
# Repl 70fcc952: collided with the existing 102_ revision in the destination
# branch. Slot 115_ on the destination chain is unused, so we rename the
# imported revision id and rechain it after 114_jd_similar_history_pgvector.
down_revision = "114_jd_similar_history_pgvector"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bigfive_department_profiles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # Multi-tenancy - NOT NULL, always from JWT (never payload)
        sa.Column("company_id", sa.String(255), nullable=False),
        sa.Column("department", sa.String(100), nullable=False),
        sa.Column("seniority_level", sa.String(50), nullable=False),
        # Running average sample count (minimum 10 to activate Layer 4)
        sa.Column(
            "sample_count",
            sa.Integer,
            nullable=False,
            server_default=sa.text("0"),
        ),
        # Big Five trait averages (0.0-1.0, alto = bom em todas inclusive stability)
        sa.Column("openness_score", sa.Float, nullable=True),
        sa.Column("conscientiousness_score", sa.Float, nullable=True),
        sa.Column("extraversion_score", sa.Float, nullable=True),
        sa.Column("agreeableness_score", sa.Float, nullable=True),
        # stability (NOT neuroticism) - consistente com CompanyCultureProfile
        sa.Column("stability_score", sa.Float, nullable=True),
        # Timestamps
        sa.Column(
            "last_updated_at",
            sa.DateTime,
            nullable=True,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # Unique composite index - one record per (company, dept, seniority)
    op.create_index(
        "ix_bigfive_dept_company_dept_seniority",
        "bigfive_department_profiles",
        ["company_id", "department", "seniority_level"],
        unique=True,
    )

    # Non-unique index on company_id alone for get_all_for_company queries
    op.create_index(
        "ix_bigfive_dept_company_id",
        "bigfive_department_profiles",
        ["company_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_bigfive_dept_company_id",
        table_name="bigfive_department_profiles",
    )
    op.drop_index(
        "ix_bigfive_dept_company_dept_seniority",
        table_name="bigfive_department_profiles",
    )
    op.drop_table("bigfive_department_profiles")
