from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.crud import fornecedor as crud
from app.database import get_db
from app.schemas.comum import Pagina, ParametrosPagina, montar_pagina
from app.schemas.fornecedor import FornecedorCreate, FornecedorOut, FornecedorUpdate
from app.schemas.pedido_compra import PedidoOut
from app.schemas.produto import ProdutoOut

router = APIRouter(prefix="/fornecedores", tags=["Fornecedores"])


@router.post("", response_model=FornecedorOut, status_code=status.HTTP_201_CREATED)
def criar_fornecedor(dados: FornecedorCreate, db: Session = Depends(get_db)):
    return crud.criar(db, dados)


@router.get("", response_model=Pagina[FornecedorOut])
def listar_fornecedores(
    nome: str | None = None,
    ativo: bool | None = None,
    pagina: ParametrosPagina = Depends(),
    db: Session = Depends(get_db),
):
    itens, total = crud.listar(db, pagina, nome, ativo)
    return montar_pagina(itens, total, pagina.offset, pagina.limit)


@router.get("/{fornecedor_id}", response_model=FornecedorOut)
def obter_fornecedor(fornecedor_id: int, db: Session = Depends(get_db)):
    return crud.obter(db, fornecedor_id)


@router.patch("/{fornecedor_id}", response_model=FornecedorOut)
def atualizar_fornecedor(fornecedor_id: int, dados: FornecedorUpdate, db: Session = Depends(get_db)):
    return crud.atualizar(db, fornecedor_id, dados)


@router.delete("/{fornecedor_id}")
def remover_fornecedor(fornecedor_id: int, db: Session = Depends(get_db)):
    crud.remover(db, fornecedor_id)
    return {"mensagem": "Fornecedor removido com sucesso."}


@router.get("/{fornecedor_id}/produtos", response_model=Pagina[ProdutoOut])
def produtos_do_fornecedor(
    fornecedor_id: int,
    pagina: ParametrosPagina = Depends(),
    db: Session = Depends(get_db),
):
    itens, total = crud.produtos_do_fornecedor(db, fornecedor_id, pagina)
    return montar_pagina(itens, total, pagina.offset, pagina.limit)


@router.get("/{fornecedor_id}/pedidos", response_model=Pagina[PedidoOut])
def pedidos_do_fornecedor(
    fornecedor_id: int,
    pagina: ParametrosPagina = Depends(),
    db: Session = Depends(get_db),
):
    itens, total = crud.pedidos_do_fornecedor(db, fornecedor_id, pagina)
    return montar_pagina(itens, total, pagina.offset, pagina.limit)