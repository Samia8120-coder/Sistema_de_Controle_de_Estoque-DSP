from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.produto import produto_fornecedor


class Fornecedor(Base):
    __tablename__ = "fornecedores"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    cnpj: Mapped[str] = mapped_column(String(18), unique=True)
    email: Mapped[str | None] = mapped_column(String(120))
    telefone: Mapped[str | None] = mapped_column(String(20))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    produtos: Mapped[list["Produto"]] = relationship(
        secondary=produto_fornecedor, back_populates="fornecedores"
    )
    pedidos: Mapped[list["PedidoCompra"]] = relationship(back_populates="fornecedor")