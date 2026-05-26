import uuid
from typing import Optional, List

from sqlmodel import Session, select, col

from app.models.area import Area


class AreaRepository:

    def __init__(self, session: Session):
        self.session = session

    # ── Crear ───────────────────────────────────────

    def add(self, area: Area) -> Area:
        self.session.add(area)
        self.session.flush()
        self.session.refresh(area)
        return area

    # ── Buscar ──────────────────────────────────────

    def get_by_id(self, area_id: uuid.UUID) -> Optional[Area]:
        return self.session.get(Area, area_id)

    def get_by_nombre(self, nombre: str) -> Optional[Area]:
        statement = select(Area).where(
            Area.nombre == nombre,
        )
        return self.session.exec(statement).first()

    # ── Listar ──────────────────────────────────────

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Area]:
        statement = (
            select(Area)
            .offset(skip)
            .limit(limit)
            .order_by(Area.nombre)
        )
        return list(self.session.exec(statement).all())

    def search_by_nombre(
        self,
        texto: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Area]:
        statement = (
            select(Area)
            .where(col(Area.nombre).contains(texto))
            .offset(skip)
            .limit(limit)
            .order_by(Area.nombre)
        )
        return list(self.session.exec(statement).all())

    # ── Actualizar ──────────────────────────────────

    def save(self, area: Area) -> Area:
        self.session.flush()
        self.session.refresh(area)
        return area

    # ── Eliminar ────────────────────────────────────

    def delete(self, area: Area) -> None:
        self.session.delete(area)
        self.session.flush()
