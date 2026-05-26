import os
import uuid
from pathlib import Path

from app.core.config import settings


# ── INICIALIZACIÓN ──────────────────────────────────

def configure_storage() -> None:
    """Configura el modo de almacenamiento al iniciar."""
    if settings.STORAGE_MODE == "cloudinary":
        _configure_cloudinary()
    else:
        _configure_local()


def _configure_cloudinary() -> None:
    import cloudinary
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )


def _configure_local() -> None:
    Path(settings.LOCAL_UPLOAD_DIR).mkdir(
        exist_ok=True,
    )


# ── UPLOAD ──────────────────────────────────────────

def upload_image(
    file_bytes: bytes,
    folder: str = "fichas-tecnicas",
    filename: str | None = None,
) -> dict:
    """
    Sube una imagen según el modo configurado.

    Returns:
        dict con url, public_id (o local path), thumbnail_url
    """
    if settings.STORAGE_MODE == "cloudinary":
        return _upload_cloudinary(file_bytes, folder)
    else:
        return _upload_local(file_bytes, folder, filename)


def _upload_cloudinary(file_bytes: bytes, folder: str) -> dict:
    import cloudinary.uploader
    from cloudinary import CloudinaryImage

    result = cloudinary.uploader.upload(
        file_bytes,
        folder=folder,
        transformation=[
            {"width": 1200, "height": 1200, "crop": "limit"},
            {"quality": "auto"},
        ],
    )

    thumbnail_url = CloudinaryImage(
        result["public_id"],
    ).build_url(
        width=300,
        height=300,
        crop="fill",
        quality="auto",
    )

    return {
        "public_id": result["public_id"],
        "url": result["secure_url"],
        "thumbnail_url": thumbnail_url,
    }


def _upload_local(
    file_bytes: bytes,
    folder: str,
    filename: str | None = None,
) -> dict:
    """Guarda archivo localmente en ./uploads/"""
    # Crear subcarpeta
    upload_dir = Path(settings.LOCAL_UPLOAD_DIR) / folder
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Generar nombre único
    ext = ".jpg"
    if filename and "." in filename:
        ext = "." + filename.rsplit(".", 1)[-1]

    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = upload_dir / unique_name

    # Guardar archivo
    file_path.write_bytes(file_bytes)

    # Construir URL local
    relative_path = f"{folder}/{unique_name}"
    url = f"/uploads/{relative_path}"

    return {
        "public_id": relative_path,
        "url": url,
        "thumbnail_url": url,  # En local usamos la misma
    }


# ── DELETE ──────────────────────────────────────────

def delete_image(public_id: str) -> bool:
    """Elimina una imagen según el modo configurado."""
    if settings.STORAGE_MODE == "cloudinary":
        return _delete_cloudinary(public_id)
    else:
        return _delete_local(public_id)


def _delete_cloudinary(public_id: str) -> bool:
    import cloudinary.uploader
    result = cloudinary.uploader.destroy(public_id)
    return result.get("result") == "ok"


def _delete_local(public_id: str) -> bool:
    """Elimina archivo local."""
    file_path = Path(settings.LOCAL_UPLOAD_DIR) / public_id
    if file_path.exists():
        file_path.unlink()
        return True
    return False
