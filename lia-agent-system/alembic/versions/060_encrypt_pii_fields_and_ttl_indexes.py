"""Add PII encryption columns (email/CPF) and TTL performance indexes.

Strategy: zero-downtime dual-write migration
============================================
1. Add nullable encrypted/hash columns to candidates, client_users, users.
2. Backfill email_hash for ALL existing rows using a deterministic SQL function
   (SHA-256 of lower(trim(email))) so that the hash-based lookup path is
   immediately usable after migration — no external backfill script needed for
   the hash column.
3. For the encrypted bytes columns (email_encrypted, cpf_encrypted) the
   backfill CANNOT be done inside Alembic because Fernet requires the
   application key. A separate scheduled task ``pii.backfill_encrypt_existing``
   handles byte-level backfill after deployment.
4. Create TTL performance indexes on ``created_at`` for cleanup job efficiency.

What this migration does NOT do
--------------------------------
- It does NOT remove plaintext columns (they stay for dual-write compatibility).
- It does NOT require any application downtime.
- Rollback drops the new columns and indexes only (plaintext data unaffected).

Plaintext deprecation timeline
-------------------------------
Phase 1 (this migration, 060): Add encrypted/hash columns; backfill email_hash.
Phase 2 (migration 061): Deploy Celery task pii.backfill_encrypt_existing to
  encrypt existing plaintext PII bytes into email_encrypted/cpf_encrypted.
Phase 3 (migration 062): Once all rows have non-null email_encrypted, enforce
  NOT NULL on encrypted columns; stop writing to plaintext columns in app code.
Phase 4 (migration 063): Drop plaintext email/cpf columns or replace with NULL.

Until Phase 3 completes, the plaintext columns are a KNOWN RISK. The dual-write
strategy ensures all NEW rows since this migration have both forms stored,
minimising the window of exposure for future breach scenarios.

Error handling
--------------
Column / index creation uses ``IF NOT EXISTS`` or catches
``sqlalchemy.exc.ProgrammingError`` (duplicate object), not broad
``except Exception: pass``. Silent swallowing of unexpected errors is not used.

Revision: 060
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.exc import ProgrammingError


revision = '060'
down_revision = '059'
branch_labels = None
depends_on = None


def _add_column_idempotent(table: str, column: sa.Column) -> None:
    """Add a column if it does not already exist (catches ProgrammingError duplicate)."""
    try:
        op.add_column(table, column)
    except ProgrammingError as exc:
        if "already exists" in str(exc).lower() or "duplicate column" in str(exc).lower():
            pass  # Idempotent: column exists, nothing to do
        else:
            raise


def _create_index_idempotent(name: str, table: str, columns: list[str]) -> None:
    """Create an index if it does not already exist."""
    try:
        op.create_index(name, table, columns)
    except ProgrammingError as exc:
        if "already exists" in str(exc).lower():
            pass  # Idempotent: index exists, nothing to do
        else:
            raise


def upgrade() -> None:
    conn = op.get_bind()

    # ── 1. Enable pgcrypto extension (idempotent) ─────────────────────────────
    conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))

    # ── 2. candidates table ───────────────────────────────────────────────────
    _add_column_idempotent("candidates", sa.Column("email_encrypted", sa.LargeBinary, nullable=True))
    _add_column_idempotent("candidates", sa.Column("email_hash", sa.String(64), nullable=True))
    _add_column_idempotent("candidates", sa.Column("cpf_encrypted", sa.LargeBinary, nullable=True))
    _create_index_idempotent("ix_candidates_email_hash", "candidates", ["email_hash"])

    # Backfill email_hash for existing rows (deterministic SHA-256, no key required)
    conn.execute(sa.text(
        """
        UPDATE candidates
           SET email_hash = encode(
                   digest(lower(trim(email)), 'sha256'),
                   'hex'
               )
         WHERE email IS NOT NULL
           AND email_hash IS NULL
        """
    ))

    # ── 3. client_users table ─────────────────────────────────────────────────
    _add_column_idempotent("client_users", sa.Column("email_encrypted", sa.LargeBinary, nullable=True))
    _add_column_idempotent("client_users", sa.Column("email_hash", sa.String(64), nullable=True))
    _create_index_idempotent("ix_client_users_email_hash", "client_users", ["email_hash"])

    conn.execute(sa.text(
        """
        UPDATE client_users
           SET email_hash = encode(
                   digest(lower(trim(email)), 'sha256'),
                   'hex'
               )
         WHERE email IS NOT NULL
           AND email_hash IS NULL
        """
    ))

    # Add unique index on (company_id, email_hash) for client_users.
    # The existing (company_id, email) index remains during dual-write phase;
    # it will be dropped in migration 063 when plaintext columns are removed.
    try:
        conn.execute(sa.text(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_client_user_company_email_hash
                ON client_users (company_id, email_hash)
             WHERE email_hash IS NOT NULL
            """
        ))
    except ProgrammingError as exc:
        if "already exists" in str(exc).lower():
            pass
        else:
            raise

    # ── 4. users (auth) table ─────────────────────────────────────────────────
    _add_column_idempotent("users", sa.Column("email_encrypted", sa.LargeBinary, nullable=True))
    _add_column_idempotent("users", sa.Column("email_hash", sa.String(64), nullable=True))
    _create_index_idempotent("ix_users_email_hash", "users", ["email_hash"])

    # Add unique index on email_hash. Existing unique constraint on plaintext email
    # remains during the dual-write phase; dropped in migration 063.
    try:
        conn.execute(sa.text(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email_hash
                ON users (email_hash)
             WHERE email_hash IS NOT NULL
            """
        ))
    except ProgrammingError as exc:
        if "already exists" in str(exc).lower():
            pass
        else:
            raise

    conn.execute(sa.text(
        """
        UPDATE users
           SET email_hash = encode(
                   digest(lower(trim(email)), 'sha256'),
                   'hex'
               )
         WHERE email IS NOT NULL
           AND email_hash IS NULL
        """
    ))

    # ── 5. TTL performance indexes (created_at) ───────────────────────────────
    ttl_tables = [
        # Primary chat table (lia_models/conversation.py → Message.__tablename__ = "messages")
        ("messages", "created_at"),
        # Legacy / alternate table names
        ("conversation_messages", "created_at"),
        ("chat_messages", "created_at"),
        ("interview_notes", "created_at"),
        ("screening_tasks", "created_at"),
        ("fairness_audit_log", "created_at"),
    ]
    for table, col in ttl_tables:
        idx_name = f"ix_{table}_{col}_ttl"
        # Check table existence before creating index to avoid aborting the transaction
        # (asyncpg does not support error recovery within a transaction block)
        table_exists = conn.execute(sa.text(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name = :t"
        ), {"t": table}).scalar()
        if not table_exists:
            continue
        try:
            conn.execute(sa.text(
                f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({col})"  # noqa: S608
            ))
        except ProgrammingError as exc:
            if "already exists" in str(exc).lower():
                pass
            else:
                raise


def downgrade() -> None:
    # Drop indexes (catch if already dropped)
    for idx in [
        "ix_candidates_email_hash",
        "ix_client_users_email_hash",
        "ix_users_email_hash",
    ]:
        try:
            op.drop_index(idx)
        except ProgrammingError as exc:
            if "does not exist" in str(exc).lower():
                pass
            else:
                raise

    # Drop columns (catch if already dropped)
    for table, col in [
        ("candidates", "email_encrypted"),
        ("candidates", "email_hash"),
        ("candidates", "cpf_encrypted"),
        ("client_users", "email_encrypted"),
        ("client_users", "email_hash"),
        ("users", "email_encrypted"),
        ("users", "email_hash"),
    ]:
        try:
            op.drop_column(table, col)
        except ProgrammingError as exc:
            if "does not exist" in str(exc).lower():
                pass
            else:
                raise
