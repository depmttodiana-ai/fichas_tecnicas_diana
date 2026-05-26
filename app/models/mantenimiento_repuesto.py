import uuid
from typing import Optional

from sqlmodel import SQLModel, Field, Relationship


class MantenimientoRepuesto(SQLModel, table=True):
    __tablename__ = "mantenimientos_repuestos"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )
    mantenimiento_id: uuid.UUID = Field(
        foreign_key="mantenimientos.id",
        index=True,
    )
    repuesto_id: uuid.UUID = Field(
        foreign_key="equipos.id",
        index=True,
    )

    # Datos del uso
    cantidad_usada: float = Field(default=1)
    observacion: Optional[str] = Field(
        default=None,
        max_length=500,
    )

    # Relaciones
    mantenimiento: Optional["Mantenimiento"] = Relationship(
        back_populates="repuestos_usados",
    )
    repuesto: Optional["Equipo"] = Relationship(
        back_populates="registros_como_repuesto",
    )
