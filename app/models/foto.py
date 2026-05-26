import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field, Relationship

from app.models.enums import TipoFotoEnum


class Foto(SQLModel, table=True):
    __tablename__ = "fotos"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )
    equipo_id: uuid.UUID = Field(
        foreign_key="equipos.id",
        index=True,
    )

    # Datos de Cloudinary
    cloudinary_id: str = Field(max_length=255)
    url: str = Field(max_length=500)
    thumbnail_url: Optional[str] = Field(
        default=None,
        max_length=500,
    )

    # Metadata de la foto
    tipo_foto: TipoFotoEnum = Field(
        default=TipoFotoEnum.GENERAL,
    )
    descripcion: Optional[str] = Field(
        default=None,
        max_length=500,
    )
    fecha: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    # Relación
    equipo: Optional["Equipo"] = Relationship(
        back_populates="fotos",
    )
