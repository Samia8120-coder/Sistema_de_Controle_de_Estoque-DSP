"""criacao inicial do esquema

Revision ID: 0001
Revises: 
Create Date: 2026-10-27 22:32:40.396856

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table('armazens',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(length=80), nullable=False),
    sa.Column('cidade', sa.String(length=80), nullable=False),
    sa.Column('endereco', sa.String(length=150), nullable=True),
    sa.Column('ativo', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_armazens')),
    sa.UniqueConstraint('nome', name=op.f('uq_armazens_nome'))
    )
    op.create_table('categorias',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(length=80), nullable=False),
    sa.Column('descricao', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_categorias')),
    sa.UniqueConstraint('nome', name=op.f('uq_categorias_nome'))
    )
    op.create_table('fornecedores',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(length=120), nullable=False),
    sa.Column('cnpj', sa.String(length=18), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=True),
    sa.Column('ativo', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_fornecedores')),
    sa.UniqueConstraint('cnpj', name=op.f('uq_fornecedores_cnpj'))
    )
    op.create_table('pedidos_compra',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('fornecedor_id', sa.Integer(), nullable=False),
    sa.Column('data_pedido', sa.DateTime(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('observacao', sa.String(length=255), nullable=True),
    sa.CheckConstraint("status IN ('aberto', 'parcial', 'recebido', 'cancelado')", name=op.f('ck_pedidos_compra_status_valido')),
    sa.ForeignKeyConstraint(['fornecedor_id'], ['fornecedores.id'], name=op.f('fk_pedidos_compra_fornecedor_id_fornecedores')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_pedidos_compra'))
    )
    op.create_table('produtos',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('codigo', sa.String(length=30), nullable=False),
    sa.Column('nome', sa.String(length=150), nullable=False),
    sa.Column('descricao', sa.String(length=255), nullable=True),
    sa.Column('preco_unitario', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('estoque_minimo', sa.Integer(), nullable=False),
    sa.Column('ativo', sa.Boolean(), nullable=False),
    sa.Column('categoria_id', sa.Integer(), nullable=False),
    sa.CheckConstraint('estoque_minimo >= 0', name=op.f('ck_produtos_minimo_nao_negativo')),
    sa.CheckConstraint('preco_unitario >= 0', name=op.f('ck_produtos_preco_nao_negativo')),
    sa.ForeignKeyConstraint(['categoria_id'], ['categorias.id'], name=op.f('fk_produtos_categoria_id_categorias')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_produtos')),
    sa.UniqueConstraint('codigo', name=op.f('uq_produtos_codigo'))
    )
    op.create_table('caracteristicas_produto',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('produto_id', sa.Integer(), nullable=False),
    sa.Column('peso_kg', sa.Numeric(precision=8, scale=3), nullable=False),
    sa.Column('altura_cm', sa.Numeric(precision=8, scale=2), nullable=False),
    sa.Column('largura_cm', sa.Numeric(precision=8, scale=2), nullable=False),
    sa.Column('profundidade_cm', sa.Numeric(precision=8, scale=2), nullable=False),
    sa.Column('unidade_medida', sa.String(length=10), nullable=False),
    sa.Column('condicao_armazenamento', sa.String(length=40), nullable=False),
    sa.Column('perecivel', sa.Boolean(), nullable=False),
    sa.CheckConstraint('altura_cm >= 0 AND largura_cm >= 0 AND profundidade_cm >= 0', name=op.f('ck_caracteristicas_produto_dimensoes_nao_negativas')),
    sa.CheckConstraint('peso_kg >= 0', name=op.f('ck_caracteristicas_produto_peso_nao_negativo')),
    sa.ForeignKeyConstraint(['produto_id'], ['produtos.id'], name=op.f('fk_caracteristicas_produto_produto_id_produtos')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_caracteristicas_produto')),
    sa.UniqueConstraint('produto_id', name=op.f('uq_caracteristicas_produto_produto_id'))
    )
    op.create_table('estoque_armazem',
    sa.Column('produto_id', sa.Integer(), nullable=False),
    sa.Column('armazem_id', sa.Integer(), nullable=False),
    sa.Column('quantidade', sa.Integer(), nullable=False),
    sa.CheckConstraint('quantidade >= 0', name=op.f('ck_estoque_armazem_saldo_nao_negativo')),
    sa.ForeignKeyConstraint(['armazem_id'], ['armazens.id'], name=op.f('fk_estoque_armazem_armazem_id_armazens')),
    sa.ForeignKeyConstraint(['produto_id'], ['produtos.id'], name=op.f('fk_estoque_armazem_produto_id_produtos')),
    sa.PrimaryKeyConstraint('produto_id', 'armazem_id', name=op.f('pk_estoque_armazem'))
    )
    op.create_table('itens_pedido_compra',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('pedido_id', sa.Integer(), nullable=False),
    sa.Column('produto_id', sa.Integer(), nullable=False),
    sa.Column('quantidade_pedida', sa.Integer(), nullable=False),
    sa.Column('quantidade_recebida', sa.Integer(), nullable=False),
    sa.Column('preco_unitario', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.CheckConstraint('preco_unitario >= 0', name=op.f('ck_itens_pedido_compra_preco_nao_negativo')),
    sa.CheckConstraint('quantidade_pedida > 0', name=op.f('ck_itens_pedido_compra_pedida_positiva')),
    sa.CheckConstraint('quantidade_recebida >= 0 AND quantidade_recebida <= quantidade_pedida', name=op.f('ck_itens_pedido_compra_recebida_valida')),
    sa.ForeignKeyConstraint(['pedido_id'], ['pedidos_compra.id'], name=op.f('fk_itens_pedido_compra_pedido_id_pedidos_compra')),
    sa.ForeignKeyConstraint(['produto_id'], ['produtos.id'], name=op.f('fk_itens_pedido_compra_produto_id_produtos')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_itens_pedido_compra')),
    sa.UniqueConstraint('pedido_id', 'produto_id', name='produto_unico_no_pedido')
    )
    op.create_table('movimentacoes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('tipo', sa.String(length=20), nullable=False),
    sa.Column('produto_id', sa.Integer(), nullable=False),
    sa.Column('quantidade', sa.Integer(), nullable=False),
    sa.Column('data_hora', sa.DateTime(), nullable=False),
    sa.Column('motivo', sa.String(length=120), nullable=False),
    sa.Column('observacao', sa.String(length=255), nullable=True),
    sa.Column('armazem_origem_id', sa.Integer(), nullable=True),
    sa.Column('armazem_destino_id', sa.Integer(), nullable=True),
    sa.Column('pedido_compra_id', sa.Integer(), nullable=True),
    sa.CheckConstraint("(tipo = 'entrada' AND armazem_destino_id IS NOT NULL AND armazem_origem_id IS NULL AND pedido_compra_id IS NOT NULL) OR (tipo = 'saida' AND armazem_origem_id IS NOT NULL AND armazem_destino_id IS NULL) OR (tipo = 'transferencia' AND armazem_origem_id IS NOT NULL AND armazem_destino_id IS NOT NULL AND armazem_origem_id <> armazem_destino_id)", name=op.f('ck_movimentacoes_armazens_conforme_tipo')),
    sa.CheckConstraint("tipo IN ('entrada', 'saida', 'transferencia')", name=op.f('ck_movimentacoes_tipo_valido')),
    sa.CheckConstraint('quantidade > 0', name=op.f('ck_movimentacoes_quantidade_positiva')),
    sa.ForeignKeyConstraint(['armazem_destino_id'], ['armazens.id'], name=op.f('fk_movimentacoes_armazem_destino_id_armazens')),
    sa.ForeignKeyConstraint(['armazem_origem_id'], ['armazens.id'], name=op.f('fk_movimentacoes_armazem_origem_id_armazens')),
    sa.ForeignKeyConstraint(['pedido_compra_id'], ['pedidos_compra.id'], name=op.f('fk_movimentacoes_pedido_compra_id_pedidos_compra')),
    sa.ForeignKeyConstraint(['produto_id'], ['produtos.id'], name=op.f('fk_movimentacoes_produto_id_produtos')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_movimentacoes'))
    )
    op.create_table('produto_fornecedor',
    sa.Column('produto_id', sa.Integer(), nullable=False),
    sa.Column('fornecedor_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['fornecedor_id'], ['fornecedores.id'], name=op.f('fk_produto_fornecedor_fornecedor_id_fornecedores'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['produto_id'], ['produtos.id'], name=op.f('fk_produto_fornecedor_produto_id_produtos'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('produto_id', 'fornecedor_id', name=op.f('pk_produto_fornecedor'))
    )


def downgrade() -> None:

    op.drop_table('produto_fornecedor')
    op.drop_table('movimentacoes')
    op.drop_table('itens_pedido_compra')
    op.drop_table('estoque_armazem')
    op.drop_table('caracteristicas_produto')
    op.drop_table('produtos')
    op.drop_table('pedidos_compra')
    op.drop_table('fornecedores')
    op.drop_table('categorias')
    op.drop_table('armazens')