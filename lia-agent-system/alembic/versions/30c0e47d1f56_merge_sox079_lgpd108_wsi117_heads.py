"""merge sox079_lgpd108_wsi117 heads

Revision ID: 30c0e47d1f56
Revises: 079_sox_audit_company_id, 5880556c6d91, 117_wsi_question_effectiveness
Create Date: 2026-05-03 23:52:26.404407

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '30c0e47d1f56'
down_revision: Union[str, None] = ('079_sox_audit_company_id', '5880556c6d91', '117_wsi_question_effectiveness')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
