"""Fase 1 Pipeline Unify — schema canônico CanonicalPipelineStage + dual-write.

Revision ID: 235
Revises: 234
Create Date: 2026-06-01

Contexto
--------
Esta migration documenta e prepara a Fase 1 da unificação de pipeline (Unify).
Antes desta migration existiam 3 shapes de stage não-unificados:

    1. pipeline_templates.stages   → {name, order, type, sla_days, instructions}
    2. job_vacancy.interview_stages → {stageName, order, sla, type="automated"}
    3. RecruitmentStage (DB)       → model rico (stage_order, action_behavior, etc.)

O canonical shape escolhido (superset) está documentado em:
    app/shared/types.py → CanonicalPipelineStage

A função translate_template_stages_to_interview_stages foi atualizada para
dual-write: grava AMBOS name+stageName e sla_days+sla para compatibilidade
retroativa com o kanban (que lê stageName).

Data migration
--------------
Neste ambiente: 0 linhas em job_vacancy.interview_stages com dados de pipeline
template → nenhuma row precisou ser convertida. O upgrade/downgrade é no-op.

Se future environments tiverem rows com o shape antigo ({stageName, sla}):
executar manualmente o script de migração de dados (ver docs/migrations/235_data.sql).

Fase futura
-----------
Após migrar kanban para ler `name` em vez de `stageName`, remover:
  - o campo stageName do dual-write no translate
  - o campo sla do dual-write no translate
  - os aliases na CanonicalPipelineStage TypedDict
"""

revision = "235"
down_revision = "234"
branch_labels = None
depends_on = None

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401


def upgrade() -> None:
    # Schema unification is handled at application layer (shared/types.py +
    # translate dual-write). No DDL changes required for this migration.
    # JSON columns (pipeline_templates.stages, job_vacancy.interview_stages)
    # store arbitrary dict — no column type change needed.
    pass


def downgrade() -> None:
    # No DDL changes to revert.
    pass
