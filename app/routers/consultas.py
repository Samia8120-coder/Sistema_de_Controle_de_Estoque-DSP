from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import RequisicaoInvalidaError
from app.schemas.estoque import ComparacaoSaldosOut, MovimentacaoPeriodoOut, SemMovimentacaoOut
from app.services import consulta_service

router = APIRouter(prefix="/consultas", tags=["Consultas"])


@router.get("/movimentacoes-periodo", response_model=list[MovimentacaoPeriodoOut])
def movimentacoes_no_periodo(
    inicio: datetime,
    fim: datetime,
    categoria_id: int | None = None,
    produto_id: int | None = None,
    db: Session = Depends(get_db),
):
    if inicio > fim:
        raise RequisicaoInvalidaError("A data de início deve ser anterior à data de fim.")
    return consulta_service.movimentacoes_no_periodo(db, inicio, fim, categoria_id, produto_id)


@router.get("/produtos-sem-movimentacao", response_model=list[SemMovimentacaoOut])
def produtos_sem_movimentacao(
    dias: int = Query(30, ge=1, description="Janela em dias sem nenhuma movimentação"),
    db: Session = Depends(get_db),
):
    return consulta_service.produtos_sem_movimentacao(db, dias)


@router.get("/comparacao-saldos", response_model=list[ComparacaoSaldosOut])
def comparacao_de_saldos(
    produto_id: int | None = None,
    categoria_id: int | None = None,
    db: Session = Depends(get_db),
):
    return consulta_service.comparacao_de_saldos(db, produto_id, categoria_id)