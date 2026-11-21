from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

produto_fornecedor = Table(
    "produto_fornecedor",
    Base.metadata,
    Column("produto_id", ForeignKey("produtos.id", ondelete="CASCADE"), primary_key=True),
    Column("fornecedor_id", ForeignKey("fornecedores.id", ondelete="CASCADE"), primary_key=True),
)


class Produto(Base):
    __tablename__ = "produtos"
    __table_args__ = (
        CheckConstraint("preco_unitario >= 0", name="preco_nao_negativo"),
        CheckConstraint("estoque_minimo >= 0", name="minimo_nao_negativo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(30), unique=True)
    nome: Mapped[str] = mapped_column(String(150))
    descricao: Mapped[str | None] = mapped_column(String(255))
    preco_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    estoque_minimo: Mapped[int] = mapped_column(Integer, default=0)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categorias.id"))

    categoria: Mapped["Categoria"] = relationship(back_populates="produtos")
    caracteristica: Mapped["CaracteristicaProduto | None"] = relationship(
        back_populates="produto", uselist=False, cascade="all, delete-orphan"
    )
    fornecedores: Mapped[list["Fornecedor"]] = relationship(
        secondary=produto_fornecedor, back_populates="produtos"
    )
    estoques: Mapped[list["EstoqueArmazem"]] = relationship(
        back_populates="produto", cascade="all, delete-orphan"
    )
    movimentacoes: Mapped[list["Movimentacao"]] = relationship(back_populates="produto")
    itens_pedido: Mapped[list["ItemPedidoCompra"]] = relationship(back_populates="produto")

    @property
    def estoque_total(self) -> int:
        return sum(e.quantidade for e in self.estoques)


class CaracteristicaProduto(Base):
    __tablename__ = "caracteristicas_produto"
    __table_args__ = (
        CheckConstraint("peso_kg >= 0", name="peso_nao_negativo"),
        CheckConstraint(
            "altura_cm >= 0 AND largura_cm >= 0 AND profundidade_cm >= 0",
            name="dimensoes_nao_negativas",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), unique=True)
    peso_kg: Mapped[Decimal] = mapped_column(Numeric(8, 3), default=0)
    altura_cm: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0)
    largura_cm: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0)
    profundidade_cm: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0)
    unidade_medida: Mapped[str] = mapped_column(String(10), default="UN")
    condicao_armazenamento: Mapped[str] = mapped_column(String(40), default="seco")
    perecivel: Mapped[bool] = mapped_column(Boolean, default=False)

    produto: Mapped["Produto"] = relationship(back_populates="caracteristica")