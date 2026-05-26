from typing import List
import uuid

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, SessionDep
from app.schemas.historial import HistorialRead
from app.services.historial import HistorialService

router = APIRouter()


@router.get(
    "/equipo/{equipo_id}",
    response_model=List[HistorialRead],
)
def historial_por_equipo(
    equipo_id: uuid.UUID,
    session: SessionDep,
    user: CurrentUser,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
):
    """Historial de cambios de un equipo."""
    service = HistorialService(session)
    return service.get_by_equipo(
        equipo_id,
        skip=skip,
        limit=limit,
    )
