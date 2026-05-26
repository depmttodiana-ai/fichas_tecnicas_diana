from typing import List
import uuid

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import (
    CurrentUser,
    SessionDep,
    require_coordinador,
)
from app.models.usuario import Usuario
from app.schemas.usuario import (
    UsuarioCreate,
    UsuarioUpdate,
    UsuarioRead,
    UsuarioList,
    UsuarioCreateByAdmin,
)
from app.services.usuario import UsuarioService

router = APIRouter()


@router.post("/", response_model=UsuarioRead, status_code=201)
def crear_usuario(
    body: UsuarioCreate,
    session: SessionDep,
    user: CurrentUser,
    _: Usuario = Depends(require_coordinador),
):
    service = UsuarioService(session)
    usuario = service.create(body)
    session.commit()
    return usuario

@router.post("/admin", response_model=UsuarioRead, status_code=201)
def crear_usuario_admin(
    body: UsuarioCreateByAdmin,   # ← Con campo rol opcional
    session: SessionDep,
    user: CurrentUser,
    _: Usuario = Depends(require_coordinador),
):
    service = UsuarioService(session)
    usuario = service.create_by_admin(body)
    session.commit()
    return usuario



@router.get("/", response_model=List[UsuarioList])
def listar_usuarios(
    session: SessionDep,
    user: CurrentUser,
    _: Usuario = Depends(require_coordinador),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
):
    service = UsuarioService(session)
    return service.get_all(skip=skip, limit=limit)


@router.get("/{usuario_id}", response_model=UsuarioRead)
def obtener_usuario(
    usuario_id: uuid.UUID,
    session: SessionDep,
    user: CurrentUser,
):
    service = UsuarioService(session)
    return service.get_by_id(usuario_id)


@router.put("/{usuario_id}", response_model=UsuarioRead)
def actualizar_usuario(
    usuario_id: uuid.UUID,
    body: UsuarioUpdate,
    session: SessionDep,
    user: CurrentUser,
    _: Usuario = Depends(require_coordinador),
):
    service = UsuarioService(session)
    usuario = service.update(usuario_id, body)
    session.commit()
    return usuario


@router.delete("/{usuario_id}", status_code=204)
def eliminar_usuario(
    usuario_id: uuid.UUID,
    session: SessionDep,
    user: CurrentUser,
    _: Usuario = Depends(require_coordinador),
):
    service = UsuarioService(session)
    service.delete(usuario_id)
    session.commit()
    return None
