import uuid
from datetime import datetime, timezone, date
from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship

from app.models.enums import (
    TipoMantenimientoEnum,
    EstadoMantenimientoEnum,
)


class Mantenimiento(SQLModel, table=True):
    __tablename__ = "mantenimientos"

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

    # Datos del mantenimiento
    tipo: TipoMantenimientoEnum
    titulo: str = Field(max_length=200)
    descripcion: Optional[str] = Field(default=None)
    trabajo_realizado: Optional[str] = Field(default=None)

    # Estado
    estado: EstadoMantenimientoEnum = Field(
        default=EstadoMantenimientoEnum.REALIZADO,
    )

    # Fechas
    fecha: date = Field(
        default_factory=lambda: datetime.now(timezone.utc).date(),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    # Relaciones
    equipo: Optional["Equipo"] = Relationship(
        back_populates="mantenimientos",
    )
    repuestos_usados: List["MantenimientoRepuesto"] = Relationship(
        back_populates="mantenimiento",
    )
