from sqlalchemy import CheckConstraint, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EstoqueArmazem(Base):
    __tablename__ = "estoque_armazem"
    __table_args__ = (CheckConstraint("quantidade >= 0", name="saldo_nao_negativo"),)

    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), primary_key=True)
    armazem_id: Mapped[int] = mapped_column(ForeignKey("armazens.id"), primary_key=True)
    quantidade: Mapped[int] = mapped_column(Integer, default=0)

    produto: Mapped["Produto"] = relationship(back_populates="estoques")
    armazem: Mapped["Armazem"] = relationship(back_populates="estoques")