"""Add learning datapoints table for gathering data to train a classifier

Revision ID: eda0c928c279
Revises: 1dafd2bf730a
Create Date: 2020-10-29 02:38:04.925464

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'eda0c928c279'
down_revision = '1dafd2bf730a'
branch_labels = None
depends_on = None


def upgrade():
    # This fixes a problem where the primary key didn't get updated in a previous migration
    op.execute("ALTER TABLE registered_user DROP CONSTRAINT registered_user_pkey")
    op.execute("ALTER TABLE registered_user ADD PRIMARY KEY (id, provider)")

    op.create_table('learning_datapoint',
                    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
                    sa.Column('campus_id', sa.Integer(), nullable=False),
                    sa.Column('menu_day', sa.Date(), nullable=False),
                    sa.Column('screenshot', sa.Text(), nullable=False),
                    sa.Column('processed_data', sa.Text(), nullable=False),
                    sa.ForeignKeyConstraint(('campus_id',), ['campus.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('learning_datapoint_submission',
                    sa.Column('user_id', sa.String(), nullable=False),
                    sa.Column('user_provider', sa.String(length=16), nullable=False),
                    sa.Column('datapoint_id', sa.Integer(), nullable=False),
                    sa.Column('submission_data', sa.Text(), nullable=False),
                    sa.ForeignKeyConstraint(('datapoint_id',), ['learning_datapoint.id'],
                                            onupdate='CASCADE', ondelete='CASCADE'),
                    sa.ForeignKeyConstraint(('user_id', 'user_provider'),
                                            ['registered_user.id', 'registered_user.provider'],
                                            onupdate='CASCADE',
                                            ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('user_id', 'user_provider', 'datapoint_id')
                    )


def downgrade():
    op.drop_table('learning_datapoint_submission')
    op.drop_table('learning_datapoint')
