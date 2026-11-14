"""adiciona telefone ao fornecedor e indice na data da movimentacao

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-29 10:32:08.195530

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0002'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.add_column('fornecedores', sa.Column('telefone', sa.String(length=20), nullable=True))
    op.create_index(op.f('ix_movimentacoes_data_hora'), 'movimentacoes', ['data_hora'], unique=False)


def downgrade() -> None:

    op.drop_index(op.f('ix_movimentacoes_data_hora'), table_name='movimentacoes')
    op.drop_column('fornecedores', 'telefone')