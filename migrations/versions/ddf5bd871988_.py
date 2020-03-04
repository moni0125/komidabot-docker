"""Add field to Translation indicating the provider of the translation. e.g. google, bing, komida, ...
Also truncates language fields

Revision ID: ddf5bd871988
Revises: b384f281e755
Create Date: 2020-03-04 14:52:00.074936

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'ddf5bd871988'
down_revision = 'b384f281e755'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('translation', sa.Column('provider', sa.String(length=16), nullable=True))
    op.execute("""
    UPDATE translation
    SET provider = 'google',
        language = LEFT(language, 2)
    """)
    op.execute("""
    UPDATE translatable
    SET original_language = LEFT(original_language, 2)
    """)
    op.execute("""
    UPDATE app_user
    SET language = LEFT(language, 2)
    """)


def downgrade():
    op.drop_column('translation', 'provider')
    op.execute("""
    UPDATE translation
    SET language = 'nl_NL'
    WHERE language = 'nl'
    """)
    op.execute("""
    UPDATE translatable
    SET original_language = 'nl_NL'
    WHERE original_language = 'nl'
    """)
    op.execute("""
    UPDATE app_user
    SET language = 'nl_NL'
    WHERE language = 'nl'
    """)
    op.execute("""
    UPDATE translation
    SET language = 'en_GB'
    WHERE language = 'en'
    """)
    op.execute("""
    UPDATE translatable
    SET original_language = 'en_GB'
    WHERE original_language = 'en'
    """)
    op.execute("""
    UPDATE app_user
    SET language = 'en_GB'
    WHERE language = 'en'
    """)
    op.execute("""
    UPDATE translation
    SET language = 'hi_IN'
    WHERE language = 'hi'
    """)
    op.execute("""
    UPDATE translatable
    SET original_language = 'hi_IN'
    WHERE original_language = 'hi'
    """)
    op.execute("""
    UPDATE app_user
    SET language = 'hi_IN'
    WHERE language = 'hi'
    """)
    op.execute("""
    UPDATE translation
    SET language = 'de_DE'
    WHERE language = 'de'
    """)
    op.execute("""
    UPDATE translatable
    SET original_language = 'de_DE'
    WHERE original_language = 'de'
    """)
    op.execute("""
    UPDATE app_user
    SET language = 'de_DE'
    WHERE language = 'de'
    """)
    op.execute("""
    UPDATE translation
    SET language = 'ko_KR'
    WHERE language = 'ko'
    """)
    op.execute("""
    UPDATE translatable
    SET original_language = 'ko_KR'
    WHERE original_language = 'ko'
    """)
    op.execute("""
    UPDATE app_user
    SET language = 'ko_KR'
    WHERE language = 'ko'
    """)
    op.execute("""
    UPDATE translation
    SET language = 'es_ES'
    WHERE language = 'es'
    """)
    op.execute("""
    UPDATE translatable
    SET original_language = 'es_ES'
    WHERE original_language = 'es'
    """)
    op.execute("""
    UPDATE app_user
    SET language = 'es_ES'
    WHERE language = 'es'
    """)
