"""Make tables be lowercase to please Postgres

Revision ID: 85b659320f83
Revises: fe4aca6853a2
Create Date: 2019-10-13 23:32:53.122630

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '85b659320f83'
down_revision = 'fe4aca6853a2'
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table('Campus', 'campus')
    op.rename_table('Translatable', 'translatable')
    op.rename_table('Translation', 'translation')
    op.rename_table('Menu', 'menu')
    op.rename_table('MenuItem', 'menu_item')
    op.rename_table('Subscription', 'subscription')


def downgrade():
    op.rename_table('campus', 'Campus')
    op.rename_table('translatable', 'Translatable')
    op.rename_table('translation', 'Translation')
    op.rename_table('menu', 'Menu')
    op.rename_table('menu_item', 'MenuItem')
    op.rename_table('subscription', 'Subscription')
