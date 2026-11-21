from pydantic import BaseModel, ConfigDict, Field


class ArmazemCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=80)
    cidade: str = Field(min_length=2, max_length=80)
    endereco: str | None = Field(default=None, max_length=150)
    ativo: bool = True


class ArmazemUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=80)
    cidade: str | None = Field(default=None, min_length=2, max_length=80)
    endereco: str | None = Field(default=None, max_length=150)
    ativo: bool | None = None


class ArmazemResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str


class ArmazemOut(ArmazemResumo):
    cidade: str
    endereco: str | None
    ativo: bool