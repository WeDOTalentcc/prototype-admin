"""Update max_seats: pro 20->10, enterprise 100->15 (market alignment, confirmed Paulo 2026-06-23).

Revision ID: 301_update_plan_seats
Revises: eefdfa8803e3
"""
from alembic import op
from sqlalchemy.sql import text

revision = "301_update_plan_seats"
down_revision = "eefdfa8803e3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(text("UPDATE company_plan_configs SET max_seats = 10 WHERE plan_code = 'pro'"))
    op.execute(text("UPDATE company_plan_configs SET max_seats = 15 WHERE plan_code = 'enterprise'"))


def downgrade() -> None:
    op.execute(text("UPDATE company_plan_configs SET max_seats = 20 WHERE plan_code = 'pro'"))
    op.execute(text("UPDATE company_plan_configs SET max_seats = 100 WHERE plan_code = 'enterprise'"))
