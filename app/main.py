from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.db import run_migrations
from app.core.storage import configure_storage


def create_app() -> FastAPI:

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── CORS ────────────────────────────────────────
    origins = [
        origin.strip()
        for origin in settings.CORS_ORIGINS.split(",")
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Registrar rutas ─────────────────────────────
    from app.api.router import api_router

    app.include_router(
        api_router,
        prefix="/api/v1",
    )

    # ── Startup ─────────────────────────────────────
    @app.on_event("startup")
    def on_startup():
        run_migrations()
        configure_storage()

    # ── Health check ────────────────────────────────
    @app.get("/health", tags=["Sistema"])
    def health_check():
        return {
            "status": "ok",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "storage": settings.STORAGE_MODE,
        }

    return app


app = create_app()
