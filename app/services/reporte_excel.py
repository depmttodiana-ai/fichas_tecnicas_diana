import uuid
from io import BytesIO
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from sqlmodel import Session

from app.repositories.equipo import EquipoRepository
from app.repositories.area import AreaRepository
from app.repositories.clasificacion import ClasificacionRepository
from app.repositories.mantenimiento import MantenimientoRepository
from app.repositories.usuario import UsuarioRepository


# ── ESTILOS ─────────────────────────────────────────

VERDE_OSCURO = PatternFill(
    start_color="2D5016",
    end_color="2D5016",
    fill_type="solid",
)
VERDE_CLARO = PatternFill(
    start_color="4A7C2E",
    end_color="4A7C2E",
    fill_type="solid",
)
GRIS_CLARO = PatternFill(
    start_color="F5F5F5",
    end_color="F5F5F5",
    fill_type="solid",
)

FUENTE_HEADER = Font(
    name="Calibri",
    size=11,
    bold=True,
    color="FFFFFF",
)
FUENTE_NORMAL = Font(
    name="Calibri",
    size=10,
)
FUENTE_TITULO = Font(
    name="Calibri",
    size=14,
    bold=True,
    color="2D5016",
)

BORDE = Border(
    left=Side(style="thin", color="CCCCCC"),
    right=Side(style="thin", color="CCCCCC"),
    top=Side(style="thin", color="CCCCCC"),
    bottom=Side(style="thin", color="CCCCCC"),
)

ALINEAR_CENTRO = Alignment(
    horizontal="center",
    vertical="center",
    wrap_text=True,
)


def _aplicar_estilo_header(ws, fila, num_cols):
    for col in range(1, num_cols + 1):
        celda = ws.cell(row=fila, column=col)
        celda.font = FUENTE_HEADER
        celda.fill = VERDE_OSCURO
        celda.alignment = ALINEAR_CENTRO
        celda.border = BORDE


def _aplicar_estilo_fila(ws, fila, num_cols, alternar=False):
    for col in range(1, num_cols + 1):
        celda = ws.cell(row=fila, column=col)
        celda.font = FUENTE_NORMAL
        celda.border = BORDE
        celda.alignment = Alignment(
            vertical="center",
            wrap_text=True,
        )
        if alternar:
            celda.fill = GRIS_CLARO


def _ajustar_anchos(ws, anchos):
    for i, ancho in enumerate(anchos, 1):
        ws.column_dimensions[get_column_letter(i)].width = ancho


# ── REPORTE DE EQUIPOS EXCEL ────────────────────────

def generar_excel_equipos(
    session: Session,
    area_id: uuid.UUID | None = None,
    clasificacion_id: uuid.UUID | None = None,
    estado: str | None = None,
    nivel: int | None = None,
) -> BytesIO:
    """Genera Excel con listado de equipos y filtros opcionales."""

    equipo_repo = EquipoRepository(session)
    area_repo = AreaRepository(session)
    clasif_repo = ClasificacionRepository(session)

    # Obtener equipos con filtros
    equipos = equipo_repo.filter(
        area_id=area_id,
        clasificacion_id=clasificacion_id,
        estado=estado,
        nivel=nivel,
        limit=1000,
    )

    wb = Workbook()

    # ── HOJA 1: LISTADO DE EQUIPOS ──────────────────
    ws = wb.active
    ws.title = "Equipos"

    # Título
    ws.merge_cells("A1:L1")
    ws["A1"] = "LISTADO DE EQUIPOS - SISTEMA DE FICHAS TÉCNICAS"
    ws["A1"].font = FUENTE_TITULO
    ws["A1"].alignment = Alignment(horizontal="center")

    ws.merge_cells("A2:L2")
    ws["A2"] = (
        f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')} | "
        f"Total: {len(equipos)} equipos"
    )
    ws["A2"].font = Font(name="Calibri", size=9, color="999999")
    ws["A2"].alignment = Alignment(horizontal="center")

    # Headers
    headers = [
        "Código", "Nombre", "Nivel", "Estado",
        "Clasificación", "Área", "Marca", "Modelo",
        "N° Serie", "Potencia", "Padre", "Fecha Creación",
    ]
    for col, header in enumerate(headers, 1):
        ws.cell(row=4, column=col, value=header)
    _aplicar_estilo_header(ws, 4, len(headers))

    # Datos
    for i, eq in enumerate(equipos):
        fila = i + 5

        nombre_area = ""
        if eq.area_id:
            area = area_repo.get_by_id(eq.area_id)
            nombre_area = area.nombre if area else ""

        nombre_clasif = ""
        if eq.clasificacion_id:
            clasif = clasif_repo.get_by_id(eq.clasificacion_id)
            nombre_clasif = clasif.nombre if clasif else ""

        nombre_padre = ""
        if eq.equipo_padre_id:
            padre = equipo_repo.get_by_id(eq.equipo_padre_id)
            nombre_padre = padre.codigo_equipo if padre else ""

        datos = [
            eq.codigo_equipo,
            eq.nombre,
            eq.nivel,
            eq.estado.value,
            nombre_clasif,
            nombre_area,
            eq.marca or "",
            eq.modelo or "",
            eq.numero_serie or "",
            eq.potencia or "",
            nombre_padre,
            eq.created_at.strftime("%d/%m/%Y") if eq.created_at else "",
        ]

        for col, valor in enumerate(datos, 1):
            ws.cell(row=fila, column=col, value=valor)

        _aplicar_estilo_fila(
            ws, fila, len(headers),
            alternar=(i % 2 == 0),
        )

    _ajustar_anchos(ws, [
        15, 30, 6, 12, 18, 20, 15, 15, 18, 12, 18, 14,
    ])

    # ── HOJA 2: RESUMEN POR ESTADO ──────────────────
    ws2 = wb.create_sheet("Resumen")
    ws2.merge_cells("A1:C1")
    ws2["A1"] = "RESUMEN POR ESTADO"
    ws2["A1"].font = FUENTE_TITULO

    resumen_headers = ["Estado", "Cantidad", "Porcentaje"]
    for col, h in enumerate(resumen_headers, 1):
        ws2.cell(row=3, column=col, value=h)
    _aplicar_estilo_header(ws2, 3, 3)

    estados_contados = {}
    for eq in equipos:
        est = eq.estado.value
        estados_contados[est] = estados_contados.get(est, 0) + 1

    total = len(equipos) or 1
    for i, (estado, cant) in enumerate(estados_contados.items()):
        fila = i + 4
        ws2.cell(row=fila, column=1, value=estado)
        ws2.cell(row=fila, column=2, value=cant)
        ws2.cell(
            row=fila, column=3,
            value=f"{(cant / total) * 100:.1f}%",
        )
        _aplicar_estilo_fila(ws2, fila, 3, alternar=(i % 2 == 0))

    _ajustar_anchos(ws2, [20, 12, 12])

    # Guardar en buffer
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


# ── REPORTE DE MANTENIMIENTOS EXCEL ─────────────────

def generar_excel_mantenimientos(
    session: Session,
    equipo_id: uuid.UUID | None = None,
    fecha_desde=None,
    fecha_hasta=None,
) -> BytesIO:
    """Genera Excel con listado de mantenimientos."""

    mantto_repo = MantenimientoRepository(session)
    equipo_repo = EquipoRepository(session)
    usuario_repo = UsuarioRepository(session)

    if equipo_id:
        mantenimientos = mantto_repo.get_by_equipo(
            equipo_id, limit=1000,
        )
    else:
        mantenimientos = mantto_repo.filter(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            limit=1000,
        )

    wb = Workbook()
    ws = wb.active
    ws.title = "Mantenimientos"

    # Título
    ws.merge_cells("A1:H1")
    ws["A1"] = "HISTORIAL DE MANTENIMIENTOS"
    ws["A1"].font = FUENTE_TITULO
    ws["A1"].alignment = Alignment(horizontal="center")

    ws.merge_cells("A2:H2")
    ws["A2"] = (
        f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')} | "
        f"Total: {len(mantenimientos)} registros"
    )
    ws["A2"].font = Font(name="Calibri", size=9, color="999999")
    ws["A2"].alignment = Alignment(horizontal="center")

    # Headers
    headers = [
        "Fecha", "Tipo", "Título", "Estado",
        "Equipo", "Código Equipo", "Realizado por",
        "Descripción",
    ]
    for col, h in enumerate(headers, 1):
        ws.cell(row=4, column=col, value=h)
    _aplicar_estilo_header(ws, 4, len(headers))

    # Datos
    for i, m in enumerate(mantenimientos):
        fila = i + 5

        equipo = equipo_repo.get_by_id(m.equipo_id)
        nombre_equipo = equipo.nombre if equipo else ""
        codigo_equipo = equipo.codigo_equipo if equipo else ""

        nombre_usuario = ""
        if m.usuario_id:
            usuario = usuario_repo.get_by_id(m.usuario_id)
            nombre_usuario = usuario.nombre if usuario else ""

        datos = [
            str(m.fecha),
            m.tipo.value,
            m.titulo,
            m.estado.value,
            nombre_equipo,
            codigo_equipo,
            nombre_usuario,
            (m.descripcion or "")[:100],
        ]

        for col, valor in enumerate(datos, 1):
            ws.cell(row=fila, column=col, value=valor)

        _aplicar_estilo_fila(
            ws, fila, len(headers),
            alternar=(i % 2 == 0),
        )

    _ajustar_anchos(ws, [12, 12, 35, 12, 25, 18, 18, 40])

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


# ── REPORTE DE REPUESTOS EXCEL ──────────────────────

def generar_excel_repuestos(
    session: Session,
) -> BytesIO:
    """Genera Excel con todos los repuestos (nivel 4+)."""

    equipo_repo = EquipoRepository(session)

    # Buscar todos los equipos que son repuestos (nivel >= 4)
    todos = equipo_repo.get_all(limit=5000)
    repuestos = [e for e in todos if e.nivel >= 4]

    wb = Workbook()
    ws = wb.active
    ws.title = "Repuestos"

    ws.merge_cells("A1:G1")
    ws["A1"] = "CATÁLOGO DE REPUESTOS"
    ws["A1"].font = FUENTE_TITULO
    ws["A1"].alignment = Alignment(horizontal="center")

    ws.merge_cells("A2:G2")
    ws["A2"] = (
        f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')} | "
        f"Total: {len(repuestos)} repuestos"
    )
    ws["A2"].font = Font(name="Calibri", size=9, color="999999")
    ws["A2"].alignment = Alignment(horizontal="center")

    headers = [
        "Código", "Nombre", "Descripción",
        "Componente Padre", "Equipo Raíz", "Estado",
        "Observaciones",
    ]
    for col, h in enumerate(headers, 1):
        ws.cell(row=4, column=col, value=h)
    _aplicar_estilo_header(ws, 4, len(headers))

    for i, r in enumerate(repuestos):
        fila = i + 5

        # Resolver padre
        nombre_padre = ""
        if r.equipo_padre_id:
            padre = equipo_repo.get_by_id(r.equipo_padre_id)
            nombre_padre = padre.nombre if padre else ""

        # Resolver equipo raíz (subir hasta nivel 1)
        nombre_raiz = ""
        actual = r
        while actual.equipo_padre_id:
            padre = equipo_repo.get_by_id(actual.equipo_padre_id)
            if padre:
                actual = padre
            else:
                break
        if actual.nivel == 1:
            nombre_raiz = actual.nombre

        datos = [
            r.codigo_equipo,
            r.nombre,
            r.descripcion or "",
            nombre_padre,
            nombre_raiz,
            r.estado.value,
            r.observaciones or "",
        ]

        for col, valor in enumerate(datos, 1):
            ws.cell(row=fila, column=col, value=valor)

        _aplicar_estilo_fila(
            ws, fila, len(headers),
            alternar=(i % 2 == 0),
        )

    _ajustar_anchos(ws, [15, 30, 30, 25, 25, 12, 30])

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer
