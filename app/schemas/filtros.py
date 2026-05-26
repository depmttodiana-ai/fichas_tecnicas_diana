import uuid
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import (
    EstadoEquipoEnum,
    TipoMantenimientoEnum,
    EstadoMantenimientoEnum,
)


class Paginacion(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


class FiltroEquipos(BaseModel):
    nombre: Optional[str] = None
    codigo: Optional[str] = None
    area_id: Optional[uuid.UUID] = None
    clasificacion_id: Optional[uuid.UUID] = None
    equipo_padre_id: Optional[uuid.UUID] = None
    estado: Optional[EstadoEquipoEnum] = None
    nivel: Optional[int] = Field(default=None, ge=1)
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None


class FiltroMantenimientos(BaseModel):
    equipo_id: Optional[uuid.UUID] = None
    tipo: Optional[TipoMantenimientoEnum] = None
    estado: Optional[EstadoMantenimientoEnum] = None
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None
    usuario_id: Optional[uuid.UUID] = None
