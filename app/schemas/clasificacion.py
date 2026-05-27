import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ClasificacionCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    descripcion: Optional[str] = Field(
        default=None,
        max_length=500,
    )


class ClasificacionUpdate(BaseModel):
    nombre: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    descripcion: Optional[str] = Field(
        default=None,
        max_length=500,
    )


class ClasificacionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nombre: str
    descripcion: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ClasificacionList(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nombre: str
    descripcion: Optional[str] = None
