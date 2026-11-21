from sqlalchemy import func, select

from app.errors import NaoEncontradoError


def obter_ou_404(db, modelo, registro_id: int, nome: str):
    objeto = db.get(modelo, registro_id)
    if objeto is None:
        raise NaoEncontradoError(f"{nome} {registro_id} não encontrado(a).")
    return objeto


def paginar(db, stmt, offset: int, limit: int, order_by=(), options=(), linhas=False):
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))

    consulta = stmt
    if options:
        consulta = consulta.options(*options)
    if order_by:
        consulta = consulta.order_by(*order_by)

    resultado = db.execute(consulta.offset(offset).limit(limit))
    itens = resultado.all() if linhas else resultado.scalars().all()
    return itens, total