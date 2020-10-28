"""Drop food_type type

Revision ID: daf22dcadb8d
Revises: fe7bda58c5a4
Create Date: 2020-10-28 01:52:05.428570

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'daf22dcadb8d'
down_revision = 'fe7bda58c5a4'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('menu_item', 'food_type')
    op.execute("DROP TYPE foodtype")


def downgrade():
    raise NotImplementedError()
