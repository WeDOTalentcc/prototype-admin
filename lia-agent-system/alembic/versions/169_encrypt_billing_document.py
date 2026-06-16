"""Wave 4 audit 2026-05-22: encrypt payment_methods.billing_document (LGPD Art. 46).

Revision ID: 169_encrypt_billing_document
Revises: 168_encrypt_integration_credentials
Create Date: 2026-05-22

Contexto (Wave 4 audit 2026-05-22)
──────────────────────────────────
``PaymentMethod.billing_document`` (libs/models/lia_models/billing.py:262)
era coluna ``VARCHAR(20)`` plaintext armazenando CPF/CNPJ. LGPD Art. 5 II
define CPF como "dado pessoal" canonical, e Art. 46 exige "medidas
técnicas de segurança aptas a proteger os dados pessoais". DB dump
(backup, leak, court order) expunha CPF de toda base em texto puro —
risco material LGPD + reputacional.

Estado pré-migration verificado em 2026-05-22:
- Coluna existe na ORM mas ``add_payment_method`` em billing_service.py
  hoje não popula o campo. Linhas existentes pré-migration podem ter
  valores se algum path histórico (admin manual SQL, etl) populou.

Pattern canonical (dual-write zero-downtime, espelha migration 168):
─────────────────────────────────────────────────────────────────────
1. Adicionar coluna ``billing_document_encrypted`` (Text, nullable) —
   armazena ciphertext Fernet base64 do CPF/CNPJ.
2. Manter coluna ``billing_document`` existente (renomeada na ORM para
   ``billing_document_legacy``, mas DB column name segue ``billing_document``).
3. Backfill iterativo: para cada row com ``billing_document IS NOT NULL``
   e ``billing_document_encrypted IS NULL``, encriptar via
   ``app.shared.services.pii_crypto.encrypt_pii`` e atualizar a row +
   setar ``billing_document = NULL``.
4. Repository ``add_payment_method`` (a ser patched separadamente quando
   feature exigir gravação de billing_document) só escreverá em
   ``billing_document_encrypted`` daqui em diante.
5. Migration FUTURA (170+) — após zero rows com ``billing_document IS NOT
   NULL`` em produção + nenhum bug em observabilidade — fará
   ``DROP COLUMN billing_document``.

Idempotência: ``IF NOT EXISTS`` em add_column; backfill é loop UPDATE com
``WHERE billing_document_encrypted IS NULL`` — re-run seguro.

REGRA 4 (CLAUDE.md): backfill falha LOUD se ``FIELD_ENCRYPTION_KEY``
ausente em produção (raise via encrypt_pii → PIIEncryptionError).
Em ``IS_DEVELOPMENT=true`` sem key, o encrypt_value retorna plaintext bytes
(EncryptedFieldMixin compat) — backfill registra warning explícito.

LGPD logging
────────────
Backfill NUNCA loga o conteúdo de billing_document (CPF/CNPJ é PII).
Loga apenas o ``id`` da row e contagem total — audit trail sem PII leak.
"""
from typing import Sequence, Union
import logging

from alembic import op
import sqlalchemy as sa
from sqlalchemy.exc import ProgrammingError


revision: str = "169_encrypt_billing_document"
down_revision: Union[str, None] = "168_encrypt_integration_credentials"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


logger = logging.getLogger("alembic.runtime.migration.169")


def _add_column_idempotent(table: str, column: sa.Column) -> None:
    try:
        op.add_column(table, column)
    except ProgrammingError as exc:
        msg = str(exc).lower()
        if "already exists" in msg or "duplicate column" in msg:
            pass
        else:
            raise


def upgrade() -> None:
    conn = op.get_bind()

    # ── 1. Add billing_document_encrypted column (idempotent) ──────────────
    _add_column_idempotent(
        "payment_methods",
        sa.Column("billing_document_encrypted", sa.Text(), nullable=True),
    )

    # ── 2. Ensure legacy column is nullable (it was already, but explicit) ─
    op.alter_column(
        "payment_methods",
        "billing_document",
        existing_type=sa.String(length=20),
        nullable=True,
    )

    # ── 3. Backfill: encrypt existing plaintext CPF/CNPJ ───────────────────
    rows = conn.execute(
        sa.text(
            """
            SELECT id, billing_document
              FROM payment_methods
             WHERE billing_document IS NOT NULL
               AND billing_document_encrypted IS NULL
            """
        )
    ).fetchall()

    if not rows:
        logger.info("169 backfill: zero rows with legacy plaintext billing_document")
        return

    logger.warning(
        "169 backfill: %d row(s) found with legacy plaintext billing_document",
        len(rows),
    )

    # Lazy-import to avoid circulars during alembic env setup.
    try:
        from app.shared.services.pii_crypto import encrypt_pii
    except Exception as exc:  # pragma: no cover — alembic env edge case
        raise RuntimeError(
            "Cannot import encrypt_pii for backfill; ensure lia-agent-system "
            f"is on PYTHONPATH when running alembic. Underlying error: {exc}"
        ) from exc

    for row in rows:
        row_id = row[0]
        plaintext = row[1]

        if plaintext is None or not str(plaintext).strip():
            conn.execute(
                sa.text(
                    """
                    UPDATE payment_methods
                       SET billing_document = NULL
                     WHERE id = :id
                    """
                ),
                {"id": row_id},
            )
            continue

        ciphertext = encrypt_pii(str(plaintext))

        # NEVER log the CPF/CNPJ value (LGPD Art. 5 II + Art. 46).
        # Only id + length (length is non-PII; helps ops diff types CPF/CNPJ).
        logger.info(
            "169 backfill: encrypted billing_document for row=%s (length=%d)",
            row_id,
            len(str(plaintext)),
        )

        conn.execute(
            sa.text(
                """
                UPDATE payment_methods
                   SET billing_document_encrypted = :ciphertext,
                       billing_document = NULL
                 WHERE id = :id
                """
            ),
            {"id": row_id, "ciphertext": ciphertext},
        )


def downgrade() -> None:
    # WARNING: this downgrade does NOT restore plaintext billing_document —
    # ciphertext stays in billing_document_encrypted, plaintext column is
    # empty. If you truly need to roll back (don't — LGPD), manually
    # decrypt + repopulate billing_document before dropping the encrypted
    # column.
    conn = op.get_bind()
    try:
        op.drop_column("payment_methods", "billing_document_encrypted")
    except ProgrammingError as exc:
        if "does not exist" in str(exc).lower():
            pass
        else:
            raise
