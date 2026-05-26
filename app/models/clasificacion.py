import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship


class ClasificacionEquipo(SQLModel, table=True):
    __tablename__ = "clasificaciones_equipo"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )
    nombre: str = Field(
        max_length=100,
        unique=True,
        index=True,
    )
    descripcion: Optional[str] = Field(
        default=None,
        max_length=500,
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    # Relación con equipos
    equipos: List["Equipo"] = Relationship(
        back_populates="clasificacion",
    )
