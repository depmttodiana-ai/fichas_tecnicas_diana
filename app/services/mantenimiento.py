from typing import List
import uuid

from fastapi import HTTPException, status
from sqlmodel import Session

from app.models.mantenimiento import Mantenimiento
from app.models.mantenimiento_repuesto import MantenimientoRepuesto
from app.repositories.mantenimiento import MantenimientoRepository
from app.repositories.equipo import EquipoRepository
from app.repositories.usuario import UsuarioRepository
from app.schemas.mantenimiento import (
    MantenimientoCreate,
    MantenimientoUpdate,
    MantenimientoRead,
    MantenimientoList,
    RepuestoUsadoRead,
)
from app.models.enums import (
    TipoMantenimientoEnum,
    EstadoMantenimientoEnum,
)


class MantenimientoService:

    def __init__(self, session: Session):
        self.session = session
        self.repo = MantenimientoRepository(session)
        self.equipo_repo = EquipoRepository(session)
        self.usuario_repo = UsuarioRepository(session)

    def create(
        self,
        body: MantenimientoCreate,
        user_id: uuid.UUID,
    ) -> MantenimientoRead:

        # Verificar que el equipo exista
        equipo = self.equipo_repo.get_by_id(body.equipo_id)
        if not equipo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El equipo no existe",
            )

        # Verificar que los repuestos existan
        if body.repuestos_usados:
            for rep in body.repuestos_usados:
                repuesto = self.equipo_repo.get_by_id(rep.repuesto_id)
                if not repuesto:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"El repuesto con id {rep.repuesto_id} no existe",
                    )

        # Crear mantenimiento
        mantenimiento = Mantenimiento(
            equipo_id=body.equipo_id,
            usuario_id=user_id,
            tipo=body.tipo,
            titulo=body.titulo,
            descripcion=body.descripcion,
            trabajo_realizado=body.trabajo_realizado,
            estado=body.estado,
            fecha=body.fecha,
        )

        mantto_creado = self.repo.add(mantenimiento)

        # Crear repuestos usados
        repuestos_creados = []
        if body.repuestos_usados:
            for rep in body.repuestos_usados:
                repuesto_usado = MantenimientoRepuesto(
                    mantenimiento_id=mantto_creado.id,
                    repuesto_id=rep.repuesto_id,
                    cantidad_usada=rep.cantidad_usada,
                    observacion=rep.observacion,
                )
                self.repo.add_repuesto_usado(repuesto_usado)
                repuestos_creados.append(repuesto_usado)

        return self._build_mantenimiento_read(
            mantto_creado,
            repuestos_creados,
        )

    def get_by_id(
        self,
        mantenimiento_id: uuid.UUID,
    ) -> MantenimientoRead:
        mantto = self.repo.get_by_id(mantenimiento_id)
        if not mantto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mantenimiento no encontrado",
            )

        repuestos = self.repo.get_repuestos_by_mantenimiento(
            mantto.id,
        )

        return self._build_mantenimiento_read(mantto, repuestos)

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[MantenimientoList]:
        manttos = self.repo.get_all(skip=skip, limit=limit)
        return [
            self._build_mantenimiento_list(m) for m in manttos
        ]

    def get_by_equipo(
        self,
        equipo_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[MantenimientoList]:
        equipo = self.equipo_repo.get_by_id(equipo_id)
        if not equipo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Equipo no encontrado",
            )

        manttos = self.repo.get_by_equipo(
            equipo_id,
            skip=skip,
            limit=limit,
        )
        return [
            self._build_mantenimiento_list(m) for m in manttos
        ]

    def filter(
        self,
        equipo_id=None,
        tipo=None,
        estado=None,
        fecha_desde=None,
        fecha_hasta=None,
        usuario_id=None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[MantenimientoList]:
        manttos = self.repo.filter(
            equipo_id=equipo_id,
            tipo=tipo,
            estado=estado,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            usuario_id=usuario_id,
            skip=skip,
            limit=limit,
        )
        return [
            self._build_mantenimiento_list(m) for m in manttos
        ]

    def update(
        self,
        mantenimiento_id: uuid.UUID,
        body: MantenimientoUpdate,
    ) -> MantenimientoRead:
        mantto = self.repo.get_by_id(mantenimiento_id)
        if not mantto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mantenimiento no encontrado",
            )

        update_data = body.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(mantto, field, value)

        mantto_actualizado = self.repo.save(mantto)
        repuestos = self.repo.get_repuestos_by_mantenimiento(
            mantto_actualizado.id,
        )

        return self._build_mantenimiento_read(
            mantto_actualizado,
            repuestos,
        )

    def delete(self, mantenimiento_id: uuid.UUID) -> None:
        mantto = self.repo.get_by_id(mantenimiento_id)
        if not mantto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mantenimiento no encontrado",
            )

        # Eliminar repuestos asociados primero
        self.repo.delete_repuestos_by_mantenimiento(mantto.id)
        self.repo.delete(mantto)

    # ── HELPERS PRIVADOS ────────────────────────────

    def _build_mantenimiento_read(
        self,
        mantto: Mantenimiento,
        repuestos: list,
    ) -> MantenimientoRead:
        """Construye MantenimientoRead con datos resueltos."""

        # Resolver nombre del equipo
        equipo = self.equipo_repo.get_by_id(mantto.equipo_id)
        nombre_equipo = equipo.nombre if equipo else None
        codigo_equipo = equipo.codigo_equipo if equipo else None

        # Resolver nombre del usuario
        nombre_usuario = None
        if mantto.usuario_id:
            usuario = self.usuario_repo.get_by_id(mantto.usuario_id)
            nombre_usuario = usuario.nombre if usuario else None

        # Construir lista de repuestos
        repuestos_read = []
        for rep in repuestos:
            repuesto_equipo = self.equipo_repo.get_by_id(
                rep.repuesto_id,
            )
            repuestos_read.append(
                RepuestoUsadoRead(
                    id=rep.id,
                    repuesto_id=rep.repuesto_id,
                    nombre_repuesto=(
                        repuesto_equipo.nombre
                        if repuesto_equipo
                        else None
                    ),
                    codigo_repuesto=(
                        repuesto_equipo.codigo_equipo
                        if repuesto_equipo
                        else None
                    ),
                    cantidad_usada=rep.cantidad_usada,
                    observacion=rep.observacion,
                )
            )

        return MantenimientoRead(
            id=mantto.id,
            equipo_id=mantto.equipo_id,
            usuario_id=mantto.usuario_id,
            tipo=mantto.tipo,
            titulo=mantto.titulo,
            descripcion=mantto.descripcion,
            trabajo_realizado=mantto.trabajo_realizado,
            estado=mantto.estado,
            fecha=mantto.fecha,
            created_at=mantto.created_at,
            nombre_equipo=nombre_equipo,
            codigo_equipo=codigo_equipo,
            nombre_usuario=nombre_usuario,
            repuestos_usados=repuestos_read,
        )

    def _build_mantenimiento_list(
        self,
        mantto: Mantenimiento,
    ) -> MantenimientoList:
        """Construye MantenimientoList con datos resueltos."""

        equipo = self.equipo_repo.get_by_id(mantto.equipo_id)
        nombre_equipo = equipo.nombre if equipo else None
        codigo_equipo = equipo.codigo_equipo if equipo else None

        return MantenimientoList(
            id=mantto.id,
            fecha=mantto.fecha,
            tipo=mantto.tipo,
            titulo=mantto.titulo,
            estado=mantto.estado,
            nombre_equipo=nombre_equipo,
            codigo_equipo=codigo_equipo,
        )

    def get_repuestos_necesarios_para_equipo(
        self,
        equipo_id: uuid.UUID,
    ) -> list:
        """
        Retorna los repuestos que necesita este equipo.
        Útil antes de hacer un mantenimiento.
        """
        from app.repositories.equipo_repuesto import (
            EquipoRepuestoRepository,
        )

        equipo = self.equipo_repo.get_by_id(equipo_id)
        if not equipo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Equipo no encontrado",
            )

        rep_repo = EquipoRepuestoRepository(self.session)
        repuestos = rep_repo.get_by_equipo(equipo_id)

        return [
            {
                "id": str(r.id),
                "codigo_repuesto": r.codigo_repuesto,
                "descripcion": r.descripcion,
                "para_que": r.para_que,
                "ubicacion": r.ubicacion,
                "cantidad_necesaria": r.cantidad_necesaria,
            }
            for r in repuestos
        ]
