from sqlalchemy import func, select

from app.crud.base import obter_ou_404, paginar
from app.errors import ConflitoError
from app.models import Categoria, Produto
from app.schemas.categoria import CategoriaCreate, CategoriaUpdate
from app.crud.produto import OPCOES_PRODUTO


def _nome_em_uso(db, nome: str, ignorar_id: int | None = None) -> bool:
    stmt = select(Categoria.id).where(func.lower(Categoria.nome) == nome.lower())
    if ignorar_id is not None:
        stmt = stmt.where(Categoria.id != ignorar_id)
    return db.scalar(stmt) is not None


def criar(db, dados: CategoriaCreate) -> Categoria:
    if _nome_em_uso(db, dados.nome):
        raise ConflitoError(f"Já existe uma categoria chamada '{dados.nome}'.")

    categoria = Categoria(**dados.model_dump())
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


def listar(db, pagina, nome: str | None = None):
    stmt = select(Categoria)
    if nome:
        stmt = stmt.where(Categoria.nome.ilike(f"%{nome}%"))
    return paginar(db, stmt, pagina.offset, pagina.limit, order_by=(Categoria.nome,))


def obter(db, categoria_id: int) -> Categoria:
    return obter_ou_404(db, Categoria, categoria_id, "Categoria")


def atualizar(db, categoria_id: int, dados: CategoriaUpdate) -> Categoria:
    categoria = obter(db, categoria_id)
    campos = dados.model_dump(exclude_unset=True, exclude_none=True)

    if "nome" in campos and _nome_em_uso(db, campos["nome"], ignorar_id=categoria_id):
        raise ConflitoError(f"Já existe uma categoria chamada '{campos['nome']}'.")

    for campo, valor in campos.items():
        setattr(categoria, campo, valor)

    db.commit()
    db.refresh(categoria)
    return categoria


def remover(db, categoria_id: int) -> None:
    categoria = obter(db, categoria_id)

    quantidade = db.scalar(
        select(func.count()).select_from(Produto).where(Produto.categoria_id == categoria_id)
    )
    if quantidade:
        raise ConflitoError(
            f"A categoria possui {quantidade} produto(s) e não pode ser removida."
        )

    db.delete(categoria)
    db.commit()


def produtos_da_categoria(db, categoria_id: int, pagina):
    obter(db, categoria_id)
    stmt = select(Produto).where(Produto.categoria_id == categoria_id)
    return paginar(
        db, stmt, pagina.offset, pagina.limit,
        order_by=(Produto.nome,), options=OPCOES_PRODUTO,
    )