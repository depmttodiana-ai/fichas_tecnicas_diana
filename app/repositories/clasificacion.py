import uuid
from typing import Optional, List

from sqlmodel import Session, select, col

from app.models.clasificacion import ClasificacionEquipo


class ClasificacionRepository:

    def __init__(self, session: Session):
        self.session = session

    # ── Crear ───────────────────────────────────────

    def add(self, clasificacion: ClasificacionEquipo) -> ClasificacionEquipo:
        self.session.add(clasificacion)
        self.session.flush()
        self.session.refresh(clasificacion)
        return clasificacion

    # ── Buscar ──────────────────────────────────────

    def get_by_id(
        self,
        clasificacion_id: uuid.UUID,
    ) -> Optional[ClasificacionEquipo]:
        return self.session.get(
            ClasificacionEquipo,
            clasificacion_id,
        )

    def get_by_nombre(self, nombre: str) -> Optional[ClasificacionEquipo]:
        statement = select(ClasificacionEquipo).where(
            ClasificacionEquipo.nombre == nombre,
        )
        return self.session.exec(statement).first()

    # ── Listar ──────────────────────────────────────

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ClasificacionEquipo]:
        statement = (
            select(ClasificacionEquipo)
            .offset(skip)
            .limit(limit)
            .order_by(ClasificacionEquipo.nombre)
        )
        return list(self.session.exec(statement).all())

    def search_by_nombre(
        self,
        texto: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ClasificacionEquipo]:
        statement = (
            select(ClasificacionEquipo)
            .where(
                col(ClasificacionEquipo.nombre).contains(texto),
            )
            .offset(skip)
            .limit(limit)
            .order_by(ClasificacionEquipo.nombre)
        )
        return list(self.session.exec(statement).all())

    # ── Actualizar ──────────────────────────────────

    def save(
        self,
        clasificacion: ClasificacionEquipo,
    ) -> ClasificacionEquipo:
        self.session.flush()
        self.session.refresh(clasificacion)
        return clasificacion

    # ── Eliminar ────────────────────────────────────

    def delete(self, clasificacion: ClasificacionEquipo) -> None:
        self.session.delete(clasificacion)
        self.session.flush()
