import uuid
from typing import Optional, List

from sqlmodel import Session, select

from app.models.usuario import Usuario


class UsuarioRepository:

    def __init__(self, session: Session):
        self.session = session

    # ── Crear ───────────────────────────────────────

    def add(self, usuario: Usuario) -> Usuario:
        self.session.add(usuario)
        self.session.flush()
        self.session.refresh(usuario)
        return usuario

    # ── Buscar ──────────────────────────────────────

    def get_by_id(self, user_id: uuid.UUID) -> Optional[Usuario]:
        return self.session.get(Usuario, user_id)

    def get_by_email(self, email: str) -> Optional[Usuario]:
        statement = select(Usuario).where(
            Usuario.email == email,
        )
        return self.session.exec(statement).first()

    # ── Listar ──────────────────────────────────────

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Usuario]:
        statement = (
            select(Usuario)
            .offset(skip)
            .limit(limit)
            .order_by(Usuario.nombre)
        )
        return list(self.session.exec(statement).all())

    # ── Actualizar ──────────────────────────────────

    def save(self, usuario: Usuario) -> Usuario:
        self.session.flush()
        self.session.refresh(usuario)
        return usuario

    # ── Eliminar ────────────────────────────────────

    def delete(self, usuario: Usuario) -> None:
        self.session.delete(usuario)
        self.session.flush()
