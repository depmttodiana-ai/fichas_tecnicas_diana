from typing import List, Optional
import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import (
    CurrentUser,
    SessionDep,
    require_editor,
)
from app.models.usuario import Usuario
from app.models.enums import (
    TipoMantenimientoEnum,
    EstadoMantenimientoEnum,
)
from app.schemas.mantenimiento import (
    MantenimientoCreate,
    MantenimientoUpdate,
    MantenimientoRead,
    MantenimientoList,
)
from app.services.mantenimiento import MantenimientoService
from app.models.equipo_repuesto import EquipoRepuesto

router = APIRouter()


@router.post(
    "/",
    response_model=MantenimientoRead,
    status_code=201,
)
def crear_mantenimiento(
    body: MantenimientoCreate,
    session: SessionDep,
    user: CurrentUser,
    _: Usuario = Depends(require_editor),
):
    service = MantenimientoService(session)
    mantto = service.create(body, user.id)
    session.commit()
    return mantto


@router.get("/", response_model=List[MantenimientoList])
def listar_mantenimientos(
    session: SessionDep,
    user: CurrentUser,
    # Paginación
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    # Filtros
    equipo_id: Optional[uuid.UUID] = Query(default=None),
    tipo: Optional[TipoMantenimientoEnum] = Query(default=None),
    estado: Optional[EstadoMantenimientoEnum] = Query(default=None),
    fecha_desde: Optional[date] = Query(default=None),
    fecha_hasta: Optional[date] = Query(default=None),
    usuario_id: Optional[uuid.UUID] = Query(default=None),
):
    service = MantenimientoService(session)

    hay_filtros = any([
        equipo_id, tipo, estado,
        fecha_desde, fecha_hasta, usuario_id,
    ])

    if hay_filtros:
        return service.filter(
            equipo_id=equipo_id,
            tipo=tipo,
            estado=estado,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            usuario_id=usuario_id,
            skip=skip,
            limit=limit,
        )

    return service.get_all(skip=skip, limit=limit)


@router.get(
    "/equipo/{equipo_id}",
    response_model=List[MantenimientoList],
)
def mantenimientos_por_equipo(
    equipo_id: uuid.UUID,
    session: SessionDep,
    user: CurrentUser,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
):
    """Historial de mantenimientos de un equipo específico."""
    service = MantenimientoService(session)
    return service.get_by_equipo(
        equipo_id,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{mantenimiento_id}",
    response_model=MantenimientoRead,
)
def obtener_mantenimiento(
    mantenimiento_id: uuid.UUID,
    session: SessionDep,
    user: CurrentUser,
):
    service = MantenimientoService(session)
    return service.get_by_id(mantenimiento_id)


@router.put(
    "/{mantenimiento_id}",
    response_model=MantenimientoRead,
)
def actualizar_mantenimiento(
    mantenimiento_id: uuid.UUID,
    body: MantenimientoUpdate,
    session: SessionDep,
    user: CurrentUser,
    _: Usuario = Depends(require_editor),
):
    service = MantenimientoService(session)
    mantto = service.update(mantenimiento_id, body)
    session.commit()
    return mantto


@router.delete("/{mantenimiento_id}", status_code=204)
def eliminar_mantenimiento(
    mantenimiento_id: uuid.UUID,
    session: SessionDep,
    user: CurrentUser,
    _: Usuario = Depends(require_editor),
):
    service = MantenimientoService(session)
    service.delete(mantenimiento_id)
    session.commit()
    return None

# ── REPUESTOS NECESARIOS ANTES DE MANTENIMIENTO ─────

@router.get(
    "/equipo/{equipo_id}/repuestos-necesarios",
    response_model=dict,
)
def repuestos_necesarios_para_mantenimiento(
    equipo_id: uuid.UUID,
    session: SessionDep,
    user: CurrentUser,
):
    """
    Antes de registrar un mantenimiento, consulta
    qué repuestos necesita este equipo.
    """
    service = MantenimientoService(session)
    repuestos = service.get_repuestos_necesarios_para_equipo(
        equipo_id,
    )

    return {
        "equipo_id": str(equipo_id),
        "repuestos_necesarios": repuestos,
        "mensaje": (
            "Estos son los repuestos que este equipo necesita. "
            "Al registrar el mantenimiento, indique cuáles usó."
        ),
    }
