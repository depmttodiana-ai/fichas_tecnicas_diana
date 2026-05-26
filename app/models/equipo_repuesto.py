import uuid
from typing import Optional

from sqlmodel import SQLModel, Field, Relationship


class EquipoRepuesto(SQLModel, table=True):
    __tablename__ = "equipos_repuestos_necesarios"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )
    equipo_id: uuid.UUID = Field(
        foreign_key="equipos.id",
        index=True,
    )

    # Datos del repuesto
    codigo_repuesto: str = Field(max_length=100)
    descripcion: str = Field(max_length=300)
    para_que: Optional[str] = Field(
        default=None,
        max_length=500,
    )
    ubicacion: Optional[str] = Field(
        default=None,
        max_length=500,
    )
    cantidad_necesaria: float = Field(default=1)
    observaciones: Optional[str] = Field(
        default=None,
        max_length=500,
    )

    # Relación
    equipo: Optional["Equipo"] = Relationship(
        back_populates="repuestos_necesarios",
    )
