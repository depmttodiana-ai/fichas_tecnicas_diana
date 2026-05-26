from enum import Enum


class RolEnum(str, Enum):
    COORDINADOR = "COORDINADOR"
    SUPERVISOR = "SUPERVISOR"
    USUARIO = "USUARIO"


class EstadoEquipoEnum(str, Enum):
    OPERATIVO = "OPERATIVO"
    PARADO = "PARADO"
    REPARACION = "REPARACION"
    BAJA = "BAJA"


class TipoFotoEnum(str, Enum):
    PLACA = "PLACA"
    GENERAL = "GENERAL"
    FALLA = "FALLA"
    DETALLE = "DETALLE"


class TipoMantenimientoEnum(str, Enum):
    PREVENTIVO = "PREVENTIVO"
    CORRECTIVO = "CORRECTIVO"
    EMERGENCIA = "EMERGENCIA"


class EstadoMantenimientoEnum(str, Enum):
    REALIZADO = "REALIZADO"
    PENDIENTE = "PENDIENTE"


# Mapeo de referencia para niveles de equipo
# El front puede usar esto para mostrar nombres
NIVEL_EQUIPO_NOMBRES: dict[int, str] = {
    1: "Equipo Principal",
    2: "Equipo Secundario",
    3: "Componente",
    4: "Repuesto",
}
