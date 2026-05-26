from typing import List
import uuid

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import (
    CurrentUser,
    SessionDep,
    require_coordinador,
)
from app.models.usuario import Usuario
from app.schemas.area import (
    AreaCreate,
    AreaUpdate,
    AreaRead,
    AreaList,
)
from app.services.area import AreaService

router = APIRouter()


@router.post("/", response_model=AreaRead, status_code=201)
def crear_area(
    body: AreaCreate,
    session: SessionDep,
    user: CurrentUser,
    _: Usuario = Depends(require_coordinador),
):
    service = AreaService(session)
    area = service.create(body)
    session.commit()
    return area


@router.get("/", response_model=List[AreaList])
def listar_areas(
    session: SessionDep,
    user: CurrentUser,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    search: str = Query(default=None),
):
    service = AreaService(session)
    if search:
        return service.search(search, skip=skip, limit=limit)
    return service.get_all(skip=skip, limit=limit)


@router.get("/{area_id}", response_model=AreaRead)
def obtener_area(
    area_id: uuid.UUID,
    session: SessionDep,
    user: CurrentUser,
):
    service = AreaService(session)
    return service.get_by_id(area_id)


@router.put("/{area_id}", response_model=AreaRead)
def actualizar_area(
    area_id: uuid.UUID,
    body: AreaUpdate,
    session: SessionDep,
    user: CurrentUser,
    _: Usuario = Depends(require_coordinador),
):
    service = AreaService(session)
    area = service.update(area_id, body)
    session.commit()
    return area


@router.delete("/{area_id}", status_code=204)
def eliminar_area(
    area_id: uuid.UUID,
    session: SessionDep,
    user: CurrentUser,
    _: Usuario = Depends(require_coordinador),
):
    service = AreaService(session)
    service.delete(area_id)
    session.commit()
    return None
