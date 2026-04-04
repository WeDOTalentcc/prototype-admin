"""Add agent_templates table for Agent Studio foundation

Revision ID: 054
Revises: 053
Create Date: 2026-04-04

WHY: Agent Studio permite que cada empresa customize os prompts dos agentes LIA
     sem tocar em código. A tabela armazena templates versionados por tenant.
     company_id=NULL → template público da WeDO (fallback).
     company_id=<id> → template customizado do cliente (prioridade sobre WeDO).

DESIGN:
  - system_prompt_yaml: conteúdo YAML com variáveis interpoláveis ({{company_name}}, etc.)
  - version: auto-incrementado a cada edição (imutabilidade de versões publicadas)
  - status: draft → published → archived (publicar = congelar a versão)
  - base_template_id: FK para o template WeDO de origem (rastreabilidade)
"""
import sqlalchemy as sa
from alembic import op

revision = '054'
down_revision = '053'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_templates",
        sa.Column("id", sa.String(255), nullable=False, primary_key=True),
        # NULL = template público da WeDO; preenchido = template do cliente
        sa.Column("company_id", sa.String(255), nullable=True),
        sa.Column("name", sa.String(500), nullable=False),
        # Domain: sourcing, pipeline, wsi, lia_assistant, job_wizard, etc.
        sa.Column("domain", sa.String(100), nullable=False),
        # Conteúdo do system prompt em YAML com variáveis {{variable_name}}
        sa.Column("system_prompt_yaml", sa.Text(), nullable=False),
        # Versão: começa em 1, incrementa a cada edição
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        # Status: draft | published | archived
        sa.Column("status", sa.String(50), nullable=False, server_default="'draft'"),
        # FK para o template WeDO base (NULL se é o original)
        sa.Column("base_template_id", sa.String(255), nullable=True),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("archived_at", sa.DateTime(), nullable=True),
    )

    # Index para busca por empresa + domínio (lookup crítico no registry)
    op.create_index(
        "ix_agent_templates_company_domain",
        "agent_templates",
        ["company_id", "domain", "status"],
    )
    # Index para templates públicos WeDO (company_id IS NULL)
    op.create_index(
        "ix_agent_templates_public",
        "agent_templates",
        ["domain", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_agent_templates_public", table_name="agent_templates")
    op.drop_index("ix_agent_templates_company_domain", table_name="agent_templates")
    op.drop_table("agent_templates")
