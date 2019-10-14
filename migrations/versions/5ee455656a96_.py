"""Rename table subscription -> user

Revision ID: 5ee455656a96
Revises: 85b659320f83
Create Date: 2019-10-14 00:49:07.272985

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '5ee455656a96'
down_revision = '85b659320f83'
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table('subscription', 'app_user')


def downgrade():
    op.rename_table('app_user', 'subscription')
