from typing import List
import uuid

from fastapi import HTTPException, status
from sqlmodel import Session

from app.models.clasificacion import ClasificacionEquipo
from app.repositories.clasificacion import ClasificacionRepository
from app.schemas.clasificacion import (
    ClasificacionCreate,
    ClasificacionUpdate,
    ClasificacionRead,
    ClasificacionList,
)


class ClasificacionService:

    def __init__(self, session: Session):
        self.session = session
        self.repo = ClasificacionRepository(session)

    def create(
        self,
        body: ClasificacionCreate,
    ) -> ClasificacionRead:
        existente = self.repo.get_by_nombre(body.nombre)
        if existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe la clasificación '{body.nombre}'",
            )

        clasificacion = ClasificacionEquipo(**body.model_dump())
        clasificacion_creada = self.repo.add(clasificacion)
        return ClasificacionRead.model_validate(clasificacion_creada)

    def get_by_id(
        self,
        clasificacion_id: uuid.UUID,
    ) -> ClasificacionRead:
        clasificacion = self.repo.get_by_id(clasificacion_id)
        if not clasificacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Clasificación no encontrada",
            )
        return ClasificacionRead.model_validate(clasificacion)

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ClasificacionList]:
        clasificaciones = self.repo.get_all(
            skip=skip,
            limit=limit,
        )
        return [
            ClasificacionList.model_validate(c)
            for c in clasificaciones
        ]

    def search(
        self,
        texto: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ClasificacionList]:
        clasificaciones = self.repo.search_by_nombre(
            texto,
            skip=skip,
            limit=limit,
        )
        return [
            ClasificacionList.model_validate(c)
            for c in clasificaciones
        ]

    def update(
        self,
        clasificacion_id: uuid.UUID,
        body: ClasificacionUpdate,
    ) -> ClasificacionRead:
        clasificacion = self.repo.get_by_id(clasificacion_id)
        if not clasificacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Clasificación no encontrada",
            )

        if body.nombre and body.nombre != clasificacion.nombre:
            existente = self.repo.get_by_nombre(body.nombre)
            if existente:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ya existe la clasificación '{body.nombre}'",
                )

        update_data = body.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(clasificacion, field, value)

        clasificacion_actualizada = self.repo.save(clasificacion)
        return ClasificacionRead.model_validate(
            clasificacion_actualizada,
        )

    def delete(self, clasificacion_id: uuid.UUID) -> None:
        clasificacion = self.repo.get_by_id(clasificacion_id)
        if not clasificacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Clasificación no encontrada",
            )
        self.repo.delete(clasificacion)
