from fastapi import APIRouter

from app.api.router.auth import router as auth_router
from app.api.router.usuarios import router as usuarios_router
from app.api.router.areas import router as areas_router
from app.api.router.clasificaciones import router as clasificaciones_router
from app.api.router.equipos import router as equipos_router
from app.api.router.repuestos import router as repuestos_router
from app.api.router.fotos import router as fotos_router
from app.api.router.mantenimientos import router as mantenimientos_router
from app.api.router.historial import router as historial_router
from app.api.router.reportes import router as reportes_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Autenticación"])
api_router.include_router(usuarios_router, prefix="/usuarios", tags=["Usuarios"])
api_router.include_router(areas_router, prefix="/areas", tags=["Áreas"])
api_router.include_router(clasificaciones_router, prefix="/clasificaciones", tags=["Clasificaciones"])
api_router.include_router(equipos_router, prefix="/equipos", tags=["Equipos"])
api_router.include_router(repuestos_router, prefix="/repuestos", tags=["Repuestos"])
api_router.include_router(fotos_router, prefix="/fotos", tags=["Fotografías"])
api_router.include_router(mantenimientos_router, prefix="/mantenimientos", tags=["Mantenimientos"])
api_router.include_router(historial_router, prefix="/historial", tags=["Historial de Cambios"])
api_router.include_router(reportes_router, prefix="/reportes", tags=["Reportes"])
