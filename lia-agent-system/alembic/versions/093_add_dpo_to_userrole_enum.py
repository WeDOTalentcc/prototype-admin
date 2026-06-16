"""Task #511 round 3 — adiciona valor 'dpo' ao enum PostgreSQL `userrole`.

Revision ID: 093_add_dpo_to_userrole_enum
Revises: 092_wsi_responses_session_fk
Create Date: 2026-04-18

Contexto
--------
A coluna `users.role` é do tipo `USER-DEFINED` (`userrole` enum nativo do
Postgres), não VARCHAR. O round 2 da Task #511 adicionou `dpo` apenas no
StrEnum Python — sem este migration, INSERTs/UPDATEs com role='dpo' falham
com `invalid input value for enum userrole`.

Esta revisão executa `ALTER TYPE userrole ADD VALUE 'dpo'`. PostgreSQL exige
que ALTER TYPE ADD VALUE rode FORA de transação (autocommit).
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "093_add_dpo_to_userrole_enum"
down_revision = "092_wsi_responses_session_fk"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ALTER TYPE ADD VALUE precisa rodar fora de bloco transacional. Alembic
    # provê `autocommit_block()` para esse caso (commita a tx pendente, roda
    # em autocommit, abre nova tx).
    with op.get_context().autocommit_block():
        op.execute(sa.text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'dpo'"))


def downgrade() -> None:
    # PostgreSQL não suporta DROP VALUE de enum nativamente. Downgrade no-op:
    # o valor `dpo` permanece no enum mas torna-se órfão (sem usuários
    # apontando para ele se a aplicação for revertida). Isso é intencional —
    # remover um enum value usado em registros existentes corromperia dados.
    pass
