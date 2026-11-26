from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectload

from app.crud.base import paginar
from app.errors import NaoEncontradoError
from app.models import ItemPedidoCompra, PedidoCompra

OPCOES_PEDIDO = (
    joinedload(PedidoCompra.fornecedor),
    selectload(PedidoCompra.itens).joinedload(ItemPedidoCompra.produto),
)

def carregar(db, pedido_id: int) -> PedidoCompra:
    pedido = db.scalar(
        select(PedidoCompra).where(PedidoCompra.id == pedido_id).options(*OPCOES_PEDIDO)
    )
    if pedido is None:
        raise NaoEncontradoError(f"Pedido de compra {pedido_id} não encontrado(a).")
    return pedido

def listar(
    db,
    pagina,
    status: str | None = None,
    fornecedor_id: int | None = None,
    data_inicio: datetime | None = None,
    data_fim: datetime | None = None,
):
    stmt = select(PedidoCompra)

    if status:
        stmt = stmt.where(PedidoCompra.status == status)
    if fornecedor_id is not None:
        stmt = stmt.where(PedidoCompra.fornecedor_id == fornecedor_id)
    if data_inicio is not None:
        stmt = stmt.where(PedidoCompra.data_pedido >= data_inicio)
    if data_fim is not None:
        stmt = stmt.where(PedidoCompra.data_pedido <= data_fim)

    return paginar(
        db, stmt, pagina.offset, pagina.limit,
        order_by=(PedidoCompra.data_pedido.desc(), PedidoCompra.id.desc()),
        options=OPCOES_PEDIDO,
    )