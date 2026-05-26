import uuid
from typing import Optional, List

from sqlmodel import Session, select

from app.models.historial_cambio import HistorialCambio


class HistorialRepository:

    def __init__(self, session: Session):
        self.session = session

    # ── Crear ───────────────────────────────────────

    def add(self, historial: HistorialCambio) -> HistorialCambio:
        self.session.add(historial)
        self.session.flush()
        self.session.refresh(historial)
        return historial

    # ── Listar por equipo ───────────────────────────

    def get_by_equipo(
        self,
        equipo_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[HistorialCambio]:
        statement = (
            select(HistorialCambio)
            .where(HistorialCambio.equipo_id == equipo_id)
            .offset(skip)
            .limit(limit)
            .order_by(HistorialCambio.fecha.desc())
        )
        return list(self.session.exec(statement).all())
