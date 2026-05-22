"""WT-P0.D: encrypt integration_connections.credentials (LGPD Art. 46 + ADR-006).

Revision ID: 168_encrypt_integration_credentials
Revises: 167_execution_plan_company_id_not_null
Create Date: 2026-05-22

Contexto (Wave 3 audit 2026-05-21, ~/Documents/wedotalent_audit_2026-05-21/audit_usuarios_integracoes.md)
─────────────────────────────────────────────────────────────────────────────────────────────────────
``IntegrationConnection.credentials`` era coluna ``JSON`` plaintext. Schema
mentia ("Encrypted credentials" no Field description) mas repo
``create_connection`` salvava raw dict. Risco LGPD direto + ADR-006 break:
DB dump (backup, leak, request-by-court) expunha API keys / OAuth tokens /
webhook secrets em texto puro.

Estado pré-migration verificado em 2026-05-22:
- ``integration_connections`` SQL ``SELECT COUNT(*)`` = 0 rows
  (defense-in-depth: ainda assim aplicamos o pattern canonical)

Pattern canonical (dual-write zero-downtime, espelha migration 060/160):
─────────────────────────────────────────────────────────────────────────
1. Adicionar coluna ``credentials_encrypted`` (Text, nullable) — armazena
   ciphertext Fernet base64 do JSON-dump dos credentials.
2. Manter coluna ``credentials`` existente (renomeada na ORM para
   ``credentials_legacy``, mas DB column name segue ``credentials``).
   Backfill iterativo: para cada row com ``credentials IS NOT NULL`` e
   ``credentials_encrypted IS NULL``, encriptar via
   ``app.shared.services.credentials_crypto.encrypt_credentials`` e
   atualizar a row + setar ``credentials = NULL``.
3. Repository ``create_connection`` / ``update_connection`` (já patcheados)
   só escrevem em ``credentials_encrypted`` daqui em diante. Nenhuma row
   nova vai para ``credentials_legacy``.
4. Migration FUTURA (169+) — após zero rows com ``credentials IS NOT NULL``
   em produção + nenhum bug em observabilidade — fará ``DROP COLUMN credentials``.

Idempotência: ``IF NOT EXISTS`` em add_column; backfill é loop UPDATE com
``WHERE credentials_encrypted IS NULL`` — re-run seguro.

REGRA 4 (CLAUDE.md): backfill falha LOUD se ``FIELD_ENCRYPTION_KEY``
ausente em produção (raise via encrypt_credentials → CredentialsEncryptionError).
Em ``IS_DEVELOPMENT=true`` sem key, o encrypt_value retorna plaintext bytes
(EncryptedFieldMixin compat) — backfill registra warning explícito.

LGPD logging
────────────
Backfill NUNCA loga o conteúdo de credentials. Loga apenas o ``id`` da row
e contagem total — para audit trail sem expor secret.
"""
from typing import Sequence, Union
import logging

from alembic import op
import sqlalchemy as sa
from sqlalchemy.exc import ProgrammingError


revision: str = "168_encrypt_integration_credentials"
down_revision: Union[str, None] = "167_execution_plan_company_id_not_null"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


logger = logging.getLogger("alembic.runtime.migration.168")


def _add_column_idempotent(table: str, column: sa.Column) -> None:
    try:
        op.add_column(table, column)
    except ProgrammingError as exc:
        if "already exists" in str(exc).lower() or "duplicate column" in str(exc).lower():
            pass
        else:
            raise


def upgrade() -> None:
    conn = op.get_bind()

    # ── 1. Add credentials_encrypted column (idempotent) ──────────────────
    _add_column_idempotent(
        "integration_connections",
        sa.Column("credentials_encrypted", sa.Text(), nullable=True),
    )

    # ── 2. Make legacy credentials column nullable (was JSON default {}) ──
    # The ORM rename is libs/models/lia_models/integration_hub.py — DB
    # column name stays "credentials".
    op.alter_column(
        "integration_connections",
        "credentials",
        existing_type=sa.JSON(),
        nullable=True,
    )

    # ── 3. Backfill: encrypt existing plaintext credentials ────────────────
    # Pull rows that still have plaintext credentials and no ciphertext yet.
    rows = conn.execute(
        sa.text(
            """
            SELECT id, credentials::text
              FROM integration_connections
             WHERE credentials IS NOT NULL
               AND credentials_encrypted IS NULL
            """
        )
    ).fetchall()

    if not rows:
        logger.info("168 backfill: zero rows with legacy plaintext credentials")
    else:
        logger.warning(
            "168 backfill: %d row(s) found with legacy plaintext credentials",
            len(rows),
        )

        # Lazy-import to avoid circulars during alembic env setup.
        import json
        try:
            from app.shared.services.credentials_crypto import encrypt_credentials
        except Exception as exc:  # pragma: no cover — Alembic env path edge case
            raise RuntimeError(
                "Cannot import encrypt_credentials for backfill; "
                "ensure lia-agent-system is on PYTHONPATH when running alembic. "
                f"Underlying error: {exc}"
            ) from exc

        for row in rows:
            row_id = row[0]
            try:
                creds_dict = json.loads(row[1]) if row[1] else None
            except (TypeError, ValueError) as exc:
                # Malformed legacy JSON — refuse to silently drop. REGRA 4.
                raise RuntimeError(
                    f"Row {row_id} has invalid JSON in credentials column; "
                    "manual investigation required before migration can proceed."
                ) from exc

            if not creds_dict:
                # Empty dict or null-equivalent — set NULL on legacy column.
                conn.execute(
                    sa.text(
                        """
                        UPDATE integration_connections
                           SET credentials = NULL
                         WHERE id = :id
                        """
                    ),
                    {"id": row_id},
                )
                continue

            ciphertext = encrypt_credentials(creds_dict)

            # NEVER log the dict contents (LGPD). Only id + key count.
            logger.info(
                "168 backfill: encrypted credentials for row=%s (keys=%d)",
                row_id,
                len(creds_dict),
            )

            conn.execute(
                sa.text(
                    """
                    UPDATE integration_connections
                       SET credentials_encrypted = :ciphertext,
                           credentials = NULL
                     WHERE id = :id
                    """
                ),
                {"id": row_id, "ciphertext": ciphertext},
            )


def downgrade() -> None:
    # WARNING: this downgrade does NOT restore plaintext credentials —
    # ciphertext stays in credentials_encrypted, plaintext column is empty.
    # If you truly need to roll back, manually decrypt + repopulate
    # credentials before dropping credentials_encrypted.
    conn = op.get_bind()
    try:
        op.drop_column("integration_connections", "credentials_encrypted")
    except ProgrammingError as exc:
        if "does not exist" in str(exc).lower():
            pass
        else:
            raise

    op.alter_column(
        "integration_connections",
        "credentials",
        existing_type=sa.JSON(),
        nullable=False,
        server_default=sa.text("{}::json"),
    )
