import uuid
from datetime import date
from typing import Optional, List

from sqlmodel import Session, select, col, and_

from app.models.equipo import Equipo
from app.models.enums import EstadoEquipoEnum


class EquipoRepository:

    def __init__(self, session: Session):
        self.session = session

    # ── Crear ───────────────────────────────────────

    def add(self, equipo: Equipo) -> Equipo:
        self.session.add(equipo)
        self.session.flush()
        self.session.refresh(equipo)
        return equipo

    # ── Buscar ──────────────────────────────────────

    def get_by_id(self, equipo_id: uuid.UUID) -> Optional[Equipo]:
        return self.session.get(Equipo, equipo_id)

    def get_by_codigo(
        self,
        codigo: str,
    ) -> Optional[Equipo]:
        statement = select(Equipo).where(
            Equipo.codigo_equipo == codigo,
        )
        return self.session.exec(statement).first()

    # ── Listar con filtros ──────────────────────────

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Equipo]:
        statement = (
            select(Equipo)
            .offset(skip)
            .limit(limit)
            .order_by(Equipo.nombre)
        )
        return list(self.session.exec(statement).all())

    def filter(
        self,
        nombre: Optional[str] = None,
        codigo: Optional[str] = None,
        area_id: Optional[uuid.UUID] = None,
        clasificacion_id: Optional[uuid.UUID] = None,
        equipo_padre_id: Optional[uuid.UUID] = None,
        estado: Optional[EstadoEquipoEnum] = None,
        nivel: Optional[int] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Equipo]:
        """Construye query dinámica con filtros opcionales."""
        conditions = []

        if nombre is not None:
            conditions.append(
                col(Equipo.nombre).contains(nombre),
            )
        if codigo is not None:
            conditions.append(
                col(Equipo.codigo_equipo).contains(codigo),
            )
        if area_id is not None:
            conditions.append(
                Equipo.area_id == area_id,
            )
        if clasificacion_id is not None:
            conditions.append(
                Equipo.clasificacion_id == clasificacion_id,
            )
        if equipo_padre_id is not None:
            conditions.append(
                Equipo.equipo_padre_id == equipo_padre_id,
            )
        if estado is not None:
            conditions.append(
                Equipo.estado == estado,
            )
        if nivel is not None:
            conditions.append(
                Equipo.nivel == nivel,
            )
        if fecha_desde is not None:
            conditions.append(
                Equipo.created_at >= fecha_desde,
            )
        if fecha_hasta is not None:
            conditions.append(
                Equipo.created_at <= fecha_hasta,
            )

        statement = select(Equipo)

        if conditions:
            statement = statement.where(and_(*conditions))

        statement = (
            statement
            .offset(skip)
            .limit(limit)
            .order_by(Equipo.nombre)
        )

        return list(self.session.exec(statement).all())

    # ── Jerarquía (árbol) ───────────────────────────

    def get_hijos_directos(
        self,
        padre_id: uuid.UUID,
    ) -> List[Equipo]:
        """Obtiene los hijos directos de un equipo."""
        statement = (
            select(Equipo)
            .where(Equipo.equipo_padre_id == padre_id)
            .order_by(Equipo.nombre)
        )
        return list(self.session.exec(statement).all())

    def get_raices(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Equipo]:
        """Equipos sin padre (nivel 1)."""
        statement = (
            select(Equipo)
            .where(Equipo.equipo_padre_id.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(Equipo.nombre)
        )
        return list(self.session.exec(statement).all())

    def tiene_hijos(self, equipo_id: uuid.UUID) -> bool:
        """Verifica si un equipo tiene sub-equipos."""
        statement = (
            select(Equipo)
            .where(Equipo.equipo_padre_id == equipo_id)
        )
        result = self.session.exec(statement).first()
        return result is not None

    # ── Actualizar ──────────────────────────────────

    def save(self, equipo: Equipo) -> Equipo:
        self.session.flush()
        self.session.refresh(equipo)
        return equipo

    # ── Eliminar ────────────────────────────────────

    def delete(self, equipo: Equipo) -> None:
        self.session.delete(equipo)
        self.session.flush()

    # ── Conteos ─────────────────────────────────────

    def count_all(self) -> int:
        statement = select(Equipo)
        return len(list(self.session.exec(statement).all()))

    def count_by_estado(
        self,
        estado: EstadoEquipoEnum,
    ) -> int:
        statement = select(Equipo).where(
            Equipo.estado == estado,
        )
        return len(list(self.session.exec(statement).all()))
