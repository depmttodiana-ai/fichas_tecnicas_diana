from typing import List
import uuid

from fastapi import HTTPException, UploadFile, status
from sqlmodel import Session

from app.models.foto import Foto
from app.repositories.foto import FotoRepository
from app.repositories.equipo import EquipoRepository
from app.schemas.foto import FotoCreate, FotoRead, FotoList
from app.core.storage import upload_image, delete_image


class FotoService:

    def __init__(self, session: Session):
        self.session = session
        self.repo = FotoRepository(session)
        self.equipo_repo = EquipoRepository(session)

    async def upload(
        self,
        equipo_id: uuid.UUID,
        file: UploadFile,
        body: FotoCreate,
    ) -> FotoRead:

        equipo = self.equipo_repo.get_by_id(equipo_id)
        if not equipo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Equipo no encontrado",
            )

        if not file.content_type or not file.content_type.startswith(
            "image/",
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo debe ser una imagen",
            )

        file_bytes = await file.read()

        # Ahora usa storage.py (local o cloudinary)
        result = upload_image(
            file_bytes,
            folder=f"fichas-tecnicas/{equipo.codigo_equipo}",
            filename=file.filename,
        )

        foto = Foto(
            equipo_id=equipo_id,
            cloudinary_id=result["public_id"],
            url=result["url"],
            thumbnail_url=result["thumbnail_url"],
            tipo_foto=body.tipo_foto,
            descripcion=body.descripcion,
        )

        foto_creada = self.repo.add(foto)
        return FotoRead.model_validate(foto_creada)

    def get_by_equipo(
        self,
        equipo_id: uuid.UUID,
    ) -> List[FotoList]:
        equipo = self.equipo_repo.get_by_id(equipo_id)
        if not equipo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Equipo no encontrado",
            )

        fotos = self.repo.get_by_equipo(equipo_id)
        return [FotoList.model_validate(f) for f in fotos]

    def delete(self, foto_id: uuid.UUID) -> None:
        foto = self.repo.get_by_id(foto_id)
        if not foto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Foto no encontrada",
            )

        delete_image(foto.cloudinary_id)
        self.repo.delete(foto)
