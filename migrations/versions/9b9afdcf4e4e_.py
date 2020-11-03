"""Add column for storing whether a user has been informed about our new site at https://komidabot.xyz/

Revision ID: 9b9afdcf4e4e
Revises: 276ad61a41a5
Create Date: 2020-09-19 20:40:11.471923

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '9b9afdcf4e4e'
down_revision = '276ad61a41a5'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('app_user', sa.Column('notified_new_site', sa.Boolean(), server_default=sa.text('false'),
                                        nullable=False))


def downgrade():
    op.drop_column('app_user', 'notified_new_site')
