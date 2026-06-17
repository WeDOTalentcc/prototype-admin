"""Add otp_attempts to shared_search_access for DB-backed OTP brute-force protection.

Adds a persistent attempt counter to SharedSearchAccess so that OTP
verification rate-limiting cannot be bypassed during Redis outages.

Security context (Task #1189):
- Previously, both OTP endpoints wrapped their Redis rate-limit checks in
  broad try/except blocks that silently swallowed all errors, making the
  limiter fail-open whenever Redis was unavailable.
- otp_attempts is incremented on every verify-otp call and checked against
  MAX_OTP_VERIFY_ATTEMPTS (10) before the Redis sliding-window check runs,
  so the hard cap is always enforced regardless of Redis state.
- otp_attempts is reset to 0 when a new OTP is issued via request-otp.
- Default 0 is safe for existing rows (they start with a clean counter).
"""
from alembic import op
import sqlalchemy as sa


revision = "216"
down_revision = "215"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "shared_search_access",
        sa.Column(
            "otp_attempts",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment=(
                "T-1189: DB-backed OTP attempt counter; enforces brute-force "
                "cap when Redis is unavailable. Reset to 0 on new OTP issue."
            ),
        ),
    )


def downgrade():
    op.drop_column("shared_search_access", "otp_attempts")
