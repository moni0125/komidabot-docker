"""Rename VEGAN to VEGETARIAN and add a real VEGAN enum option

Revision ID: bd04cd56036f
Revises: bc1ef0083bb4
Create Date: 2020-10-08 01:52:43.143274

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'bd04cd56036f'
down_revision = 'bc1ef0083bb4'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    COMMIT
    """)
    op.execute("""
    ALTER TYPE coursesubtype RENAME VALUE 'VEGAN' TO 'VEGETARIAN'
    """)
    op.execute("""
    ALTER TYPE coursesubtype ADD VALUE IF NOT EXISTS 'VEGAN' AFTER 'VEGETARIAN'
    """)


def downgrade():
    raise NotImplementedError()
