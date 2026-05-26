from sqlmodel import SQLModel, Session, create_engine

from app.core.config import settings

# Engine
# Para SQLite necesitamos connect_args
# Para PostgreSQL no
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args=connect_args,
)


def create_db_and_tables() -> None:
    """Crea todas las tablas definidas en los modelos."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency de FastAPI para obtener una sesión de BD."""
    with Session(engine) as session:
        yield session
