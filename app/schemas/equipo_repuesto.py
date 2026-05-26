import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class EquipoRepuestoCreate(BaseModel):
    codigo_repuesto: str = Field(min_length=1, max_length=100)
    descripcion: str = Field(min_length=1, max_length=300)
    para_que: Optional[str] = Field(
        default=None,
        max_length=500,
    )
    ubicacion: Optional[str] = Field(
        default=None,
        max_length=500,
    )
    cantidad_necesaria: float = Field(default=1, gt=0)
    observaciones: Optional[str] = Field(
        default=None,
        max_length=500,
    )


class EquipoRepuestoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    equipo_id: uuid.UUID
    codigo_repuesto: str
    descripcion: str
    para_que: Optional[str] = None
    ubicacion: Optional[str] = None
    cantidad_necesaria: float
    observaciones: Optional[str] = None
