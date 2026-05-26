import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AreaCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=150)
    codigo: Optional[str] = Field(
        default=None,
        max_length=20,
    )
    descripcion: Optional[str] = Field(
        default=None,
        max_length=500,
    )


class AreaUpdate(BaseModel):
    nombre: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=150,
    )
    codigo: Optional[str] = Field(
        default=None,
        max_length=20,
    )
    descripcion: Optional[str] = Field(
        default=None,
        max_length=500,
    )


class AreaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nombre: str
    codigo: Optional[str] = None
    descripcion: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AreaList(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nombre: str
    codigo: Optional[str] = None
