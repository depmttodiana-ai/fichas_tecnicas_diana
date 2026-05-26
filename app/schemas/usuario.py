import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, EmailStr

from app.models.enums import RolEnum


# ── SCHEMA PARA REGISTRO (sin rol, siempre USUARIO) ──

class UsuarioCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=5, max_length=150)
    password: str = Field(min_length=8, max_length=128)
    # NO incluye rol, siempre será USUARIO por defecto


# ── SCHEMA PARA CREAR USUARIO DESDE COORDINADOR ──

class UsuarioCreateByAdmin(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=5, max_length=150)
    password: str = Field(min_length=8, max_length=128)
    rol: RolEnum = RolEnum.USUARIO  # Puede elegir rol


# ── SCHEMA PARA ACTUALIZAR (rol solo por admin) ──

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    email: Optional[str] = Field(
        default=None,
        min_length=5,
        max_length=150,
    )
    password: Optional[str] = Field(
        default=None,
        min_length=8,
        max_length=128,
    )
    rol: Optional[RolEnum] = None     # Solo coord. puede enviar esto
    activo: Optional[bool] = None



class UsuarioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nombre: str
    email: EmailStr
    rol: RolEnum
    activo: bool
    created_at: datetime
    updated_at: datetime


class UsuarioList(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nombre: str
    email: EmailStr
    rol: RolEnum
    activo: bool
