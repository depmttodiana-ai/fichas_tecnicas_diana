from app.models import RolEnum
from fastapi import HTTPException, status
from sqlmodel import Session

from app.models.usuario import Usuario
from app.repositories.usuario import UsuarioRepository
from app.schemas.auth import LoginRequest, LoginResponse, MeResponse
from app.schemas.usuario import UsuarioCreate, UsuarioRead
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)


class AuthService:

    def __init__(self, session: Session):
        self.session = session
        self.repo = UsuarioRepository(session)

    def register(self, body: UsuarioCreate) -> UsuarioRead:
    

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
            rol=RolEnum.USUARIO,  # ← SIEMPRE USUARIO, ignora cualquier otro valor
        )
    
        usuario_creado = self.repo.add(usuario)
        return UsuarioRead.model_validate(usuario_creado)

    def login(self, body: LoginRequest) -> LoginResponse:
        """Autentica un usuario y retorna JWT."""

        # Buscar usuario por email
        usuario = self.repo.get_by_email(body.email)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
            )

        # Verificar que esté activo
        if not usuario.activo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario desactivado",
            )

        # Verificar password
        if not verify_password(body.password, usuario.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
            )

        # Generar JWT
        token = create_access_token(
            data={
                "sub": str(usuario.id),
                "rol": usuario.rol.value,
            },
        )

        # Construir respuesta
        me = MeResponse.model_validate(usuario)

        return LoginResponse(
            access_token=token,
            token_type="bearer",
            usuario=me,
        )

    def get_me(self, usuario: Usuario) -> MeResponse:
        """Retorna los datos del usuario actual."""
        return MeResponse.model_validate(usuario)
