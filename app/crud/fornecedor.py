import re

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload, selectinload

from app.crud.base import obter_ou_404, paginar
from app.crud.produto import OPCOES_PRODUTO
from app.errors import ConflitoError, RequisicaoInvalidaError
from app.models import Fornecedor, ItemPedidoCompra, PedidoCompra, Produto
from app.schemas.fornecedor import FornecedorCreate, FornecedorUpdate


def normalizar_cnpj(cnpj: str) -> str:
    digitos = re.sub(r"\D", "", cnpj)
    if len(digitos) != 14:
        raise RequisicaoInvalidaError("O CNPJ deve ter 14 dígitos.")
    return f"{digitos[:2]}.{digitos[2:5]}.{digitos[5:8]}/{digitos[8:12]}-{digitos[12:]}"


def criar(db, dados: FornecedorCreate) -> Fornecedor:
    cnpj = normalizar_cnpj(dados.cnpj)

    if db.scalar(select(Fornecedor.id).where(Fornecedor.cnpj == cnpj)):
        raise ConflitoError(f"Já existe um fornecedor com o CNPJ {cnpj}.")

    campos = dados.model_dump()
    campos["cnpj"] = cnpj
    fornecedor = Fornecedor(**campos)
    db.add(fornecedor)
    db.commit()
    db.refresh(fornecedor)
    return fornecedor


def listar(db, pagina, nome: str | None = None, ativo: bool | None = None):
    stmt = select(Fornecedor)
    if nome:
        stmt = stmt.where(Fornecedor.nome.ilike(f"%{nome}%"))
    if ativo is not None:
        stmt = stmt.where(Fornecedor.ativo == ativo)
    return paginar(db, stmt, pagina.offset, pagina.limit, order_by=(Fornecedor.nome,))


def obter(db, fornecedor_id: int) -> Fornecedor:
    return obter_ou_404(db, Fornecedor, fornecedor_id, "Fornecedor")


def atualizar(db, fornecedor_id: int, dados: FornecedorUpdate) -> Fornecedor:
    fornecedor = obter(db, fornecedor_id)
    campos = dados.model_dump(exclude_unset=True, exclude_none=True)

    for campo, valor in campos.items():
        setattr(fornecedor, campo, valor)

    db.commit()
    db.refresh(fornecedor)
    return fornecedor


def remover(db, fornecedor_id: int) -> None:
    fornecedor = obter(db, fornecedor_id)

    pedidos = db.scalar(
        select(func.count()).select_from(PedidoCompra).where(PedidoCompra.fornecedor_id == fornecedor_id)
    )
    if pedidos:
        raise ConflitoError(
            f"O fornecedor possui {pedidos} pedido(s) de compra. "
            "Em vez de excluir, desative-o (ativo=false)."
        )

    db.delete(fornecedor)
    db.commit()


def produtos_do_fornecedor(db, fornecedor_id: int, pagina):
    obter(db, fornecedor_id)
    stmt = select(Produto).join(Produto.fornecedores).where(Fornecedor.id == fornecedor_id)
    return paginar(
        db, stmt, pagina.offset, pagina.limit,
        order_by=(Produto.nome,), options=OPCOES_PRODUTO,
    )


def pedidos_do_fornecedor(db, fornecedor_id: int, pagina):
    obter(db, fornecedor_id)
    stmt = select(PedidoCompra).where(PedidoCompra.fornecedor_id == fornecedor_id)
    opcoes = (
        joinedload(PedidoCompra.fornecedor),
        selectinload(PedidoCompra.itens).joinedload(ItemPedidoCompra.produto),
    )
    return paginar(
        db, stmt, pagina.offset, pagina.limit,
        order_by=(PedidoCompra.data_pedido.desc(),), options=opcoes,
    )