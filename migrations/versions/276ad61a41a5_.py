"""Change food type in menu items to course type and sub type

Revision ID: 276ad61a41a5
Revises: ddf5bd871988
Create Date: 2020-03-10 12:23:22.996161

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = '276ad61a41a5'
down_revision = 'ddf5bd871988'
branch_labels = None
depends_on = None

course_type = pg.ENUM('SOUP', 'DAILY', 'PASTA', 'GRILL', 'SALAD', 'SUB', name='coursetype')
course_sub_type = pg.ENUM('NORMAL', 'VEGAN', name='coursesubtype')


def upgrade():
    course_type.create(op.get_bind())
    course_sub_type.create(op.get_bind())

    op.add_column('menu_item', sa.Column('course_type', course_type, nullable=True))
    op.add_column('menu_item', sa.Column('course_sub_type', course_sub_type, nullable=True))
    op.add_column('menu_item', sa.Column('course_attributes', sa.Text(), nullable=False,
                                         default='[]', server_default='[]'))

    op.execute("""
    UPDATE menu_item
    SET course_type = 'SOUP', course_sub_type = 'NORMAL'
    WHERE food_type = 'SOUP'
    """)
    op.execute("""
    UPDATE menu_item
    SET course_type = 'DAILY', course_sub_type = 'NORMAL'
    WHERE food_type = 'MEAT'
    """)
    op.execute("""
    UPDATE menu_item
    SET course_type = 'DAILY', course_sub_type = 'VEGAN'
    WHERE food_type = 'VEGAN'
    """)
    op.execute("""
    UPDATE menu_item
    SET course_type = 'GRILL', course_sub_type = 'NORMAL'
    WHERE food_type = 'GRILL'
    """)
    op.execute("""
    UPDATE menu_item
    SET course_type = 'PASTA', course_sub_type = 'NORMAL'
    WHERE food_type = 'PASTA_MEAT'
    """)
    op.execute("""
    UPDATE menu_item
    SET course_type = 'PASTA', course_sub_type = 'VEGAN'
    WHERE food_type = 'PASTA_VEGAN'
    """)
    op.execute("""
    UPDATE menu_item
    SET course_type = 'SALAD', course_sub_type = 'NORMAL'
    WHERE food_type = 'SALAD'
    """)
    op.execute("""
    UPDATE menu_item
    SET course_type = 'SUB', course_sub_type = 'NORMAL'
    WHERE food_type = 'SUB'
    """)

    op.alter_column('menu_item', 'course_type', nullable=False)
    op.alter_column('menu_item', 'course_sub_type', nullable=False)


def downgrade():
    op.drop_column('menu_item', 'course_attributes')
    op.drop_column('menu_item', 'course_sub_type')
    op.drop_column('menu_item', 'course_type')

    course_sub_type.drop(op.get_bind())
    course_type.drop(op.get_bind())
