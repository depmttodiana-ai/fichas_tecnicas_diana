from typing import List

from fastapi import APIRouter, Depends

from app.core.dependencies import CurrentUser, SessionDep
from app.repositories.equipo_repuesto import EquipoRepuestoRepository
from app.schemas.equipo_repuesto import EquipoRepuestoRead

router = APIRouter()


@router.get("/", response_model=List[EquipoRepuestoRead])
def listar_todos_repuestos(
    session: SessionDep,
    user: CurrentUser,
):
    repo = EquipoRepuestoRepository(session)
    repuestos = repo.get_all()
    return [EquipoRepuestoRead.model_validate(r) for r in repuestos]
