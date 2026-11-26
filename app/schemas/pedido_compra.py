from datetime import datetime
from decimal import decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.fornecedor import FornecedorResumo
from app.schemas.produto import ProdutoResumo


class ItemPedidoIn(BaseModel):
    produto_id: int = Field(gt=0)
    quantidade: int = Field(gt=0)
    preco_unitario: Decimal | None = Field(default=None, ge=0, decimal_places=2)

class PedidoCreate(BaseModel):
    fornecedor_id: int = Field(gt=0)
    observacao: str | None = Field(default=None, max_length=255)
    itens: list[ItemPedidoIn] = Field(min_length=1)

class ItemPedidoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    produto: ProdutoResumo
    quantidade_pedida: int
    quantidade_recebida: int
    quantidade_pendente: int
    preco_unitario: float

class PedidoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fornecedor: FornecedorResumo
    data_pedido: datetime
    status: str
    observacao: str | None
    valor_total: float
    itens: list[ItemPedidoOut]

class ItemRecebimento(BaseModel):
    produto_id: int = Field(gt=0)
    quantidade: int = Field(gt=0)

class RecebimentoIn(BaseModel):
    armazem_id: int = Field(gt=0)
    itens: list[ItemRecebimento] = Field(min_length=1)