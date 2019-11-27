"""empty message

Revision ID: 92e4e9f8ff64
Revises: e18b14ed6b98
Create Date: 2019-11-27 10:57:33.180423

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '92e4e9f8ff64'
down_revision = 'e18b14ed6b98'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('campus', 'external_id',
                    existing_type=sa.INTEGER(),
                    nullable=False)
    op.drop_column('campus', 'page_url')


def downgrade():
    op.add_column('campus', sa.Column('page_url', sa.TEXT(), autoincrement=False, nullable=True))
    op.alter_column('campus', 'external_id',
                    existing_type=sa.INTEGER(),
                    nullable=True)
