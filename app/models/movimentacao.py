from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class Movimentacao(Base):
    __tablename__ = "movimentacoes"
    __table_args__ = (
        CheckConstraint("tipo IN ('entrada', 'saida', 'transferencia')", name="tipo_valido"),
        CheckConstraint("quantidade > 0", name="quantidade_positiva"),
        CheckConstraint(
            "(tipo = 'entrada' AND armazem_destino_id IS NOT NULL) "
            "AND armazem_origem_id IS NULL AND pedido_compra_id IS NOT NULL) "
            "OR (tipo = 'saida' AND armazem_origem_id IS NOT NULL "
            "AND armazem_destino_id IS NULL) "
            "OR (tipo = 'transferencia' AND armazem_origem_id IS NOT NULL "
            "AND armazem_destino_id IS NOT NULL "
            "AND armazem_origem_id <> armazem_destino_id)", name="armazens_conforme_tipo",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[str] = mapped_column(String(20))
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"))
    quantidade: Mapped[int] = mapped_column(Integer)
    data_hora: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)
    motivo: Mapped[str] = mapped_column(String(120))
    observacao: Mapped[str | None] = mapped_column(String(255))
    armazem_origem_id: Mapped[int | None] = mapped_column(ForeignKey("armazens.id"))
    armazem_destino_id: Mapped[int | None] = mapped_column(ForeignKey("armazens.id"))
    pedido_compra_id: Mapped[int | None] = mapped_column(ForeignKey("pedidos_compra.id"))

    produto: Mapped["Produto"] = relationship(back_populates="movimentacoes")
    armazem_origem: Mapped["Armazem | None"] = relationship(foreign_keys=[armazem_origem_id])
    armazem_destino: Mapped["Armazem | None"] = relationship(foreign_keys=[armazem_destino_id])
    pedido: Mapped["PedidoCompra | None"] = relationship(back_populates="movimentacoes")