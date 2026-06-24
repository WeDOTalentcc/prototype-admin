"""295_add_department_color

Adds color column to departments table.
B3 fix — department color was ignored by UI because column didn't exist.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '295'
down_revision = '294'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('departments', sa.Column('color', sa.String(100), nullable=True))


def downgrade():
    op.drop_column('departments', 'color')
