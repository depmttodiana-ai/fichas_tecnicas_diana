import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlmodel import Session

from app.models.equipo import Equipo
from app.models.historial_cambio import HistorialCambio
from app.repositories.equipo import EquipoRepository
from app.repositories.area import AreaRepository
from app.repositories.clasificacion import ClasificacionRepository
from app.repositories.foto import FotoRepository
from app.repositories.historial import HistorialRepository
from app.schemas.equipo import (
    EquipoCreate,
    EquipoUpdate,
    EquipoRead,
    EquipoList,
    EquipoArbolRead,
    EquipoArbolNodo,
    EquipoCambioEstado,
    SubEquipoRead,
)
from app.schemas.foto import FotoList
from app.models.enums import EstadoEquipoEnum


from app.models.equipo_repuesto import EquipoRepuesto
from app.repositories.equipo_repuesto import EquipoRepuestoRepository
from app.schemas.equipo_repuesto import (
    EquipoRepuestoCreate,
    EquipoRepuestoRead,
)

class EquipoService:

    def __init__(self, session: Session):
        self.session = session
        self.repo = EquipoRepository(session)
        self.area_repo = AreaRepository(session)
        self.clasif_repo = ClasificacionRepository(session)
        self.foto_repo = FotoRepository(session)
        self.historial_repo = HistorialRepository(session)
        self.repuesto_repo = EquipoRepuestoRepository(session)  # NUEVO


    # ── CREAR ───────────────────────────────────────

    def create(
        self,
        body: EquipoCreate,
        user_id: uuid.UUID,
    ) -> EquipoRead:

        # Validar código único
        existente = self.repo.get_by_codigo(body.codigo_equipo)
        if existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un equipo con código '{body.codigo_equipo}'",
            )

        # Validar que el área exista
        if body.area_id:
            area = self.area_repo.get_by_id(body.area_id)
            if not area:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El área no existe",
                )

        # Validar que la clasificación exista
        if body.clasificacion_id:
            clasif = self.clasif_repo.get_by_id(body.clasificacion_id)
            if not clasif:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La clasificación no existe",
                )

        # ── AUTO-CALCULAR NIVEL ─────────────────────
        nivel = 1  # Por defecto, equipo raíz

        if body.equipo_padre_id:
            padre = self.repo.get_by_id(body.equipo_padre_id)
            if not padre:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El equipo padre no existe",
                )
            nivel = padre.nivel + 1

        # Crear equipo
        equipo = Equipo(
            codigo_equipo=body.codigo_equipo,
            nombre=body.nombre,
            descripcion=body.descripcion,
            clasificacion_id=body.clasificacion_id,
            equipo_padre_id=body.equipo_padre_id,
            area_id=body.area_id,
            nivel=nivel,
            marca=body.marca,
            modelo=body.modelo,
            numero_serie=body.numero_serie,
            potencia=body.potencia,
            voltaje=body.voltaje,
            rpm=body.rpm,
            capacidad=body.capacidad,
            anio_fabricacion=body.anio_fabricacion,
            proveedor=body.proveedor,
            fecha_adquisicion=body.fecha_adquisicion,
            estado=body.estado,
            motivo_estado=body.motivo_estado,
            observaciones=body.observaciones,
            created_by=user_id,
            updated_by=user_id,
        )

        equipo_creado = self.repo.add(equipo)

        # Registrar en historial
        historial = HistorialCambio(
            equipo_id=equipo_creado.id,
            usuario_id=user_id,
            campo="CREACION",
            valor_anterior=None,
            valor_nuevo=equipo_creado.nombre,
            observacion="Equipo registrado en el sistema",
        )
        self.historial_repo.add(historial)

        return self._build_equipo_read(equipo_creado)

    # ── OBTENER POR ID ──────────────────────────────

    def get_by_id(self, equipo_id: uuid.UUID) -> EquipoRead:
        equipo = self.repo.get_by_id(equipo_id)
        if not equipo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Equipo no encontrado",
            )
        return self._build_equipo_read(equipo)

    # ── OBTENER ÁRBOL ───────────────────────────────

    def get_arbol(
        self,
        equipo_id: uuid.UUID,
    ) -> EquipoArbolRead:
        equipo = self.repo.get_by_id(equipo_id)
        if not equipo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Equipo no encontrado",
            )

        nombre_area = None
        if equipo.area_id:
            area = self.area_repo.get_by_id(equipo.area_id)
            nombre_area = area.nombre if area else None

        nombre_clasif = None
        if equipo.clasificacion_id:
            clasif = self.clasif_repo.get_by_id(
                equipo.clasificacion_id,
            )
            nombre_clasif = clasif.nombre if clasif else None

        hijos = self._build_tree(equipo.id)

        return EquipoArbolRead(
            id=equipo.id,
            codigo_equipo=equipo.codigo_equipo,
            nombre=equipo.nombre,
            nivel=equipo.nivel,
            estado=equipo.estado,
            nombre_area=nombre_area,
            nombre_clasificacion=nombre_clasif,
            hijos=hijos,
        )

    # ── FILTRAR / LISTAR ────────────────────────────

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[EquipoList]:
        equipos = self.repo.get_all(skip=skip, limit=limit)
        return [self._build_equipo_list(e) for e in equipos]

    def get_raices(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[EquipoList]:
        equipos = self.repo.get_raices(skip=skip, limit=limit)
        return [self._build_equipo_list(e) for e in equipos]

    def filter(
        self,
        nombre: Optional[str] = None,
        codigo: Optional[str] = None,
        area_id: Optional[uuid.UUID] = None,
        clasificacion_id: Optional[uuid.UUID] = None,
        equipo_padre_id: Optional[uuid.UUID] = None,
        estado: Optional[EstadoEquipoEnum] = None,
        nivel: Optional[int] = None,
        fecha_desde=None,
        fecha_hasta=None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[EquipoList]:
        equipos = self.repo.filter(
            nombre=nombre,
            codigo=codigo,
            area_id=area_id,
            clasificacion_id=clasificacion_id,
            equipo_padre_id=equipo_padre_id,
            estado=estado,
            nivel=nivel,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            skip=skip,
            limit=limit,
        )
        return [self._build_equipo_list(e) for e in equipos]

    # ── ACTUALIZAR ──────────────────────────────────

    def update(
        self,
        equipo_id: uuid.UUID,
        body: EquipoUpdate,
        user_id: uuid.UUID,
    ) -> EquipoRead:
        equipo = self.repo.get_by_id(equipo_id)
        if not equipo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Equipo no encontrado",
            )

        update_data = body.model_dump(exclude_unset=True)

        if "codigo_equipo" in update_data:
            nuevo_codigo = update_data["codigo_equipo"]
            if nuevo_codigo != equipo.codigo_equipo:
                existente = self.repo.get_by_codigo(nuevo_codigo)
                if existente:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Ya existe equipo con código '{nuevo_codigo}'",
                    )

        if "equipo_padre_id" in update_data:
            padre_id = update_data["equipo_padre_id"]
            if padre_id:
                padre = self.repo.get_by_id(padre_id)
                if not padre:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="El equipo padre no existe",
                    )
                # Auto-actualizar nivel
                update_data["nivel"] = padre.nivel + 1
            else:
                update_data["nivel"] = 1

        if "area_id" in update_data:
            if update_data["area_id"]:
                area = self.area_repo.get_by_id(update_data["area_id"])
                if not area:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="El área no existe",
                    )

        if "clasificacion_id" in update_data:
            if update_data["clasificacion_id"]:
                clasif = self.clasif_repo.get_by_id(
                    update_data["clasificacion_id"],
                )
                if not clasif:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="La clasificación no existe",
                    )

        for field, new_value in update_data.items():
            old_value = getattr(equipo, field, None)
            old_str = str(old_value) if old_value is not None else None
            new_str = str(new_value) if new_value is not None else None

            if old_str != new_str:
                historial = HistorialCambio(
                    equipo_id=equipo.id,
                    usuario_id=user_id,
                    campo=field,
                    valor_anterior=old_str,
                    valor_nuevo=new_str,
                )
                self.historial_repo.add(historial)
                setattr(equipo, field, new_value)

        equipo.updated_by = user_id
        equipo_actualizado = self.repo.save(equipo)

        return self._build_equipo_read(equipo_actualizado)

    # ── CAMBIO DE ESTADO ────────────────────────────

    def change_state(
        self,
        equipo_id: uuid.UUID,
        body: EquipoCambioEstado,
        user_id: uuid.UUID,
    ) -> EquipoRead:
        equipo = self.repo.get_by_id(equipo_id)
        if not equipo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Equipo no encontrado",
            )

        estado_anterior = equipo.estado

        historial = HistorialCambio(
            equipo_id=equipo.id,
            usuario_id=user_id,
            campo="estado",
            valor_anterior=estado_anterior.value,
            valor_nuevo=body.estado.value,
            observacion=body.motivo_estado,
        )
        self.historial_repo.add(historial)

        equipo.estado = body.estado
        equipo.motivo_estado = body.motivo_estado
        equipo.updated_by = user_id

        equipo_actualizado = self.repo.save(equipo)
        return self._build_equipo_read(equipo_actualizado)

    # ── ELIMINAR ────────────────────────────────────

    def delete(self, equipo_id: uuid.UUID) -> None:
        equipo = self.repo.get_by_id(equipo_id)
        if not equipo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Equipo no encontrado",
            )

        if self.repo.tiene_hijos(equipo_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "No se puede eliminar porque tiene "
                    "sub-equipos. Elimine primero los hijos."
                ),
            )

        self.repo.delete(equipo)

    # ── HELPERS PRIVADOS ────────────────────────────

    def _build_equipo_read(self, equipo: Equipo) -> EquipoRead:
        nombre_area = None
        if equipo.area_id:
            area = self.area_repo.get_by_id(equipo.area_id)
            nombre_area = area.nombre if area else None

        nombre_clasif = None
        if equipo.clasificacion_id:
            clasif = self.clasif_repo.get_by_id(
                equipo.clasificacion_id,
            )
            nombre_clasif = clasif.nombre if clasif else None

        nombre_padre = None
        if equipo.equipo_padre_id:
            padre = self.repo.get_by_id(equipo.equipo_padre_id)
            nombre_padre = padre.nombre if padre else None

        hijos = self.repo.get_hijos_directos(equipo.id)
        sub_equipos = [
            SubEquipoRead(
                id=h.id,
                codigo_equipo=h.codigo_equipo,
                nombre=h.nombre,
                nivel=h.nivel,
                estado=h.estado,
            )
            for h in hijos
        ]

        fotos_db = self.foto_repo.get_by_equipo(equipo.id)
        fotos = [
            FotoList(
                id=f.id,
                thumbnail_url=f.thumbnail_url,
                url=f.url,
                tipo_foto=f.tipo_foto,
            )
            for f in fotos_db
        ]

        # ── REPUESTOS NECESARIOS ────────────────────
        repuestos_db = self.repuesto_repo.get_by_equipo(equipo.id)
        repuestos = [
            EquipoRepuestoRead.model_validate(r)
            for r in repuestos_db
        ]

        return EquipoRead(
            id=equipo.id,
            codigo_equipo=equipo.codigo_equipo,
            nombre=equipo.nombre,
            descripcion=equipo.descripcion,
            nivel=equipo.nivel,
            clasificacion_id=equipo.clasificacion_id,
            nombre_clasificacion=nombre_clasif,
            area_id=equipo.area_id,
            nombre_area=nombre_area,
            equipo_padre_id=equipo.equipo_padre_id,
            nombre_equipo_padre=nombre_padre,
            marca=equipo.marca,
            modelo=equipo.modelo,
            numero_serie=equipo.numero_serie,
            potencia=equipo.potencia,
            voltaje=equipo.voltaje,
            rpm=equipo.rpm,
            capacidad=equipo.capacidad,
            anio_fabricacion=equipo.anio_fabricacion,
            proveedor=equipo.proveedor,
            fecha_adquisicion=equipo.fecha_adquisicion,
            estado=equipo.estado,
            motivo_estado=equipo.motivo_estado,
            observaciones=equipo.observaciones,
            created_at=equipo.created_at,
            updated_at=equipo.updated_at,
            created_by=equipo.created_by,
            updated_by=equipo.updated_by,
            sub_equipos=sub_equipos,
            fotos=fotos,
            repuestos_necesarios=repuestos,  # NUEVO
        )

    def _build_equipo_list(self, equipo: Equipo) -> EquipoList:
        nombre_area = None
        if equipo.area_id:
            area = self.area_repo.get_by_id(equipo.area_id)
            nombre_area = area.nombre if area else None

        nombre_clasif = None
        if equipo.clasificacion_id:
            clasif = self.clasif_repo.get_by_id(
                equipo.clasificacion_id,
            )
            nombre_clasif = clasif.nombre if clasif else None

        return EquipoList(
            id=equipo.id,
            codigo_equipo=equipo.codigo_equipo,
            nombre=equipo.nombre,
            nivel=equipo.nivel,
            estado=equipo.estado,
            nombre_area=nombre_area,
            nombre_clasificacion=nombre_clasif,
            marca=equipo.marca,
        )

    def _build_tree(
        self,
        padre_id: uuid.UUID,
    ) -> List[EquipoArbolNodo]:
        hijos = self.repo.get_hijos_directos(padre_id)

        nodos = []
        for hijo in hijos:
            nietos = self._build_tree(hijo.id)
            nodo = EquipoArbolNodo(
                id=hijo.id,
                codigo_equipo=hijo.codigo_equipo,
                nombre=hijo.nombre,
                nivel=hijo.nivel,
                estado=hijo.estado,
                hijos=nietos,
            )
            nodos.append(nodo)

        return nodos
