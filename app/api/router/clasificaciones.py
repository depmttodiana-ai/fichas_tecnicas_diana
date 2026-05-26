from typing import List
import uuid

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import (
    CurrentUser,
    SessionDep,
    require_coordinador,
)
from app.models.usuario import Usuario
from app.schemas.clasificacion import (
    ClasificacionCreate,
    ClasificacionUpdate,
    ClasificacionRead,
    ClasificacionList,
)
from app.services.clasificacion import ClasificacionService

router = APIRouter()


@router.post("/", response_model=ClasificacionRead, status_code=201)
def crear_clasificacion(
    body: ClasificacionCreate,
    session: SessionDep,
    user: CurrentUser,
    _: Usuario = Depends(require_coordinador),
):
    service = ClasificacionService(session)
    clasificacion = service.create(body)
    session.commit()
    return clasificacion


@router.get("/", response_model=List[ClasificacionList])
def listar_clasificaciones(
    session: SessionDep,
    user: CurrentUser,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    search: str = Query(default=None),
):
    service = ClasificacionService(session)
    if search:
        return service.search(search, skip=skip, limit=limit)
    return service.get_all(skip=skip, limit=limit)


@router.get("/{clasificacion_id}", response_model=ClasificacionRead)
def obtener_clasificacion(
    clasificacion_id: uuid.UUID,
    session: SessionDep,
    user: CurrentUser,
):
    service = ClasificacionService(session)
    return service.get_by_id(clasificacion_id)


@router.put("/{clasificacion_id}", response_model=ClasificacionRead)
def actualizar_clasificacion(
    clasificacion_id: uuid.UUID,
    body: ClasificacionUpdate,
    session: SessionDep,
    user: CurrentUser,
    _: Usuario = Depends(require_coordinador),
):
    service = ClasificacionService(session)
    clasificacion = service.update(clasificacion_id, body)
    session.commit()
    return clasificacion


@router.delete("/{clasificacion_id}", status_code=204)
def eliminar_clasificacion(
    clasificacion_id: uuid.UUID,
    session: SessionDep,
    user: CurrentUser,
    _: Usuario = Depends(require_coordinador),
):
    service = ClasificacionService(session)
    service.delete(clasificacion_id)
    session.commit()
    return None
