"""Add field to users to indicate whether they've received an introduction to the bot yet

Revision ID: 93b9de63cd7b
Revises: 92e4e9f8ff64
Create Date: 2019-11-27 16:14:21.089378

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '93b9de63cd7b'
down_revision = '92e4e9f8ff64'
branch_labels = None
depends_on = None


def upgrade():
    # Manual query because apparently relying on alembic doesn't work here
    op.execute("""
    ALTER TABLE app_user ADD COLUMN onboarding_done BOOLEAN NOT NULL DEFAULT FALSE
    """)


def downgrade():
    op.drop_column('app_user', 'onboarding_done')
