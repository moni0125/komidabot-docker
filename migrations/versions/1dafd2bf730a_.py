"""Add course allergens column to menu item table

Revision ID: 1dafd2bf730a
Revises: aa31c90dc353
Create Date: 2020-10-28 15:32:49.787976

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '1dafd2bf730a'
down_revision = 'aa31c90dc353'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('menu_item', sa.Column('course_allergens', sa.Text(), server_default='[]', nullable=False))


def downgrade():
    op.drop_column('menu_item', 'course_allergens')
