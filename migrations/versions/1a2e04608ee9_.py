"""Add web_subscriptions and provider column to registered_user table

Revision ID: 1a2e04608ee9
Revises: d225cbda8c77
Create Date: 2020-10-25 18:55:31.881046

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '1a2e04608ee9'
down_revision = 'd225cbda8c77'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('registered_user', sa.Column('provider', sa.String(length=16), nullable=False))
    op.add_column('registered_user', sa.Column('web_subscriptions', sa.String(), server_default='[]', nullable=False))


def downgrade():
    op.drop_column('registered_user', 'web_subscriptions')
    op.drop_column('registered_user', 'provider')
