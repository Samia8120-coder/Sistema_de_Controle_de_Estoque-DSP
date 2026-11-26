from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import consulta_service

router = APIRouter(prefix="/estatisticas", tags=["Estatísticas"])


@router.get("")
def estatisticas(db: Session = Depends(get_db)):
    return consulta_service.estatisticas(db)