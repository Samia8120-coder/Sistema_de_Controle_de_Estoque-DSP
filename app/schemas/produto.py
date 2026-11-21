from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.categoria import CategoriaOut
from app.schemas.fornecedor import FornecedorResumo


class CaracteristicaIn(BaseModel):
    peso_kg: Decimal = Field(default=Decimal("0"), ge=0)
    altura_cm: Decimal = Field(default=Decimal("0"), ge=0)
    largura_cm: Decimal = Field(default=Decimal("0"), ge=0)
    profundidade_cm: Decimal = Field(default=Decimal("0"), ge=0)
    unidade_medida: str = Field(default="UN", max_length=10)
    condicao_armazenamento: str = Field(default="seco", max_length=40)
    perecivel: bool = False


class CaracteristicaUpdate(BaseModel):
    peso_kg: Decimal | None = Field(default=None, ge=0)
    altura_cm: Decimal | None = Field(default=None, ge=0)
    largura_cm: Decimal | None = Field(default=None, ge=0)
    profundidade_cm: Decimal | None = Field(default=None, ge=0)
    unidade_medida: str | None = Field(default=None, max_length=10)
    condicao_armazenamento: str | None = Field(default=None, max_length=40)
    perecivel: bool | None = None


class CaracteristicaOut(CaracteristicaIn):
    model_config = ConfigDict(from_attributes=True)


class ProdutoCreate(BaseModel):
    codigo: str = Field(min_length=2, max_length=30)
    nome: str = Field(min_length=2, max_length=150)
    descricao: str | None = Field(default=None, max_length=255)
    preco_unitario: Decimal = Field(ge=0, decimal_places=2)
    estoque_minimo: int = Field(default=0, ge=0)
    categoria_id: int = Field(gt=0)
    ativo: bool = True
    caracteristica: CaracteristicaIn | None = None
    fornecedores_ids: list[int] = []


class ProdutoUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=150)
    descricao: str | None = Field(default=None, max_length=255)
    preco_unitario: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    estoque_minimo: int | None = Field(default=None, ge=0)
    categoria_id: int | None = Field(default=None, gt=0)
    ativo: bool | None = None
    caracteristica: CaracteristicaUpdate | None = None
    fornecedores_ids: list[int] | None = None


class ProdutoResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    nome: str


class ProdutoOut(ProdutoResumo):
    descricao: str | None
    preco_unitario: float
    estoque_minimo: int
    ativo: bool
    categoria: CategoriaOut
    caracteristica: CaracteristicaOut | None
    fornecedores: list[FornecedorResumo]
    estoque_total: int