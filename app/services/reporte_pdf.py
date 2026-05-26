import uuid
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

from app.repositories.equipo import EquipoRepository
from app.repositories.area import AreaRepository
from app.repositories.clasificacion import ClasificacionRepository
from app.repositories.mantenimiento import MantenimientoRepository
from app.repositories.foto import FotoRepository
from app.repositories.historial import HistorialRepository
from app.repositories.usuario import UsuarioRepository


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

    return styles


# ── COLORES CORPORATIVOS ────────────────────────────

VERDE_OSCURO = colors.HexColor("#2d5016")
VERDE_CLARO = colors.HexColor("#4a7c2e")
GRIS_CLARO = colors.HexColor("#f5f5f5")
GRIS_MEDIO = colors.HexColor("#e0e0e0")


# ── HEADER Y FOOTER DE PÁGINA ───────────────────────

def _header_footer(canvas, doc):
    canvas.saveState()

    # Header
    canvas.setFillColor(VERDE_OSCURO)
    canvas.rect(
        0, letter[1] - 40,
        letter[0], 40,
        fill=True,
        stroke=False,
    )
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(
        30,
        letter[1] - 28,
        "FICHAS TÉCNICAS - PALMA ACEITERA",
    )
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(
        letter[0] - 30,
        letter[1] - 28,
        f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
    )

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


# ── FICHA TÉCNICA INDIVIDUAL PDF ────────────────────

def generar_ficha_equipo_pdf(
    session: Session,
    equipo_id: uuid.UUID,
) -> BytesIO:
    """Genera PDF con la ficha técnica completa de un equipo."""

    equipo_repo = EquipoRepository(session)
    area_repo = AreaRepository(session)
    clasif_repo = ClasificacionRepository(session)
    foto_repo = FotoRepository(session)
    mantto_repo = MantenimientoRepository(session)
    historial_repo = HistorialRepository(session)
    usuario_repo = UsuarioRepository(session)

    equipo = equipo_repo.get_by_id(equipo_id)
    if not equipo:
        raise ValueError("Equipo no encontrado")

    # Resolver nombres
    nombre_area = ""
    if equipo.area_id:
        area = area_repo.get_by_id(equipo.area_id)
        nombre_area = area.nombre if area else ""

    nombre_clasif = ""
    if equipo.clasificacion_id:
        clasif = clasif_repo.get_by_id(equipo.clasificacion_id)
        nombre_clasif = clasif.nombre if clasif else ""

    nombre_padre = ""
    if equipo.equipo_padre_id:
        padre = equipo_repo.get_by_id(equipo.equipo_padre_id)
        nombre_padre = padre.nombre if padre else ""

    # Datos para el PDF
    hijos = equipo_repo.get_hijos_directos(equipo.id)
    mantenimientos = mantto_repo.get_by_equipo(equipo.id, limit=50)
    historial = historial_repo.get_by_equipo(equipo.id, limit=50)
    fotos = foto_repo.get_by_equipo(equipo.id)

    # Construir PDF
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

    # ── TÍTULO ──────────────────────────────────────
    elementos.append(
        Paragraph(
            f"FICHA TÉCNICA: {equipo.nombre}",
            styles["TituloPrincipal"],
        )
    )
    elementos.append(
        Paragraph(
            f"Código: {equipo.codigo_equipo} | "
            f"Nivel: {equipo.nivel}",
            styles["Subtitulo"],
        )
    )
    elementos.append(Spacer(1, 10))

    # ── DATOS GENERALES ─────────────────────────────
    elementos.append(
        Paragraph("DATOS GENERALES", styles["Subtitulo"]),
    )

    datos_generales = [
        ["Código:", equipo.codigo_equipo,
         "Nombre:", equipo.nombre],
        ["Clasificación:", nombre_clasif,
         "Área:", nombre_area],
        ["Equipo Padre:", nombre_padre or "N/A",
         "Nivel:", str(equipo.nivel)],
        ["Estado:", equipo.estado.value,
         "Motivo Estado:", equipo.motivo_estado or "N/A"],
        ["Descripción:", equipo.descripcion or "N/A", "", ""],
    ]

    tabla_datos = Table(
        datos_generales,
        colWidths=[80, 170, 80, 170],
    )
    tabla_datos.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#555")),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#555")),
        ("BACKGROUND", (0, 0), (-1, 0), GRIS_CLARO),
        ("BACKGROUND", (0, 2), (-1, 2), GRIS_CLARO),
        ("BACKGROUND", (0, 4), (-1, 4), GRIS_CLARO),
        ("GRID", (0, 0), (-1, -1), 0.5, GRIS_MEDIO),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elementos.append(tabla_datos)
    elementos.append(Spacer(1, 15))

    # ── DATOS DE PLACA ──────────────────────────────
    elementos.append(
        Paragraph("DATOS DE PLACA / DATASHEET", styles["Subtitulo"]),
    )

    datos_placa = [
        ["Marca:", equipo.marca or "N/A",
         "Modelo:", equipo.modelo or "N/A"],
        ["N° Serie:", equipo.numero_serie or "N/A",
         "Potencia:", equipo.potencia or "N/A"],
        ["Voltaje:", equipo.voltaje or "N/A",
         "RPM:", equipo.rpm or "N/A"],
        ["Capacidad:", equipo.capacidad or "N/A",
         "Año Fab.:", str(equipo.anio_fabricacion) if equipo.anio_fabricacion else "N/A"],
        ["Proveedor:", equipo.proveedor or "N/A",
         "Fecha Adq.:", str(equipo.fecha_adquisicion.date()) if equipo.fecha_adquisicion else "N/A"],
    ]

    tabla_placa = Table(
        datos_placa,
        colWidths=[80, 170, 80, 170],
    )
    tabla_placa.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#555")),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#555")),
        ("BACKGROUND", (0, 0), (-1, 0), GRIS_CLARO),
        ("BACKGROUND", (0, 2), (-1, 2), GRIS_CLARO),
        ("BACKGROUND", (0, 4), (-1, 4), GRIS_CLARO),
        ("GRID", (0, 0), (-1, -1), 0.5, GRIS_MEDIO),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elementos.append(tabla_placa)
    elementos.append(Spacer(1, 15))

    # ── SUB-EQUIPOS ─────────────────────────────────
    if hijos:
        elementos.append(
            Paragraph(
                f"SUB-EQUIPOS / COMPONENTES ({len(hijos)})",
                styles["Subtitulo"],
            ),
        )

        header_hijos = [
            "Código", "Nombre", "Nivel",
            "Estado", "Marca",
        ]
        filas_hijos = [header_hijos]
        for h in hijos:
            filas_hijos.append([
                h.codigo_equipo,
                h.nombre,
                str(h.nivel),
                h.estado.value,
                h.marca or "N/A",
            ])

        tabla_hijos = Table(
            filas_hijos,
            colWidths=[100, 180, 40, 80, 100],
        )
        tabla_hijos.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), VERDE_OSCURO),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, GRIS_MEDIO),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elementos.append(tabla_hijos)
        elementos.append(Spacer(1, 15))

    # ── MANTENIMIENTOS ──────────────────────────────
    if mantenimientos:
        elementos.append(
            Paragraph(
                f"HISTORIAL DE MANTENIMIENTOS ({len(mantenimientos)})",
                styles["Subtitulo"],
            ),
        )

        header_mantto = [
            "Fecha", "Tipo", "Título", "Estado",
        ]
        filas_mantto = [header_mantto]
        for m in mantenimientos:
            filas_mantto.append([
                str(m.fecha),
                m.tipo.value,
                m.titulo[:40],
                m.estado.value,
            ])

        tabla_mantto = Table(
            filas_mantto,
            colWidths=[70, 80, 220, 80],
        )
        tabla_mantto.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), VERDE_OSCURO),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, GRIS_MEDIO),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elementos.append(tabla_mantto)
        elementos.append(Spacer(1, 15))

    # ── HISTORIAL DE CAMBIOS ────────────────────────
    if historial:
        elementos.append(
            Paragraph(
                f"HISTORIAL DE CAMBIOS ({len(historial)})",
                styles["Subtitulo"],
            ),
        )

        header_hist = [
            "Fecha", "Campo", "Anterior", "Nuevo",
        ]
        filas_hist = [header_hist]
        for h in historial:
            usuario = None
            if h.usuario_id:
                usuario = usuario_repo.get_by_id(h.usuario_id)

            filas_hist.append([
                str(h.fecha.date()),
                h.campo,
                (h.valor_anterior or "N/A")[:25],
                (h.valor_nuevo or "N/A")[:25],
            ])

        tabla_hist = Table(
            filas_hist,
            colWidths=[70, 100, 150, 150],
        )
        tabla_hist.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), VERDE_OSCURO),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, GRIS_MEDIO),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elementos.append(tabla_hist)

    # ── OBSERVACIONES ───────────────────────────────
    if equipo.observaciones:
        elementos.append(Spacer(1, 15))
        elementos.append(
            Paragraph("OBSERVACIONES", styles["Subtitulo"]),
        )
        elementos.append(
            Paragraph(equipo.observaciones, styles["Valor"]),
        )

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
    elementos.append(Spacer(1, 15))

    for m in mantenimientos:
        # Nombre del técnico
        nombre_tecnico = "N/A"
        if m.usuario_id:
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
                ("BACKGROUND", (0, 0), (-1, 0), VERDE_CLARO),
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
