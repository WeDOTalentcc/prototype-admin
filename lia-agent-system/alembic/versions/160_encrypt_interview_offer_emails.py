"""P0.B (audit 2026-05-21): Encrypt PII email columns em interview + offer_proposals.

Closes P0.B do handoff §3. Tabelas afetadas:

- ``interviews``        : candidate_email, interviewer_email, graph_organizer_email
- ``interview_feedbacks``: interviewer_email
- ``offer_proposals``   : candidate_email

ANTES desta migration, esses 5 emails ficavam em plaintext no DB. Risco LGPD
direto: DB dump (backup, leak, request-by-court) expunha PII facilmente,
mesmo com Candidate.email já encriptada (migration 060+111) — atacante
pulava direto pra interview_feedbacks ou offer_proposals.

Estrategia canonical (zero-downtime dual-write phase, idêntica a 060):

1. Adicionar colunas ``*_encrypted`` (LargeBinary) + ``*_hash`` (String(64))
   em cada um dos 5 sites. Hash apenas onde lookup por email faz sentido
   (omitido pra graph_organizer_email — query path improvável).
2. Backfill ``*_hash`` em SQL puro (SHA-256 deterministico, sem precisar
   chave Fernet).
3. Flipar ``candidate_email`` e ``interviewer_email`` (originalmente NOT NULL)
   pra ``nullable=True`` — necessário pra hybrid_property poder gravar
   plaintext column = NULL após encryption no Fernet column.
4. NÃO dropar plaintext columns nesta migration (dual-write transition).

Backfill Fernet bytes (encrypted columns) requer chave aplicação — separate
Celery task ``pii.backfill_encrypt_interview_offer_existing`` em commit
seguinte (mesmo padrão de Phase 2 de 060/061).

Roll-out timeline:
- Phase 1 (esta migration 160): colunas adicionadas + hash backfilled +
  raw flipa nullable=True. App ainda escreve plaintext (dual-write).
- Phase 2 (Celery task separada): backfill *_encrypted dos rows existentes.
- Phase 3 (migration 161+ futura): forçar NOT NULL nas encrypted columns,
  parar de escrever em plaintext (depende dos callers usarem hybrid_property).
- Phase 4 (migration 162+ futura): dropar plaintext columns.

Revision ID: 160_encrypt_interview_offer_emails
Revises: 159_merge_heads_151_158
Create Date: 2026-05-21

Pattern canonical: migration 060_encrypt_pii_fields_and_ttl_indexes.py.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.exc import ProgrammingError


# revision identifiers, used by Alembic.
revision: str = "160_encrypt_interview_offer_emails"
down_revision: Union[str, None] = "159_merge_heads_151_158"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _add_column_idempotent(table: str, column: sa.Column) -> None:
    """Add a column if it does not already exist (idempotent)."""
    try:
        op.add_column(table, column)
    except ProgrammingError as exc:
        if "already exists" in str(exc).lower():
            pass
        else:
            raise


def _create_index_idempotent(name: str, table: str, columns: list[str]) -> None:
    """Create an index if it does not already exist."""
    try:
        op.create_index(name, table, columns)
    except ProgrammingError as exc:
        if "already exists" in str(exc).lower():
            pass
        else:
            raise


def upgrade() -> None:
    conn = op.get_bind()

    # ── pgcrypto extension (idempotent, may already exist from 060) ───────
    conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))

    # ──────────────────────────────────────────────────────────────────────
    # 1. interviews table — 3 emails encrypted
    # ──────────────────────────────────────────────────────────────────────
    _add_column_idempotent(
        "interviews",
        sa.Column("candidate_email_encrypted", sa.LargeBinary, nullable=True),
    )
    _add_column_idempotent(
        "interviews",
        sa.Column("candidate_email_hash", sa.String(64), nullable=True),
    )
    _add_column_idempotent(
        "interviews",
        sa.Column("interviewer_email_encrypted", sa.LargeBinary, nullable=True),
    )
    _add_column_idempotent(
        "interviews",
        sa.Column("interviewer_email_hash", sa.String(64), nullable=True),
    )
    _add_column_idempotent(
        "interviews",
        sa.Column("graph_organizer_email_encrypted", sa.LargeBinary, nullable=True),
    )
    # graph_organizer_email_hash omitido: query path improvável (e-mail do
    # organizador via Microsoft Graph não é indexed lookup).

    _create_index_idempotent(
        "ix_interviews_candidate_email_hash", "interviews", ["candidate_email_hash"]
    )
    _create_index_idempotent(
        "ix_interviews_interviewer_email_hash", "interviews", ["interviewer_email_hash"]
    )

    # Backfill hashes em SQL puro (deterministic SHA-256).
    conn.execute(sa.text(
        """
        UPDATE interviews
           SET candidate_email_hash = encode(
                   digest(lower(trim(candidate_email)), 'sha256'),
                   'hex'
               )
         WHERE candidate_email IS NOT NULL
           AND candidate_email_hash IS NULL
        """
    ))
    conn.execute(sa.text(
        """
        UPDATE interviews
           SET interviewer_email_hash = encode(
                   digest(lower(trim(interviewer_email)), 'sha256'),
                   'hex'
               )
         WHERE interviewer_email IS NOT NULL
           AND interviewer_email_hash IS NULL
        """
    ))

    # Flipar plaintext columns NOT NULL → nullable (transition phase
    # requirement: hybrid_property precisa poder gravar plaintext = NULL).
    op.alter_column(
        "interviews", "candidate_email",
        existing_type=sa.String(255),
        nullable=True,
    )
    op.alter_column(
        "interviews", "interviewer_email",
        existing_type=sa.String(255),
        nullable=True,
    )
    # graph_organizer_email já era nullable.

    # ──────────────────────────────────────────────────────────────────────
    # 2. interview_feedbacks table — 1 email encrypted
    # ──────────────────────────────────────────────────────────────────────
    _add_column_idempotent(
        "interview_feedbacks",
        sa.Column("interviewer_email_encrypted", sa.LargeBinary, nullable=True),
    )
    _add_column_idempotent(
        "interview_feedbacks",
        sa.Column("interviewer_email_hash", sa.String(64), nullable=True),
    )
    _create_index_idempotent(
        "ix_interview_feedbacks_interviewer_email_hash",
        "interview_feedbacks",
        ["interviewer_email_hash"],
    )
    conn.execute(sa.text(
        """
        UPDATE interview_feedbacks
           SET interviewer_email_hash = encode(
                   digest(lower(trim(interviewer_email)), 'sha256'),
                   'hex'
               )
         WHERE interviewer_email IS NOT NULL
           AND interviewer_email_hash IS NULL
        """
    ))
    op.alter_column(
        "interview_feedbacks", "interviewer_email",
        existing_type=sa.String(255),
        nullable=True,
    )

    # ──────────────────────────────────────────────────────────────────────
    # 3. offer_proposals table — 1 email encrypted
    # ──────────────────────────────────────────────────────────────────────
    _add_column_idempotent(
        "offer_proposals",
        sa.Column("candidate_email_encrypted", sa.LargeBinary, nullable=True),
    )
    _add_column_idempotent(
        "offer_proposals",
        sa.Column("candidate_email_hash", sa.String(64), nullable=True),
    )
    _create_index_idempotent(
        "ix_offer_proposals_candidate_email_hash",
        "offer_proposals",
        ["candidate_email_hash"],
    )
    conn.execute(sa.text(
        """
        UPDATE offer_proposals
           SET candidate_email_hash = encode(
                   digest(lower(trim(candidate_email)), 'sha256'),
                   'hex'
               )
         WHERE candidate_email IS NOT NULL
           AND candidate_email_hash IS NULL
        """
    ))
    # offer_proposals.candidate_email já era nullable.


def downgrade() -> None:
    """Drop encrypted/hash columns. Plaintext columns and data unaffected.

    Restores NOT NULL constraints on raw columns (defensive rollback —
    may FAIL if any row has NULL after dual-write transition, in which case
    the rollback is intentionally aborted to prevent data corruption).
    """
    # interviews
    op.drop_index("ix_interviews_interviewer_email_hash", table_name="interviews")
    op.drop_index("ix_interviews_candidate_email_hash", table_name="interviews")
    op.drop_column("interviews", "graph_organizer_email_encrypted")
    op.drop_column("interviews", "interviewer_email_hash")
    op.drop_column("interviews", "interviewer_email_encrypted")
    op.drop_column("interviews", "candidate_email_hash")
    op.drop_column("interviews", "candidate_email_encrypted")
    op.alter_column(
        "interviews", "candidate_email",
        existing_type=sa.String(255),
        nullable=False,
    )
    op.alter_column(
        "interviews", "interviewer_email",
        existing_type=sa.String(255),
        nullable=False,
    )

    # interview_feedbacks
    op.drop_index(
        "ix_interview_feedbacks_interviewer_email_hash",
        table_name="interview_feedbacks",
    )
    op.drop_column("interview_feedbacks", "interviewer_email_hash")
    op.drop_column("interview_feedbacks", "interviewer_email_encrypted")
    op.alter_column(
        "interview_feedbacks", "interviewer_email",
        existing_type=sa.String(255),
        nullable=False,
    )

    # offer_proposals
    op.drop_index(
        "ix_offer_proposals_candidate_email_hash",
        table_name="offer_proposals",
    )
    op.drop_column("offer_proposals", "candidate_email_hash")
    op.drop_column("offer_proposals", "candidate_email_encrypted")
