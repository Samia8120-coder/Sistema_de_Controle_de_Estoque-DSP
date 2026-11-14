import logging

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import registrar_handlers
from app.routers import (
    armazens,
    categorias,
    consultas,
    estatisticas,
    estoque,
    fornecedores,
    movimentacoes,
    pedidos_compra,
    produtos,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

app = FastAPI(
    title="Controle de Estoque",
    description="API de controle de estoque de uma distribuidora com vários armazéns.",
    version="1.0.0",
)

registrar_handlers(app)

app.include_router(categorias.router)
app.include_router(fornecedores.router)
app.include_router(armazens.router)
app.include_router(produtos.router)
app.include_router(pedidos_compra.router)
app.include_router(movimentacoes.router)
app.include_router(estoque.router)
app.include_router(consultas.router)
app.include_router(estatisticas.router)


@app.get("/saude", tags=["Sistema"])
def saude(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "banco": "conectado"}