"""Change registered_users table to have an internal id, rather than having a primary key based on 2 columns

Revision ID: 2887dcc37788
Revises: eda0c928c279
Create Date: 2020-11-02 22:43:08.274496

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '2887dcc37788'
down_revision = 'eda0c928c279'
branch_labels = None
depends_on = None


def upgrade():
    # Primary key shuffling
    op.rename_table('registered_user', 'registered_users')
    op.alter_column('registered_users', 'id', new_column_name='subject')
    id_seq = sa.Sequence('registered_users_id_seq')
    op.execute(sa.schema.CreateSequence(id_seq))
    op.add_column('registered_users', sa.Column('id', sa.Integer(), nullable=False, server_default=id_seq.next_value()))

    op.drop_constraint('learning_datapoint_submission_user_id_fkey', 'learning_datapoint_submission',
                       type_='foreignkey')
    op.drop_constraint('registered_user_pkey', 'registered_users', type_='primary')
    op.create_unique_constraint('registered_users_provider_subject_key', 'registered_users', ['provider', 'subject'])

    # Foreign keys also need updating
    op.alter_column('learning_datapoint_submission', 'user_id', new_column_name='user_subject')
    op.add_column('learning_datapoint_submission',
                  sa.Column('user_id', sa.Integer(), autoincrement=False))
    op.execute("""
    UPDATE learning_datapoint_submission
    SET user_id = users.id
    FROM (SELECT id, subject, provider FROM registered_users) AS users
    WHERE learning_datapoint_submission.user_subject = users.subject
        AND learning_datapoint_submission.user_provider = users.provider
    """)
    op.alter_column('learning_datapoint_submission', 'user_id', nullable=False)
    op.drop_constraint('learning_datapoint_submission_pkey', 'learning_datapoint_submission', type_='primary')
    op.create_primary_key('learning_datapoint_submission_pkey', 'learning_datapoint_submission',
                          ['user_id', 'datapoint_id'])
    op.drop_column('learning_datapoint_submission', 'user_provider')
    op.drop_column('learning_datapoint_submission', 'user_subject')

    op.create_primary_key('registered_users_pkey', 'registered_users', ['id'])
    op.create_foreign_key('learning_datapoint_submission_user_id_fkey', 'learning_datapoint_submission',
                          'registered_users', ['user_id'], ['id'], onupdate='CASCADE', ondelete='CASCADE')

    # Replace enabled with more informative version having dates
    op.add_column('registered_users', sa.Column('activated_on', sa.DateTime(), nullable=True))
    op.add_column('registered_users', sa.Column('registered_on', sa.DateTime(), server_default=sa.text('now()'),
                                                nullable=False))
    op.execute("UPDATE registered_users SET activated_on = NOW() WHERE enabled = TRUE")
    op.drop_column('registered_users', 'enabled')

    # Add new tables for roles
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_table(
        'user_roles',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['registered_users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'role_id')
    )


def downgrade():
    # Remove roles tables
    op.drop_table('user_roles')
    op.drop_table('roles')

    # Bring back enabled column
    op.add_column('registered_users', sa.Column('enabled', sa.BOOLEAN(), server_default=sa.text('false'),
                                                autoincrement=False, nullable=False))
    op.execute("UPDATE registered_users SET enabled = TRUE WHERE activated_on IS NOT NULL")
    op.drop_column('registered_users', 'registered_on')
    op.drop_column('registered_users', 'activated_on')

    # Undo foreign keys updating after primary key shuffling
    op.drop_constraint('learning_datapoint_submission_user_id_fkey', 'learning_datapoint_submission',
                       type_='foreignkey')
    op.drop_constraint('registered_users_pkey', 'registered_users', type_='primary')

    op.add_column('learning_datapoint_submission',
                  sa.Column('user_subject', sa.String(), autoincrement=False))
    op.add_column('learning_datapoint_submission',
                  sa.Column('user_provider', sa.String(16), autoincrement=False))
    op.drop_constraint('learning_datapoint_submission_pkey', 'learning_datapoint_submission', type_='primary')
    op.create_primary_key('learning_datapoint_submission_pkey', 'learning_datapoint_submission',
                          ['user_subject', 'user_provider', 'datapoint_id'])
    op.execute("""
    UPDATE learning_datapoint_submission
    SET user_subject = users.subject, user_provider = users.provider
    FROM (SELECT id, subject, provider FROM registered_users) AS users
    WHERE learning_datapoint_submission.user_id = users.id
    """)
    op.alter_column('learning_datapoint_submission', 'user_subject', nullable=False)
    op.alter_column('learning_datapoint_submission', 'user_provider', nullable=False)
    op.drop_column('learning_datapoint_submission', 'user_id')
    op.alter_column('learning_datapoint_submission', 'user_subject', new_column_name='user_id')

    op.drop_constraint('registered_users_provider_subject_key', 'registered_users', type_='unique')
    op.create_primary_key('registered_user_pkey', 'registered_users', ['subject', 'provider'])
    op.create_foreign_key('learning_datapoint_submission_user_id_fkey', 'learning_datapoint_submission',
                          'registered_users', ['user_id', 'user_provider'], ['subject', 'provider'],
                          onupdate='CASCADE', ondelete='CASCADE')

    # Undo primary key shuffling
    op.drop_column('registered_users', 'id')
    op.execute(sa.schema.DropSequence(sa.Sequence('registered_users_id_seq')))
    op.alter_column('registered_users', 'subject', new_column_name='id')
    op.rename_table('registered_users', 'registered_user')
