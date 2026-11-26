from datetime import datetime

from pydantic import BaseModel


class SaldoArmazemOut(BaseModel):
    armazem_id: int
    armazem_nome: str
    quantidade: int

class EstoqueProdutoOut(BaseModel):
    produto_id: int
    codigo: str
    nome: str
    estoque_minimo: int
    estoque_total: int
    abaixo_do_minimo: bool
    saldos: list[SaldoArmazemOut]

class EstoqueResumoOut(BaseModel):
    produto_id: int
    codigo: str
    nome: str
    estoque_minimo: int
    estoque_total: int
    falta_para_minimo: int

class SaldoProdutoArmazemOut(BaseModel):
    produto_id: int
    codigo: str
    nome: str
    quantidade: int

class MovimentacaoPeriodoOut(BaseModel):
    produto_id: int
    codigo: str
    nome: str
    total_entradas: int
    total_saidas: int
    total_transferido: int
    saldo_do_periodo: int

class SemMovimentacaoOut(BaseModel):
    produto_id: int
    codigo: str
    nome: str
    estoque_total: int
    ultima_movimentacao: datetime | None

class ComparacaoSaldosOut(BaseModel):
    produto_id: int
    codigo: str
    nome: str
    total: int
    saldos: list(SaldoArmazemOut)