import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship

from app.models.enums import EstadoEquipoEnum


class Equipo(SQLModel, table=True):
    __tablename__ = "equipos"

    # ── PK ──────────────────────────────────────────────
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )

    # ── Identificación ──────────────────────────────────
    codigo_equipo: str = Field(
        max_length=50,
        unique=True,
        index=True,
    )
    nombre: str = Field(
        max_length=200,
        index=True,
    )
    descripcion: Optional[str] = Field(default=None)

    # ── Foreign Keys ────────────────────────────────────
    clasificacion_id: Optional[uuid.UUID] = Field(
        default=None,
        foreign_key="clasificaciones_equipo.id",
    )
    equipo_padre_id: Optional[uuid.UUID] = Field(
        default=None,
        foreign_key="equipos.id",
    )
    area_id: Optional[uuid.UUID] = Field(
        default=None,
        foreign_key="areas.id",
    )
    created_by: Optional[uuid.UUID] = Field(
        default=None,
        foreign_key="usuarios.id",
    )
    updated_by: Optional[uuid.UUID] = Field(
        default=None,
        foreign_key="usuarios.id",
    )

    # ── Nivel jerárquico (flexible) ─────────────────────
    nivel: int = Field(default=1)

    # ── Datos de placa / datasheet ──────────────────────
    marca: Optional[str] = Field(default=None, max_length=100)
    modelo: Optional[str] = Field(default=None, max_length=100)
    numero_serie: Optional[str] = Field(default=None, max_length=100)
    potencia: Optional[str] = Field(default=None, max_length=50)
    voltaje: Optional[str] = Field(default=None, max_length=50)
    rpm: Optional[str] = Field(default=None, max_length=50)
    capacidad: Optional[str] = Field(default=None, max_length=50)
    anio_fabricacion: Optional[int] = Field(default=None)
    proveedor: Optional[str] = Field(default=None, max_length=150)
    fecha_adquisicion: Optional[datetime] = Field(default=None)

    # ── Estado ──────────────────────────────────────────
    estado: EstadoEquipoEnum = Field(
        default=EstadoEquipoEnum.OPERATIVO,
        index=True,
    )
    motivo_estado: Optional[str] = Field(default=None)

    # ── Metadatos ───────────────────────────────────────
    observaciones: Optional[str] = Field(default=None)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    # ── Relaciones ──────────────────────────────────────

    # Jerarquía recursiva (padre ↔ hijos)
    equipo_padre: Optional["Equipo"] = Relationship(
        back_populates="sub_equipos",
        sa_relationship_kwargs={
            "remote_side": "[Equipo.id]",
        },
    )
    sub_equipos: List["Equipo"] = Relationship(
        back_populates="equipo_padre",
    )

    # Clasificación
    clasificacion: Optional["ClasificacionEquipo"] = Relationship(
        back_populates="equipos",
    )

    # Área / ubicación
    area: Optional["Area"] = Relationship(
        back_populates="equipos",
    )

    # Fotografías
    fotos: List["Foto"] = Relationship(
        back_populates="equipo",
    )

    # Mantenimientos realizados
    mantenimientos: List["Mantenimiento"] = Relationship(
        back_populates="equipo",
    )

    # Historial de cambios
    historial_cambios: List["HistorialCambio"] = Relationship(
        back_populates="equipo",
    )

    # Registros donde este equipo fue usado como repuesto
    registros_como_repuesto: List["MantenimientoRepuesto"] = Relationship(
        back_populates="repuesto",
    )
      # Repuestos necesarios para este equipo
    repuestos_necesarios: List["EquipoRepuesto"] = Relationship(
        back_populates="equipo",
    )
