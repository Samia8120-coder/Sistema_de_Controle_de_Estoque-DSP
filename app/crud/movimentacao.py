from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import joinedload

from app.crud.base import obter_ou_404, paginar
from app.models import Movimentacao

OPCOES_MOVIMENTACAO = (
    joinedload(Movimentacao.produto),
    joinedload(Movimentacao.armazem_origem),
    joinedload(Movimentacao.armazem_destino),
)


def listar(
    db,
    pagina,
    tipo: str | None = None,
    produto_id: int | None = None,
    armazem_id: int | None = None,
    data_inicio: datetime | None = None,
    data_fim: datetime | None = None,
):
    stmt = select(Movimentacao)

    if tipo:
        stmt = stmt.where(Movimentacao.tipo == tipo)
    if produto_id is not None:
        stmt = stmt.where(Movimentacao.produto_id == produto_id)
    if armazem_id is not None:
        stmt = stmt.where(
            or_(
                Movimentacao.armazem_origem_id == armazem_id,
                Movimentacao.armazem_destino_id == armazem_id,
            )
        )
    if data_inicio is not None:
        stmt = stmt.where(Movimentacao.data_hora >= data_inicio)
    if data_fim is not None:
        stmt = stmt.where(Movimentacao.data_hora <= data_fim)

    return paginar(
        db, stmt, pagina.offset, pagina.limit,
        order_by=(Movimentacao.data_hora.desc(), Movimentacao.id.desc()),
        options=OPCOES_MOVIMENTACAO,
    )


def obter(db, movimentacao_id: int) -> Movimentacao:
    obter_ou_404(db, Movimentacao, movimentacao_id, "Movimentação")
    return db.scalar(
        select(Movimentacao)
        .where(Movimentacao.id == movimentacao_id)
        .options(*OPCOES_MOVIMENTACAO)
    )