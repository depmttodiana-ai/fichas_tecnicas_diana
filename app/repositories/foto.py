import uuid
from typing import Optional, List

from sqlmodel import Session, select

from app.models.foto import Foto
from app.models.enums import TipoFotoEnum


class FotoRepository:

    def __init__(self, session: Session):
        self.session = session

    # ── Crear ───────────────────────────────────────

    def add(self, foto: Foto) -> Foto:
        self.session.add(foto)
        self.session.flush()
        self.session.refresh(foto)
        return foto

    # ── Buscar ──────────────────────────────────────

    def get_by_id(self, foto_id: uuid.UUID) -> Optional[Foto]:
        return self.session.get(Foto, foto_id)

    # ── Listar por equipo ───────────────────────────

    def get_by_equipo(
        self,
        equipo_id: uuid.UUID,
    ) -> List[Foto]:
        statement = (
            select(Foto)
            .where(Foto.equipo_id == equipo_id)
            .order_by(Foto.fecha.desc())
        )
        return list(self.session.exec(statement).all())

    def get_by_equipo_y_tipo(
        self,
        equipo_id: uuid.UUID,
        tipo: TipoFotoEnum,
    ) -> List[Foto]:
        statement = (
            select(Foto)
            .where(
                Foto.equipo_id == equipo_id,
                Foto.tipo_foto == tipo,
            )
            .order_by(Foto.fecha.desc())
        )
        return list(self.session.exec(statement).all())

    # ── Eliminar ────────────────────────────────────

    def delete(self, foto: Foto) -> None:
        self.session.delete(foto)
        self.session.flush()
