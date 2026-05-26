import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field, Relationship


class HistorialCambio(SQLModel, table=True):
    __tablename__ = "historial_cambios"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )
    equipo_id: uuid.UUID = Field(
        foreign_key="equipos.id",
        index=True,
    )
    usuario_id: Optional[uuid.UUID] = Field(
        default=None,
        foreign_key="usuarios.id",
    )

    # Datos del cambio
    campo: str = Field(max_length=100)
    valor_anterior: Optional[str] = Field(default=None)
    valor_nuevo: Optional[str] = Field(default=None)
    observacion: Optional[str] = Field(default=None)

    # Fecha
    fecha: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    # Relación
    equipo: Optional["Equipo"] = Relationship(
        back_populates="historial_cambios",
    )
