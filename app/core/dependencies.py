import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.security import decode_access_token
from app.models.usuario import Usuario
from app.models.enums import RolEnum

# ── Para Swagger: login con email+password ──────────
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login-swagger",
)

# ── Para código externo: Bearer token directo ───────
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[Session, Depends(get_session)],
) -> Usuario:
    """
    Dependency que extrae el usuario actual desde el JWT.
    Swagger pasa el token automáticamente tras login.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id_str: str | None = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    usuario = session.get(Usuario, user_id)
    if usuario is None:
        raise credentials_exception

    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado",
        )

    return usuario


# ── Type alias ──────────────────────────────────────

CurrentUser = Annotated[Usuario, Depends(get_current_user)]
SessionDep = Annotated[Session, Depends(get_session)]


# ── Dependencies por rol ────────────────────────────

def require_roles(*roles: RolEnum):
    def role_checker(user: CurrentUser) -> Usuario:
        if user.rol not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere uno de estos roles: {[r.value for r in roles]}",
            )
        return user
    return role_checker


def require_coordinador(user: CurrentUser) -> Usuario:
    if user.rol != RolEnum.COORDINADOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el coordinador puede realizar esta acción",
        )
    return user


def require_supervisor_or_above(user: CurrentUser) -> Usuario:
    if user.rol not in (RolEnum.COORDINADOR, RolEnum.SUPERVISOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol de coordinador o supervisor",
        )
    return user


def require_editor(user: CurrentUser) -> Usuario:
    if user.rol not in (RolEnum.COORDINADOR, RolEnum.SUPERVISOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para editar",
        )
    return user
