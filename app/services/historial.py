from typing import List
import uuid

from fastapi import HTTPException, status
from sqlmodel import Session

from app.repositories.historial import HistorialRepository
from app.repositories.usuario import UsuarioRepository
from app.repositories.equipo import EquipoRepository
from app.schemas.historial import HistorialRead


class HistorialService:

    def __init__(self, session: Session):
        self.session = session
        self.repo = HistorialRepository(session)
        self.usuario_repo = UsuarioRepository(session)
        self.equipo_repo = EquipoRepository(session)

    def get_by_equipo(
        self,
        equipo_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[HistorialRead]:

        # Verificar que el equipo exista
        equipo = self.equipo_repo.get_by_id(equipo_id)
        if not equipo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Equipo no encontrado",
            )

        historiales = self.repo.get_by_equipo(
            equipo_id,
            skip=skip,
            limit=limit,
        )

        resultado = []
        for h in historiales:
            nombre_usuario = None
            if h.usuario_id:
                usuario = self.usuario_repo.get_by_id(h.usuario_id)
                nombre_usuario = usuario.nombre if usuario else None

            resultado.append(
                HistorialRead(
                    id=h.id,
                    equipo_id=h.equipo_id,
                    usuario_id=h.usuario_id,
                    nombre_usuario=nombre_usuario,
                    campo=h.campo,
                    valor_anterior=h.valor_anterior,
                    valor_nuevo=h.valor_nuevo,
                    observacion=h.observacion,
                    fecha=h.fecha,
                )
            )

        return resultado
