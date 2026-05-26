import uuid
from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    TipoMantenimientoEnum,
    EstadoMantenimientoEnum,
)


# ── REPUESTO USADO ─────────────────────────────────

class RepuestoUsadoCreate(BaseModel):
    repuesto_id: uuid.UUID
    cantidad_usada: float = Field(default=1, gt=0)
    observacion: Optional[str] = Field(
        default=None,
        max_length=500,
    )


class RepuestoUsadoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    repuesto_id: uuid.UUID
    nombre_repuesto: Optional[str] = None
    codigo_repuesto: Optional[str] = None
    cantidad_usada: float
    observacion: Optional[str] = None


# ── MANTENIMIENTO ──────────────────────────────────

class MantenimientoCreate(BaseModel):
    equipo_id: uuid.UUID
    tipo: TipoMantenimientoEnum
    titulo: str = Field(min_length=1, max_length=200)
    descripcion: Optional[str] = None
    trabajo_realizado: Optional[str] = None
    estado: EstadoMantenimientoEnum = (
        EstadoMantenimientoEnum.REALIZADO
    )
    fecha: date

    # Repuestos que se usaron en este trabajo
    repuestos_usados: List[RepuestoUsadoCreate] = []


class MantenimientoUpdate(BaseModel):
    tipo: Optional[TipoMantenimientoEnum] = None
    titulo: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    descripcion: Optional[str] = None
    trabajo_realizado: Optional[str] = None
    estado: Optional[EstadoMantenimientoEnum] = None
    fecha: Optional[date] = None


class MantenimientoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    equipo_id: uuid.UUID
    usuario_id: Optional[uuid.UUID] = None

    tipo: TipoMantenimientoEnum
    titulo: str
    descripcion: Optional[str] = None
    trabajo_realizado: Optional[str] = None
    estado: EstadoMantenimientoEnum
    fecha: date
    created_at: datetime

    # Datos resueltos
    nombre_equipo: Optional[str] = None
    codigo_equipo: Optional[str] = None
    nombre_usuario: Optional[str] = None

    # Repuestos usados
    repuestos_usados: List[RepuestoUsadoRead] = []


class MantenimientoList(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    fecha: date
    tipo: TipoMantenimientoEnum
    titulo: str
    estado: EstadoMantenimientoEnum
    nombre_equipo: Optional[str] = None
    codigo_equipo: Optional[str] = None
