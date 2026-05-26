from sqlmodel import SQLModel, Session, create_engine

from app.core.config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args=connect_args,
    # Importante para serverless: conexiones efímeras
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=2,
)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def run_migrations() -> None:
    """Ejecuta alembic upgrade head."""
    import subprocess
    import os

    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )
        if result.returncode == 0:
            print(f"Migraciones: {result.stdout.strip()}")
        else:
            print(f"Error migraciones: {result.stderr.strip()}")
    except Exception as e:
        print(f"Migraciones no ejecutadas: {e}")


def get_session():
    with Session(engine) as session:
        yield session
