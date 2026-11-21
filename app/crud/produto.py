from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload, selectinload

from app.crud.base import obter_ou_404, paginar
from app.errors import ConflitoError, NaoEncontradoError
from app.models import (
    CaracteristicaProduto,
    Categoria,
    Fornecedor,
    ItemPedidoCompra,
    Movimentacao,
    Produto,
)
from app.schemas.produto import ProdutoCreate, ProdutoUpdate

OPCOES_PRODUTO = (
    joinedload(Produto.categoria),
    joinedload(Produto.caracteristica),
    selectinload(Produto.fornecedores),
    selectinload(Produto.estoques),
)


def _buscar_fornecedores(db, ids: list[int]) -> list[Fornecedor]:
    ids_unicos = sorted(set(ids))
    if not ids_unicos:
        return []

    encontrados = db.scalars(select(Fornecedor).where(Fornecedor.id.in_(ids_unicos))).all()
    faltando = set(ids_unicos) - {f.id for f in encontrados}
    if faltando:
        raise NaoEncontradoError(f"Fornecedor(es) inexistente(s): {sorted(faltando)}.")
    return list(encontrados)


def _carregar(db, produto_id: int) -> Produto:
    produto = db.scalar(
        select(Produto).where(Produto.id == produto_id).options(*OPCOES_PRODUTO)
    )
    if produto is None:
        raise NaoEncontradoError(f"Produto {produto_id} não encontrado(a).")
    return produto


def criar(db, dados: ProdutoCreate) -> Produto:
    if db.scalar(select(Produto.id).where(func.lower(Produto.codigo) == dados.codigo.lower())):
        raise ConflitoError(f"Já existe um produto com o código '{dados.codigo}'.")

    obter_ou_404(db, Categoria, dados.categoria_id, "Categoria")
    fornecedores = _buscar_fornecedores(db, dados.fornecedores_ids)

    campos = dados.model_dump(exclude={"caracteristica", "fornecedores_ids"})
    produto = Produto(**campos)
    produto.fornecedores = fornecedores

    if dados.caracteristica is not None:
        produto.caracteristica = CaracteristicaProduto(**dados.caracteristica.model_dump())

    db.add(produto)
    db.commit()
    return _carregar(db, produto.id)


def listar(
    db,
    pagina,
    nome: str | None = None,
    categoria_id: int | None = None,
    fornecedor_id: int | None = None,
    ativo: bool | None = None,
    preco_min: Decimal | None = None,
    preco_max: Decimal | None = None,
):
    stmt = select(Produto)

    if fornecedor_id is not None:
        stmt = stmt.join(Produto.fornecedores).where(Fornecedor.id == fornecedor_id)
    if nome:
        stmt = stmt.where(Produto.nome.ilike(f"%{nome}%"))
    if categoria_id is not None:
        stmt = stmt.where(Produto.categoria_id == categoria_id)
    if ativo is not None:
        stmt = stmt.where(Produto.ativo == ativo)
    if preco_min is not None:
        stmt = stmt.where(Produto.preco_unitario >= preco_min)
    if preco_max is not None:
        stmt = stmt.where(Produto.preco_unitario <= preco_max)

    return paginar(
        db, stmt, pagina.offset, pagina.limit,
        order_by=(Produto.nome,), options=OPCOES_PRODUTO,
    )


def obter(db, produto_id: int) -> Produto:
    return _carregar(db, produto_id)


def atualizar(db, produto_id: int, dados: ProdutoUpdate) -> Produto:
    produto = _carregar(db, produto_id)
    campos = dados.model_dump(
        exclude_unset=True, exclude_none=True, exclude={"caracteristica", "fornecedores_ids"}
    )

    if "categoria_id" in campos:
        obter_ou_404(db, Categoria, campos["categoria_id"], "Categoria")

    if campos.get("ativo") is False and produto.ativo and produto.estoque_total > 0:
        raise ConflitoError(
            "O produto ainda possui saldo em estoque e não pode ser desativado."
        )

    for campo, valor in campos.items():
        setattr(produto, campo, valor)

    if dados.fornecedores_ids is not None:
        produto.fornecedores = _buscar_fornecedores(db, dados.fornecedores_ids)

    if dados.caracteristica is not None:
        novos = dados.caracteristica.model_dump(exclude_unset=True, exclude_none=True)
        if produto.caracteristica is None:
            produto.caracteristica = CaracteristicaProduto(**novos)
        else:
            for campo, valor in novos.items():
                setattr(produto.caracteristica, campo, valor)

    db.commit()
    db.expire_all()
    return _carregar(db, produto_id)


def remover(db, produto_id: int) -> None:
    produto = _carregar(db, produto_id)

    if produto.estoque_total > 0:
        raise ConflitoError("O produto possui saldo em estoque e não pode ser excluído.")

    movimentacoes = db.scalar(
        select(func.count()).select_from(Movimentacao).where(Movimentacao.produto_id == produto_id)
    )
    itens = db.scalar(
        select(func.count()).select_from(ItemPedidoCompra).where(ItemPedidoCompra.produto_id == produto_id)
    )
    if movimentacoes or itens:
        raise ConflitoError(
            "O produto possui histórico de movimentações ou pedidos. "
            "Em vez de excluir, desative-o (ativo=false)."
        )

    db.delete(produto)
    db.commit()


def movimentacoes_do_produto(db, produto_id: int, pagina):
    from app.crud.movimentacao import OPCOES_MOVIMENTACAO

    _carregar(db, produto_id)
    stmt = select(Movimentacao).where(Movimentacao.produto_id == produto_id)
    return paginar(
        db, stmt, pagina.offset, pagina.limit,
        order_by=(Movimentacao.data_hora.desc(), Movimentacao.id.desc()),
        options=OPCOES_MOVIMENTACAO,
    )