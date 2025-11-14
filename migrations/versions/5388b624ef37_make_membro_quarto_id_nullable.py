"""make_membro_quarto_id_nullable

Revision ID: 5388b624ef37
Revises: a80b8cbc182e
Create Date: 2025-11-07 13:41:55.325678

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5388b624ef37'
down_revision: Union[str, Sequence[str], None] = 'a80b8cbc182e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Make quarto_id nullable in membros table
    op.alter_column('membros', 'quarto_id',
                    existing_type=sa.INTEGER(),
                    nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Make quarto_id NOT NULL again (rollback)
    op.alter_column('membros', 'quarto_id',
                    existing_type=sa.INTEGER(),
                    nullable=False)
