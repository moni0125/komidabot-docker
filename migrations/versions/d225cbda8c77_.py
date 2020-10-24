"""Added registered_user and app_settings table

Revision ID: d225cbda8c77
Revises: 528821121657
Create Date: 2020-10-24 22:29:31.746859

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'd225cbda8c77'
down_revision = '528821121657'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('registered_user',
                    sa.Column('id', sa.String(), nullable=False),
                    sa.Column('name', sa.String(), nullable=False),
                    sa.Column('email', sa.String(), nullable=False),
                    sa.Column('profile_picture', sa.String(), nullable=False),
                    sa.Column('enabled', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('email')
                    )

    op.create_table('app_settings',
                    sa.Column('name', sa.String(), nullable=False),
                    sa.Column('value', sa.String(), server_default=sa.text('null'), nullable=False),
                    sa.PrimaryKeyConstraint('name')
                    )


def downgrade():
    op.drop_table('app_settings')
    op.drop_table('registered_user')
