from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Armazem(Base):
    __tablename__ = "armazens"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(80), unique=True)
    cidade: Mapped[str] = mapped_column(String(80))
    endereco: Mapped[str | None] = mapped_column(String(150))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    estoques: Mapped[list["EstoqueArmazem"]] = relationship(back_populates="armazem")