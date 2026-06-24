"""merge 299 300 heads

Revision ID: eefdfa8803e3
Revises: 299_index_integration_catalog_is_master, 300_approval_sprint2
Create Date: 2026-06-21 20:50:06.982242

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eefdfa8803e3'
down_revision: Union[str, None] = ('299_index_integration_catalog_is_master', '300_approval_sprint2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
