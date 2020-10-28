"""Add dessert type to coursetype enum

Revision ID: aa31c90dc353
Revises: daf22dcadb8d
Create Date: 2020-10-28 02:34:17.867680

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'aa31c90dc353'
down_revision = 'daf22dcadb8d'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    COMMIT
    """)
    op.execute("""
    ALTER TYPE coursetype ADD VALUE IF NOT EXISTS 'DESSERT' AFTER 'SUB'
    """)


def downgrade():
    raise NotImplementedError()
