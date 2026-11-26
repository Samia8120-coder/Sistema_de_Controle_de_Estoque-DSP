import logging
from datetime import datetime

from sqlalchemy import select

from app.crud.pedido_compra import carregar as carregar_pedido
from app.errors import ConflitoError, NaoEncontradoError, RequisicaoInvalidaError
from app.models import Armazem, EstoqueArmazem, Movimentacao, PedidoCompra, Produto
from app.schemas.movimentacao import SaidaIn, TransferenciaIn
from app.schemas.pedido_compra import RecebimentoIn
from app.services.transacao import transacao

logger = logging.getLogger("estoque")


def _produto_ativo(db, produto_id: int) -> Produto:
    produto = db.get(Produto, produto_id)
    if produto is None:
        raise NaoEncontradoError(f"Produto {produto_id} não encontrado(a).")
    if not produto.ativo:
        raise ConflitoError(f"O produto '{produto.nome}' está inativo e não pode ser movimentado.")
    return produto


def _armazem_ativo(db, armazem_id: int) -> Armazem:
    armazem = db.get(Armazem, armazem_id)
    if armazem is None:
        raise NaoEncontradoError(f"Armazém {armazem_id} não encontrado(a).")
    if not armazem.ativo:
        raise ConflitoError(f"O armazém '{armazem.nome}' está inativo e não pode receber operações.")
    return armazem


def _saldo_travado(db, produto_id: int, armazem_id: int) -> EstoqueArmazem | None:
    return db.scalar(
        select(EstoqueArmazem)
        .where(
            EstoqueArmazem.produto_id == produto_id,
            EstoqueArmazem.armazem_id == armazem_id,
        )
        .with_for_update()
    )


def _saldo_ou_novo(db, produto_id: int, armazem_id: int) -> EstoqueArmazem:
    saldo = _saldo_travado(db, produto_id, armazem_id)
    if saldo is None:
        saldo = EstoqueArmazem(produto_id=produto_id, armazem_id=armazem_id, quantidade=0)
        db.add(saldo)
    return saldo


def registrar_saida(db, dados: SaidaIn, data_hora: datetime | None = None) -> Movimentacao:
    produto = _produto_ativo(db, dados.produto_id)
    armazem = _armazem_ativo(db, dados.armazem_id)

    with transacao(db):
        saldo = _saldo_travado(db, produto.id, armazem.id)
        disponivel = saldo.quantidade if saldo else 0

        if disponivel < dados.quantidade:
            raise ConflitoError(
                f"Saldo insuficiente de '{produto.nome}' no armazém '{armazem.nome}': "
                f"disponível {disponivel}, solicitado {dados.quantidade}."
            )

        saldo.quantidade -= dados.quantidade

        movimentacao = Movimentacao(
            tipo="saida",
            produto_id=produto.id,
            quantidade=dados.quantidade,
            motivo=dados.motivo,
            observacao=dados.observacao,
            armazem_origem_id=armazem.id,
            data_hora=data_hora or datetime.now(),
        )
        db.add(movimentacao)

    logger.info("SAIDA produto=%s armazem=%s qtd=%s", produto.id, armazem.id, dados.quantidade)
    db.refresh(movimentacao)
    return movimentacao


def registrar_transferencia(
    db, dados: TransferenciaIn, data_hora: datetime | None = None
) -> Movimentacao:
    if dados.armazem_origem_id == dados.armazem_destino_id:
        raise RequisicaoInvalidaError("O armazém de origem e o de destino devem ser diferentes.")

    produto = _produto_ativo(db, dados.produto_id)
    origem = _armazem_ativo(db, dados.armazem_origem_id)
    destino = _armazem_ativo(db, dados.armazem_destino_id)

    with transacao(db):
        saldos = {}
        for armazem_id in sorted((origem.id, destino.id)):
            saldos[armazem_id] = _saldo_travado(db, produto.id, armazem_id)

        saldo_origem = saldos[origem.id]
        disponivel = saldo_origem.quantidade if saldo_origem else 0

        if disponivel < dados.quantidade:
            raise ConflitoError(
                f"Saldo insuficiente de '{produto.nome}' no armazém '{origem.nome}': "
                f"disponível {disponivel}, solicitado {dados.quantidade}."
            )

        saldo_destino = saldos[destino.id]
        if saldo_destino is None:
            saldo_destino = EstoqueArmazem(produto_id=produto.id, armazem_id=destino.id, quantidade=0)
            db.add(saldo_destino)

        saldo_origem.quantidade -= dados.quantidade
        saldo_destino.quantidade += dados.quantidade

        movimentacao = Movimentacao(
            tipo="transferencia",
            produto_id=produto.id,
            quantidade=dados.quantidade,
            motivo=dados.motivo,
            observacao=dados.observacao,
            armazem_origem_id=origem.id,
            armazem_destino_id=destino.id,
            data_hora=data_hora or datetime.now(),
        )
        db.add(movimentacao)

    logger.info(
        "TRANSFERENCIA produto=%s de=%s para=%s qtd=%s",
        produto.id, origem.id, destino.id, dados.quantidade,
    )
    db.refresh(movimentacao)
    return movimentacao


def receber_pedido(
    db, pedido_id: int, dados: RecebimentoIn, data_hora: datetime | None = None
) -> PedidoCompra:
    pedido = db.scalar(
        select(PedidoCompra).where(PedidoCompra.id == pedido_id).with_for_update()
    )
    if pedido is None:
        raise NaoEncontradoError(f"Pedido de compra {pedido_id} não encontrado(a).")

    if pedido.status == "cancelado":
        raise ConflitoError("O pedido está cancelado e não pode receber mercadorias.")
    if pedido.status == "recebido":
        raise ConflitoError("O pedido já foi totalmente recebido.")

    armazem = _armazem_ativo(db, dados.armazem_id)

    ids_recebidos = [item.produto_id for item in dados.itens]
    if len(ids_recebidos) != len(set(ids_recebidos)):
        raise RequisicaoInvalidaError("O mesmo produto aparece mais de uma vez no recebimento.")

    itens_do_pedido = {item.produto_id: item for item in pedido.itens}

    with transacao(db):
        for recebido in dados.itens:
            item = itens_do_pedido.get(recebido.produto_id)
            if item is None:
                raise ConflitoError(
                    f"O produto {recebido.produto_id} não faz parte do pedido {pedido_id}."
                )

            produto = _produto_ativo(db, recebido.produto_id)

            if recebido.quantidade > item.quantidade_pendente:
                raise ConflitoError(
                    f"Quantidade acima do pendente para '{produto.nome}': "
                    f"pendente {item.quantidade_pendente}, informado {recebido.quantidade}."
                )

            item.quantidade_recebida += recebido.quantidade

            saldo = _saldo_ou_novo(db, produto.id, armazem.id)
            saldo.quantidade += recebido.quantidade

            db.add(
                Movimentacao(
                    tipo="entrada",
                    produto_id=produto.id,
                    quantidade=recebido.quantidade,
                    motivo=f"recebimento do pedido de compra {pedido.id}",
                    armazem_destino_id=armazem.id,
                    pedido_compra_id=pedido.id,
                    data_hora=data_hora or datetime.now(),
                )
            )

        todos_completos = all(i.quantidade_recebida == i.quantidade_pedida for i in pedido.itens)
        pedido.status = "recebido" if todos_completos else "parcial"

    logger.info("RECEBIMENTO pedido=%s armazem=%s status=%s", pedido.id, armazem.id, pedido.status)
    db.expire_all()
    return carregar_pedido(db, pedido_id)