import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class HistorialRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    equipo_id: uuid.UUID
    usuario_id: Optional[uuid.UUID] = None
    nombre_usuario: Optional[str] = None

    campo: str
    valor_anterior: Optional[str] = None
    valor_nuevo: Optional[str] = None
    observacion: Optional[str] = None
    fecha: datetime
