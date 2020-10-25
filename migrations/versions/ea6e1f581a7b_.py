"""Add external id column to menu items

Revision ID: ea6e1f581a7b
Revises: 1a2e04608ee9
Create Date: 2020-10-25 21:42:34.054774

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'ea6e1f581a7b'
down_revision = '1a2e04608ee9'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('menu_item', sa.Column('external_id', sa.Integer(), server_default=sa.text('NULL'), nullable=True))
    op.create_unique_constraint(None, 'menu_item', ['external_id'])


def downgrade():
    op.drop_constraint(None, 'menu_item', type_='unique')
    op.drop_column('menu_item', 'external_id')
