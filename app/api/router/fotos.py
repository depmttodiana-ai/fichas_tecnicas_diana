from typing import List
import uuid

from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi import Query

from app.core.dependencies import (
    CurrentUser,
    SessionDep,
    require_editor,
)
from app.models.usuario import Usuario
from app.models.enums import TipoFotoEnum
from app.schemas.foto import FotoCreate, FotoRead, FotoList
from app.services.foto import FotoService

router = APIRouter()


@router.post(
    "/upload/{equipo_id}",
    response_model=FotoRead,
    status_code=201,
)
async def subir_foto(
    equipo_id: uuid.UUID,
    session: SessionDep,
    user: CurrentUser,
    _: Usuario = Depends(require_editor),
    file: UploadFile = File(...),
    tipo_foto: TipoFotoEnum = Form(default=TipoFotoEnum.GENERAL),
    descripcion: str = Form(default=None),
):
    body = FotoCreate(
        tipo_foto=tipo_foto,
        descripcion=descripcion,
    )
    service = FotoService(session)
    foto = await service.upload(equipo_id, file, body)
    session.commit()
    return foto


@router.get(
    "/equipo/{equipo_id}",
    response_model=List[FotoList],
)
def fotos_por_equipo(
    equipo_id: uuid.UUID,
    session: SessionDep,
    user: CurrentUser,
):
    service = FotoService(session)
    return service.get_by_equipo(equipo_id)


@router.delete("/{foto_id}", status_code=204)
def eliminar_foto(
    foto_id: uuid.UUID,
    session: SessionDep,
    user: CurrentUser,
    _: Usuario = Depends(require_editor),
):
    service = FotoService(session)
    service.delete(foto_id)
    session.commit()
    return None
