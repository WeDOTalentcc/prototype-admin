"""Reset admindemo@wedotalent.cc password to Admin@LIA2026 (prod seed fix).

Revision ID: 302_reset_admindemo_password
Revises: 301_update_plan_seats
"""
from alembic import op
from sqlalchemy.sql import text

revision = "302_reset_admindemo_password"
down_revision = "301_update_plan_seats"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        text(
            """
            UPDATE users
            SET password_hash = :hash,
                updated_at    = NOW()
            WHERE email = 'admindemo@wedotalent.cc'
            """
        ),
        {"hash": "$2b$12$qDm4tE6ixjYfIuBgdZEzmOyvHVapGMO.V3D6aogY6Wpn1PX1mFYMG"},
    )


def downgrade() -> None:
    pass
