import logging

from sqlalchemy import select

from app.crud.pedido_compra import carregar
from app.errors import ConflitoError, NaoEncontradoError, RequisicaoInvalidaError
from app.models import Fornecedor, ItemPedidoCompra, PedidoCompra, Produto
from app.schemas.pedido_compra import PedidoCreate
from app.services.transacao import transacao

logger = logging.getLogger("estoque")


def criar_pedido(db, dados: PedidoCreate) -> PedidoCompra:
    fornecedor = db.get(Fornecedor, dados.fornecedor_id)
    if fornecedor is None:
        raise NaoEncontradoError(f"Fornecedor {dados.fornecedor_id} não encontrado(a).")
    if not fornecedor.ativo:
        raise ConflitoError(f"O fornecedor '{fornecedor.nome}' está inativo.")

    ids = [item.produto_id for item in dados.itens]
    if len(ids) != len(set(ids)):
        raise RequisicaoInvalidaError("O mesmo produto aparece mais de uma vez no pedido.")

    produtos_do_fornecedor = {p.id for p in fornecedor.produtos}

    with transacao(db):
        pedido = PedidoCompra(fornecedor_id=fornecedor.id, observacao=dados.observacao)
        db.add(pedido)

        for item in dados.itens:
            produto = db.get(Produto, item.produto_id)
            if produto is None:
                raise NaoEncontradoError(f"Produto {item.produto_id} não encontrado(a).")
            if not produto.ativo:
                raise ConflitoError(f"O produto '{produto.nome}' está inativo.")
            if produto.id not in produtos_do_fornecedor:
                raise ConflitoError(
                    f"O fornecedor '{fornecedor.nome}' não fornece o produto '{produto.nome}'."
                )

            pedido.itens.append(
                ItemPedidoCompra(
                    produto_id=produto.id,
                    quantidade_pedida=item.quantidade,
                    preco_unitario=(
                        item.preco_unitario
                        if item.preco_unitario is not None
                        else produto.preco_unitario
                    ),
                )
            )

    logger.info("PEDIDO criado id=%s fornecedor=%s itens=%s", pedido.id, fornecedor.id, len(ids))
    return carregar(db, pedido.id)


def cancelar_pedido(db, pedido_id: int) -> PedidoCompra:
    pedido = carregar(db, pedido_id)

    if pedido.status != "aberto":
        raise ConflitoError(
            f"Só é possível cancelar pedidos com status 'aberto' (status atual: '{pedido.status}')."
        )

    pedido.status = "cancelado"
    db.commit()
    logger.info("PEDIDO cancelado id=%s", pedido_id)
    return carregar(db, pedido_id)


def remover_pedido(db, pedido_id: int) -> None:
    pedido = carregar(db, pedido_id)

    if pedido.status in ("parcial", "recebido"):
        raise ConflitoError(
            "O pedido já teve mercadorias recebidas e não pode ser excluído."
        )

    db.delete(pedido)
    db.commit()
    logger.info("PEDIDO removido id=%s", pedido_id)