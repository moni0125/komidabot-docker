"""Add data_frozen column to menu_item table

Revision ID: fe7bda58c5a4
Revises: ea6e1f581a7b
Create Date: 2020-10-25 23:21:51.975403

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'fe7bda58c5a4'
down_revision = 'ea6e1f581a7b'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('menu_item', sa.Column('data_frozen', sa.Boolean(), server_default=sa.text('false'), nullable=False))


def downgrade():
    op.drop_column('menu_item', 'data_frozen')
