from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Datetime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PedidoCompra(Base):
    __tablename__ = "pedidos_compra"
    __table_args__ = (
        CheckConstraint(
            "status IN ('aberto', 'parcial', 'recebido', 'cancelado')", name="status_valido"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    fornecedor_id: Mapped[int] = mapped_column(ForeignKey("fornecedores.id"))
    data_pedido: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    status: Mapped[str] = mapped_column(String(20), default="aberto")
    observacao: Mapped[str | None] = mapped_column(String(255))

    fornecedor: Mapped["Fornecedor"] = relationship(back_populates="pedidos")
    itens: Mapped[list["ItemPedidoCompra"]] = relationship(
        back_populates="pedido", cascade="all, delete-orphan"
    )
    movimentacoes: Mapped[list["Movimentacao"]] = relationship(back_populates="pedido")

    @property
    def valor_total(self) -> Decimal:
        return sum((i.quantidade_pedida * i.preco_unitario for i in self.itens), Decimal("0"))


class ItemPedidoCompra(Base):
    __tablename__ = "itens_pedido_compra"
    __table_args__ = (
        UniqueConstraint("pedido_id", "produto_id", name="produto_unico_no_pedido"),
        CheckConstraint("quantidade_pedida > 0", name="pedida_positiva"),
        CheckConstraint(
            "quantidade_recebida >= 0 AND quantidade_recebida <= quantidade_pedida", name="recebida_valida",
        ),
        CheckConstraint("preco_unitario >= 0", name="preco_nao_negativo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    pedido_id: Mapped[int] = mapped_column(ForeignKey("pedidos_compra.id"))
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"))
    quantidade_pedida: Mapped[int] = mapped_column(Integer)
    quantidade_recebida: Mapped[int] = mapped_column(Integer, default=0)
    preco_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    pedido: Mapped["PedidoCompra"] = relationship(back_populates="itens")
    produto: Mapped["Produto"] = relationship(back_populates="itens_pedido")


    @property
    def quantidade_pendente(self) -> int:
        return self.quantidade_pedida - self.quantidade_recebida