"""add edu_org_id column to clubs

Revision ID: c3b4a2d9e6f1
Revises: 9a1d2c7ef4b8
Create Date: 2026-02-23 00:03:00.000000+00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c3b4a2d9e6f1"
down_revision: Union[str, Sequence[str], None] = "9a1d2c7ef4b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("clubs", sa.Column("edu_org_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_clubs_edu_org_id"), "clubs", ["edu_org_id"], unique=False)

    # Add FK only when educational_organizations table exists in the target DB.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = 'educational_organizations'
            ) THEN
                IF NOT EXISTS (
                    SELECT 1
                    FROM information_schema.table_constraints
                    WHERE table_schema = 'public'
                      AND table_name = 'clubs'
                      AND constraint_name = 'fk_clubs_edu_org_id_educational_organizations'
                ) THEN
                    ALTER TABLE clubs
                    ADD CONSTRAINT fk_clubs_edu_org_id_educational_organizations
                    FOREIGN KEY (edu_org_id)
                    REFERENCES educational_organizations (id);
                END IF;
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE clubs
        DROP CONSTRAINT IF EXISTS fk_clubs_edu_org_id_educational_organizations;
        """
    )
    op.drop_index(op.f("ix_clubs_edu_org_id"), table_name="clubs")
    op.drop_column("clubs", "edu_org_id")
