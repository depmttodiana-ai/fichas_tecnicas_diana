from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.dependencies import CurrentUser, SessionDep
from app.core.security import verify_password, create_access_token
from app.repositories.usuario import UsuarioRepository
from app.schemas.auth import LoginRequest, LoginResponse, MeResponse
from app.schemas.usuario import UsuarioCreate, UsuarioRead
from app.services.auth import AuthService

router = APIRouter()


@router.post("/register", response_model=UsuarioRead, status_code=201)
def register(
    body: UsuarioCreate,
    session: SessionDep,
):
    service = AuthService(session)
    usuario = service.register(body)
    session.commit()
    return usuario


@router.post("/login", response_model=LoginResponse)
def login(
    body: LoginRequest,
    session: SessionDep,
):
    service = AuthService(session)
    resultado = service.login(body)
    return resultado


@router.post("/login-swagger", include_in_schema=False)
def login_swagger(
    session: SessionDep,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    repo = UsuarioRepository(session)

    usuario = repo.get_by_email(form_data.username)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado",
        )

    if not verify_password(form_data.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    token = create_access_token(
        data={
            "sub": str(usuario.id),
            "rol": usuario.rol.value,
        },
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }



@router.get("/me", response_model=MeResponse)
def me(
    current_user: CurrentUser,
    session: SessionDep,
):
    service = AuthService(session)
    return service.get_me(current_user)
