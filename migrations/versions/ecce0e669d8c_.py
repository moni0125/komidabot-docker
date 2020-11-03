"""Add snack type to coursetype enum

Revision ID: ecce0e669d8c
Revises: 2887dcc37788
Create Date: 2020-11-03 17:35:48.126589

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ecce0e669d8c'
down_revision = '2887dcc37788'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    COMMIT
    """)
    op.execute("""
    ALTER TYPE coursetype ADD VALUE IF NOT EXISTS 'SNACK' AFTER 'DESSERT'
    """)


def downgrade():
    raise NotImplementedError()
