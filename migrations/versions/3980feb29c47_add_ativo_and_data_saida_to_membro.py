"""add_ativo_and_data_saida_to_membro

Revision ID: 3980feb29c47
Revises: 5388b624ef37
Create Date: 2025-11-07 17:08:41.247046

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3980feb29c47'
down_revision: Union[str, Sequence[str], None] = '5388b624ef37'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Adiciona campo ativo (padrão True para membros existentes)
    op.add_column('membros', sa.Column('ativo', sa.Boolean(), nullable=False, server_default='true'))
    # Adiciona campo data_saida (nullable)
    op.add_column('membros', sa.Column('data_saida', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove os campos adicionados
    op.drop_column('membros', 'data_saida')
    op.drop_column('membros', 'ativo')
