from datetime import datetime, timedelta

from sqlalchemy import case, func, select

from app.crud.base import obter_ou_404, paginar
from app.models import (
    Armazem,
    Categoria,
    EstoqueArmazem,
    Fornecedor,
    Movimentacao,
    PedidoCompra,
    Produto,
)


def _total_por_produto():
    return (
        select(
            EstoqueArmazem.produto_id.label("produto_id"),
            func.coalesce(func.sum(EstoqueArmazem.quantidade), 0).label("total"),
        )
        .group_by(EstoqueArmazem.produto_id)
        .subquery()
    )


def estoque_do_produto(db, produto_id: int) -> dict:
    produto = obter_ou_404(db, Produto, produto_id, "Produto")

    saldos = db.execute(
        select(Armazem.id, Armazem.nome, EstoqueArmazem.quantidade)
        .join(EstoqueArmazem, EstoqueArmazem.armazem_id == Armazem.id)
        .where(EstoqueArmazem.produto_id == produto_id)
        .order_by(Armazem.nome)
    ).all()

    total = sum(s.quantidade for s in saldos)
    return {
        "produto_id": produto.id,
        "codigo": produto.codigo,
        "nome": produto.nome,
        "estoque_minimo": produto.estoque_minimo,
        "estoque_total": total,
        "abaixo_do_minimo": total < produto.estoque_minimo,
        "saldos": [
            {"armazem_id": s.id, "armazem_nome": s.nome, "quantidade": s.quantidade}
            for s in saldos
        ],
    }


def listar_estoque(db, pagina, apenas_abaixo_do_minimo: bool = False, categoria_id: int | None = None):
    totais = _total_por_produto()
    total_col = func.coalesce(totais.c.total, 0)

    stmt = (
        select(
            Produto.id.label("produto_id"),
            Produto.codigo,
            Produto.nome,
            Produto.estoque_minimo,
            total_col.label("estoque_total"),
            (Produto.estoque_minimo - total_col).label("falta_para_minimo"),
        )
        .outerjoin(totais, totais.c.produto_id == Produto.id)
        .where(Produto.ativo.is_(True))
    )

    if categoria_id is not None:
        stmt = stmt.where(Produto.categoria_id == categoria_id)
    if apenas_abaixo_do_minimo:
        stmt = stmt.where(total_col < Produto.estoque_minimo)

    ordem = (
        ((Produto.estoque_minimo - total_col).desc(), Produto.nome)
        if apenas_abaixo_do_minimo
        else (Produto.nome,)
    )
    linhas, total = paginar(db, stmt, pagina.offset, pagina.limit, order_by=ordem, linhas=True)

    itens = [
        {
            "produto_id": l.produto_id,
            "codigo": l.codigo,
            "nome": l.nome,
            "estoque_minimo": l.estoque_minimo,
            "estoque_total": l.estoque_total,
            "falta_para_minimo": max(l.falta_para_minimo, 0),
        }
        for l in linhas
    ]
    return itens, total


def movimentacoes_no_periodo(
    db, inicio: datetime, fim: datetime, categoria_id: int | None = None, produto_id: int | None = None
) -> list[dict]:
    entradas = func.coalesce(
        func.sum(case((Movimentacao.tipo == "entrada", Movimentacao.quantidade), else_=0)), 0
    )
    saidas = func.coalesce(
        func.sum(case((Movimentacao.tipo == "saida", Movimentacao.quantidade), else_=0)), 0
    )
    transferido = func.coalesce(
        func.sum(case((Movimentacao.tipo == "transferencia", Movimentacao.quantidade), else_=0)), 0
    )

    stmt = (
        select(
            Produto.id,
            Produto.codigo,
            Produto.nome,
            entradas.label("entradas"),
            saidas.label("saidas"),
            transferido.label("transferido"),
        )
        .join(Movimentacao, Movimentacao.produto_id == Produto.id)
        .where(Movimentacao.data_hora >= inicio, Movimentacao.data_hora <= fim)
        .group_by(Produto.id, Produto.codigo, Produto.nome)
        .order_by(Produto.nome)
    )
    if categoria_id is not None:
        stmt = stmt.where(Produto.categoria_id == categoria_id)
    if produto_id is not None:
        stmt = stmt.where(Produto.id == produto_id)

    return [
        {
            "produto_id": l.id,
            "codigo": l.codigo,
            "nome": l.nome,
            "total_entradas": l.entradas,
            "total_saidas": l.saidas,
            "total_transferido": l.transferido,
            "saldo_do_periodo": l.entradas - l.saidas,
        }
        for l in db.execute(stmt).all()
    ]


def produtos_sem_movimentacao(db, dias: int) -> list[dict]:
    limite = datetime.now() - timedelta(days=dias)

    ultima = (
        select(
            Movimentacao.produto_id.label("produto_id"),
            func.max(Movimentacao.data_hora).label("ultima"),
        )
        .group_by(Movimentacao.produto_id)
        .subquery()
    )
    totais = _total_por_produto()

    stmt = (
        select(
            Produto.id,
            Produto.codigo,
            Produto.nome,
            ultima.c.ultima,
            func.coalesce(totais.c.total, 0).label("estoque_total"),
        )
        .outerjoin(ultima, ultima.c.produto_id == Produto.id)
        .outerjoin(totais, totais.c.produto_id == Produto.id)
        .where(Produto.ativo.is_(True))
        .where((ultima.c.ultima.is_(None)) | (ultima.c.ultima < limite))
        .order_by(Produto.nome)
    )

    return [
        {
            "produto_id": l.id,
            "codigo": l.codigo,
            "nome": l.nome,
            "estoque_total": l.estoque_total,
            "ultima_movimentacao": l.ultima,
        }
        for l in db.execute(stmt).all()
    ]


def comparacao_de_saldos(db, produto_id: int | None = None, categoria_id: int | None = None) -> list[dict]:
    stmt = (
        select(
            Produto.id,
            Produto.codigo,
            Produto.nome,
            Armazem.id.label("armazem_id"),
            Armazem.nome.label("armazem_nome"),
            EstoqueArmazem.quantidade,
        )
        .join(EstoqueArmazem, EstoqueArmazem.produto_id == Produto.id)
        .join(Armazem, Armazem.id == EstoqueArmazem.armazem_id)
        .where(EstoqueArmazem.quantidade > 0)
        .order_by(Produto.nome, Armazem.nome)
    )
    if produto_id is not None:
        stmt = stmt.where(Produto.id == produto_id)
    if categoria_id is not None:
        stmt = stmt.where(Produto.categoria_id == categoria_id)

    agrupado: dict[int, dict] = {}
    for l in db.execute(stmt).all():
        item = agrupado.setdefault(
            l.id,
            {"produto_id": l.id, "codigo": l.codigo, "nome": l.nome, "total": 0, "saldos": []},
        )
        item["total"] += l.quantidade
        item["saldos"].append(
            {"armazem_id": l.armazem_id, "armazem_nome": l.armazem_nome, "quantidade": l.quantidade}
        )
    return list(agrupado.values())


def estatisticas(db) -> dict:
    por_categoria = db.execute(
        select(Categoria.nome, func.count(Produto.id))
        .outerjoin(Produto, Produto.categoria_id == Categoria.id)
        .group_by(Categoria.id, Categoria.nome)
        .order_by(Categoria.nome)
    ).all()

    por_tipo = db.execute(
        select(Movimentacao.tipo, func.count(Movimentacao.id), func.sum(Movimentacao.quantidade))
        .group_by(Movimentacao.tipo)
        .order_by(Movimentacao.tipo)
    ).all()

    por_status = db.execute(
        select(PedidoCompra.status, func.count(PedidoCompra.id))
        .group_by(PedidoCompra.status)
        .order_by(PedidoCompra.status)
    ).all()

    por_armazem = db.execute(
        select(
            Armazem.nome,
            func.count(EstoqueArmazem.produto_id),
            func.coalesce(func.sum(EstoqueArmazem.quantidade), 0),
        )
        .outerjoin(EstoqueArmazem, EstoqueArmazem.armazem_id == Armazem.id)
        .group_by(Armazem.id, Armazem.nome)
        .order_by(Armazem.nome)
    ).all()

    valor_estoque = db.scalar(
        select(func.coalesce(func.sum(EstoqueArmazem.quantidade * Produto.preco_unitario), 0))
        .select_from(EstoqueArmazem)
        .join(Produto, Produto.id == EstoqueArmazem.produto_id)
    )

    preco = db.execute(
        select(func.avg(Produto.preco_unitario), func.min(Produto.preco_unitario), func.max(Produto.preco_unitario))
    ).one()

    totais = _total_por_produto()
    abaixo_do_minimo = db.scalar(
        select(func.count())
        .select_from(Produto)
        .outerjoin(totais, totais.c.produto_id == Produto.id)
        .where(Produto.ativo.is_(True))
        .where(func.coalesce(totais.c.total, 0) < Produto.estoque_minimo)
    )

    return {
        "total_produtos": db.scalar(select(func.count(Produto.id))),
        "produtos_ativos": db.scalar(select(func.count(Produto.id)).where(Produto.ativo.is_(True))),
        "total_fornecedores": db.scalar(select(func.count(Fornecedor.id))),
        "total_armazens": db.scalar(select(func.count(Armazem.id))),
        "produtos_por_categoria": {nome: qtd for nome, qtd in por_categoria},
        "movimentacoes_por_tipo": {
            tipo: {"quantidade_de_movimentacoes": qtd, "unidades_movimentadas": int(unidades)}
            for tipo, qtd, unidades in por_tipo
        },
        "pedidos_por_status": {status: qtd for status, qtd in por_status},
        "estoque_por_armazem": {
            nome: {"produtos_diferentes": produtos, "unidades": int(unidades)}
            for nome, produtos, unidades in por_armazem
        },
        "valor_total_em_estoque": float(valor_estoque),
        "preco_medio": float(preco[0]) if preco[0] is not None else 0.0,
        "preco_minimo": float(preco[1]) if preco[1] is not None else 0.0,
        "preco_maximo": float(preco[2]) if preco[2] is not None else 0.0,
        "produtos_abaixo_do_minimo": abaixo_do_minimo,
    }