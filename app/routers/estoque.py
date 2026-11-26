from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.comum import Pagina, ParametrosPagina, montar_pagina
from app.schemas.estoque import EstoqueProdutoOut, EstoqueResumoOut
from app.services import consulta_service

router = APIRouter(prefix="/estoque", tags=["Estoque"])


@router.get("", response_model=Pagina[EstoqueResumoOut])
def listar_estoque(
    categoria_id: int | None = None,
    pagina: ParametrosPagina = Depends(),
    db: Session = Depends(get_db),
):
    itens, total = consulta_service.listar_estoque(db, pagina, categoria_id=categoria_id)
    return montar_pagina(itens, total, pagina.offset, pagina.limit)


@router.get("/abaixo-do-minimo", response_model=Pagina[EstoqueResumoOut])
def produtos_abaixo_do_minimo(
    categoria_id: int | None = None,
    pagina: ParametrosPagina = Depends(),
    db: Session = Depends(get_db),
):
    itens, total = consulta_service.listar_estoque(
        db, pagina, apenas_abaixo_do_minimo=True, categoria_id=categoria_id
    )
    return montar_pagina(itens, total, pagina.offset, pagina.limit)


@router.get("/produtos/{produto_id}", response_model=EstoqueProdutoOut)
def estoque_do_produto(produto_id: int, db: Session = Depends(get_db)):
    return consulta_service.estoque_do_produto(db, produto_id)