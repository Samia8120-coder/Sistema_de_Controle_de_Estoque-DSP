from sqlalchemy import func, select

from app.crud.base import obter_ou_404, paginar
from app.errors import ConflitoError
from app.models import Armazem, EstoqueArmazem, Movimentacao, Produto
from app.schemas.armazem import ArmazemCreate, ArmazemUpdate


def _nome_em_uso(db, nome: str, ignorar_id: int | None = None) -> bool:
    stmt = select(Armazem.id).where(func.lower(Armazem.nome) == nome.lower())
    if ignorar_id is not None:
        stmt = stmt.where(Armazem.id != ignorar_id)
    return db.scalar(stmt) is not None


def _saldo_total(db, armazem_id: int) -> int:
    return db.scalar(
        select(func.coalesce(func.sum(EstoqueArmazem.quantidade), 0)).where(
            EstoqueArmazem.armazem_id == armazem_id
        )
    )


def criar(db, dados: ArmazemCreate) -> Armazem:
    if _nome_em_uso(db, dados.nome):
        raise ConflitoError(f"Já existe um armazém chamado '{dados.nome}'.")

    armazem = Armazem(**dados.model_dump())
    db.add(armazem)
    db.commit()
    db.refresh(armazem)
    return armazem


def listar(db, pagina, nome: str | None = None, cidade: str | None = None, ativo: bool | None = None):
    stmt = select(Armazem)
    if nome:
        stmt = stmt.where(Armazem.nome.ilike(f"%{nome}%"))
    if cidade:
        stmt = stmt.where(Armazem.cidade.ilike(f"%{cidade}%"))
    if ativo is not None:
        stmt = stmt.where(Armazem.ativo == ativo)
    return paginar(db, stmt, pagina.offset, pagina.limit, order_by=(Armazem.nome,))


def obter(db, armazem_id: int) -> Armazem:
    return obter_ou_404(db, Armazem, armazem_id, "Armazém")


def atualizar(db, armazem_id: int, dados: ArmazemUpdate) -> Armazem:
    armazem = obter(db, armazem_id)
    campos = dados.model_dump(exclude_unset=True, exclude_none=True)

    if "nome" in campos and _nome_em_uso(db, campos["nome"], ignorar_id=armazem_id):
        raise ConflitoError(f"Já existe um armazém chamado '{campos['nome']}'.")

    if campos.get("ativo") is False and armazem.ativo and _saldo_total(db, armazem_id) > 0:
        raise ConflitoError(
            "O armazém ainda possui mercadorias em estoque. "
            "Transfira os produtos antes de desativá-lo."
        )

    for campo, valor in campos.items():
        setattr(armazem, campo, valor)

    db.commit()
    db.refresh(armazem)
    return armazem


def remover(db, armazem_id: int) -> None:
    armazem = obter(db, armazem_id)

    if _saldo_total(db, armazem_id) > 0:
        raise ConflitoError("O armazém possui mercadorias em estoque e não pode ser removido.")

    movimentacoes = db.scalar(
        select(func.count()).select_from(Movimentacao).where(
            (Movimentacao.armazem_origem_id == armazem_id)
            | (Movimentacao.armazem_destino_id == armazem_id)
        )
    )
    if movimentacoes:
        raise ConflitoError(
            "O armazém possui histórico de movimentações. Em vez de excluir, desative-o."
        )

    for saldo in list(armazem.estoques):
        db.delete(saldo)
    db.delete(armazem)
    db.commit()


def estoque_do_armazem(db, armazem_id: int, pagina):
    obter(db, armazem_id)
    stmt = (
        select(Produto.id.label("produto_id"), Produto.codigo, Produto.nome, EstoqueArmazem.quantidade)
        .join(EstoqueArmazem, EstoqueArmazem.produto_id == Produto.id)
        .where(EstoqueArmazem.armazem_id == armazem_id)
    )
    return paginar(
        db, stmt, pagina.offset, pagina.limit,
        order_by=(Produto.nome,), linhas=True,
    )