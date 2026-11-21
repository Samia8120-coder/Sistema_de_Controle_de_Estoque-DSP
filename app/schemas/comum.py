import math
from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")


class Pagina(BaseModel, Generic[T]):
    items: list[T]
    total: int
    offset: int
    limit: int
    pagina_atual: int
    total_paginas: int


class ParametrosPagina:
    def __init__(
        self,
        offset: int = Query(0, ge=0, description="Quantos registros pular"),
        limit: int = Query(10, ge=1, le=100, description="Quantos registros devolver"),
    ):
        self.offset = offset
        self.limit = limit


def montar_pagina(items, total: int, offset: int, limit: int) -> dict:
    return {
        "items": items,
        "total": total,
        "offset": offset,
        "limit": limit,
        "pagina_atual": offset // limit + 1,
        "total_paginas": math.ceil(total / limit) if total else 0,
    }