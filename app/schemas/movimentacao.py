from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.armazem import ArmazemResumo
from app.schemas.produto import ProdutoResumo


class SaidaIn(BaseModel):
    produto_id: int = Field(gt=0)
    armazem_id: int = Field(gt=0)
    quantidade: int = Field(gt=0)
    motivo: str = Field(default="venda a cliente", min_length=3, max_length=120)
    observacao: str | None = Field(default=None, max_length=255)

class TransferenciaIn(BaseModel):
    produto_id: int = Field(gt=0)
    armazem_origem_id: int = Field(gt=0)
    armazem_destino_id: int = Field(gt=0)
    quantidade: int = Field(gt=0)
    motivo: str = Field(default="transferencia entre depositos", min_length=3, max_length=120)
    observacao: str | None = Field(default=None, max_length=255)

class MovimentacaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo: str
    produto: ProdutoResumo
    quantidade: int
    data_hora: datetime
    motivo: str
    observacao: str | None
    armazem_origem: ArmazemResumo | None
    armazem_destino: ArmazemResumo | None
    pedido_compra_id: int | None
