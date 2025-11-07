"""remove_unique_constraints_from_membro

Revision ID: bca6842a041d
Revises: 3980feb29c47
Create Date: 2025-11-07 17:13:50.991363

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bca6842a041d'
down_revision: Union[str, Sequence[str], None] = '3980feb29c47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Remove unique constraint from email
    op.drop_constraint('membros_email_key', 'membros', type_='unique')
    
    # Remove unique constraint from telephone
    op.drop_constraint('membros_telephone_key', 'membros', type_='unique')


def downgrade() -> None:
    """Downgrade schema."""
    # Restore unique constraint on email
    op.create_unique_constraint('membros_email_key', 'membros', ['email'])
    
    # Restore unique constraint on telephone
    op.create_unique_constraint('membros_telephone_key', 'membros', ['telephone'])
