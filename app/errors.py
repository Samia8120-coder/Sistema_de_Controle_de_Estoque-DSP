import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

logger = logging.getLogger("estoque")


class NaoEncontradoError(Exception):
    pass


class ConflitoError(Exception):
    pass


class RequisicaoInvalidaError(Exception):
    pass


def resposta(status: int, mensagem: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"detail": mensagem})


def registrar_handlers(app: FastAPI) -> None:
    @app.exception_handler(NaoEncontradoError)
    async def nao_encontrado(request: Request, exc: NaoEncontradoError):
        return resposta(404, str(exc))

    @app.exception_handler(ConflitoError)
    async def conflito(request: Request, exc: ConflitoError):
        return resposta(409, str(exc))

    @app.exception_handler(RequisicaoInvalidaError)
    async def requisicao_invalida(request: Request, exc: RequisicaoInvalidaError):
        return resposta(400, str(exc))

    @app.exception_handler(IntegrityError)
    async def integridade(request: Request, exc: IntegrityError):
        logger.warning("Violação de integridade: %s", exc.orig)
        texto = str(exc.orig).lower()

        if "unique" in texto or "duplicate" in texto:
            return resposta(409, "Já existe um registro com esses dados únicos.")
        if "foreign key" in texto:
            return resposta(409, "O registro está ligado a outro registro (chave estrangeira).")
        if "check" in texto:
            return resposta(409, "Os dados violam uma restrição de integridade do sistema.")
        return resposta(409, "A operação viola uma restrição de integridade.")

    @app.exception_handler(OperationalError)
    async def conexao(request: Request, exc: OperationalError):
        logger.error("Erro de conexão com o banco: %s", exc.orig)
        return resposta(503, "Banco de dados indisponível no momento. Tente novamente.")

    @app.exception_handler(SQLAlchemyError)
    async def erro_banco(request: Request, exc: SQLAlchemyError):
        logger.error("Falha de persistência: %s", exc)
        return resposta(500, "Falha ao processar a operação no banco de dados.")