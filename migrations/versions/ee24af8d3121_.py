"""Remove size constraint on AppUser internal ID.

Revision ID: ee24af8d3121
Revises: 5cd86de4dffe
Create Date: 2020-02-27 12:43:51.806644

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'ee24af8d3121'
down_revision = '5cd86de4dffe'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    ALTER TABLE app_user
        ALTER COLUMN internal_id TYPE VARCHAR;
    """)


def downgrade():
    op.execute("""
    ALTER TABLE app_user
        ALTER COLUMN internal_id TYPE VARCHAR(32);
    """)
