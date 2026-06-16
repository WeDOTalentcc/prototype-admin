"""add rails_user_id to users table (Phase 1 Auth Decoupling)

Phase 1 Rails Elimination (2026-06-10):
  - Adds rails_user_id INTEGER UNIQUE to users table.
  - Enables DB-backed cache for Rails user resolution (rails_user_sync.py).
  - After first Rails JWT request, company_id is resolved from local DB
    instead of making a synchronous HTTP call to Rails GET /v1/me.

Feature flag: FASTAPI_RAILS_DB_CACHE=true (default) uses this column.
Rollback: set FASTAPI_RAILS_DB_CACHE=false — column stays but is not used.

Revision IDs
------------
Revises: 259
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "260"
down_revision = "259"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add rails_user_id column (nullable — not all users came from Rails)
    op.add_column(
        "users",
        sa.Column("rails_user_id", sa.Integer(), nullable=True),
    )
    # Unique partial index: only enforces uniqueness for non-null values
    # (multiple users can have rails_user_id=NULL; only one can have rails_user_id=42)
    op.execute(
        "CREATE UNIQUE INDEX ix_users_rails_user_id ON users(rails_user_id) "
        "WHERE rails_user_id IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_users_rails_user_id")
    op.drop_column("users", "rails_user_id")
