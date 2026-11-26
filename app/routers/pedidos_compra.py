from datetime import datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.crud import pedido_compra as crud
from app.database import get_db
from app.schemas.comum import Pagina, ParametrosPagina, montar_pagina
from app.schemas.pedido_compra import PedidoCreate, PedidoOut, RecebimentoIn
from app.services import movimentacao_service, pedido_service

router = APIRouter(prefix="/pedidos-compra", tags=["Pedidos de compra"])


@router.post("", response_model=PedidoOut, status_code=status.HTTP_201_CREATED)
def criar_pedido(dados: PedidoCreate, db: Session = Depends(get_db)):
    return pedido_service.criar_pedido(db, dados)


@router.get("", response_model=Pagina[PedidoOut])
def listar_pedidos(
    status: str | None = None,
    fornecedor_id: int | None = None,
    data_inicio: datetime | None = None,
    data_fim: datetime | None = None,
    pagina: ParametrosPagina = Depends(),
    db: Session = Depends(get_db),
):
    itens, total = crud.listar(db, pagina, status, fornecedor_id, data_inicio, data_fim)
    return montar_pagina(itens, total, pagina.offset, pagina.limit)


@router.get("/{pedido_id}", response_model=PedidoOut)
def obter_pedido(pedido_id: int, db: Session = Depends(get_db)):
    return crud.carregar(db, pedido_id)


@router.post("/{pedido_id}/receber", response_model=PedidoOut)
def receber_pedido(pedido_id: int, dados: RecebimentoIn, db: Session = Depends(get_db)):
    return movimentacao_service.receber_pedido(db, pedido_id, dados)


@router.post("/{pedido_id}/cancelar", response_model=PedidoOut)
def cancelar_pedido(pedido_id: int, db: Session = Depends(get_db)):
    return pedido_service.cancelar_pedido(db, pedido_id)


@router.delete("/{pedido_id}")
def remover_pedido(pedido_id: int, db: Session = Depends(get_db)):
    pedido_service.remover_pedido(db, pedido_id)
    return {"mensagem": "Pedido removido com sucesso."}