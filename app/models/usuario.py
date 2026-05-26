import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field

from app.models.enums import RolEnum


class Usuario(SQLModel, table=True):
    __tablename__ = "usuarios"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )
    nombre: str = Field(max_length=100)
    email: str = Field(
        max_length=150,
        unique=True,
        index=True,
    )
    password_hash: str = Field(max_length=255)
    rol: RolEnum = Field(default=RolEnum.USUARIO)
    activo: bool = Field(default=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
