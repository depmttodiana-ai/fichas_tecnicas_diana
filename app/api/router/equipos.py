from typing import List, Optional
import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, Query, Form, File, UploadFile, HTTPException

from app.core.dependencies import (
    CurrentUser,
    SessionDep,
    require_editor,
)
from app.models.enums import EstadoEquipoEnum, TipoFotoEnum
from app.models.usuario import Usuario
from app.schemas.equipo import (
    EquipoCreate,
    EquipoUpdate,
    EquipoRead,
    EquipoList,
    EquipoArbolRead,
    EquipoCambioEstado,
)
from app.schemas.foto import FotoCreate
from app.services.equipo import EquipoService
from app.services.foto import FotoService
from app.schemas.equipo_repuesto import (
    EquipoRepuestoCreate,
    EquipoRepuestoRead,
)
from app.repositories.equipo_repuesto import EquipoRepuestoRepository
from app.repositories.equipo import EquipoRepository
from app.models.equipo_repuesto import EquipoRepuesto
router = APIRouter()


# ── HELPER: Procesar fotos del form ────────────────

async def _procesar_fotos(
    foto_service: FotoService,
    equipo_id: uuid.UUID,
    fotos_data: list[tuple[Optional[UploadFile], TipoFotoEnum]],
) -> list[dict]:
    """
    Recibe lista de tuplas (archivo, tipo).
    Sube solo las que tengan archivo válido.
    """
    fotos_subidas = []

    for archivo, tipo in fotos_data:
        if archivo and archivo.filename:
            foto_body = FotoCreate(
                tipo_foto=tipo,
                descripcion=None,
            )
            foto_creada = await foto_service.upload(
                equipo_id,
                archivo,
                foto_body,
            )
            fotos_subidas.append({
                "id": str(foto_creada.id),
                "url": foto_creada.url,
                "tipo": tipo.value,
            })

    return fotos_subidas


# ── CREAR EQUIPO (FORM + HASTA 10 FOTOS CON TIPO) ─

@router.post("/", response_model=EquipoRead, status_code=201)
async def crear_equipo(
    session: SessionDep,
    user: CurrentUser,
    _: Usuario = Depends(require_editor),

    # ── Campos del formulario ──────────────────────
    codigo_equipo: str = Form(..., min_length=1, max_length=50),
    nombre: str = Form(..., min_length=1, max_length=200),
    descripcion: Optional[str] = Form(default=None),

    clasificacion_id: Optional[str] = Form(default=None),
    equipo_padre_id: Optional[str] = Form(default=None),
    area_id: Optional[str] = Form(default=None),

    # Datos de placa
    marca: Optional[str] = Form(default=None),
    modelo: Optional[str] = Form(default=None),
    numero_serie: Optional[str] = Form(default=None),
    potencia: Optional[str] = Form(default=None),
    voltaje: Optional[str] = Form(default=None),
    rpm: Optional[str] = Form(default=None),
    capacidad: Optional[str] = Form(default=None),
    anio_fabricacion: Optional[int] = Form(default=None),
    proveedor: Optional[str] = Form(default=None),
    fecha_adquisicion: Optional[str] = Form(default=None),

    # Estado
    estado: EstadoEquipoEnum = Form(
        default=EstadoEquipoEnum.OPERATIVO,
    ),
    motivo_estado: Optional[str] = Form(default=None),
    observaciones: Optional[str] = Form(default=None),

    # ── Repuestos necesarios (JSON string) ─────────
    repuestos_necesarios: Optional[str] = Form(default=None),

    # ── Fotos con tipo ─────────────────────────────
    foto1: Optional[UploadFile] = File(default=None),
    tipo_foto1: TipoFotoEnum = Form(
        default=TipoFotoEnum.GENERAL,
    ),
    foto2: Optional[UploadFile] = File(default=None),
    tipo_foto2: TipoFotoEnum = Form(
        default=TipoFotoEnum.GENERAL,
    ),
    foto3: Optional[UploadFile] = File(default=None),
    tipo_foto3: TipoFotoEnum = Form(
        default=TipoFotoEnum.GENERAL,
    ),
    foto4: Optional[UploadFile] = File(default=None),
    tipo_foto4: TipoFotoEnum = Form(
        default=TipoFotoEnum.GENERAL,
    ),
    foto5: Optional[UploadFile] = File(default=None),
    tipo_foto5: TipoFotoEnum = Form(
        default=TipoFotoEnum.GENERAL,
    ),
    
):

    # ── Convertir UUIDs ────────────────────────────
    clasificacion_uuid = None
    if clasificacion_id and clasificacion_id.strip():
        try:
            clasificacion_uuid = uuid.UUID(clasificacion_id)
        except ValueError:
            pass

    padre_uuid = None
    if equipo_padre_id and equipo_padre_id.strip():
        try:
            padre_uuid = uuid.UUID(equipo_padre_id)
        except ValueError:
            pass

    area_uuid = None
    if area_id and area_id.strip():
        try:
            area_uuid = uuid.UUID(area_id)
        except ValueError:
            pass

    # ── Convertir fecha ────────────────────────────
    fecha_adq = None
    if fecha_adquisicion and fecha_adquisicion.strip():
        try:
            fecha_adq = datetime.fromisoformat(fecha_adquisicion)
        except ValueError:
            pass

    # ── Parsear repuestos necesarios ────────────────
    import json
    repuestos_data = []
    if repuestos_necesarios and repuestos_necesarios.strip():
        try:
            repuestos_data = json.loads(repuestos_necesarios)
        except (json.JSONDecodeError, TypeError):
            pass

    # ── Construir schema ───────────────────────────
    body = EquipoCreate(
        codigo_equipo=codigo_equipo,
        nombre=nombre,
        descripcion=descripcion,
        clasificacion_id=clasificacion_uuid,
        equipo_padre_id=padre_uuid,
        area_id=area_uuid,
        marca=marca,
        modelo=modelo,
        numero_serie=numero_serie,
        potencia=potencia,
        voltaje=voltaje,
        rpm=rpm,
        capacidad=capacidad,
        anio_fabricacion=anio_fabricacion,
        proveedor=proveedor,
        fecha_adquisicion=fecha_adq,
        estado=estado,
        motivo_estado=motivo_estado,
        observaciones=observaciones,
    )

    # ── Crear equipo ───────────────────────────────
    equipo_service = EquipoService(session)
    equipo_creado = equipo_service.create(body, user.id)

    # ── Guardar repuestos necesarios ────────────────


    if repuestos_data:
        rep_repo = EquipoRepuestoRepository(session)
        for rep in repuestos_data:
            if rep.get("codigo_repuesto") and rep.get("descripcion"):
                nuevo_rep = EquipoRepuesto(
                    equipo_id=equipo_creado.id,
                    codigo_repuesto=rep["codigo_repuesto"],
                    descripcion=rep["descripcion"],
                    para_que=rep.get("para_que"),
                    ubicacion=rep.get("ubicacion"),
                    cantidad_necesaria=rep.get(
                        "cantidad_necesaria", 1,
                    ),
                    observaciones=rep.get("observaciones"),
                )
                rep_repo.add(nuevo_rep)

    # ── Procesar fotos ─────────────────────────────
    fotos_data = [
        (foto1, tipo_foto1), (foto2, tipo_foto2),
        (foto3, tipo_foto3), (foto4, tipo_foto4),
        (foto5, tipo_foto5),
    ]

    if any(f[0] for f in fotos_data):
        foto_service = FotoService(session)
        await _procesar_fotos(
            foto_service,
            equipo_creado.id,
            fotos_data,
        )

    session.commit()
    return equipo_service.get_by_id(equipo_creado.id)


# ── SUBIR MÁS FOTOS DESPUÉS (BATCH) ───────────────

@router.post(
    "/{equipo_id}/fotos",
    response_model=dict,
    status_code=201,
)
async def subir_fotos_batch(
    equipo_id: uuid.UUID,
    session: SessionDep,
    user: CurrentUser,
    _: Usuario = Depends(require_editor),
    foto1: Optional[UploadFile] = File(default=None),
    tipo_foto1: TipoFotoEnum = Form(
        default=TipoFotoEnum.GENERAL,
    ),
    foto2: Optional[UploadFile] = File(default=None),
    tipo_foto2: TipoFotoEnum = Form(
        default=TipoFotoEnum.GENERAL,
    ),
    foto3: Optional[UploadFile] = File(default=None),
    tipo_foto3: TipoFotoEnum = Form(
        default=TipoFotoEnum.GENERAL,
    ),
    foto4: Optional[UploadFile] = File(default=None),
    tipo_foto4: TipoFotoEnum = Form(
        default=TipoFotoEnum.GENERAL,
    ),
    foto5: Optional[UploadFile] = File(default=None),
    tipo_foto5: TipoFotoEnum = Form(
        default=TipoFotoEnum.GENERAL,
    ),
    
):
    """Agrega más fotos a un equipo existente."""

    fotos_data = [
        (foto1, tipo_foto1),
        (foto2, tipo_foto2),
        (foto3, tipo_foto3),
        (foto4, tipo_foto4),
        (foto5, tipo_foto5),
    ]

    if not any(f[0] for f in fotos_data):
        return {"mensaje": "No se enviaron fotos", "fotos": []}

    foto_service = FotoService(session)
    fotos_subidas = await _procesar_fotos(
        foto_service,
        equipo_id,
        fotos_data,
    )

    session.commit()

    return {
        "mensaje": f"{len(fotos_subidas)} foto(s) subida(s)",
        "fotos": fotos_subidas,
    }


# ── LISTAR CON FILTROS ─────────────────────────────

@router.get("/", response_model=List[EquipoList])
def listar_equipos(
    session: SessionDep,
    user: CurrentUser,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    nombre: Optional[str] = Query(default=None),
    codigo: Optional[str] = Query(default=None),
    area_id: Optional[uuid.UUID] = Query(default=None),
    clasificacion_id: Optional[uuid.UUID] = Query(default=None),
    equipo_padre_id: Optional[uuid.UUID] = Query(default=None),
    estado: Optional[EstadoEquipoEnum] = Query(default=None),
    nivel: Optional[int] = Query(default=None, ge=1),
    fecha_desde: Optional[date] = Query(default=None),
    fecha_hasta: Optional[date] = Query(default=None),
):
    service = EquipoService(session)

    hay_filtros = any([
        nombre, codigo, area_id, clasificacion_id,
        equipo_padre_id, estado, nivel,
        fecha_desde, fecha_hasta,
    ])

    if hay_filtros:
        return service.filter(
            nombre=nombre,
            codigo=codigo,
            area_id=area_id,
            clasificacion_id=clasificacion_id,
            equipo_padre_id=equipo_padre_id,
            estado=estado,
            nivel=nivel,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            skip=skip,
            limit=limit,
        )

    return service.get_all(skip=skip, limit=limit)


# ── EQUIPOS RAÍZ ───────────────────────────────────

@router.get("/raices", response_model=List[EquipoList])
def listar_equipos_raiz(
    session: SessionDep,
    user: CurrentUser,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
):
    service = EquipoService(session)
    return service.get_raices(skip=skip, limit=limit)


# ── OBTENER POR ID ─────────────────────────────────

@router.get("/{equipo_id}", response_model=EquipoRead)
def obtener_equipo(
    equipo_id: uuid.UUID,
    session: SessionDep,
    user: CurrentUser,
):
    service = EquipoService(session)
    return service.get_by_id(equipo_id)


# ── ÁRBOL JERÁRQUICO ───────────────────────────────

@router.get("/{equipo_id}/arbol", response_model=EquipoArbolRead)
def obtener_arbol_equipo(
    equipo_id: uuid.UUID,
    session: SessionDep,
    user: CurrentUser,
):
    service = EquipoService(session)
    return service.get_arbol(equipo_id)


# ── ACTUALIZAR ─────────────────────────────────────

@router.put("/{equipo_id}", response_model=EquipoRead)
def actualizar_equipo(
    equipo_id: uuid.UUID,
    body: EquipoUpdate,
    session: SessionDep,
    user: CurrentUser,
    _: Usuario = Depends(require_editor),
):
    service = EquipoService(session)
    equipo = service.update(equipo_id, body, user.id)
    session.commit()
    return equipo


# ── CAMBIO DE ESTADO ───────────────────────────────

@router.patch(
    "/{equipo_id}/estado",
    response_model=EquipoRead,
)
def cambiar_estado(
    equipo_id: uuid.UUID,
    body: EquipoCambioEstado,
    session: SessionDep,
    user: CurrentUser,
    _: Usuario = Depends(require_editor),
):
    service = EquipoService(session)
    equipo = service.change_state(equipo_id, body, user.id)
    session.commit()
    return equipo


# ── ELIMINAR ───────────────────────────────────────

@router.delete("/{equipo_id}", status_code=204)
def eliminar_equipo(
    equipo_id: uuid.UUID,
    session: SessionDep,
    user: CurrentUser,
    _: Usuario = Depends(require_editor),
):
    service = EquipoService(session)
    service.delete(equipo_id)
    session.commit()
    return None


# ── REPUESTOS NECESARIOS ────────────────────────────

@router.get(
    "/{equipo_id}/repuestos-necesarios",
    response_model=List[EquipoRepuestoRead],
)
def listar_repuestos_necesarios(
    equipo_id: uuid.UUID,
    session: SessionDep,
    user: CurrentUser,
):
    """Lista los repuestos que necesita este equipo."""
    repo = EquipoRepuestoRepository(session)
    repuestos = repo.get_by_equipo(equipo_id)
    return [
        EquipoRepuestoRead.model_validate(r)
        for r in repuestos
    ]


@router.post(
    "/{equipo_id}/repuestos-necesarios",
    response_model=EquipoRepuestoRead,
    status_code=201,
)
def agregar_repuesto_necesario(
    equipo_id: uuid.UUID,
    body: EquipoRepuestoCreate,
    session: SessionDep,
    user: CurrentUser,
    _: Usuario = Depends(require_editor),
):
    """Agrega un repuesto necesario a un equipo."""
    equipo_repo = EquipoRepository(session)
    equipo = equipo_repo.get_by_id(equipo_id)
    if not equipo:
        raise HTTPException(404, "Equipo no encontrado")

    rep_repo = EquipoRepuestoRepository(session)
    nuevo = EquipoRepuesto(
        equipo_id=equipo_id,
        codigo_repuesto=body.codigo_repuesto,
        descripcion=body.descripcion,
        para_que=body.para_que,
        ubicacion=body.ubicacion,
        cantidad_necesaria=body.cantidad_necesaria,
        observaciones=body.observaciones,
    )
    rep_creado = rep_repo.add(nuevo)
    session.commit()
    return EquipoRepuestoRead.model_validate(rep_creado)


@router.delete(
    "/{equipo_id}/repuestos-necesarios/{repuesto_id}",
    status_code=204,
)
def eliminar_repuesto_necesario(
    equipo_id: uuid.UUID,
    repuesto_id: uuid.UUID,
    session: SessionDep,
    user: CurrentUser,
    _: Usuario = Depends(require_editor),
):
    """Elimina un repuesto necesario del equipo."""
    rep_repo = EquipoRepuestoRepository(session)
    repuesto = rep_repo.get_by_id(repuesto_id)
    if not repuesto or repuesto.equipo_id != equipo_id:
        raise HTTPException(404, "Repuesto no encontrado")

    rep_repo.delete(repuesto)
    session.commit()
    return None