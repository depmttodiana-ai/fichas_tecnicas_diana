import os
import uuid
import urllib.request
from io import BytesIO
from datetime import datetime

from sqlmodel import Session
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    PageBreak,
    Image,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from app.core.config import settings
from app.repositories.equipo import EquipoRepository
from app.repositories.area import AreaRepository
from app.repositories.clasificacion import ClasificacionRepository
from app.repositories.mantenimiento import MantenimientoRepository
from app.repositories.foto import FotoRepository
from app.repositories.historial import HistorialRepository
from app.models.enums import TipoFotoEnum
from app.repositories.usuario import UsuarioRepository

LOGO_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "assets", "logo.jpg",
)


def _open_image_bytes(url_or_path: str) -> BytesIO | None:
    if url_or_path.startswith("http"):
        try:
            with urllib.request.urlopen(url_or_path, timeout=10) as resp:
                data = resp.read()
                if len(data) == 0:
                    return None
                return BytesIO(data)
        except Exception as e:
            print(f"[PDF] Error al descargar imagen desde URL: {e}")
            return None
    local = url_or_path.lstrip("/")
    if os.path.exists(local):
        with open(local, "rb") as f:
            return BytesIO(f.read())
    print(f"[PDF] No se encontró la imagen local: {local}")
    return None


# ── ESTILOS ─────────────────────────────────────────

def _get_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="TituloPrincipal",
        fontName="Helvetica-Bold",
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=20,
        textColor=colors.HexColor("#1a1a1a"),
    ))

    styles.add(ParagraphStyle(
        name="Subtitulo",
        fontName="Helvetica-Bold",
        fontSize=13,
        alignment=TA_LEFT,
        spaceBefore=15,
        spaceAfter=8,
        textColor=colors.HexColor("#333333"),
    ))

    styles.add(ParagraphStyle(
        name="Etiqueta",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=colors.HexColor("#555555"),
    ))

    styles.add(ParagraphStyle(
        name="Valor",
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#1a1a1a"),
    ))

    styles.add(ParagraphStyle(
        name="Footer",
        fontName="Helvetica",
        fontSize=7,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#999999"),
    ))

    styles.add(ParagraphStyle(
        name="TitleCustom",
        parent=styles["Title"],
        fontSize=18,
        textColor=colors.HexColor("#1F4E79"),
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="SubTitleCustom",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#2E75B6"),
        alignment=TA_CENTER,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="SectionStyle",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.white,
        alignment=TA_CENTER,
        spaceBefore=14,
        spaceAfter=6,
        leftIndent=6,
    ))

    return styles


# ── COLORES CORPORATIVOS ────────────────────────────

VERDE_OSCURO = colors.HexColor("#1F4E79")
VERDE_CLARO = colors.HexColor("#2E75B6")
GRIS_CLARO = colors.HexColor("#f5f5f5")
GRIS_MEDIO = colors.HexColor("#e0e0e0")
AZUL_OSCURO = colors.HexColor("#1F4E79")
AZUL_MEDIO = colors.HexColor("#2E75B6")
AZUL_CLARO = colors.HexColor("#D6E4F0")
BLANCO_HUESO = colors.HexColor("#F2F6FA")


# ── HEADER Y FOOTER DE PÁGINA ───────────────────────

def _header_footer(canvas, doc):
    canvas.saveState()

    # Footer
    canvas.setFillColor(colors.HexColor("#999999"))
    canvas.setFont("Helvetica", 7)
    canvas.drawCentredString(
        letter[0] / 2,
        25,
        f"Página {doc.page} | Sistema de Fichas Técnicas",
    )
    canvas.setStrokeColor(GRIS_MEDIO)
    canvas.setLineWidth(0.5)
    canvas.line(30, 35, letter[0] - 30, 35)

    canvas.restoreState()


def _build_header_bar(doc, styles):
    """Crea una tabla/barra azul con nombre de empresa y fecha."""
    page_width = doc.pagesize[0] - doc.leftMargin - doc.rightMargin
    fecha_str = datetime.now().strftime('%d/%m/%Y %H:%M')
    bar_style = ParagraphStyle(
        "BarStyle", parent=styles["Normal"],
        fontSize=10, leading=13,
        textColor=colors.white,
        alignment=TA_LEFT,
    )
    fecha_style = ParagraphStyle(
        "FechaStyle", parent=styles["Normal"],
        fontSize=8, leading=13,
        textColor=colors.white,
        alignment=TA_RIGHT,
    )
    bar_table = Table(
        [[Paragraph("FICHAS TÉCNICAS - PALMA ACEITERA", bar_style),
          Paragraph(f"Generado: {fecha_str}", fecha_style)]],
        colWidths=[page_width * 0.65, page_width * 0.35],
    )
    bar_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), AZUL_OSCURO),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return bar_table


# ── HELPER: Construir ficha estructurada ──────────────────

def _build_ficha_estructurada(equipo, nombre_area, nombre_clasif, nombre_padre, hijos):
    """Convierte un equipo ORM en el formato estructurado de ficha técnica."""
    secciones = []

    # ── Ubicaciones del Equipo ──
    ubi = {"nombre": "Ubicaciones del Equipo", "campos": []}
    ubi["campos"].append({"clave": "Código", "valor": equipo.codigo_equipo})
    if nombre_clasif:
        ubi["campos"].append({"clave": "Clasificación", "valor": nombre_clasif})
    if nombre_area:
        ubi["campos"].append({"clave": "Área / Ubicación", "valor": nombre_area})
    ubi["campos"].append({"clave": "Nivel Jerárquico", "valor": str(equipo.nivel)})
    if nombre_padre:
        ubi["campos"].append({"clave": "Equipo Padre", "valor": nombre_padre})
    secciones.append(ubi)

    # ── Datos del Fabricante ──
    fab = {"nombre": "Datos del Fabricante", "campos": []}
    for k, v in [
        ("Marca", equipo.marca),
        ("Modelo", equipo.modelo),
        ("N° Serie", equipo.numero_serie),
        ("Año Fabricación", str(equipo.anio_fabricacion) if equipo.anio_fabricacion else None),
        ("Proveedor", equipo.proveedor),
    ]:
        if v:
            fab["campos"].append({"clave": k, "valor": v})
    if fab["campos"]:
        secciones.append(fab)

    # ── Datos de Placa / Datasheet ──
    pla = {"nombre": "Datos de Placa / Datasheet", "campos": []}
    for k, v in [
        ("Potencia", equipo.potencia),
        ("Voltaje", equipo.voltaje),
        ("RPM", equipo.rpm),
        ("Capacidad", equipo.capacidad),
    ]:
        if v:
            pla["campos"].append({"clave": k, "valor": v})
    if pla["campos"]:
        secciones.append(pla)

    # ── Datos de la Unidad ──
    uni = {"nombre": "Datos de la Unidad", "campos": []}
    if equipo.fecha_adquisicion:
        uni["campos"].append({
            "clave": "Fecha de Adquisición",
            "valor": equipo.fecha_adquisicion.strftime("%d/%m/%Y"),
        })
    uni["campos"].append({"clave": "Estado", "valor": equipo.estado.value})
    if equipo.motivo_estado:
        uni["campos"].append({"clave": "Motivo de Estado", "valor": equipo.motivo_estado})
    if equipo.created_at:
        uni["campos"].append({
            "clave": "Fecha de Registro",
            "valor": equipo.created_at.strftime("%d/%m/%Y"),
        })
    if equipo.descripcion:
        uni["campos"].append({"clave": "Descripción", "valor": equipo.descripcion})
    secciones.append(uni)

    # ── Sub-Equipos ──
    if hijos:
        subs = {"nombre": "Sub-Equipos / Componentes", "campos": []}
        for s in hijos:
            subs["campos"].append({
                "clave": s.codigo_equipo,
                "valor": f"{s.nombre} — {s.estado.value}",
            })
        secciones.append(subs)

    # ── Observaciones ──
    if equipo.observaciones:
        secciones.append({
            "nombre": "Observaciones",
            "campos": [{"clave": "Observaciones", "valor": equipo.observaciones}],
        })

    return {
        "empresa": settings.APP_NAME,
        "titulo": "Ficha Técnica del Equipo",
        "funcion": "",
        "equipo": equipo.nombre,
        "tag": equipo.codigo_equipo,
        "secciones": secciones,
    }


# ── FICHA TÉCNICA INDIVIDUAL PDF ────────────────────

def generar_ficha_equipo_pdf(
    session: Session,
    equipo_id: uuid.UUID,
) -> BytesIO:
    """Genera PDF con la ficha técnica completa de un equipo."""

    equipo_repo = EquipoRepository(session)
    area_repo = AreaRepository(session)
    clasif_repo = ClasificacionRepository(session)

    equipo = equipo_repo.get_by_id(equipo_id)
    if not equipo:
        raise ValueError("Equipo no encontrado")

    # Resolver nombres
    nombre_area = area_repo.get_by_id(equipo.area_id).nombre if equipo.area_id else ""
    nombre_clasif = clasif_repo.get_by_id(equipo.clasificacion_id).nombre if equipo.clasificacion_id else ""
    nombre_padre = ""
    if equipo.equipo_padre_id:
        padre = equipo_repo.get_by_id(equipo.equipo_padre_id)
        nombre_padre = padre.nombre if padre else ""
    hijos = equipo_repo.get_hijos_directos(equipo.id)

    ficha = _build_ficha_estructurada(
        equipo, nombre_area, nombre_clasif, nombre_padre, hijos,
    )

    buffer = BytesIO()
    styles = _get_styles()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=60,
        bottomMargin=50,
        leftMargin=30,
        rightMargin=30,
    )

    elementos = []

    # ── Logo full-width ──
    if os.path.exists(LOGO_PATH):
        page_width = doc.pagesize[0] - doc.leftMargin - doc.rightMargin
        logo = Image(LOGO_PATH, width=page_width, height=page_width * 360 / 2428)
        elementos.append(logo)
        elementos.append(Spacer(1, 4))

    # ── Barra azul con membreté ──
    elementos.append(_build_header_bar(doc, styles))
    elementos.append(Spacer(1, 6))

    # ── Título ──
    titulo_style = ParagraphStyle(
        "TituloFicha", parent=styles["Normal"],
        fontSize=20, leading=24,
        textColor=AZUL_OSCURO,
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    elementos.append(Paragraph("FICHA TÉCNICA", titulo_style))
    nombre_style = ParagraphStyle(
        "NombreFicha", parent=styles["Normal"],
        fontSize=13, leading=16,
        textColor=colors.HexColor("#555555"),
        alignment=TA_CENTER,
        spaceAfter=10,
    )
    elementos.append(Paragraph(ficha["equipo"], nombre_style))

    # ── Info básica ──
    key_s = ParagraphStyle("Key", parent=styles["Normal"], fontSize=9, leading=11)
    val_s = ParagraphStyle("Val", parent=styles["Normal"], fontSize=9, leading=11)

    info_data = [
        [Paragraph("<b>Equipo</b>", key_s), Paragraph(ficha["equipo"], val_s)],
        [Paragraph("<b>TAG</b>", key_s), Paragraph(ficha["tag"], val_s)],
    ]
    col_w = (doc.pagesize[0] - doc.leftMargin - doc.rightMargin) / 2
    info_table = Table(info_data, colWidths=[col_w, col_w])
    info_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#AAAAAA")),
        ("BACKGROUND", (0, 0), (0, -1), AZUL_CLARO),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elementos.append(info_table)
    elementos.append(Spacer(1, 4))

    # ── Secciones ──
    for seccion in ficha["secciones"]:
        section_hdr_style = ParagraphStyle(
            "SectionHdr", parent=styles["Normal"],
            fontSize=10, leading=13,
            textColor=colors.white,
            alignment=TA_CENTER,
            backColor=AZUL_MEDIO,
            spaceBefore=8, spaceAfter=4,
            leftIndent=6,
        )
        elementos.append(Paragraph(seccion['nombre'], section_hdr_style))

        table_data = []
        for campo in seccion["campos"]:
            valor = campo["valor"] if campo["valor"] else "—"
            table_data.append([
                Paragraph(f"<b>{campo['clave']}</b>", key_s),
                Paragraph(valor, val_s),
            ])

        t = Table(table_data, colWidths=[col_w, col_w])
        style_cmds = [
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
            ("BACKGROUND", (0, 0), (0, -1), BLANCO_HUESO),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]
        for i in range(len(table_data)):
            if i % 2 == 0:
                style_cmds.append(
                    ("BACKGROUND", (1, i), (1, i), colors.HexColor("#F8FAFC")),
                )

        t.setStyle(TableStyle(style_cmds))
        elementos.append(t)
        elementos.append(Spacer(1, 4))

    # ── Foto del Equipo ──
    foto_repo = FotoRepository(session)
    fotos = foto_repo.get_by_equipo_y_tipo(equipo_id, TipoFotoEnum.GENERAL)
    if not fotos:
        fotos = foto_repo.get_by_equipo(equipo_id)
    if fotos:
        foto_bytes = _open_image_bytes(fotos[0].url)
        if foto_bytes:
            foto_img = Image(foto_bytes, width=col_w * 2, height=180)
            section_hdr_style = ParagraphStyle(
                "SectionHdr", parent=styles["Normal"],
                fontSize=10, leading=13,
                textColor=colors.white,
                alignment=TA_CENTER,
                backColor=AZUL_MEDIO,
                spaceBefore=8, spaceAfter=4,
                leftIndent=6,
            )
            elementos.append(Paragraph("Foto del Equipo", section_hdr_style))
            elementos.append(foto_img)
            elementos.append(Spacer(1, 6))

    # ── CONSTRUIR ───────────────────────────────────
    doc.build(
        elementos,
        onFirstPage=_header_footer,
        onLaterPages=_header_footer,
    )

    buffer.seek(0)
    return buffer


# ── HISTORIAL DE MANTENIMIENTO DE UN EQUIPO PDF ─────

def generar_historial_mantenimiento_pdf(
    session: Session,
    equipo_id: uuid.UUID,
) -> BytesIO:
    """Genera PDF con el historial completo de mantenimientos."""

    equipo_repo = EquipoRepository(session)
    mantto_repo = MantenimientoRepository(session)
    usuario_repo = UsuarioRepository(session)

    equipo = equipo_repo.get_by_id(equipo_id)
    if not equipo:
        raise ValueError("Equipo no encontrado")

    mantenimientos = mantto_repo.get_by_equipo(equipo_id, limit=200)

    buffer = BytesIO()
    styles = _get_styles()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=60,
        bottomMargin=50,
        leftMargin=30,
        rightMargin=30,
    )

    elementos = []

    # ── Logo ──
    if os.path.exists(LOGO_PATH):
        page_width = doc.pagesize[0] - doc.leftMargin - doc.rightMargin
        logo = Image(LOGO_PATH, width=page_width, height=page_width * 360 / 2428)
        elementos.append(logo)
        elementos.append(Spacer(1, 4))

    # ── Barra azul con membreté ──
    elementos.append(_build_header_bar(doc, styles))
    elementos.append(Spacer(1, 6))

    elementos.append(
        Paragraph(
            f"HISTORIAL DE MANTENIMIENTOS",
            styles["TituloPrincipal"],
        ),
    )
    elementos.append(
        Paragraph(
            f"{equipo.nombre} | Código: {equipo.codigo_equipo}",
            styles["Subtitulo"],
        ),
    )
    elementos.append(
        Paragraph(
            f"Total registros: {len(mantenimientos)}",
            styles["Valor"],
        ),
    )
    elementos.append(Spacer(1, 8))

    for m in mantenimientos:
        # Nombre del técnico
        nombre_tecnico = m.realizado_por or "N/A"
        if m.realizado_por:
            nombre_tecnico = m.realizado_por
        elif m.usuario_id:
            tecnico = usuario_repo.get_by_id(m.usuario_id)
            nombre_tecnico = tecnico.nombre if tecnico else "N/A"

        # Repuestos usados
        repuestos = mantto_repo.get_repuestos_by_mantenimiento(m.id)

        bloque = [
            ["Fecha:", str(m.fecha), "Tipo:", m.tipo.value],
            ["Título:", m.titulo, "Estado:", m.estado.value],
            ["Realizado por:", nombre_tecnico, "", ""],
        ]

        if m.descripcion:
            bloque.append([
                "Descripción:",
                m.descripcion[:80],
                "",
                "",
            ])

        if m.trabajo_realizado:
            bloque.append([
                "Trabajo Realizado:",
                m.trabajo_realizado[:80],
                "",
                "",
            ])

        tabla = Table(bloque, colWidths=[90, 180, 60, 130])
        tabla.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#555")),
            ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#555")),
            ("BACKGROUND", (0, 0), (-1, 0), GRIS_CLARO),
            ("GRID", (0, 0), (-1, -1), 0.5, GRIS_MEDIO),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ]))
        elementos.append(tabla)

        # Repuestos usados debajo
        if repuestos:
            filas_rep = [["Repuestos Usados:", "Cant.", "Obs."]]
            for r in repuestos:
                repuesto = equipo_repo.get_by_id(r.repuesto_id)
                nombre_rep = repuesto.nombre if repuesto else "N/A"
                filas_rep.append([
                    nombre_rep,
                    str(r.cantidad_usada),
                    r.observacion or "",
                ])

            tabla_rep = Table(filas_rep, colWidths=[250, 50, 160])
            tabla_rep.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL_MEDIO),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, GRIS_MEDIO),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            elementos.append(Spacer(1, 3))
            elementos.append(tabla_rep)

        elementos.append(Spacer(1, 12))

    doc.build(
        elementos,
        onFirstPage=_header_footer,
        onLaterPages=_header_footer,
    )

    buffer.seek(0)
    return buffer


# ── LISTADO DE EQUIPOS PDF ──────────────────────────

def generar_listado_equipos_pdf(
    session: Session,
    area_id: uuid.UUID | None = None,
    clasificacion_id: uuid.UUID | None = None,
    estado: str | None = None,
    nivel: int | None = None,
) -> BytesIO:
    from app.repositories.equipo import EquipoRepository
    from app.repositories.area import AreaRepository
    from app.repositories.clasificacion import ClasificacionRepository

    equipo_repo = EquipoRepository(session)
    area_repo = AreaRepository(session)
    clasif_repo = ClasificacionRepository(session)

    equipos = equipo_repo.filter(
        area_id=area_id,
        clasificacion_id=clasificacion_id,
        estado=estado,
        nivel=nivel,
        limit=1000,
    )

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(letter),
        leftMargin=20, rightMargin=20,
        topMargin=50, bottomMargin=40,
    )
    estilos = _get_styles()
    elementos = []

    # ── Logo ──
    if os.path.exists(LOGO_PATH):
        page_width = doc.pagesize[0] - doc.leftMargin - doc.rightMargin
        logo = Image(LOGO_PATH, width=page_width, height=page_width * 360 / 2428)
        elementos.append(logo)
        elementos.append(Spacer(1, 4))

    # ── Barra azul con membreté ──
    elementos.append(_build_header_bar(doc, estilos))
    elementos.append(Spacer(1, 6))

    elementos.append(Paragraph("LISTADO DE EQUIPOS", estilos["TituloPrincipal"]))
    elementos.append(Paragraph(
        f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')} | "
        f"Total: {len(equipos)} equipos",
        estilos["Footer"],
    ))
    elementos.append(Spacer(1, 6))

    headers = ["Código", "Nombre", "Nivel", "Estado", "Clasificación", "Área", "Marca", "Modelo"]
    data = [headers]
    for eq in equipos:
        nombre_area = area_repo.get_by_id(eq.area_id).nombre if eq.area_id else ""
        nombre_clasif = clasif_repo.get_by_id(eq.clasificacion_id).nombre if eq.clasificacion_id else ""
        data.append([
            eq.codigo_equipo,
            eq.nombre,
            str(eq.nivel),
            eq.estado.value,
            nombre_clasif,
            nombre_area,
            eq.marca or "",
            eq.modelo or "",
        ])

    col_widths = [70, 160, 35, 70, 110, 110, 90, 90]
    tabla = Table(data, colWidths=col_widths, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL_OSCURO),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.5, GRIS_MEDIO),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elementos.append(tabla)

    doc.build(elementos, onFirstPage=_header_footer, onLaterPages=_header_footer)
    buffer.seek(0)
    return buffer


# ── LISTADO DE MANTENIMIENTOS PDF ───────────────────

def generar_listado_mantenimientos_pdf(
    session: Session,
    equipo_id: uuid.UUID | None = None,
    fecha_desde=None,
    fecha_hasta=None,
) -> BytesIO:
    from app.repositories.mantenimiento import MantenimientoRepository
    from app.repositories.equipo import EquipoRepository
    from app.repositories.usuario import UsuarioRepository

    mantto_repo = MantenimientoRepository(session)
    equipo_repo = EquipoRepository(session)
    usuario_repo = UsuarioRepository(session)

    if equipo_id:
        mantenimientos = mantto_repo.get_by_equipo(equipo_id, limit=1000)
    else:
        mantenimientos = mantto_repo.filter(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            limit=1000,
        )

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(letter),
        leftMargin=20, rightMargin=20,
        topMargin=50, bottomMargin=40,
    )
    estilos = _get_styles()
    elementos = []

    # ── Logo ──
    if os.path.exists(LOGO_PATH):
        page_width = doc.pagesize[0] - doc.leftMargin - doc.rightMargin
        logo = Image(LOGO_PATH, width=page_width, height=page_width * 360 / 2428)
        elementos.append(logo)
        elementos.append(Spacer(1, 4))

    # ── Barra azul con membreté ──
    elementos.append(_build_header_bar(doc, estilos))
    elementos.append(Spacer(1, 6))

    elementos.append(Paragraph("HISTORIAL DE MANTENIMIENTOS", estilos["TituloPrincipal"]))
    elementos.append(Paragraph(
        f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')} | "
        f"Total: {len(mantenimientos)} registros",
        estilos["Footer"],
    ))
    elementos.append(Spacer(1, 6))

    headers = ["Fecha", "Tipo", "Título", "Estado", "Equipo", "Código", "Realizado por"]
    data = [headers]
    for m in mantenimientos:
        equipo = equipo_repo.get_by_id(m.equipo_id)
        nombre_equipo = equipo.nombre if equipo else ""
        codigo_equipo = equipo.codigo_equipo if equipo else ""
        nombre_usuario = m.realizado_por if m.realizado_por else ""
        if not nombre_usuario and m.usuario_id:
            usuario = usuario_repo.get_by_id(m.usuario_id)
            nombre_usuario = usuario.nombre if usuario else ""

        data.append([
            str(m.fecha),
            m.tipo.value,
            m.titulo,
            m.estado.value,
            nombre_equipo,
            codigo_equipo,
            nombre_usuario,
        ])

    col_widths = [70, 65, 150, 65, 110, 65, 90]
    tabla = Table(data, colWidths=col_widths, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), VERDE_OSCURO),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.5, GRIS_MEDIO),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elementos.append(tabla)

    doc.build(elementos, onFirstPage=_header_footer, onLaterPages=_header_footer)
    buffer.seek(0)
    return buffer


# ── CATÁLOGO DE REPUESTOS PDF ───────────────────────

def generar_catalogo_repuestos_pdf(
    session: Session,
) -> BytesIO:
    from app.repositories.equipo import EquipoRepository

    equipo_repo = EquipoRepository(session)

    todos = equipo_repo.get_all(limit=5000)
    repuestos = [e for e in todos if e.nivel >= 4]

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(letter),
        leftMargin=20, rightMargin=20,
        topMargin=50, bottomMargin=40,
    )
    estilos = _get_styles()
    elementos = []

    # ── Logo ──
    if os.path.exists(LOGO_PATH):
        page_width = doc.pagesize[0] - doc.leftMargin - doc.rightMargin
        logo = Image(LOGO_PATH, width=page_width, height=page_width * 360 / 2428)
        elementos.append(logo)
        elementos.append(Spacer(1, 4))

    # ── Barra azul con membreté ──
    elementos.append(_build_header_bar(doc, estilos))
    elementos.append(Spacer(1, 6))

    elementos.append(Paragraph("CATÁLOGO DE REPUESTOS", estilos["TituloPrincipal"]))
    elementos.append(Paragraph(
        f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')} | "
        f"Total: {len(repuestos)} repuestos",
        estilos["Footer"],
    ))
    elementos.append(Spacer(1, 6))

    headers = ["Código", "Nombre", "Descripción", "Componente Padre", "Estado"]
    data = [headers]
    for r in repuestos:
        nombre_padre = ""
        if r.equipo_padre_id:
            padre = equipo_repo.get_by_id(r.equipo_padre_id)
            nombre_padre = padre.nombre if padre else ""
        data.append([
            r.codigo_equipo,
            r.nombre,
            (r.descripcion or "")[:80],
            nombre_padre,
            r.estado.value,
        ])

    col_widths = [70, 160, 200, 160, 70]
    tabla = Table(data, colWidths=col_widths, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), VERDE_OSCURO),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.5, GRIS_MEDIO),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elementos.append(tabla)

    doc.build(elementos, onFirstPage=_header_footer, onLaterPages=_header_footer)
    buffer.seek(0)
    return buffer
