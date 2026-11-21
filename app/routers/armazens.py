from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.crud import armazem as crud
from app.database import get_db
from app.schemas.armazem import ArmazemCreate, ArmazemOut, ArmazemUpdate
from app.schemas.comum import Pagina, ParametrosPagina, montar_pagina
from app.schemas.estoque import SaldoProdutoNoArmazemOut

router = APIRouter(prefix="/armazens", tags=["Armazéns"])


@router.post("", response_model=ArmazemOut, status_code=status.HTTP_201_CREATED)
def criar_armazem(dados: ArmazemCreate, db: Session = Depends(get_db)):
    return crud.criar(db, dados)


@router.get("", response_model=Pagina[ArmazemOut])
def listar_armazens(
    nome: str | None = None,
    cidade: str | None = None,
    ativo: bool | None = None,
    pagina: ParametrosPagina = Depends(),
    db: Session = Depends(get_db),
):
    itens, total = crud.listar(db, pagina, nome, cidade, ativo)
    return montar_pagina(itens, total, pagina.offset, pagina.limit)


@router.get("/{armazem_id}", response_model=ArmazemOut)
def obter_armazem(armazem_id: int, db: Session = Depends(get_db)):
    return crud.obter(db, armazem_id)


@router.patch("/{armazem_id}", response_model=ArmazemOut)
def atualizar_armazem(armazem_id: int, dados: ArmazemUpdate, db: Session = Depends(get_db)):
    return crud.atualizar(db, armazem_id, dados)


@router.delete("/{armazem_id}")
def remover_armazem(armazem_id: int, db: Session = Depends(get_db)):
    crud.remover(db, armazem_id)
    return {"mensagem": "Armazém removido com sucesso."}


@router.get("/{armazem_id}/estoque", response_model=Pagina[SaldoProdutoNoArmazemOut])
def estoque_do_armazem(
    armazem_id: int,
    pagina: ParametrosPagina = Depends(),
    db: Session = Depends(get_db),
):
    linhas, total = crud.estoque_do_armazem(db, armazem_id, pagina)
    itens = [
        {"produto_id": l.produto_id, "codigo": l.codigo, "nome": l.nome, "quantidade": l.quantidade}
        for l in linhas
    ]
    return montar_pagina(itens, total, pagina.offset, pagina.limit)