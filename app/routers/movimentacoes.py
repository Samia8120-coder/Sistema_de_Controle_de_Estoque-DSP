from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.crud import movimentacao as crud
from app.database import get_db
from app.schemas.comum import Pagina, ParametrosPagina, montar_pagina
from app.schemas.movimentacao import MovimentacaoOut, SaidaIn, TransferenciaIn
from app.services import movimentacao_service

router = APIRouter(prefix="/movimentacoes", tags=["Movimentações"])


@router.post("/saida", response_model=MovimentacaoOut, status_code=status.HTTP_201_CREATED)
def registrar_saida(dados: SaidaIn, db: Session = Depends(get_db)):
    movimentacao = movimentacao_service.registrar_saida(db, dados)
    return crud.obter(db, movimentacao.id)


@router.post("/transferencia", response_model=MovimentacaoOut, status_code=status.HTTP_201_CREATED)
def registrar_transferencia(dados: TransferenciaIn, db: Session = Depends(get_db)):
    movimentacao = movimentacao_service.registrar_transferencia(db, dados)
    return crud.obter(db, movimentacao.id)


@router.get("", response_model=Pagina[MovimentacaoOut])
def listar_movimentacoes(
    tipo: Literal["entrada", "saida", "transferencia"] | None = None,
    produto_id: int | None = None,
    armazem_id: int | None = None,
    data_inicio: datetime | None = None,
    data_fim: datetime | None = None,
    pagina: ParametrosPagina = Depends(),
    db: Session = Depends(get_db),
):
    itens, total = crud.listar(db, pagina, tipo, produto_id, armazem_id, data_inicio, data_fim)
    return montar_pagina(itens, total, pagina.offset, pagina.limit)


@router.get("/{movimentacao_id}", response_model=MovimentacaoOut)
def obter_movimentacao(movimentacao_id: int, db: Session = Depends(get_db)):
    return crud.obter(db, movimentacao_id)