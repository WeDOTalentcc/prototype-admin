"""Add search_fingerprint to search_feedbacks (Fase 2 — ancora feedback aos criterios da busca).

Revision ID: 225
Revises: 224
Create Date: 2026-05-29

O feedback (like/dislike) e ancorado ao CONJUNTO DE CRITERIOS da busca (query +
filtros no search_spec), nao a uma vaga nem ao recrutador. search_fingerprint e um
hash estavel desses criterios (app/api/v1/candidate_search/_shared.py
:_generate_search_fingerprint), permitindo re-hidratar o ranking aprendido ao
re-executar ou resgatar a busca (historico/lista/pool).

Coluna nullable (sem backfill: feedback antigo fica sem fingerprint = nao-ancorado).
Index para lookup por (user_id, search_fingerprint).

NOTA numeracao: criada como 225 (down=224) porque enquanto a 222 era head, outro
workstream adicionou 223_agent_studio_perf_indexes + 224_fk_closure_agent_studio.
DB ja estava em 224. (REGRA 5 — verificar numeracao considerando branches recentes.)
"""
from alembic import op
import sqlalchemy as sa

revision = "225"
down_revision = "224"
branch_labels = None
depends_on = None

TABLE = "search_feedbacks"


def upgrade() -> None:
    op.add_column(TABLE, sa.Column("search_fingerprint", sa.String(), nullable=True))
    op.create_index(
        "ix_search_feedbacks_search_fingerprint", TABLE, ["search_fingerprint"]
    )


def downgrade() -> None:
    op.drop_index("ix_search_feedbacks_search_fingerprint", table_name=TABLE)
    op.drop_column(TABLE, "search_fingerprint")
