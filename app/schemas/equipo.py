import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EstadoEquipoEnum
from app.schemas.foto import FotoList
from app.schemas.equipo_repuesto import EquipoRepuestoRead


# ── CREATE (schema interno, no se expone como JSON) ─

class EquipoCreate(BaseModel):
    """Schema interno que construye el router desde los Form fields."""
    codigo_equipo: str = Field(min_length=1, max_length=50)
    nombre: str = Field(min_length=1, max_length=200)
    descripcion: Optional[str] = None

    clasificacion_id: Optional[uuid.UUID] = None
    equipo_padre_id: Optional[uuid.UUID] = None
    area_id: Optional[uuid.UUID] = None

    # Datos de placa
    marca: Optional[str] = Field(default=None, max_length=100)
    modelo: Optional[str] = Field(default=None, max_length=100)
    numero_serie: Optional[str] = Field(default=None, max_length=100)
    potencia: Optional[str] = Field(default=None, max_length=50)
    voltaje: Optional[str] = Field(default=None, max_length=50)
    rpm: Optional[str] = Field(default=None, max_length=50)
    capacidad: Optional[str] = Field(default=None, max_length=50)
    anio_fabricacion: Optional[int] = None
    proveedor: Optional[str] = Field(default=None, max_length=150)
    fecha_adquisicion: Optional[datetime] = None

    # Estado
    estado: EstadoEquipoEnum = EstadoEquipoEnum.OPERATIVO
    motivo_estado: Optional[str] = None

    observaciones: Optional[str] = None


# ── UPDATE ──────────────────────────────────────────

class EquipoUpdate(BaseModel):
    codigo_equipo: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=50,
    )
    nombre: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    descripcion: Optional[str] = None

    clasificacion_id: Optional[uuid.UUID] = None
    equipo_padre_id: Optional[uuid.UUID] = None
    area_id: Optional[uuid.UUID] = None

    marca: Optional[str] = Field(default=None, max_length=100)
    modelo: Optional[str] = Field(default=None, max_length=100)
    numero_serie: Optional[str] = Field(default=None, max_length=100)
    potencia: Optional[str] = Field(default=None, max_length=50)
    voltaje: Optional[str] = Field(default=None, max_length=50)
    rpm: Optional[str] = Field(default=None, max_length=50)
    capacidad: Optional[str] = Field(default=None, max_length=50)
    anio_fabricacion: Optional[int] = None
    proveedor: Optional[str] = Field(default=None, max_length=150)
    fecha_adquisicion: Optional[datetime] = None

    estado: Optional[EstadoEquipoEnum] = None
    motivo_estado: Optional[str] = None

    observaciones: Optional[str] = None


# ── READ (detalle completo) ────────────────────────

class SubEquipoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    codigo_equipo: str
    nombre: str
    nivel: int
    estado: EstadoEquipoEnum
    repuestos_necesarios: List[EquipoRepuestoRead] = []


class EquipoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    codigo_equipo: str
    nombre: str
    descripcion: Optional[str] = None
    nivel: int

    clasificacion_id: Optional[uuid.UUID] = None
    nombre_clasificacion: Optional[str] = None
    area_id: Optional[uuid.UUID] = None
    nombre_area: Optional[str] = None
    equipo_padre_id: Optional[uuid.UUID] = None
    nombre_equipo_padre: Optional[str] = None

    marca: Optional[str] = None
    modelo: Optional[str] = None
    numero_serie: Optional[str] = None
    potencia: Optional[str] = None
    voltaje: Optional[str] = None
    rpm: Optional[str] = None
    capacidad: Optional[str] = None
    anio_fabricacion: Optional[int] = None
    proveedor: Optional[str] = None
    fecha_adquisicion: Optional[datetime] = None

    estado: EstadoEquipoEnum
    motivo_estado: Optional[str] = None

    observaciones: Optional[str] = None

    created_at: datetime
    updated_at: datetime
    created_by: Optional[uuid.UUID] = None
    updated_by: Optional[uuid.UUID] = None

    sub_equipos: List[SubEquipoRead] = []
    fotos: List[FotoList] = []


# ── ÁRBOL JERÁRQUICO ───────────────────────────────

class EquipoArbolNodo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    codigo_equipo: str
    nombre: str
    nivel: int
    estado: EstadoEquipoEnum
    hijos: List["EquipoArbolNodo"] = []


EquipoArbolNodo.model_rebuild()


class EquipoArbolRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    codigo_equipo: str
    nombre: str
    nivel: int
    estado: EstadoEquipoEnum
    nombre_area: Optional[str] = None
    nombre_clasificacion: Optional[str] = None
    hijos: List[EquipoArbolNodo] = []


# ── CAMBIO DE ESTADO ───────────────────────────────

class EquipoCambioEstado(BaseModel):
    estado: EstadoEquipoEnum
    motivo_estado: Optional[str] = None


# ── LISTADO ────────────────────────────────────────

class EquipoList(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    codigo_equipo: str
    nombre: str
    nivel: int
    estado: EstadoEquipoEnum
    nombre_area: Optional[str] = None
    nombre_clasificacion: Optional[str] = None
    marca: Optional[str] = None
