import uuid
from io import BytesIO

import qrcode
from qrcode.image.pil import PilImage
from PIL import Image, ImageDraw, ImageFont
from sqlmodel import Session

from app.core.config import settings
from app.repositories.equipo import EquipoRepository
from app.repositories.area import AreaRepository
from app.repositories.clasificacion import ClasificacionRepository


def generar_qr_equipo(
    session: Session,
    equipo_id: uuid.UUID,
) -> BytesIO:
    """
    Genera imagen QR con la URL de la ficha técnica.
    El QR incluye el logo/nombre del equipo centrado.
    """

    equipo_repo = EquipoRepository(session)
    area_repo = AreaRepository(session)
    clasif_repo = ClasificacionRepository(session)

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

    # URL que codifica el QR
    qr_url = f"{settings.BASE_URL}/equipo/{equipo.id}"

    # ── Generar QR ──────────────────────────────────
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_url)
    qr.make(fit=True)

    qr_img = qr.make_image(
        fill_color="#2d5016",
        back_color="white",
    ).convert("RGB")

    # ── Crear imagen final con info ─────────────────
    ancho_qr = qr_img.size[0]
    alto_info = 120
    alto_total = qr_img.size[1] + alto_info

    # Imagen final
    img_final = Image.new(
        "RGB",
        (ancho_qr, alto_total),
        "white",
    )

    # Pegar QR
    img_final.paste(qr_img, (0, 0))

    # Dibujar info debajo del QR
    draw = ImageDraw.Draw(img_final)

    # Intentar usar fuente del sistema
    try:
        fuente_bold = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            18,
        )
        fuente_normal = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            14,
        )
        fuente_peq = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            12,
        )
    except (OSError, IOError):
        fuente_bold = ImageFont.load_default()
        fuente_normal = ImageFont.load_default()
        fuente_peq = ImageFont.load_default()

    # Línea verde decorativa
    y_qr = qr_img.size[1]
    draw.rectangle(
        [(0, y_qr), (ancho_qr, y_qr + 4)],
        fill="#2d5016",
    )

    # Código del equipo
    draw.text(
        (20, y_qr + 12),
        equipo.codigo_equipo,
        fill="#2d5016",
        font=fuente_bold,
    )

    # Nombre del equipo
    nombre_corto = equipo.nombre[:35]
    if len(equipo.nombre) > 35:
        nombre_corto += "..."
    draw.text(
        (20, y_qr + 38),
        nombre_corto,
        fill="#333333",
        font=fuente_normal,
    )

    # Clasificación y área
    info_extra = []
    if nombre_clasif:
        info_extra.append(nombre_clasif)
    if nombre_area:
        info_extra.append(nombre_area)
    info_text = " | ".join(info_extra)

    draw.text(
        (20, y_qr + 60),
        info_text,
        fill="#777777",
        font=fuente_peq,
    )

    # Estado con color
    estado_colores = {
        "OPERATIVO": "#2d8a2d",
        "PARADO": "#cc3333",
        "REPARACION": "#cc8800",
        "BAJA": "#666666",
    }
    estado_color = estado_colores.get(
        equipo.estado.value,
        "#333333",
    )
    draw.text(
        (20, y_qr + 82),
        f"Estado: {equipo.estado.value}",
        fill=estado_color,
        font=fuente_peq,
    )

    # Marca / modelo
    if equipo.marca:
        marca_modelo = equipo.marca
        if equipo.modelo:
            marca_modelo += f" {equipo.modelo}"
        draw.text(
            (20, y_qr + 100),
            marca_modelo,
            fill="#999999",
            font=fuente_peq,
        )

    # ── Guardar en buffer ───────────────────────────
    buffer = BytesIO()
    img_final.save(buffer, format="PNG", quality=95)
    buffer.seek(0)

    return buffer


def generar_qr_masivo(
    session: Session,
    equipo_ids: list[uuid.UUID],
) -> BytesIO:
    """
    Genera una hoja con múltiples QR codes
    para imprimir en etiquetas.
    """

    qr_buffers = []
    for eq_id in equipo_ids:
        try:
            buf = generar_qr_equipo(session, eq_id)
            img = Image.open(buf)
            qr_buffers.append(img)
        except ValueError:
            continue

    if not qr_buffers:
        raise ValueError("No se generaron QR codes")

    # Layout: 2 columnas
    cols = 2
    ancho_qr = qr_buffers[0].size[0]
    alto_qr = qr_buffers[0].size[1]
    margen = 20

    filas = (len(qr_buffers) + cols - 1) // cols
    ancho_hoja = (ancho_qr * cols) + (margen * (cols + 1))
    alto_hoja = (alto_qr * filas) + (margen * (filas + 1)) + 60

    hoja = Image.new("RGB", (ancho_hoja, alto_hoja), "white")
    draw = ImageDraw.Draw(hoja)

    try:
        fuente_titulo = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            20,
        )
    except (OSError, IOError):
        fuente_titulo = ImageFont.load_default()

    # Título
    draw.text(
        (margen, 15),
        "FICHAS TÉCNICAS - CÓDIGOS QR",
        fill="#2d5016",
        font=fuente_titulo,
    )
    draw.rectangle(
        [(margen, 45), (ancho_hoja - margen, 47)],
        fill="#2d5016",
    )

    # Pegar QRs
    y_inicio = 60
    for i, qr_img in enumerate(qr_buffers):
        col = i % cols
        fila = i // cols
        x = margen + (col * (ancho_qr + margen))
        y = y_inicio + (fila * (alto_qr + margen))
        hoja.paste(qr_img, (x, y))

    buffer = BytesIO()
    hoja.save(buffer, format="PNG", quality=95)
    buffer.seek(0)

    return buffer
