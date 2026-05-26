from typing import List
import uuid

from fastapi import HTTPException, status
from sqlmodel import Session

from app.models.usuario import Usuario
from app.repositories.usuario import UsuarioRepository
from app.schemas.usuario import (
    UsuarioCreate,
    UsuarioUpdate,
    UsuarioRead,
    UsuarioList,
    UsuarioCreateByAdmin,
)
from app.core.security import hash_password


class UsuarioService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = UsuarioRepository(session)

    def create_by_admin(
        self,
        body: UsuarioCreateByAdmin,
    ) -> UsuarioRead:
        """Crea usuario con rol específico (solo coord.)."""

        existente = self.repo.get_by_email(body.email)
        if existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado",
            )

        usuario = Usuario(
            nombre=body.nombre,
            email=body.email,
            password_hash=hash_password(body.password),
            rol=body.rol,  # ← El coord. elige el rol
        )

        usuario_creado = self.repo.add(usuario)
        return UsuarioRead.model_validate(usuario_creado)

    def create(self, body: UsuarioCreate) -> UsuarioRead:
        # Verificar email único
        existente = self.repo.get_by_email(body.email)
        if existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado",
            )

        usuario = Usuario(
            nombre=body.nombre,
            email=body.email,
            password_hash=hash_password(body.password),
            rol=body.rol,
        )

        usuario_creado = self.repo.add(usuario)
        return UsuarioRead.model_validate(usuario_creado)

    def get_by_id(self, usuario_id: uuid.UUID) -> UsuarioRead:
        usuario = self.repo.get_by_id(usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )
        return UsuarioRead.model_validate(usuario)

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[UsuarioList]:
        usuarios = self.repo.get_all(skip=skip, limit=limit)
        return [UsuarioList.model_validate(u) for u in usuarios]

    def update(
        self,
        usuario_id: uuid.UUID,
        body: UsuarioUpdate,
    ) -> UsuarioRead:
        usuario = self.repo.get_by_id(usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )

        # Si cambia el email, verificar que no exista
        if body.email and body.email != usuario.email:
            existente = self.repo.get_by_email(body.email)
            if existente:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El email ya está registrado",
                )

        # Actualizar solo campos que llegaron
        update_data = body.model_dump(exclude_unset=True)

        # Si viene password, hashearlo
        if "password" in update_data:
            update_data["password_hash"] = hash_password(
                update_data.pop("password"),
            )

        for field, value in update_data.items():
            setattr(usuario, field, value)

        usuario_actualizado = self.repo.save(usuario)
        return UsuarioRead.model_validate(usuario_actualizado)

    def delete(self, usuario_id: uuid.UUID) -> None:
        usuario = self.repo.get_by_id(usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )
        self.repo.delete(usuario)
