import uuid
from datetime import date
from typing import Optional, List

from sqlmodel import Session, select, and_, col

from app.models.mantenimiento import Mantenimiento
from app.models.mantenimiento_repuesto import MantenimientoRepuesto
from app.models.enums import (
    TipoMantenimientoEnum,
    EstadoMantenimientoEnum,
)


class MantenimientoRepository:

    def __init__(self, session: Session):
        self.session = session

    # ── Mantenimiento ───────────────────────────────

    def add(
        self,
        mantenimiento: Mantenimiento,
    ) -> Mantenimiento:
        self.session.add(mantenimiento)
        self.session.flush()
        self.session.refresh(mantenimiento)
        return mantenimiento

    def get_by_id(
        self,
        mantenimiento_id: uuid.UUID,
    ) -> Optional[Mantenimiento]:
        return self.session.get(
            Mantenimiento,
            mantenimiento_id,
        )

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Mantenimiento]:
        statement = (
            select(Mantenimiento)
            .offset(skip)
            .limit(limit)
            .order_by(Mantenimiento.fecha.desc())
        )
        return list(self.session.exec(statement).all())

    def filter(
        self,
        equipo_id: Optional[uuid.UUID] = None,
        tipo: Optional[TipoMantenimientoEnum] = None,
        estado: Optional[EstadoMantenimientoEnum] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        usuario_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Mantenimiento]:
        conditions = []

        if equipo_id is not None:
            conditions.append(
                Mantenimiento.equipo_id == equipo_id,
            )
        if tipo is not None:
            conditions.append(
                Mantenimiento.tipo == tipo,
            )
        if estado is not None:
            conditions.append(
                Mantenimiento.estado == estado,
            )
        if fecha_desde is not None:
            conditions.append(
                Mantenimiento.fecha >= fecha_desde,
            )
        if fecha_hasta is not None:
            conditions.append(
                Mantenimiento.fecha <= fecha_hasta,
            )
        if usuario_id is not None:
            conditions.append(
                Mantenimiento.usuario_id == usuario_id,
            )

        statement = select(Mantenimiento)

        if conditions:
            statement = statement.where(and_(*conditions))

        statement = (
            statement
            .offset(skip)
            .limit(limit)
            .order_by(Mantenimiento.fecha.desc())
        )

        return list(self.session.exec(statement).all())

    def get_by_equipo(
        self,
        equipo_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Mantenimiento]:
        statement = (
            select(Mantenimiento)
            .where(Mantenimiento.equipo_id == equipo_id)
            .offset(skip)
            .limit(limit)
            .order_by(Mantenimiento.fecha.desc())
        )
        return list(self.session.exec(statement).all())

    def save(
        self,
        mantenimiento: Mantenimiento,
    ) -> Mantenimiento:
        self.session.flush()
        self.session.refresh(mantenimiento)
        return mantenimiento

    def delete(
        self,
        mantenimiento: Mantenimiento,
    ) -> None:
        self.session.delete(mantenimiento)
        self.session.flush()

    # ── Repuestos usados ────────────────────────────

    def add_repuesto_usado(
        self,
        repuesto_usado: MantenimientoRepuesto,
    ) -> MantenimientoRepuesto:
        self.session.add(repuesto_usado)
        self.session.flush()
        self.session.refresh(repuesto_usado)
        return repuesto_usado

    def get_repuestos_by_mantenimiento(
        self,
        mantenimiento_id: uuid.UUID,
    ) -> List[MantenimientoRepuesto]:
        statement = (
            select(MantenimientoRepuesto)
            .where(
                MantenimientoRepuesto.mantenimiento_id
                == mantenimiento_id,
            )
        )
        return list(self.session.exec(statement).all())

    def delete_repuestos_by_mantenimiento(
        self,
        mantenimiento_id: uuid.UUID,
    ) -> None:
        repuestos = self.get_repuestos_by_mantenimiento(
            mantenimiento_id,
        )
        for repuesto in repuestos:
            self.session.delete(repuesto)
        self.session.flush()
