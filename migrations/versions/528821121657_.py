"""Rename user_subscription to user_day_campus_preference

Revision ID: 528821121657
Revises: bd04cd56036f
Create Date: 2020-10-20 17:47:05.866470

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '528821121657'
down_revision = 'bd04cd56036f'
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table('user_subscription', 'user_day_campus_preference')


def downgrade():
    op.rename_table('user_day_campus_preference', 'user_subscription')
