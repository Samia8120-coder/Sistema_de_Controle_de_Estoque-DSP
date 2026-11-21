from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.crud import categoria as crud
from app.database import get_db
from app.schemas.categoria import CategoriaCreate, CategoriaOut, CategoriaUpdate
from app.schemas.comum import Pagina, ParametrosPagina, montar_pagina
from app.schemas.produto import ProdutoOut

router = APIRouter(prefix="/categorias", tags=["Categorias"])


@router.post("", response_model=CategoriaOut, status_code=status.HTTP_201_CREATED)
def criar_categoria(dados: CategoriaCreate, db: Session = Depends(get_db)):
    return crud.criar(db, dados)


@router.get("", response_model=Pagina[CategoriaOut])
def listar_categorias(
    nome: str | None = None,
    pagina: ParametrosPagina = Depends(),
    db: Session = Depends(get_db),
):
    itens, total = crud.listar(db, pagina, nome)
    return montar_pagina(itens, total, pagina.offset, pagina.limit)


@router.get("/{categoria_id}", response_model=CategoriaOut)
def obter_categoria(categoria_id: int, db: Session = Depends(get_db)):
    return crud.obter(db, categoria_id)


@router.patch("/{categoria_id}", response_model=CategoriaOut)
def atualizar_categoria(categoria_id: int, dados: CategoriaUpdate, db: Session = Depends(get_db)):
    return crud.atualizar(db, categoria_id, dados)


@router.delete("/{categoria_id}")
def remover_categoria(categoria_id: int, db: Session = Depends(get_db)):
    crud.remover(db, categoria_id)
    return {"mensagem": "Categoria removida com sucesso."}


@router.get("/{categoria_id}/produtos", response_model=Pagina[ProdutoOut])
def produtos_da_categoria(
    categoria_id: int,
    pagina: ParametrosPagina = Depends(),
    db: Session = Depends(get_db),
):
    itens, total = crud.produtos_da_categoria(db, categoria_id, pagina)
    return montar_pagina(itens, total, pagina.offset, pagina.limit)