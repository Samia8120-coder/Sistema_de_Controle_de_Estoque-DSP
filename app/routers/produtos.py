from decimal import Decimal

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.crud import produto as crud
from app.database import get_db
from app.schemas.comum import Pagina, ParametrosPagina, montar_pagina
from app.schemas.movimentacao import MovimentacaoOut
from app.schemas.produto import ProdutoCreate, ProdutoOut, ProdutoUpdate

router = APIRouter(prefix="/produtos", tags=["Produtos"])


@router.post("", response_model=ProdutoOut, status_code=status.HTTP_201_CREATED)
def criar_produto(dados: ProdutoCreate, db: Session = Depends(get_db)):
    return crud.criar(db, dados)


@router.get("", response_model=Pagina[ProdutoOut])
def listar_produtos(
    nome: str | None = None,
    categoria_id: int | None = None,
    fornecedor_id: int | None = None,
    ativo: bool | None = None,
    preco_min: Decimal | None = None,
    preco_max: Decimal | None = None,
    pagina: ParametrosPagina = Depends(),
    db: Session = Depends(get_db),
):
    itens, total = crud.listar(
        db, pagina, nome, categoria_id, fornecedor_id, ativo, preco_min, preco_max
    )
    return montar_pagina(itens, total, pagina.offset, pagina.limit)


@router.get("/{produto_id}", response_model=ProdutoOut)
def obter_produto(produto_id: int, db: Session = Depends(get_db)):
    return crud.obter(db, produto_id)


@router.patch("/{produto_id}", response_model=ProdutoOut)
def atualizar_produto(produto_id: int, dados: ProdutoUpdate, db: Session = Depends(get_db)):
    return crud.atualizar(db, produto_id, dados)


@router.delete("/{produto_id}")
def remover_produto(produto_id: int, db: Session = Depends(get_db)):
    crud.remover(db, produto_id)
    return {"mensagem": "Produto removido com sucesso."}


@router.get("/{produto_id}/movimentacoes", response_model=Pagina[MovimentacaoOut])
def movimentacoes_do_produto(
    produto_id: int,
    pagina: ParametrosPagina = Depends(),
    db: Session = Depends(get_db),
):
    itens, total = crud.movimentacoes_do_produto(db, produto_id, pagina)
    return montar_pagina(itens, total, pagina.offset, pagina.limit)