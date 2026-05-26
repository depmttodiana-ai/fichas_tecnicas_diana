from typing import List
import uuid

from fastapi import HTTPException, status
from sqlmodel import Session

from app.models.area import Area
from app.repositories.area import AreaRepository
from app.schemas.area import (
    AreaCreate,
    AreaUpdate,
    AreaRead,
    AreaList,
)


class AreaService:

    def __init__(self, session: Session):
        self.session = session
        self.repo = AreaRepository(session)

    def create(self, body: AreaCreate) -> AreaRead:
        # Verificar nombre único
        existente = self.repo.get_by_nombre(body.nombre)
        if existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un área con el nombre '{body.nombre}'",
            )

        area = Area(**body.model_dump())
        area_creada = self.repo.add(area)
        return AreaRead.model_validate(area_creada)

    def get_by_id(self, area_id: uuid.UUID) -> AreaRead:
        area = self.repo.get_by_id(area_id)
        if not area:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Área no encontrada",
            )
        return AreaRead.model_validate(area)

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AreaList]:
        areas = self.repo.get_all(skip=skip, limit=limit)
        return [AreaList.model_validate(a) for a in areas]

    def search(
        self,
        texto: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AreaList]:
        areas = self.repo.search_by_nombre(
            texto,
            skip=skip,
            limit=limit,
        )
        return [AreaList.model_validate(a) for a in areas]

    def update(
        self,
        area_id: uuid.UUID,
        body: AreaUpdate,
    ) -> AreaRead:
        area = self.repo.get_by_id(area_id)
        if not area:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Área no encontrada",
            )

        # Si cambia nombre, verificar único
        if body.nombre and body.nombre != area.nombre:
            existente = self.repo.get_by_nombre(body.nombre)
            if existente:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ya existe un área con el nombre '{body.nombre}'",
                )

        update_data = body.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(area, field, value)

        area_actualizada = self.repo.save(area)
        return AreaRead.model_validate(area_actualizada)

    def delete(self, area_id: uuid.UUID) -> None:
        area = self.repo.get_by_id(area_id)
        if not area:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Área no encontrada",
            )
        self.repo.delete(area)
