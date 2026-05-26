from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── App ─────────────────────────────────────────
    APP_NAME: str = "Fichas Técnicas - Palma Aceitera"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ── Database ────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./fichas_tecnicas.db"

    # ── JWT ─────────────────────────────────────────
    SECRET_KEY: str = "cambiar-esta-clave-en-produccion"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 480

    # ── Cloudinary ──────────────────────────────────
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # ── Storage ─────────────────────────────────────
    STORAGE_MODE: str = "local"
    LOCAL_UPLOAD_DIR: str = "uploads"

    # ── URL base para QR codes ──────────────────────
    BASE_URL: str = "http://localhost:8000"

    # ── CORS ────────────────────────────────────────
    CORS_ORIGINS: str = "*"


settings = Settings()
