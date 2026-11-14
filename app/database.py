from sqlalchemy import MetaData, create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import DATABASE_URL

eh_sqlite = DATABASE_URL.startswith("sqlite")

connect_args = {"check_same_thread": False} if eh_sqlite else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)

if eh_sqlite:

    @event.listens_for(engine, "connect")
    def ativar_chaves_estrangeiras(conexao, _):
        cursor = conexao.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False)

convencao_nomes = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=convencao_nomes)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()