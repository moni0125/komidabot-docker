"""Change price columns to store as numerics instead of strings

Revision ID: e18b14ed6b98
Revises: 3806b46f7f00
Create Date: 2019-11-07 00:53:28.115755

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'e18b14ed6b98'
down_revision = '3806b46f7f00'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    ALTER TABLE menu_item
        ALTER COLUMN price_students TYPE NUMERIC(4, 2) USING
            CASE
                WHEN price_students = ''
                    THEN 0.0
                ELSE substring(REPLACE(price_students, ',', '.') FROM 2)::numeric(4,2)
            END,
        ALTER COLUMN price_staff TYPE NUMERIC(4, 2) USING
            CASE
                WHEN price_staff = ''
                    THEN 0.0
                ELSE substring(REPLACE(price_staff, ',', '.') FROM 2)::numeric(4,2)
            END,
        ALTER COLUMN price_staff DROP NOT NULL
    """)

    op.execute("""
    UPDATE menu_item
        SET price_staff = NULL
        WHERE price_staff = '0.0'
    """)


def downgrade():
    raise NotImplementedError()
