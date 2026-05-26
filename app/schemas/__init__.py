from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    MeResponse,
)
from app.schemas.usuario import (
    UsuarioCreate,
    UsuarioUpdate,
    UsuarioRead,
    UsuarioList,
)
from app.schemas.area import (
    AreaCreate,
    AreaUpdate,
    AreaRead,
    AreaList,
)
from app.schemas.clasificacion import (
    ClasificacionCreate,
    ClasificacionUpdate,
    ClasificacionRead,
    ClasificacionList,
)
from app.schemas.equipo import (
    EquipoCreate,
    EquipoUpdate,
    EquipoRead,
    EquipoList,
    EquipoArbolRead,
    EquipoCambioEstado,
    SubEquipoRead,
)
from app.schemas.foto import (
    FotoCreate,
    FotoRead,
    FotoList,
)
from app.schemas.mantenimiento import (
    MantenimientoCreate,
    MantenimientoUpdate,
    MantenimientoRead,
    MantenimientoList,
    RepuestoUsadoCreate,
    RepuestoUsadoRead,
)
from app.schemas.historial import (
    HistorialRead,
)
from app.schemas.filtros import (
    FiltroEquipos,
    FiltroMantenimientos,
    Paginacion,
)
