import uuid
from typing import List, Optional

from sqlmodel import Session, select

from app.models.equipo_repuesto import EquipoRepuesto


class EquipoRepuestoRepository:

    def __init__(self, session: Session):
        self.session = session

    def add(
        self,
        repuesto: EquipoRepuesto,
    ) -> EquipoRepuesto:
        self.session.add(repuesto)
        self.session.flush()
        self.session.refresh(repuesto)
        return repuesto

    def get_by_id(
        self,
        repuesto_id: uuid.UUID,
    ) -> Optional[EquipoRepuesto]:
        return self.session.get(EquipoRepuesto, repuesto_id)

    def get_by_equipo(
        self,
        equipo_id: uuid.UUID,
    ) -> List[EquipoRepuesto]:
        statement = (
            select(EquipoRepuesto)
            .where(EquipoRepuesto.equipo_id == equipo_id)
            .order_by(EquipoRepuesto.descripcion)
        )
        return list(self.session.exec(statement).all())

    def delete(self, repuesto: EquipoRepuesto) -> None:
        self.session.delete(repuesto)
        self.session.flush()

    def delete_by_equipo(self, equipo_id: uuid.UUID) -> None:
        repuestos = self.get_by_equipo(equipo_id)
        for r in repuestos:
            self.session.delete(r)
        self.session.flush()
