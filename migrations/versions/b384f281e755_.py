"""Add column to AppUser to store data that some providers may need to store.

Revision ID: b384f281e755
Revises: ee24af8d3121
Create Date: 2020-02-27 12:52:40.163394

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b384f281e755'
down_revision = 'ee24af8d3121'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('app_user', sa.Column('data', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('app_user', 'data')
