import uuid
from datetime import date
from typing import Optional, List

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse

from app.core.dependencies import CurrentUser, SessionDep
from app.core.config import settings

from app.services.reporte_pdf import (
    generar_ficha_equipo_pdf,
    generar_historial_mantenimiento_pdf,
)
from app.services.reporte_excel import (
    generar_excel_equipos,
    generar_excel_mantenimientos,
    generar_excel_repuestos,
)
from app.services.reporte_qr import (
    generar_qr_equipo,
    generar_qr_masivo,
)
from app.services.equipo import EquipoService

router = APIRouter()


# ── PÁGINA WEB: Ficha técnica (accesible sin auth) ──

@router.get(
    "/equipo/{equipo_id}/web",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def ficha_web(
    equipo_id: uuid.UUID,
    session: SessionDep,
):
    """
    Página HTML pública de la ficha técnica.
    Es a lo que apunta el QR.
    Sin autenticación requerida.
    """
    service = EquipoService(session)

    try:
        equipo = service.get_by_id(equipo_id)
    except Exception:
        return HTMLResponse(
            content=_html_error("Equipo no encontrado"),
            status_code=404,
        )

    # Construir HTML
    sub_equipos_html = ""
    for sub in equipo.sub_equipos:
        sub_equipos_html += f"""
        <tr>
            <td><span class="badge badge-nivel">Nivel {sub.nivel}</span></td>
            <td><strong>{sub.codigo_equipo}</strong></td>
            <td>{sub.nombre}</td>
            <td><span class="badge badge-{sub.estado.value.lower()}">{sub.estado.value}</span></td>
        </tr>
        """

    fotos_html = ""
    for foto in equipo.fotos:
        fotos_html += f"""
        <a href="{foto.url}" target="_blank" class="foto-link">
            <img src="{foto.thumbnail_url or foto.url}"
                 alt="{foto.tipo_foto.value}"
                 class="foto-thumb">
            <span class="foto-tipo">{foto.tipo_foto.value}</span>
        </a>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{equipo.codigo_equipo} - {equipo.nombre}</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: 'Inter', sans-serif;
                background: #f0f2f5;
                color: #1a1a1a;
                line-height: 1.6;
            }}
            .header {{
                background: linear-gradient(135deg, #2d5016 0%, #4a7c2e 100%);
                color: white;
                padding: 24px 20px;
                text-align: center;
            }}
            .header h1 {{ font-size: 20px; font-weight: 700; }}
            .header .codigo {{ font-size: 14px; opacity: 0.9; margin-top: 4px; }}
            .container {{ max-width: 800px; margin: 0 auto; padding: 16px; }}
            .card {{
                background: white;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 16px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            }}
            .card h2 {{
                font-size: 15px;
                color: #2d5016;
                border-bottom: 2px solid #e8f5e0;
                padding-bottom: 8px;
                margin-bottom: 16px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .campo {{
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                border-bottom: 1px solid #f0f0f0;
            }}
            .campo:last-child {{ border-bottom: none; }}
            .campo-label {{
                font-weight: 600;
                color: #666;
                font-size: 13px;
            }}
            .campo-valor {{
                font-size: 13px;
                text-align: right;
                color: #1a1a1a;
            }}
            .badge {{
                display: inline-block;
                padding: 3px 10px;
                border-radius: 20px;
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
            }}
            .badge-operativo {{ background: #e8f5e0; color: #2d5016; }}
            .badge-parado {{ background: #fde8e8; color: #cc3333; }}
            .badge-reparacion {{ background: #fff3e0; color: #cc8800; }}
            .badge-baja {{ background: #f0f0f0; color: #666; }}
            .badge-nivel {{ background: #e3f2fd; color: #1565c0; }}
            table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 12px;
            }}
            th {{
                background: #2d5016;
                color: white;
                padding: 10px 12px;
                text-align: left;
                font-size: 11px;
                text-transform: uppercase;
            }}
            td {{ padding: 10px 12px; border-bottom: 1px solid #f0f0f0; }}
            tr:hover {{ background: #f8fdf5; }}
            .fotos-grid {{
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
            }}
            .foto-link {{
                text-decoration: none;
                text-align: center;
            }}
            .foto-thumb {{
                width: 100px;
                height: 100px;
                object-fit: cover;
                border-radius: 8px;
                border: 2px solid #e0e0e0;
            }}
            .foto-tipo {{
                display: block;
                font-size: 10px;
                color: #777;
                margin-top: 4px;
            }}
            .acciones {{
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
                margin-top: 8px;
            }}
            .btn {{
                flex: 1;
                min-width: 140px;
                padding: 14px 16px;
                border: none;
                border-radius: 10px;
                font-family: 'Inter', sans-serif;
                font-size: 13px;
                font-weight: 600;
                text-decoration: none;
                text-align: center;
                cursor: pointer;
                transition: transform 0.15s, box-shadow 0.15s;
            }}
            .btn:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}
            .btn-pdf {{
                background: linear-gradient(135deg, #cc3333 0%, #e04040 100%);
                color: white;
            }}
            .btn-excel {{
                background: linear-gradient(135deg, #2d5016 0%, #4a7c2e 100%);
                color: white;
            }}
            .btn-historial {{
                background: linear-gradient(135deg, #1565c0 0%, #1e88e5 100%);
                color: white;
            }}
            .footer {{
                text-align: center;
                padding: 20px;
                font-size: 11px;
                color: #999;
            }}
            @media (max-width: 480px) {{
                .campo {{ flex-direction: column; }}
                .campo-valor {{ text-align: left; margin-top: 2px; }}
                .acciones {{ flex-direction: column; }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{equipo.nombre}</h1>
            <div class="codigo">{equipo.codigo_equipo} &mdash; <span class="badge badge-{equipo.estado.value.lower()}">{equipo.estado.value}</span></div>
        </div>

        <div class="container">
            <!-- Acciones -->
            <div class="card">
                <h2>Descargar</h2>
                <div class="acciones">
                    <a href="/api/v1/reportes/equipo/{equipo.id}/pdf"
                       class="btn btn-pdf">
                        Ficha PDF
                    </a>
                    <a href="/api/v1/reportes/equipos/excel"
                       class="btn btn-excel">
                        Excel Equipos
                    </a>
                    <a href="/api/v1/reportes/equipo/{equipo.id}/mantenimientos/pdf"
                       class="btn btn-historial">
                        Mantenimientos
                    </a>
                </div>
            </div>

            <!-- Datos generales -->
            <div class="card">
                <h2>Datos Generales</h2>
                <div class="campo">
                    <span class="campo-label">Clasificación</span>
                    <span class="campo-valor">{equipo.nombre_clasificacion or 'N/A'}</span>
                </div>
                <div class="campo">
                    <span class="campo-label">Área</span>
                    <span class="campo-valor">{equipo.nombre_area or 'N/A'}</span>
                </div>
                <div class="campo">
                    <span class="campo-label">Nivel</span>
                    <span class="campo-valor">{equipo.nivel}</span>
                </div>
                <div class="campo">
                    <span class="campo-label">Equipo Padre</span>
                    <span class="campo-valor">{equipo.nombre_equipo_padre or 'N/A (Raíz)'}</span>
                </div>
                <div class="campo">
                    <span class="campo-label">Estado</span>
                    <span class="campo-valor">
                        <span class="badge badge-{equipo.estado.value.lower()}">{equipo.estado.value}</span>
                    </span>
                </div>
                {f'<div class="campo"><span class="campo-label">Motivo</span><span class="campo-valor">{equipo.motivo_estado}</span></div>' if equipo.motivo_estado else ''}
            </div>

            <!-- Datos de placa -->
            <div class="card">
                <h2>Datos de Placa / Datasheet</h2>
                <div class="campo">
                    <span class="campo-label">Marca</span>
                    <span class="campo-valor">{equipo.marca or 'N/A'}</span>
                </div>
                <div class="campo">
                    <span class="campo-label">Modelo</span>
                    <span class="campo-valor">{equipo.modelo or 'N/A'}</span>
                </div>
                <div class="campo">
                    <span class="campo-label">N° Serie</span>
                    <span class="campo-valor">{equipo.numero_serie or 'N/A'}</span>
                </div>
                <div class="campo">
                    <span class="campo-label">Potencia</span>
                    <span class="campo-valor">{equipo.potencia or 'N/A'}</span>
                </div>
                <div class="campo">
                    <span class="campo-label">Voltaje</span>
                    <span class="campo-valor">{equipo.voltaje or 'N/A'}</span>
                </div>
                <div class="campo">
                    <span class="campo-label">RPM</span>
                    <span class="campo-valor">{equipo.rpm or 'N/A'}</span>
                </div>
                <div class="campo">
                    <span class="campo-label">Capacidad</span>
                    <span class="campo-valor">{equipo.capacidad or 'N/A'}</span>
                </div>
                <div class="campo">
                    <span class="campo-label">Año Fabricación</span>
                    <span class="campo-valor">{equipo.anio_fabricacion or 'N/A'}</span>
                </div>
                <div class="campo">
                    <span class="campo-label">Proveedor</span>
                    <span class="campo-valor">{equipo.proveedor or 'N/A'}</span>
                </div>
            </div>

            <!-- Sub-equipos -->
            {"" if not equipo.sub_equipos else f'''
            <div class="card">
                <h2>Sub-Equipos / Componentes ({len(equipo.sub_equipos)})</h2>
                <table>
                    <tr>
                        <th>Nivel</th>
                        <th>Código</th>
                        <th>Nombre</th>
                        <th>Estado</th>
                    </tr>
                    {sub_equipos_html}
                </table>
            </div>
            '''}

            <!-- Fotos -->
            {"" if not equipo.fotos else f'''
            <div class="card">
                <h2>Fotografías ({len(equipo.fotos)})</h2>
                <div class="fotos-grid">
                    {fotos_html}
                </div>
            </div>
            '''}

            <!-- Observaciones -->
            {"" if not equipo.observaciones else f'''
            <div class="card">
                <h2>Observaciones</h2>
                <p style="font-size:13px;">{equipo.observaciones}</p>
            </div>
            '''}

            <div class="footer">
                Sistema de Fichas Técnicas &mdash; Palma Aceitera<br>
                Generado: {equipo.created_at.strftime('%d/%m/%Y')}
            </div>
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=html)


def _html_error(mensaje: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Error</title>
        <style>
            body {{
                font-family: 'Inter', sans-serif;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                background: #f0f2f5;
                color: #333;
            }}
            .error-box {{
                background: white;
                padding: 40px;
                border-radius: 12px;
                text-align: center;
                box-shadow: 0 2px 12px rgba(0,0,0,0.1);
            }}
            h1 {{ color: #cc3333; font-size: 48px; margin-bottom: 10px; }}
            p {{ color: #666; }}
        </style>
    </head>
    <body>
        <div class="error-box">
            <h1>404</h1>
            <p>{mensaje}</p>
        </div>
    </body>
    </html>
    """


# ── QR: Individual ──────────────────────────────────

@router.get("/equipo/{equipo_id}/qr")
def qr_equipo(
    equipo_id: uuid.UUID,
    session: SessionDep,
    user: CurrentUser,
):
    """Genera QR code con link a la ficha técnica del equipo."""
    try:
        buffer = generar_qr_equipo(session, equipo_id)
    except ValueError as e:
        raise HTTPException(404, str(e))

    return StreamingResponse(
        buffer,
        media_type="image/png",
        headers={
            "Content-Disposition": (
                f'attachment; filename="qr_{equipo_id}.png"'
            ),
        },
    )


# ── QR: Masivo (hoja para imprimir) ─────────────────

@router.post("/qr/masivo")
def qr_masivo(
    equipo_ids: List[uuid.UUID],
    session: SessionDep,
    user: CurrentUser,
):
    """Genera hoja con múltiples QR codes para imprimir."""
    try:
        buffer = generar_qr_masivo(session, equipo_ids)
    except ValueError as e:
        raise HTTPException(400, str(e))

    return StreamingResponse(
        buffer,
        media_type="image/png",
        headers={
            "Content-Disposition": (
                'attachment; filename="qr_equipos.png"'
            ),
        },
    )


# ── PDF: Ficha técnica ──────────────────────────────

@router.get("/equipo/{equipo_id}/pdf")
def ficha_equipo_pdf(
    equipo_id: uuid.UUID,
    session: SessionDep,
    user: CurrentUser,
):
    try:
        buffer = generar_ficha_equipo_pdf(session, equipo_id)
    except ValueError as e:
        raise HTTPException(404, str(e))

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="ficha_{equipo_id}.pdf"'
            ),
        },
    )


# ── PDF: Historial de mantenimiento ─────────────────

@router.get("/equipo/{equipo_id}/mantenimientos/pdf")
def historial_mantenimiento_pdf(
    equipo_id: uuid.UUID,
    session: SessionDep,
    user: CurrentUser,
):
    try:
        buffer = generar_historial_mantenimiento_pdf(
            session, equipo_id,
        )
    except ValueError as e:
        raise HTTPException(404, str(e))

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="mantenimientos_{equipo_id}.pdf"'
            ),
        },
    )


# ── EXCEL: Listado de equipos ───────────────────────

@router.get("/equipos/excel")
def equipos_excel(
    session: SessionDep,
    user: CurrentUser,
    area_id: Optional[uuid.UUID] = Query(default=None),
    clasificacion_id: Optional[uuid.UUID] = Query(default=None),
    estado: Optional[str] = Query(default=None),
    nivel: Optional[int] = Query(default=None, ge=1),
):
    buffer = generar_excel_equipos(
        session,
        area_id=area_id,
        clasificacion_id=clasificacion_id,
        estado=estado,
        nivel=nivel,
    )

    return StreamingResponse(
        buffer,
        media_type=(
            "application/vnd.openxmlformats-officedocument"
            ".spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": (
                'attachment; filename="equipos.xlsx"'
            ),
        },
    )


# ── EXCEL: Mantenimientos ───────────────────────────

@router.get("/mantenimientos/excel")
def mantenimientos_excel(
    session: SessionDep,
    user: CurrentUser,
    equipo_id: Optional[uuid.UUID] = Query(default=None),
    fecha_desde: Optional[date] = Query(default=None),
    fecha_hasta: Optional[date] = Query(default=None),
):
    buffer = generar_excel_mantenimientos(
        session,
        equipo_id=equipo_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )

    return StreamingResponse(
        buffer,
        media_type=(
            "application/vnd.openxmlformats-officedocument"
            ".spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": (
                'attachment; filename="mantenimientos.xlsx"'
            ),
        },
    )


# ── EXCEL: Catálogo de repuestos ────────────────────

@router.get("/repuestos/excel")
def repuestos_excel(
    session: SessionDep,
    user: CurrentUser,
):
    buffer = generar_excel_repuestos(session)

    return StreamingResponse(
        buffer,
        media_type=(
            "application/vnd.openxmlformats-officedocument"
            ".spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": (
                'attachment; filename="repuestos.xlsx"'
            ),
        },
    )
