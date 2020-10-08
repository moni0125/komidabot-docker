"""Add new FoodType enum values

Revision ID: 4fafafd2400f
Revises: 7751a57b029e
Create Date: 2019-10-28 19:54:52.943891

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '4fafafd2400f'
down_revision = '7751a57b029e'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    COMMIT
    """)
    op.execute("""
    ALTER TYPE foodtype ADD VALUE IF NOT EXISTS 'SALAD' AFTER 'PASTA_VEGAN'
    """)
    op.execute("""
    ALTER TYPE foodtype ADD VALUE IF NOT EXISTS 'SUB' AFTER 'SALAD'
    """)


def downgrade():
    raise NotImplementedError()
