import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TipoFotoEnum


class FotoCreate(BaseModel):
    tipo_foto: TipoFotoEnum = TipoFotoEnum.GENERAL
    descripcion: Optional[str] = Field(
        default=None,
        max_length=500,
    )
    # NOTA: el archivo se recibe como UploadFile
    # en el endpoint, no en este schema.
    # Los datos de Cloudinary (url, cloudinary_id)
    # se agregan después del upload.


class FotoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    equipo_id: uuid.UUID
    cloudinary_id: str
    url: str
    thumbnail_url: Optional[str] = None
    tipo_foto: TipoFotoEnum
    descripcion: Optional[str] = None
    fecha: datetime


class FotoList(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    thumbnail_url: Optional[str] = None
    url: str
    tipo_foto: TipoFotoEnum
