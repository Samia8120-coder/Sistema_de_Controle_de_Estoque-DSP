from pydantic import BaseModel, ConfigDict, Field

PADRAO_EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class FornecedorCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    cnpj: str = Field(min_length=14, max_length=18)
    email: str | None = Field(default=None, pattern=PADRAO_EMAIL, max_length=120)
    telefone: str | None = Field(default=None, max_length=20)
    ativo: bool = True


class FornecedorUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=120)
    email: str | None = Field(default=None, pattern=PADRAO_EMAIL, max_length=120)
    telefone: str | None = Field(default=None, max_length=20)
    ativo: bool | None = None


class FornecedorResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    cnpj: str


class FornecedorOut(FornecedorResumo):
    email: str | None
    telefone: str | None
    ativo: bool