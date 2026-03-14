"""add_token_cost_to_extraction_run

Revision ID: a2c4e6f8b0d1
Revises: 4f1e280d00cf
Create Date: 2026-03-14 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'a2c4e6f8b0d1'
down_revision: Union[str, Sequence[str], None] = '4f1e280d00cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('extraction_run', sa.Column('tokens_in', sa.Integer(), nullable=True))
    op.add_column('extraction_run', sa.Column('tokens_out', sa.Integer(), nullable=True))
    op.add_column('extraction_run', sa.Column('cost_usd', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('extraction_run', 'cost_usd')
    op.drop_column('extraction_run', 'tokens_out')
    op.drop_column('extraction_run', 'tokens_in')
